"""Activa el modo dueño en ESTA máquina, sin pedirle nada al que lo corre.

Es lo que ejecutan `./run.sh owner` y `MV_ProjectManagement_OWNER.bat`. La
promesa es un doble clic: si falta algo, lo resuelve solo en vez de imprimir
instrucciones para que las haga una persona.

## Cómo resuelve la clave privada, en orden

1. **Variable de entorno** `MVPM_LICENSE_PRIVATE_KEY`, si está.
2. **Archivo local** `~/.mv_project_management/clave_privada_owner`, donde este
   mismo script la dejó la primera vez. Por esto sólo hace falta correrlo una
   vez por máquina: después ya no hay nada que configurar nunca más.
3. **La genera él mismo**, y de paso pega la clave pública en
   `mvpm/licensing.py`. Sólo desde un checkout del repo, y una única vez.
4. **Se la pide a quien lo corre**, en una instalación descargada: por
   `--clave`, por un `clave_owner.txt` al lado del programa, o pegándola en la
   consola. Se guarda en (2) y no se vuelve a preguntar en esa máquina.

El paso 4 existe porque el dueño también usa el ZIP y el instalador, no sólo su
checkout: antes esa copia se negaba y lo mandaba a "instalá la Owner Edition",
que es justo lo que no siempre tiene a mano. Traer una clave que ya existe no
es lo mismo que fabricar una nueva — un cliente no tiene ninguna que traer.

## Por qué el paso 3 no reabre el agujero que cerramos

Generar un par de claves a demanda sería exactamente el bypass viejo si
cualquiera pudiera hacerlo: un cliente correría esto, se autogeneraría un par,
se pegaría su propia clave pública y entraría sin pagar.

El paso 3 corre **sólo desde un checkout del repositorio**: se exige que existan
`.git/` y `packaging/generar_claves_licencia.py`. Ninguno de los dos viaja en lo
que recibe un cliente — `packaging/build_release.py` arma el ZIP portable con
`mvpm/`, `app/`, `api/` y `tests/` más un puñado de archivos sueltos, y de
`packaging/` sólo incluye el EULA; el instalador `.exe` lleva el programa
congelado, no el repo. O sea que un cliente nunca cumple la condición: cae en el
mensaje de "esto es una instalación de cliente" y el candado sigue en pie.

El segundo cerrojo es que, en cuanto vos publicás una versión,
`CLAVE_PUBLICA_EMBEBIDA` deja de estar vacía: si alguien lograra correr esto
sobre una copia con clave pública ya embebida, pisarla no le serviría de nada
para las licencias que emite tu servidor, y su marcador no valdría en ninguna
otra instalación.
"""

import os
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

ARCHIVO_CLAVE = "clave_privada_owner"


def _es_checkout_del_repo() -> bool:
    """¿Estamos corriendo desde el repositorio y no desde una instalación?

    Las dos señales son cosas que el cliente nunca recibe: el directorio de git
    y el generador de claves (`packaging/` sólo aporta el EULA al ZIP)."""
    return (ROOT / ".git").exists() and (
        ROOT / "packaging" / "generar_claves_licencia.py").exists()


def _ruta_clave_local() -> Path:
    from mvpm import rutas
    return Path.home() / rutas.NOMBRE_CARPETA / ARCHIVO_CLAVE


def _leer_clave_local() -> str:
    try:
        return _ruta_clave_local().read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _guardar_clave_local(clave: str) -> Path:
    ruta = _ruta_clave_local()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(clave, encoding="utf-8")
    try:
        # Sólo el dueño de la cuenta puede leerla. En Windows el modo de POSIX
        # no aplica igual, pero tampoco molesta.
        ruta.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return ruta


#: Archivo que el dueño puede dejar al lado del programa con su clave, para no
#: tener que pegarla a mano. Se borra apenas se guarda en el perfil del usuario:
#: no tiene sentido dejar la clave privada suelta en la carpeta del programa,
#: que es justo la que se comprime cuando se arma un ZIP.
ARCHIVO_CLAVE_SUELTA = "clave_owner.txt"


def _pedir_clave() -> str:
    """La clave privada que trae el dueño a una instalación descargada.

    Tres formas, de la más automática a la más manual: un argumento, un archivo
    al lado del programa, o pegarla cuando se la pide. Ninguna sirve para un
    cliente, que no tiene la clave — por eso esto no reabre el candado.
    """
    argv = sys.argv[1:]
    for i, arg in enumerate(argv):
        if arg == "--clave" and i + 1 < len(argv):
            return argv[i + 1].strip()
        if arg.startswith("--clave="):
            return arg.split("=", 1)[1].strip()

    suelta = ROOT / ARCHIVO_CLAVE_SUELTA
    if suelta.exists():
        try:
            clave = suelta.read_text(encoding="utf-8").strip()
        except OSError:
            clave = ""
        if clave:
            print(f"Encontré tu clave en {suelta}.")
            try:
                suelta.unlink()
                print("La moví a tus datos de usuario y borré ese archivo:")
                print("dejarla suelta acá la metería en cualquier ZIP que armes.")
            except OSError:
                print("No pude borrar ese archivo — borralo a mano.")
            return clave

    if not sys.stdin or not sys.stdin.isatty():
        # Sin consola interactiva (doble clic que no abre terminal, CI) no hay
        # a quién preguntarle: se cae al mensaje de instalación de cliente.
        return ""
    print("Esta copia todavía no está activada como la del dueño.")
    print()
    print("Pegá tu CLAVE PRIVADA de licencias: 43 caracteres sin espacios, del")
    print("estilo 'JIHgwW...NREJm0'. No es tu email ni tu contraseña — el email")
    print("identifica la licencia, pero lo que la firma es esta clave.")
    print("La generó packaging/generar_claves_licencia.py y quedó guardada en")
    print("tu gestor de contraseñas.")
    print()
    print("(Si no la tenés a mano, dejá vacío y Enter y volvé cuando la tengas.")
    print(" No hay ningún paquete que venga ya activado: eso existió y era el")
    print(" agujero — el archivo que lo activaba quedó en un repo público y le")
    print(" daba el producto pago a cualquiera. Se paga una vez por máquina.)")
    print()
    for intento in range(3):
        try:
            pegado = input("MVPM_LICENSE_PRIVATE_KEY = ").strip()
        except (EOFError, KeyboardInterrupt):
            return ""
        if not pegado:
            return ""
        motivo = _por_que_no_parece_una_clave(pegado)
        if motivo is None:
            return pegado
        # Se avisa ANTES de guardar nada. Antes esto se aceptaba, se escribía
        # en el perfil del usuario y recién al fallar la firma se borraba: el
        # usuario veía "Clave guardada" seguido de "esa clave no sirve", que es
        # justo el orden que hace pensar que se rompió algo.
        print(f"  -> {motivo}")
        if intento < 2:
            print("     Probá de nuevo.")
            print()
    return ""


#: Largo de la clave privada Ed25519 en el base64url que usa licensing.py
#: (32 bytes crudos, sin el relleno '=').
_LARGO_CLAVE = 43


def _por_que_no_parece_una_clave(texto: str) -> str | None:
    """Por qué lo pegado no puede ser la clave privada, o None si podría serlo.

    Es una revisión de forma, no de validez: la prueba de verdad es firmar. Sólo
    sirve para responder con algo útil en vez de un "no sirve para firmar"
    genérico cuando lo pegado es obviamente otra cosa.
    """
    if "@" in texto:
        return ("eso es un email, no la clave. El email va adentro de la "
                "licencia; la clave es la cadena de 43 caracteres.")
    if " " in texto:
        return "tiene espacios: la clave no lleva ninguno, revisá cómo la copiaste."
    if len(texto) != _LARGO_CLAVE:
        return (f"tiene {len(texto)} caracteres y la clave tiene {_LARGO_CLAVE}: "
                f"{'quedó cortada al copiarla' if len(texto) < _LARGO_CLAVE else 'se copió de más'}.")
    if not all(c.isalnum() or c in "-_" for c in texto):
        return "tiene caracteres que la clave no usa (sólo letras, números, - y _)."
    return None


def _generar_y_persistir() -> tuple[str, str]:
    """Genera el par, guarda la privada y pega la pública en licensing.py.
    Devuelve (privada, publica) en base64url."""
    sys.path.insert(0, str(ROOT / "packaging"))
    from generar_claves_licencia import escribir_clave_publica, generar

    privada, publica = generar()
    escribir_clave_publica(publica)
    ruta = _guardar_clave_local(privada)
    print("Primera vez en esta máquina: generé tu par de claves de licencias.")
    print(f"  Clave privada guardada en: {ruta}")
    print("  Clave pública escrita en:  mvpm/licensing.py")
    print()
    return privada, publica


def _avisos_de_publicacion(privada: str) -> None:
    print()
    print("-" * 68)
    print("Para VENDER (no hace falta para usar tu propia copia):")
    print("  1. Commiteá el cambio de mvpm/licensing.py (la clave pública).")
    print("  2. Cargá esta misma clave privada como MVPM_LICENSE_PRIVATE_KEY en:")
    print("       - Vercel  -> Settings -> Environment Variables")
    print("     Sin eso, el checkout no puede emitir licencias al cobrar.")
    print("     En GitHub NO hace falta cargar nada: ningún build firma nada.")
    print(f"  MVPM_LICENSE_PRIVATE_KEY={privada}")
    print("-" * 68)


def main() -> int:
    clave = os.environ.get("MVPM_LICENSE_PRIVATE_KEY", "").strip()
    recien_generada = False
    recien_guardada = False

    if not clave:
        clave = _leer_clave_local()

    if not clave:
        if not _es_checkout_del_repo():
            # Instalación descargada (ZIP o instalador): no se puede generar un
            # par acá —eso sería el bypass— pero el dueño SÍ puede traer la
            # clave que ya tiene. Un cliente no la tiene, así que sigue afuera.
            clave = _pedir_clave()
            if not clave:
                print(
                    "Esto es una instalación de cliente, no la del dueño.\n"
                    "\n"
                    "El modo dueño se activa con una licencia firmada, y la clave\n"
                    "para firmarla no viaja en lo que se distribuye — por eso una\n"
                    "copia instalada no puede activarse sola.\n"
                    "\n"
                    "Si sos el dueño, pegá tu clave privada de licencias cuando\n"
                    "este script te la pida: se guarda una sola vez y no vuelve a\n"
                    "preguntarte nunca más en esta máquina.",
                    file=sys.stderr,
                )
                return 1
            ruta = _guardar_clave_local(clave)
            recien_guardada = True
            print(f"Clave guardada en: {ruta}")
            print("No vas a tener que pegarla de nuevo en esta máquina.")
            print()
        else:
            clave, publica = _generar_y_persistir()
            recien_generada = True
            # La pública recién escrita en licensing.py no la ve un módulo que
            # ya esté importado, así que para ESTA corrida se pasa por entorno.
            os.environ["MVPM_LICENSE_PUBLIC_KEY"] = publica

    # licensing.py lee las claves del entorno en cada llamada, así que alcanza
    # con dejarlas acá: no hace falta recargar nada.
    os.environ["MVPM_LICENSE_PRIVATE_KEY"] = clave

    from mvpm import owner

    try:
        marcador = owner.activar()
    except (RuntimeError, ValueError):
        # Clave mal pegada (cortada, con espacios, de otro par). Se borra la
        # que se acababa de guardar para que el próximo intento vuelva a
        # preguntar en vez de fallar callado para siempre.
        ruta = owner.ruta_clave_local()
        if recien_guardada and ruta.exists():
            ruta.unlink()
        print(
            "Esa clave no sirve para firmar: quedó cortada al pegarla, o es de\n"
            "otro par de claves. Volvé a correr esto y pegala completa.",
            file=sys.stderr,
        )
        return 1

    if not owner.es_owner():
        # Firmó, pero esta copia no puede verificar: su CLAVE_PUBLICA_EMBEBIDA
        # es de otro par. Pasa si se activa con la clave vieja una copia ya
        # publicada con claves nuevas.
        print(
            "Se escribió el marcador pero esta copia no lo reconoce: la clave\n"
            "pública que trae es de otro par. Usá la clave privada que\n"
            "corresponde a esta versión del programa.",
            file=sys.stderr,
        )
        return 1

    print(f"Modo owner activado: {marcador}")
    print("Abrí el programa como siempre: ya corre sin el candado de los 7 días.")

    if recien_generada:
        _avisos_de_publicacion(clave)
    return 0


if __name__ == "__main__":
    sys.exit(main())
