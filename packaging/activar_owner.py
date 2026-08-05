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
   `mvpm/licensing.py`. Sólo en este caso hay setup, y ocurre una única vez.

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
    print("       - GitHub  -> Settings -> Secrets and variables -> Actions")
    print("     Sin eso, el checkout no puede emitir licencias al cobrar y el")
    print("     build de la Owner Edition no puede firmar su marcador.")
    print(f"  MVPM_LICENSE_PRIVATE_KEY={privada}")
    print("-" * 68)


def main() -> int:
    clave = os.environ.get("MVPM_LICENSE_PRIVATE_KEY", "").strip()
    recien_generada = False

    if not clave:
        clave = _leer_clave_local()

    if not clave:
        if not _es_checkout_del_repo():
            print(
                "Esto es una instalación de cliente, no la del dueño.\n"
                "\n"
                "El modo dueño se activa con una licencia firmada, y la clave para\n"
                "firmarla no viaja en lo que se distribuye — por eso una copia\n"
                "instalada no puede activarse sola.\n"
                "\n"
                "Si sos el dueño: corré esto desde tu copia del repositorio, o\n"
                "instalá la Owner Edition, que ya viene con el modo activado.",
                file=sys.stderr,
            )
            return 1
        clave, publica = _generar_y_persistir()
        recien_generada = True
        # La pública recién escrita en licensing.py no la ve un módulo que ya
        # esté importado, así que para ESTA corrida se pasa por entorno.
        os.environ["MVPM_LICENSE_PUBLIC_KEY"] = publica

    # licensing.py lee las claves del entorno en cada llamada, así que alcanza
    # con dejarlas acá: no hace falta recargar nada.
    os.environ["MVPM_LICENSE_PRIVATE_KEY"] = clave

    from mvpm import owner

    marcador = owner.activar()
    print(f"Modo owner activado: {marcador}")
    print("Abrí el programa como siempre: ya corre sin el candado de los 7 días.")

    if recien_generada:
        _avisos_de_publicacion(clave)
    return 0


if __name__ == "__main__":
    sys.exit(main())
