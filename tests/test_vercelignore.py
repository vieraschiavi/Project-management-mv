# © 2026 Martín Viera. Todos los derechos reservados.
"""Tests de `.vercelignore` — qué se sube al deploy de la landing.

Sin este archivo, Vercel subía el repo entero y el deploy moría con
"Total bundle size (505.03 MB) exceeds the maximum function size (500 MB)":
`api/main.py` disparaba un build de Python con todo `requirements.txt`
(~350 MB) y encima viajaban los 144 MB de instaladores de `INSTALADOR/`.
Estuvo roto 13 deploys seguidos, producción incluida, sin que nada avisara —
la suite pasaba igual porque ningún test miraba el deploy.

Las reglas no se interpretan a mano acá: se le pregunta a `git check-ignore`,
que usa exactamente la misma sintaxis que Vercel (.gitignore). Un test que
reimplemente el matcher verifica su propia reimplementación, no el archivo.
"""

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

RAIZ = Path(__file__).resolve().parent.parent
VERCELIGNORE = RAIZ / ".vercelignore"


@pytest.fixture(scope="module")
def se_ignora(tmp_path_factory):
    """(ruta) -> bool, resuelto por git con las reglas de `.vercelignore`.

    Se arma un repo vacío con el `.vercelignore` puesto como `.gitignore`.
    `--no-index` permite preguntar por rutas que no existen en ese repo, así
    que no hace falta materializar el árbol.
    """
    if shutil.which("git") is None:  # pragma: no cover
        pytest.skip("hace falta git para interpretar las reglas de ignorado")
    carpeta = tmp_path_factory.mktemp("vercelignore")
    subprocess.run(["git", "init", "-q", "."], cwd=carpeta, check=True)
    shutil.copy(VERCELIGNORE, carpeta / ".gitignore")

    def consulta(ruta: str) -> bool:
        return subprocess.run(
            ["git", "check-ignore", "--no-index", "-q", ruta],
            cwd=carpeta).returncode == 0

    return consulta


def test_existe():
    assert VERCELIGNORE.exists(), (
        "sin .vercelignore, Vercel sube el repo entero y el deploy pasa el "
        "límite de 500 MB")


# ------------------------------------------------- lo que NO puede subir

@pytest.mark.parametrize("ruta", [
    "api/main.py",          # dispara el build de Python: la causa del 505 MB
    "requirements.txt",     # pandas + pyarrow + streamlit
    "mvpm/db.py",           # el motor no corre en Vercel
    "app/app.py",           # el dashboard tampoco
    "INSTALADOR/CLIENTE/MVProjectManagement_Setup_v0.2.0.exe",
    "INSTALADOR/OWNER/MVProjectManagementOwner_Setup_v0.2.0.exe",
    "owner/MV_Project_Management_OWNER.zip",
    "tests/test_core.py",
    "packaging/mvpm.spec",
    "distribucion/powerbi/verificar_conexion.py",
])
def test_no_se_sube(se_ignora, ruta):
    assert se_ignora(ruta), f"{ruta} se estaría subiendo a Vercel y no debería"


def test_ningun_ejecutable_viajaria_en_el_deploy(se_ignora):
    """Antes esto recorría los `.exe` RASTREADOS y comprobaba que `.vercelignore`
    los excluyera. Ya no hay ninguno: los instaladores salieron del árbol de git
    (`tests/test_workflows.py::test_ningun_ejecutable_esta_versionado`), que es
    una garantía más fuerte — no se suben a Vercel porque no existen en el repo.

    El test se mantiene mirando rutas hipotéticas, no archivos reales, porque
    `.vercelignore` sigue siendo la última red: si mañana alguien commitea un
    `.exe` esquivando el otro test, esto asegura que al menos no se despliegue.
    `git check-ignore --no-index` responde sobre una ruta que no existe."""
    for ruta in ("INSTALADOR/CLIENTE/loquesea.exe",
                 "packaging/Output/MVProjectManagement_Setup.exe",
                 "desktop/release/MVProjectManagement-Desktop-Setup.exe"):
        assert se_ignora(ruta), f"{ruta} se subiría a Vercel"


# -------------------------------------------------- lo que SÍ tiene que subir

@pytest.mark.parametrize("ruta", [
    "vercel.json",                          # rewrites, CSP y headers
    "package.json",                         # @vercel/blob para las funciones
    "landing/index.html",
    "landing/en/index.html",
    "landing/pt/index.html",
    "landing/video/demo.mp4",
    "landing/og-image.jpg",
])
def test_si_se_sube(se_ignora, ruta):
    assert not se_ignora(ruta), f"{ruta} hace falta en el deploy y quedó excluido"


def test_todas_las_funciones_serverless_suben(se_ignora):
    """Las funciones .js de `api/` son lo único ejecutable del deploy: si una
    queda afuera, el checkout de MercadoPago devuelve 404 en producción."""
    funciones = [p for p in _rastreados()
                 if p.startswith("api/") and p.endswith(".js")]
    assert len(funciones) >= 4, f"se esperaban varias funciones, hay {funciones}"
    for fn in funciones:
        assert not se_ignora(fn), f"{fn} quedó excluida del deploy"


def test_todo_lo_que_sirve_la_landing_sube(se_ignora):
    """Cualquier archivo dentro de `landing/` es alcanzable por HTTP —
    `vercel.json` reescribe `/(.*)` a `/landing/$1`— así que ninguno puede
    quedar afuera."""
    for archivo in _rastreados():
        if archivo.startswith("landing/"):
            assert not se_ignora(archivo), f"{archivo} no llegaría al sitio"


def _rastreados() -> list[str]:
    salida = subprocess.run(["git", "ls-files"], cwd=RAIZ,
                            capture_output=True, text=True, check=True)
    return [linea for linea in salida.stdout.splitlines() if linea]
