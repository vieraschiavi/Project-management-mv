# © 2026 Martín Viera. Todos los derechos reservados.
"""Genera el paquete portable descargable (ZIP con el launcher .bat + fuente).

No requiere Windows ni PyInstaller — es la opción de distribución que se
puede construir y verificar en cualquier sistema (mismo criterio que la
"Opción B: portable" de MV Data Governance). El instalador .exe real se
compila aparte, en CI, con PyInstaller + Inno Setup
(.github/workflows/build_windows.yml).
"""

import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"

INCLUDE_DIRS = ["mvpm", "app", "api", "tests"]
INCLUDE_FILES = [
    "MV_ProjectManagement.bat", "requirements.txt", "README.md", "run.sh",
    "LICENSE", "packaging/EULA.txt",
    # `run.sh owner` existe también en el paquete del cliente, así que el script
    # que invoca tiene que estar o el usuario ve un "no such file" en vez del
    # motivo real. Incluirlo no afloja nada: se niega a activar salvo desde un
    # checkout del repo, y para eso pide `.git` y
    # packaging/generar_claves_licencia.py — ninguno de los dos viaja acá.
    "packaging/activar_owner.py",
]

EXCLUDE_NAMES = {"__pycache__", ".venv", ".pytest_cache", ".git"}


def _should_skip(path: Path) -> bool:
    return any(part in EXCLUDE_NAMES for part in path.parts)


def build_portable_zip(version: str = "0.1.0",
                       reemplazos: dict[str, str] | None = None) -> Path:
    """El ZIP portable. `reemplazos` cambia el contenido de un archivo puntual
    (ruta relativa -> texto) SIN tocar el árbol de trabajo.

    Lo de "sin tocar el árbol" no es un detalle de estilo: lo usa el paquete del
    dueño para poner `ES_OWNER_BUILD = True` adentro del ZIP, y si eso se
    hiciera escribiendo el archivo real, un error a mitad de camino dejaría el
    repositorio con la constante en True. Commitear eso deja SIN CANDADO a todas
    las copias, incluida la que baja un cliente.
    """
    DIST_DIR.mkdir(exist_ok=True)
    zip_path = DIST_DIR / f"MVProjectManagement_portable_v{version}.zip"
    reemplazos = reemplazos or {}

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirname in INCLUDE_DIRS:
            src_dir = ROOT / dirname
            for path in src_dir.rglob("*"):
                if path.is_file() and not _should_skip(path.relative_to(ROOT)):
                    interno = path.relative_to(ROOT).as_posix()
                    if interno in reemplazos:
                        zf.writestr(interno, reemplazos[interno])
                    else:
                        zf.write(path, path.relative_to(ROOT))
        for filename in INCLUDE_FILES:
            src = ROOT / filename
            if src.exists():
                zf.write(src, src.relative_to(ROOT))

    return zip_path


#: Dónde queda el ZIP del dueño dentro del repo.
ZIP_OWNER = ROOT / "owner" / "MV_Project_Management_OWNER.zip"

#: Lo que este paquete tiene de más. Ninguno es un secreto — ver el docstring.
EXTRAS_OWNER = [
    # El instalador: copia esto a una carpeta, arma el entorno y deja icono en
    # el escritorio y en el menú Inicio, más un desinstalador.
    "INSTALAR_OWNER.bat",
    # Sin el icono, el acceso directo sale con el de la consola de Windows.
    "packaging/assets/icon.ico",
    "MV_ProjectManagement_OWNER.bat",
    "packaging/generar_claves_licencia.py",
]


def build_owner_zip(version: str = "0.1.0", destino: Path | None = None) -> Path:
    """El paquete portable más las herramientas de activación del dueño.

    `destino` es para los tests. Sin él escribe en `ZIP_OWNER`, que es un archivo
    VERSIONADO: un test que llame a esto sin destino deja el repositorio sucio en
    cada corrida de la suite, con un ZIP que sólo difiere en los timestamps
    internos. Pasó, y el riesgo real no es el ruido en `git status` sino que
    alguien commitee un paquete armado desde un árbol a medio editar.

    Abre sin candado y sin pedir nada: ni clave, ni token, ni archivo al lado.
    Lo consigue con `ES_OWNER_BUILD = True` en `mvpm/edicion.py`, escrito
    ADENTRO del ZIP y nunca en el árbol de trabajo (ver `build_portable_zip`).

    ## Qué cambió, y por qué

    Antes esto se lograba metiendo el marcador FIRMADO en la raíz del ZIP. Se
    sacó: ese archivo se podía copiar a cualquier otra instalación y, peor,
    pegado en el campo de licencia de la app era una licencia `enterprise`
    válida. Y estuvo versionado en un repositorio que resultó ser público.

    La constante no tiene ninguna de esas dos formas de escaparse: no es un
    token que se pueda pegar en ningún lado, y no desbloquea ninguna copia que
    no sea ésta.

    ## En qué se apoya

    En que este ZIP no sea descargable por cualquiera — o sea, en que el
    repositorio sea PRIVADO, que es lo que hoy es. Un ZIP con `mvpm/` en texto
    plano no puede sostener nada más fuerte: cualquiera que lo tenga puede
    editar esa línea. Por eso el candado de verdad, el que no depende de la
    visibilidad del repositorio, vive en el `.exe`, donde `mvpm/` va compilado a
    `.pyd` (`packaging/strip_py_sources.py`).

    Va además con las herramientas de activación por marcador, que siguen
    sirviendo en cualquier máquina y no dependen de nada de esto.
    """
    edicion_owner = (ROOT / "mvpm" / "edicion.py").read_text(encoding="utf-8").replace(
        "ES_OWNER_BUILD = False", "ES_OWNER_BUILD = True")
    if "ES_OWNER_BUILD = True" not in edicion_owner:
        raise RuntimeError(
            "No pude marcar mvpm/edicion.py como Owner Edition: el paquete del "
            "dueño saldría con el candado de cliente puesto.")

    base = build_portable_zip(version=version,
                              reemplazos={"mvpm/edicion.py": edicion_owner})
    salida = Path(destino) if destino is not None else ZIP_OWNER
    salida.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(base, salida)
    with zipfile.ZipFile(salida, "a", zipfile.ZIP_DEFLATED) as zf:
        for extra in EXTRAS_OWNER:
            src = ROOT / extra
            if not src.exists():
                raise RuntimeError(
                    f"Falta {extra}: el paquete del dueño saldría sin con qué "
                    "activar y no se distinguiría del de cliente.")
            zf.write(src, extra)
    base.unlink(missing_ok=True)
    return salida


if __name__ == "__main__":
    import sys

    if "--owner" in sys.argv[1:]:
        path = build_owner_zip()
        print(f"Paquete del DUEÑO generado: {path} ({path.stat().st_size / 1024:.0f} KB)")
    else:
        path = build_portable_zip()
        print(f"Paquete portable generado: {path} ({path.stat().st_size / 1024:.0f} KB)")
