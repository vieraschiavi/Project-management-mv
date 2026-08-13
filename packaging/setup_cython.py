# © 2026 Martín Viera. Todos los derechos reservados.
"""Compila mvpm/*.py a extensiones nativas (Cython) para los builds de
Windows (ver .github/workflows/build_windows.yml y build_electron.yml).

Por qué: packaging/mvpm.spec empaqueta mvpm/ dentro del .exe copiando el
directorio tal cual (datas=...). Sin este paso, cualquiera que extraiga el
instalador o el onefile con una herramienta como pyinstxtractor se lleva el
código fuente completo y legible: el esquema de licencias
(mvpm/licensing.py), las queries de los conectores ERP, las plantillas de
gobernanza, todo. Cython compila cada módulo a C y de ahí a un binario
nativo (.pyd en Windows, .so en Linux/Mac) — no es irrompible ante alguien
decidido con un desensamblador, pero saca el código fuente en texto plano
de la ecuación, que es el escenario de "descomprimir y copiar" que se
quiere evitar.

mvpm/__init__.py queda sin compilar a propósito: sólo define constantes no
sensibles (APP_NAME, VERSION, BRAND) y dejarlo como .py evita cualquier
sorpresa de import de paquete. app/app.py también queda afuera porque
Streamlit lo necesita como archivo .py real para `streamlit run <script>`.

Uso (ver los workflows para el comando exacto):
    python packaging/setup_cython.py build_ext --inplace
"""

import os
from pathlib import Path

from Cython.Build import cythonize
from setuptools import setup

ROOT = Path(__file__).resolve().parent.parent
MVPM_DIR = ROOT / "mvpm"

EXCLUDE = {"__init__.py"}

# setuptools resuelve el paquete/destino de "build_ext --inplace" a partir
# de la ruta del archivo fuente relativa al cwd — con rutas absolutas
# termina copiando el .so a un lugar incorrecto (mismatch de paquete). Por
# eso se corre siempre parado en ROOT y con rutas relativas tipo "mvpm/x.py".
os.chdir(ROOT)

MODULES = sorted(
    str(p.relative_to(ROOT)) for p in MVPM_DIR.glob("*.py") if p.name not in EXCLUDE
)

setup(
    name="mvpm_compiled",
    ext_modules=cythonize(
        MODULES,
        compiler_directives={"language_level": "3"},
        build_dir=str(ROOT / "build" / "cython"),
    ),
)
