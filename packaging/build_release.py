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


#: Dónde queda el ZIP del dueño dentro del repo. Va versionado a propósito:
#: el repo es privado, así que "bajarlo de GitHub" ES el control de acceso.
ZIP_OWNER = ROOT / "owner" / "MV_Project_Management_OWNER.zip"


def build_owner_zip(version: str = "0.1.0") -> Path:
    """El mismo paquete portable, más el marcador firmado en la raíz.

    Es la versión del dueño: se descarga del repo privado, se descomprime y se
    abre — sin pegar claves, sin cargar secretos y sin esperar un build de
    Windows. El marcador va en la RAÍZ del paquete porque es una de las rutas
    donde `mvpm/owner.py` busca (`_RAIZ_PROGRAMA / MARCADOR`); en
    `packaging/OWNER_EDITION` no lo encontraría.

    Por qué esto no afloja el candado de nadie: lo único que hace distinto a
    este ZIP es un archivo que NO está en INCLUDE_FILES, así que el paquete de
    cliente —el que se publica en la web— no lo lleva ni puede llevarlo por
    accidente. Los tests de tests/test_owner.py lo fijan.
    """
    marcador = ROOT / "packaging" / "OWNER_EDITION"
    contenido = marcador.read_text(encoding="utf-8")
    if not [ln for ln in contenido.splitlines()
            if ln.strip() and not ln.strip().startswith("#")]:
        raise RuntimeError(
            "packaging/OWNER_EDITION no tiene un token firmado: el ZIP del "
            "dueño saldría con el candado de cliente puesto. Firmalo con "
            "packaging/firmar_marcador_owner.py (necesita MVPM_LICENSE_PRIVATE_KEY).")

    base = build_portable_zip(version=version)
    ZIP_OWNER.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(base, ZIP_OWNER)
    with zipfile.ZipFile(ZIP_OWNER, "a", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("OWNER_EDITION", contenido)
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
