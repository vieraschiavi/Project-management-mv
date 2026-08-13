# © 2026 Martín Viera. Todos los derechos reservados.
"""La semántica del binario que se instala, que NO es la que prueba la suite.

Los builds de Windows compilan `mvpm/*.py` a binario nativo con Cython
(`packaging/setup_cython.py`). El resto de los 690 tests corre sobre los `.py`
en Python puro — o sea que cubren un artefacto distinto del que recibe el
usuario, y cualquier diferencia de comportamiento entre los dos es invisible
para ellos.

Ya pasó una vez, y así se ve desde el lado del usuario:

    TypeError: Expected str, got float
    mvpm/db.py:489 en cargar_datos_de_ejemplo

El botón "Cargar datos de ejemplo" no funcionaba en el programa instalado, y
funcionaba perfecto en desarrollo.
"""

import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SETUP_CYTHON = RAIZ / "packaging" / "setup_cython.py"


def test_cython_no_hace_cumplir_las_anotaciones():
    """Cython trae `annotation_typing` en True: interpreta las anotaciones
    PEP 484 como declaraciones de tipo y las hace cumplir en runtime. CPython
    no — para el intérprete son documentación.

    Con el enforcement puesto, `_id_para(nombre: str | None)` en
    `db.cargar_datos_de_ejemplo` rechazaba el NaN de una fila sin dueño
    asignado (un float, caso legítimo) ANTES de entrar al cuerpo, donde la
    primera línea lo maneja con `pd.isna()`.

    Hay 116 firmas anotadas en `mvpm/`. Cada una es una instancia potencial
    del mismo bug, y ninguna la puede ver esta suite.
    """
    fuente = SETUP_CYTHON.read_text(encoding="utf-8")
    directivas = re.search(r"compiler_directives=\{(.*?)\}", fuente, re.DOTALL)
    assert directivas, "no se encontró el bloque compiler_directives"
    assert re.search(r'"annotation_typing"\s*:\s*False', directivas.group(1)), (
        "falta `\"annotation_typing\": False`. Sin eso el binario que se "
        "instala rechaza en runtime valores que el código maneja bien, y la "
        "suite entera —que corre en Python puro— pasa en verde igual.")


def test_los_datos_de_la_demo_traen_los_nan_que_disparaban_el_bug():
    """Que el caso siga siendo real y no una precaución sobre algo que ya no
    pasa: las columnas que alimentan a `_id_para` tienen que seguir mezclando
    `str` con el `float` NaN de las filas sin persona asignada.

    Si algún día la demo dejara de tener NaN ahí, el bug no se reproduciría
    aunque el enforcement volviera — y este archivo estaría protegiendo algo
    que dejó de existir."""
    from mvpm import demo_data

    tipos_dueno = {type(v).__name__ for v in demo_data.projects()["dueno"]}
    tipos_resp = {type(v).__name__ for v in demo_data.tasks()["responsable"]}
    assert "float" in tipos_dueno and "str" in tipos_dueno, (
        f"projects()['dueno'] ya no mezcla str y NaN: {tipos_dueno}")
    assert "float" in tipos_resp and "str" in tipos_resp, (
        f"tasks()['responsable'] ya no mezcla str y NaN: {tipos_resp}")


@pytest.mark.skipif(
    subprocess.run([sys.executable, "-c", "import Cython"],
                   capture_output=True).returncode != 0,
    reason="Cython no está instalado (sólo lo instalan los builds de Windows)",
)
def test_compilado_de_verdad_una_anotacion_no_rechaza_un_nan(tmp_path):
    """El test que de verdad cierra el caso: compila un módulo con las MISMAS
    directivas que usa el build real y lo ejecuta.

    Los tres tests de arriba comparan texto; éste compila. Sin él, alguien
    podría dejar la directiva escrita y romper el comportamiento igual (por
    ejemplo cambiando la versión de Cython), con todo en verde.

    Se saltea cuando Cython no está instalado: no viaja en requirements-dev
    porque sólo lo necesitan los builds de Windows, y no vale sumarlo a cada
    corrida de CI por este test.
    """
    modulo = tmp_path / "anotada.py"
    modulo.write_text(textwrap.dedent('''
        def id_para(nombre: str | None) -> int | None:
            """Misma firma que _id_para en db.cargar_datos_de_ejemplo."""
            if nombre is None or (isinstance(nombre, float) and nombre != nombre):
                return None
            return len(nombre)
    '''), encoding="utf-8")

    # Las directivas se leen del archivo real: si alguien las cambia, este
    # test compila con las nuevas y falla si rompen el comportamiento.
    fuente = SETUP_CYTHON.read_text(encoding="utf-8")
    directivas = re.search(r"compiler_directives=\{(.*?)\},\s*\n\s*build_dir",
                           fuente, re.DOTALL)
    assert directivas, "no se pudieron extraer las directivas del build real"
    # Se limpian los comentarios para poder evaluarlo como literal de Python.
    crudo = re.sub(r"#[^\n]*", "", directivas.group(1))
    dirs = eval("{" + crudo + "}")  # noqa: S307 — literal del propio repo

    setup_py = tmp_path / "setup.py"
    setup_py.write_text(textwrap.dedent(f'''
        from Cython.Build import cythonize
        from setuptools import setup
        setup(name="anotada", ext_modules=cythonize(
            ["anotada.py"], compiler_directives={dirs!r}))
    '''), encoding="utf-8")

    r = subprocess.run(
        [sys.executable, "setup.py", "build_ext", "--inplace"],
        cwd=tmp_path, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        pytest.skip(f"no se pudo compilar en este entorno: {r.stderr[-300:]}")

    prueba = subprocess.run(
        [sys.executable, "-c",
         "import anotada;"
         "assert anotada.__file__.endswith(('.so', '.pyd')), anotada.__file__;"
         "print(anotada.id_para(float('nan')), anotada.id_para('Ana Perez'))"],
        cwd=tmp_path, capture_output=True, text=True, timeout=120)

    assert prueba.returncode == 0, (
        "el módulo COMPILADO rechaza un NaN que el mismo código en Python puro "
        f"acepta — es el bug que rompía la demo:\n{prueba.stderr[-500:]}")
    assert prueba.stdout.split() == ["None", "9"], (
        f"el compilado no se comporta como el .py: {prueba.stdout!r}")
