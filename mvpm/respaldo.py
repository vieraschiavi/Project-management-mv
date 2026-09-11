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


def a_bytes() -> bytes:
    """El respaldo como bytes, para ofrecerlo como descarga en el navegador.

    Pasa por un archivo temporal porque la API de SQLite escribe en un archivo,
    no en memoria; el temporal se borra siempre, incluso si algo falla.
    """
    tmp = Path(tempfile.mkdtemp(prefix="mvpm_respaldo_")) / "respaldo.db"
    try:
        crear(tmp)
        return tmp.read_bytes()
    finally:
        shutil.rmtree(tmp.parent, ignore_errors=True)


def verificar(origen: str | Path | bytes) -> dict:
    """¿Este archivo es una base de este producto y está sana?

    Devuelve `{"valido": bool, "motivo": str | None, "conteos": dict}`. No
    lanza excepción ante un archivo cualquiera: que alguien suba un PDF por
    error es un caso esperable, no un error del programa.
    """
    tmpdir = None
    try:
        if isinstance(origen, bytes):
            tmpdir = Path(tempfile.mkdtemp(prefix="mvpm_verificar_"))
            ruta = tmpdir / "candidato.db"
            ruta.write_bytes(origen)
        else:
            ruta = Path(origen)
            if not ruta.exists():
                return {"valido": False, "motivo": "El archivo no existe.",
                        "conteos": {}}

        try:
            conn = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)
        except sqlite3.Error as e:
            return {"valido": False, "motivo": f"No se pudo abrir: {e}",
                    "conteos": {}}
        try:
            try:
                estado = conn.execute("PRAGMA integrity_check").fetchone()[0]
            except sqlite3.DatabaseError:
                return {"valido": False,
                        "motivo": "El archivo no es una base SQLite.",
                        "conteos": {}}
            if estado != "ok":
                return {"valido": False,
                        "motivo": f"La base está dañada ({estado}).",
                        "conteos": {}}

            presentes = {f[0] for f in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            faltan = [t for t in TABLAS_MINIMAS if t not in presentes]
            if faltan:
                return {"valido": False,
                        "motivo": ("El archivo es una base SQLite pero no de "
                                   f"este programa: faltan {', '.join(faltan)}."),
                        "conteos": {}}

            conteos = {}
            for tabla in TABLAS_A_CONTAR:
                if tabla in presentes:
                    conteos[tabla] = conn.execute(
                        f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]  # noqa: S608
            return {"valido": True, "motivo": None, "conteos": conteos}
        finally:
            conn.close()
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


def restaurar(origen: str | Path | bytes, ahora: datetime | None = None) -> dict:
    """Reemplaza la base por la del respaldo. Devuelve qué quedó y dónde.

    Es la única operación que destruye datos, así que:

      1. exige que el archivo pase `verificar()` — un corrupto o uno de otro
         programa no llega a tocar nada;
      2. guarda la base actual al lado antes de pisarla, con fecha en el
         nombre. Equivocarse de archivo tiene que ser reversible.
    """
    revision = verificar(origen)
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
        if isinstance(origen, bytes):
            ruta = tmpdir / "nuevo.db"
            ruta.write_bytes(origen)
        else:
            ruta = Path(origen)

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
