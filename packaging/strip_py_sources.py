# © 2026 Martín Viera. Todos los derechos reservados.
"""Borra los .py de mvpm/ ya compilados a .pyd/.so, para que el instalador
sólo empaquete el binario — nunca el código fuente en texto plano.

Se corre en CI, DESPUÉS de packaging/setup_cython.py y ANTES de PyInstaller
(ver .github/workflows/build_electron.yml). Nunca se
ejecuta contra el checkout normal del repo fuera de esos jobs efímeros:
borrar acá no toca lo versionado, sólo el workspace del runner.

Aborta si algún módulo no tiene su .pyd/.so compilado al lado — mejor
romper el build en CI que publicar un instalador a medio proteger.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MVPM_DIR = ROOT / "mvpm"
KEEP = {"__init__.py"}
COMPILED_SUFFIXES = (".pyd", ".so")


def main() -> int:
    py_files = [p for p in MVPM_DIR.glob("*.py") if p.name not in KEEP]
    # Un módulo compilado con Cython aparece como <nombre>.<abi-tag>.pyd/.so,
    # no <nombre>.pyd exacto — se busca por prefijo del stem.
    missing = [
        p for p in py_files
        if not any(
            sib.name.startswith(p.stem + ".") and sib.suffix in COMPILED_SUFFIXES
            for sib in MVPM_DIR.iterdir()
        )
    ]
    if missing:
        nombres = ", ".join(p.name for p in missing)
        print(f"ERROR: faltan binarios compilados para: {nombres}", file=sys.stderr)
        return 1

    for p in py_files:
        p.unlink()
        print(f"Borrado (ya compilado): {p.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
