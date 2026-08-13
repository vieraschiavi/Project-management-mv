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
        compiler_directives={
            "language_level": "3",
            # EL bug que rompia la demo en el programa instalado:
            #
            #   TypeError: Expected str, got float
            #   mvpm/db.py:489 en cargar_datos_de_ejemplo
            #
            # Cython trae `annotation_typing` en True: interpreta las
            # anotaciones PEP 484 como DECLARACIONES DE TIPO y las hace
            # cumplir en runtime. CPython no: para el interprete son
            # documentacion y no chequea nada.
            #
            # O sea que el binario que se instala tiene semantica distinta
            # de todo lo que se prueba. `_id_para(nombre: str | None)`
            # recibe el NaN de una fila sin dueno asignado -un float, caso
            # legitimo que la primera linea del cuerpo maneja con
            # pd.isna()- y compilado revienta ANTES de entrar al cuerpo.
            #
            # No es un caso aislado: hay 116 firmas anotadas en mvpm/, y
            # ninguna la puede cubrir la suite, que corre en Python puro
            # donde las anotaciones son inertes. Por eso el arreglo va aca
            # y no en la funcion: apagar el enforcement alinea el binario
            # con lo que se testea, en vez de ir corrigiendo anotaciones de
            # a una a medida que exploten en la maquina de un usuario.
            #
            # Verificado compilando de verdad (Cython 3.2.9 + gcc), mismo
            # modulo con y sin la directiva:
            #   con enforcement -> TypeError: expected str, got float
            #   sin enforcement -> None, y los str siguen andando igual
            #
            # No se pierde nada de la proteccion del codigo: la directiva
            # cambia el chequeo de tipos, no la compilacion a binario.
            "annotation_typing": False,
        },
        build_dir=str(ROOT / "build" / "cython"),
    ),
)
