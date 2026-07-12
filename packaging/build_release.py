"""Genera el paquete portable descargable (ZIP con el launcher .bat + fuente).

No requiere Windows ni PyInstaller — es la opción de distribución que se
puede construir y verificar en cualquier sistema (mismo criterio que la
"Opción B: portable" de MV Data Governance). El instalador .exe real se
compila aparte, en CI, con PyInstaller + Inno Setup
(.github/workflows/build_windows.yml).
"""

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"

INCLUDE_DIRS = ["mvpm", "app", "api", "tests"]
INCLUDE_FILES = ["MV_ProjectManagement.bat", "requirements.txt", "README.md", "run.sh"]

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


if __name__ == "__main__":
    path = build_portable_zip()
    print(f"Paquete portable generado: {path} ({path.stat().st_size / 1024:.0f} KB)")
