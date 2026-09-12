# © 2026 Martín Viera. Todos los derechos reservados.
"""Respaldo y restauración de la base, en un solo archivo que se puede guardar.

## Por qué esto existe, y por qué no alcanzaba con exportar

`mvpm/exporters.py` exporta las tablas **derivadas** —proyectos y tareas a
CSV, Excel o JSON— y eso no es un respaldo: deja afuera los usuarios, el
historial completo de `versiones` (que es donde vive la gobernanza y que por
diseño nunca se pisa), el organigrama y el registro de accesos. Y sobre todo:
no se puede volver atrás con eso. Un respaldo del que no se puede restaurar es
una lista de datos, no un respaldo.

El caso real: el portafolio entero de un cliente vive en UN archivo SQLite
dentro de su VM. Si ese disco se pierde, se pierde todo, y el producto no
ofrecía ni sacar una copia ni volver de ella.

## Por qué no se copia el archivo a mano

Porque se probó y **pierde datos en silencio**, que es la peor forma de
fallar. La base corre en modo WAL: las transacciones recientes viven en
`datos.db-wal` hasta que SQLite hace checkpoint. Copiar sólo `datos.db` con la
aplicación abierta produce un archivo que:

  · abre sin ningún error,
  · pasa cualquier chequeo de integridad,
  · y **no tiene lo último que se guardó**.

Medido: con la app corriendo, un dato guardado justo antes de copiar no
aparecía en la copia. Nadie se entera hasta el día que hay que restaurar.

Acá se usa `sqlite3.Connection.backup()`, la API de respaldo en caliente de
SQLite: toma una instantánea coherente aunque haya gente escribiendo, e
incluye lo que está en el WAL. El resultado es un `.db` único y autosuficiente
— sin `-wal` ni `-shm` al lado que haya que acordarse de copiar también.

## Por qué se verifica ANTES de restaurar

Restaurar es la única operación del producto que **destruye** datos: pisa la
base del cliente. Un archivo corrupto, truncado a medio descargar, o
directamente de otro programa, no puede llegar a pisar nada. Por eso
`restaurar()` exige que el archivo pase `verificar()` primero, y además guarda
la base que estaba como `datos.db.antes-de-restaurar-<fecha>`: equivocarse de
archivo tiene que ser reversible, no terminal.
"""

from __future__ import annotations

import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from . import db

#: Tablas que tiene que traer un archivo para ser una base de este producto.
#: No es la lista completa a propósito: si se agrega una tabla nueva, un
#: respaldo hecho con la versión anterior tiene que poder restaurarse igual.
#: Éstas son las que, si faltan, garantizan que el archivo no es de acá.
TABLAS_MINIMAS = ("usuarios", "proyectos", "tareas", "empresas", "versiones")

#: Lo que se le muestra al usuario como resumen de lo que hay adentro.
TABLAS_A_CONTAR = ("usuarios", "proyectos", "tareas", "empresas", "versiones",
                   "organigrama_personas")

# ------------------------------------------------------------------ cifrado
#
# Un respaldo del portafolio de un cliente en un pendrive ES el portafolio del
# cliente en un pendrive. Por eso se puede cifrar con una frase — opcional, y
# opcional a propósito: cifrar introduce una forma NUEVA de perder los datos
# (frase olvidada = respaldo inservible), así que la decisión es de quien
# conoce su situación, no del programa.
#
# El archivo cifrado arranca con una marca propia. Sin eso, `verificar()`
# diría "no es una base SQLite" ante un respaldo perfectamente válido, y quien
# lo hizo concluiría que se le corrompió el archivo en vez de que le falta la
# frase. Un mensaje equivocado en ese momento es lo que hace que alguien tire
# un respaldo bueno.

#: Primeros bytes de un respaldo cifrado. Lleva versión para poder cambiar el
#: esquema sin que los archivos viejos dejen de reconocerse.
MARCA_CIFRADO = b"MVPMBK1\n"

#: Iteraciones para derivar la clave de la frase. Mismo criterio que el login
#: (`mvpm/auth.py`): hace costoso probar frases a lo bruto sobre un archivo
#: robado, que es justo el escenario del pendrive perdido.
_ITERACIONES_FRASE = 200_000
_LARGO_SAL = 16


def esta_cifrado(datos: bytes) -> bool:
    return datos.startswith(MARCA_CIFRADO)


def _clave_desde(frase: str, sal: bytes) -> bytes:
    import base64
    import hashlib

    return base64.urlsafe_b64encode(hashlib.pbkdf2_hmac(
        "sha256", frase.encode("utf-8"), sal, _ITERACIONES_FRASE))


def _cifrar(datos: bytes, frase: str) -> bytes:
    import secrets

    from cryptography.fernet import Fernet

    sal = secrets.token_bytes(_LARGO_SAL)
    token = Fernet(_clave_desde(frase, sal)).encrypt(datos)
    return MARCA_CIFRADO + sal + token


def _descifrar(datos: bytes, frase: str | None) -> bytes:
    """Devuelve el contenido en claro. Lanza ValueError con un motivo legible.

    Los dos errores se distinguen a propósito: "falta la frase" y "la frase no
    es ésta" llevan a acciones distintas, y decir sólo "no se pudo abrir" hace
    que alguien descarte un respaldo que está entero.
    """
    from cryptography.fernet import Fernet, InvalidToken

    if not frase:
        raise ValueError("El respaldo está cifrado: hace falta la frase.")
    sal = datos[len(MARCA_CIFRADO):len(MARCA_CIFRADO) + _LARGO_SAL]
    token = datos[len(MARCA_CIFRADO) + _LARGO_SAL:]
    try:
        return Fernet(_clave_desde(frase, sal)).decrypt(token)
    except InvalidToken:
        raise ValueError("La frase no coincide con la de este respaldo.") from None


def _en_claro(origen: str | Path | bytes, frase: str | None) -> bytes:
    """Los bytes de la base, venga el origen cifrado o no."""
    datos = origen if isinstance(origen, bytes) else Path(origen).read_bytes()
    return _descifrar(datos, frase) if esta_cifrado(datos) else datos


def nombre_sugerido(ahora: datetime | None = None) -> str:
    """Nombre de archivo con fecha y hora, para que dos respaldos no se pisen."""
    ahora = ahora or datetime.now(timezone.utc)
    return f"mvpm_respaldo_{ahora.strftime('%Y-%m-%d_%H%M')}.db"


def crear(destino: str | Path) -> Path:
    """Escribe una instantánea coherente de la base en `destino`.

    Funciona con la aplicación abierta y gente escribiendo: es el punto de
    usar la API de respaldo de SQLite en vez de copiar el archivo.
    """
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    origen = sqlite3.connect(db._DB_FILE)
    try:
        copia = sqlite3.connect(destino)
        try:
            origen.backup(copia)
            # El respaldo hereda el modo WAL del original y queda con un
            # `-wal` y un `-shm` al lado. El `.db` solo YA está completo —se
            # verificó—, pero una carpeta de respaldos con tres archivos por
            # copia invita a llevarse el equivocado o a dudar de cuál importa.
            # Pasar a DELETE hace checkpoint y borra los dos archivos sueltos:
            # queda un único archivo que se manda por mail y listo.
            copia.execute("PRAGMA journal_mode = DELETE")
        finally:
            copia.close()
    finally:
        origen.close()
    return destino


def a_bytes(frase: str | None = None) -> bytes:
    """El respaldo como bytes, para ofrecerlo como descarga en el navegador.

    Con `frase`, el resultado sale cifrado. Pasa por un archivo temporal
    porque la API de SQLite escribe en un archivo, no en memoria; el temporal
    se borra siempre, incluso si algo falla.
    """
    tmp = Path(tempfile.mkdtemp(prefix="mvpm_respaldo_")) / "respaldo.db"
    try:
        crear(tmp)
        crudo = tmp.read_bytes()
        return _cifrar(crudo, frase) if frase else crudo
    finally:
        shutil.rmtree(tmp.parent, ignore_errors=True)


def verificar(origen: str | Path | bytes, frase: str | None = None) -> dict:
    """¿Este archivo es una base de este producto y está sana?

    Devuelve `{"valido", "motivo", "conteos", "cifrado"}`. No lanza excepción
    ante un archivo cualquiera: que alguien suba un PDF por error es un caso
    esperable, no un error del programa.

    `cifrado` viaja aparte del motivo para que la pantalla pueda pedir la
    frase en vez de mostrar un error: un respaldo cifrado sin frase no está
    roto, le falta un dato.
    """
    tmpdir = None
    try:
        if not isinstance(origen, bytes) and not Path(origen).exists():
            return {"valido": False, "motivo": "El archivo no existe.",
                    "conteos": {}, "cifrado": False}
        crudos = origen if isinstance(origen, bytes) else Path(origen).read_bytes()
        cifrado = esta_cifrado(crudos)
        if cifrado:
            try:
                crudos = _descifrar(crudos, frase)
            except ValueError as e:
                return {"valido": False, "motivo": str(e), "conteos": {}, "cifrado": True}

        tmpdir = Path(tempfile.mkdtemp(prefix="mvpm_verificar_"))
        ruta = tmpdir / "candidato.db"
        ruta.write_bytes(crudos)
        del crudos

        try:
            conn = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)
        except sqlite3.Error as e:
            return {"valido": False, "motivo": f"No se pudo abrir: {e}",
                    "conteos": {}, "cifrado": cifrado}
        try:
            try:
                estado = conn.execute("PRAGMA integrity_check").fetchone()[0]
            except sqlite3.DatabaseError:
                return {"valido": False,
                        "motivo": "El archivo no es una base SQLite.",
                        "conteos": {}, "cifrado": cifrado}
            if estado != "ok":
                return {"valido": False,
                        "motivo": f"La base está dañada ({estado}).",
                        "conteos": {}, "cifrado": cifrado}

            presentes = {f[0] for f in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            faltan = [t for t in TABLAS_MINIMAS if t not in presentes]
            if faltan:
                return {"valido": False,
                        "motivo": ("El archivo es una base SQLite pero no de "
                                   f"este programa: faltan {', '.join(faltan)}."),
                        "conteos": {}, "cifrado": cifrado}

            conteos = {}
            for tabla in TABLAS_A_CONTAR:
                if tabla in presentes:
                    conteos[tabla] = conn.execute(
                        f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]  # noqa: S608
            return {"valido": True, "motivo": None, "conteos": conteos, "cifrado": cifrado}
        finally:
            conn.close()
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


def restaurar(origen: str | Path | bytes, frase: str | None = None,
              ahora: datetime | None = None) -> dict:
    """Reemplaza la base por la del respaldo. Devuelve qué quedó y dónde.

    Es la única operación que destruye datos, así que:

      1. exige que el archivo pase `verificar()` — un corrupto o uno de otro
         programa no llega a tocar nada;
      2. guarda la base actual al lado antes de pisarla, con fecha en el
         nombre. Equivocarse de archivo tiene que ser reversible.
    """
    revision = verificar(origen, frase)
    if not revision["valido"]:
        raise ValueError(revision["motivo"])

    ahora = ahora or datetime.now(timezone.utc)
    actual = Path(db._DB_FILE)
    actual.parent.mkdir(parents=True, exist_ok=True)

    copia_previa = None
    if actual.exists():
        copia_previa = actual.with_name(
            f"{actual.name}.antes-de-restaurar-{ahora.strftime('%Y-%m-%d_%H%M%S')}")
        shutil.copyfile(actual, copia_previa)

    tmpdir = Path(tempfile.mkdtemp(prefix="mvpm_restaurar_"))
    try:
        # Siempre por el temporal: si el respaldo venía cifrado, lo que hay
        # que restaurar es el contenido en claro, no el archivo tal cual.
        # `verificar()` ya confirmó arriba que la frase es la correcta.
        ruta = tmpdir / "nuevo.db"
        ruta.write_bytes(_en_claro(origen, frase))

        # Se escribe con la API de respaldo y no con un copyfile: así los
        # `-wal`/`-shm` que pudieran estar al lado de la base vieja quedan
        # coherentes con el contenido nuevo. Copiar el archivo encima dejaría
        # un WAL viejo apuntando a datos que ya no están.
        nuevo = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)
        try:
            destino = sqlite3.connect(actual)
            try:
                nuevo.backup(destino)
            finally:
                destino.close()
        finally:
            nuevo.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    return {"conteos": revision["conteos"],
            "copia_previa": str(copia_previa) if copia_previa else None}


# ------------------------------------------------- respaldo automático

#: Dónde van los respaldos que se hacen solos, dentro de la carpeta de datos:
#: si el dato del cliente no sale de su máquina, la copia tampoco.
CARPETA_AUTOMATICOS = "respaldos"

#: Cuántos automáticos se conservan. Sin un tope, la carpeta crece hasta
#: llenar el disco de la VM del cliente — y un disco lleno deja de guardar el
#: trabajo del día, o sea que el respaldo termina causando la pérdida que
#: venía a evitar.
RETENER = 7

#: Ídem para las copias que deja `restaurar()`. Se conservan menos porque
#: pesan lo mismo que la base entera y sólo sirven para deshacer una
#: restauración reciente.
RETENER_PREVIAS = 3

#: Cada cuánto corresponde uno nuevo.
CADA_HORAS = 24


def carpeta_automaticos() -> Path:
    return Path(db._DB_FILE).parent / CARPETA_AUTOMATICOS


def listar_automaticos() -> list[Path]:
    """Del más nuevo al más viejo."""
    carpeta = carpeta_automaticos()
    if not carpeta.exists():
        return []
    return sorted(carpeta.glob("mvpm_respaldo_*.db*"),
                  key=lambda p: p.stat().st_mtime, reverse=True)


def toca_respaldar(cada_horas: int = CADA_HORAS, ahora: datetime | None = None) -> bool:
    """¿Pasó suficiente tiempo desde el último automático?"""
    hechos = listar_automaticos()
    if not hechos:
        return True
    ahora = ahora or datetime.now(timezone.utc)
    ultimo = datetime.fromtimestamp(hechos[0].stat().st_mtime, tz=timezone.utc)
    return (ahora - ultimo).total_seconds() >= cada_horas * 3600


def purgar(retener: int = RETENER) -> list[Path]:
    """Borra los automáticos más viejos. Devuelve los que borró."""
    sobran = listar_automaticos()[retener:]
    for viejo in sobran:
        viejo.unlink(missing_ok=True)
    return sobran


def purgar_previas(retener: int = RETENER_PREVIAS) -> list[Path]:
    """Ídem con las copias que deja una restauración."""
    actual = Path(db._DB_FILE)
    previas = sorted(actual.parent.glob(f"{actual.name}.antes-de-restaurar-*"),
                     key=lambda p: p.stat().st_mtime, reverse=True)
    for viejo in previas[retener:]:
        viejo.unlink(missing_ok=True)
    return previas[retener:]


def automatico(frase: str | None = None, cada_horas: int = CADA_HORAS,
               forzar: bool = False, ahora: datetime | None = None) -> Path | None:
    """Hace un respaldo si toca, rota los viejos y devuelve el archivo nuevo.

    Devuelve None cuando todavía no corresponde — así el que llama puede
    invocarlo en cada arranque sin preguntar nada.

    Pensado para dos usos:

      · un `cron` o el Programador de tareas del cliente, vía
        `python -m mvpm.respaldo`, que es la forma que de verdad sirve;
      · el arranque de la aplicación, como red de seguridad para cuando nadie
        configuró el cron. No lo reemplaza: si el servidor pasa una semana sin
        que nadie abra el tablero, tampoco hay respaldo.
    """
    ahora = ahora or datetime.now(timezone.utc)
    if not forzar and not toca_respaldar(cada_horas, ahora):
        return None

    carpeta = carpeta_automaticos()
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / nombre_sugerido(ahora)
    if frase:
        # Cifrado: se arma en claro aparte y se escribe ya cifrado, para que
        # el archivo en claro no llegue a existir en la carpeta de respaldos.
        destino = destino.with_suffix(".db.cifrado")
        destino.write_bytes(a_bytes(frase))
    else:
        crear(destino)

    purgar()
    purgar_previas()
    return destino


def _main(argv: list[str] | None = None) -> int:
    """`python -m mvpm.respaldo` — para el cron del cliente.

    La frase de cifrado se toma de `MVPM_RESPALDO_FRASE` y nunca de un
    argumento: lo que se pasa por línea de comandos queda en el historial del
    shell y en la lista de procesos, a la vista de cualquiera en esa máquina.
    """
    import argparse
    import os

    p = argparse.ArgumentParser(
        description="Respaldo automático de MV Project Management.")
    p.add_argument("--forzar", action="store_true",
                   help="Respaldar aunque no hayan pasado las horas.")
    p.add_argument("--cada-horas", type=int, default=CADA_HORAS)
    args = p.parse_args(argv)

    hecho = automatico(frase=os.environ.get("MVPM_RESPALDO_FRASE") or None,
                       cada_horas=args.cada_horas, forzar=args.forzar)
    if hecho is None:
        print("Todavía no corresponde un respaldo nuevo.")
    else:
        print(f"Respaldo: {hecho} ({hecho.stat().st_size / 1024:.0f} KB)")
        print(f"Se conservan los últimos {RETENER}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
