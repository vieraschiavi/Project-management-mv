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
    "LICENSE.txt", "packaging/EULA.txt",
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


def build_portable_zip(version: str = "0.1.0") -> Path:
    DIST_DIR.mkdir(exist_ok=True)
    zip_path = DIST_DIR / f"MVProjectManagement_portable_v{version}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirname in INCLUDE_DIRS:
            src_dir = ROOT / dirname
            for path in src_dir.rglob("*"):
                if path.is_file() and not _should_skip(path.relative_to(ROOT)):
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
    "MV_ProjectManagement_OWNER.bat",
    "packaging/generar_claves_licencia.py",
]


def build_owner_zip(version: str = "0.1.0") -> Path:
    """El paquete portable más las herramientas de activación del dueño.

    ## Qué cambió, y por qué

    Antes este ZIP llevaba el marcador FIRMADO en la raíz: se descomprimía y ya
    estaba activado, sin pegar nada. Se diseñó así dando por sentado que el
    repositorio era privado. No lo era. El resultado fue que el producto pago
    quedó descargable por cualquiera —y no sólo en modo dueño: ese token pegado
    en el campo de licencia daba una licencia `enterprise` válida—.

    Así que el paquete del dueño ya no lleva ningún secreto adentro. Lo que lo
    hace distinto del de cliente son dos archivos que no le sirven a nadie sin
    la clave privada:

    * `MV_ProjectManagement_OWNER.bat` — el doble clic que activa la máquina.
    * `packaging/generar_claves_licencia.py` — para generar el par la primera
      vez. Ojo: `activar_owner.py` sólo genera desde un checkout del repo (pide
      `.git/`), así que incluirlo acá no habilita a un cliente a fabricarse un
      par; es para que el dueño lo tenga a mano.

    La activación pasó a ser una vez por máquina: se pega la clave privada, se
    guarda en el perfil del usuario, y desde ahí TODAS las formas de abrir el
    programa —este ZIP, el `.exe`, `run.sh`, el `.bat` de cliente— se activan
    solas vía `owner.activar_automatico()`. Es un paso más que antes; a cambio,
    lo que se publica no desbloquea el producto de nadie.
    """
    base = build_portable_zip(version=version)
    ZIP_OWNER.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(base, ZIP_OWNER)
    with zipfile.ZipFile(ZIP_OWNER, "a", zipfile.ZIP_DEFLATED) as zf:
        for extra in EXTRAS_OWNER:
            src = ROOT / extra
            if not src.exists():
                raise RuntimeError(
                    f"Falta {extra}: el paquete del dueño saldría sin con qué "
                    "activar y no se distinguiría del de cliente.")
            zf.write(src, extra)
    base.unlink(missing_ok=True)
    return ZIP_OWNER


if __name__ == "__main__":
    import sys

    if "--owner" in sys.argv[1:]:
        path = build_owner_zip()
        print(f"Paquete del DUEÑO generado: {path} ({path.stat().st_size / 1024:.0f} KB)")
    else:
        path = build_portable_zip()
        print(f"Paquete portable generado: {path} ({path.stat().st_size / 1024:.0f} KB)")
