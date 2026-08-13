# © 2026 Martín Viera. Todos los derechos reservados.
"""`packaging/mvpm_launcher.py` es el punto de entrada del .exe (PyInstaller) y
de la ventana de Electron. Nada de lo que hace se ejercita corriendo la app
desde el repo, así que sus fallas aparecen recién en el instalador ya
compilado — donde no hay consola para leer el error.
"""

import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LAUNCHER = RAIZ / "packaging" / "mvpm_launcher.py"


def _flags() -> list[str]:
    """Los argumentos que el launcher le arma a `streamlit run`."""
    fuente = LAUNCHER.read_text(encoding="utf-8")
    bloque = re.search(r"sys\.argv\s*=\s*\[(.*?)\]", fuente, re.DOTALL)
    assert bloque, "no se encontró el sys.argv que el launcher le pasa a streamlit"
    # Sólo los literales entre comillas: los comentarios quedan afuera solos.
    return re.findall(r'"([^"]*)"', bloque.group(1))


def test_el_launcher_apaga_el_modo_desarrollo_de_streamlit():
    """El .exe moría en el arranque con

        RuntimeError: server.port does not work when global.developmentMode is true.

    Streamlit decide si está en modo desarrollo mirando su propia ruta
    (`_global_development_mode`): da True cuando "site-packages" no aparece en
    su `__file__`. Congelado con PyInstaller el módulo vive en
    `_MEIxxxxx/streamlit/config.py`, así que el empaquetado arranca creyéndose
    un checkout de desarrollo — y ahí `_check_conflicts` prohíbe fijar
    `server.port`, que es justo lo que el launcher necesita para que Electron
    sepa a qué puerto apuntar la ventana.

    Corriendo desde el repo no pasa nunca (Streamlit sí está en site-packages),
    o sea que ningún otro test de esta suite lo puede ver.
    """
    flags = _flags()
    assert "--server.port" in flags, (
        "si el launcher dejara de fijar el puerto, este test ya no hace falta — "
        "pero Electron necesita saber a dónde apuntar, así que revisá el cambio")

    assert "--global.developmentMode" in flags, (
        "sin este flag el .exe no abre: Streamlit se cree en modo desarrollo "
        "adentro del bundle y rechaza --server.port")
    assert flags[flags.index("--global.developmentMode") + 1] == "false"


def test_streamlit_sigue_rechazando_server_port_en_modo_desarrollo():
    """Fija la razón de ser del flag de arriba, contra el Streamlit instalado.

    Si una versión futura deja de prohibirlo, este test se pone rojo y el flag
    pasa a ser ruido que se puede sacar. Si en cambio le cambian el nombre a la
    opción, el flag del launcher dejaría de tener efecto y el .exe volvería a
    no abrir — con el test estático de arriba pasando igual, porque compara
    contra un string. Por eso hace falta ejercitar a Streamlit de verdad.

    Corre en un subproceso: `load_config_options` pisa el estado global de
    configuración de Streamlit, y hacerlo dentro del proceso de pytest le
    cambiaría la config a los demás tests.
    """
    codigo = (
        "from streamlit.web import bootstrap\n"
        "try:\n"
        "    bootstrap.load_config_options("
        "{'server_port': 8599, 'global_developmentMode': True})\n"
        "    print('SIN-ERROR')\n"
        "except RuntimeError as e:\n"
        "    print('RUNTIMEERROR:', e)\n"
    )
    salida = subprocess.run(
        [sys.executable, "-c", codigo], capture_output=True, text=True, timeout=120,
    ).stdout
    assert "RUNTIMEERROR" in salida and "server.port" in salida, (
        "Streamlit ya no rechaza server.port en modo desarrollo: revisar si "
        f"--global.developmentMode sigue haciendo falta en el launcher. Salida: {salida!r}")


def test_el_launcher_arranca_con_la_combinacion_que_usa_el_exe():
    """La otra mitad: con el flag puesto, fijar el puerto tiene que dejar de
    ser un conflicto. Es la condición que el .exe necesita para abrir."""
    codigo = (
        "from streamlit.web import bootstrap\n"
        "bootstrap.load_config_options("
        "{'server_port': 8599, 'global_developmentMode': False})\n"
        "print('OK')\n"
    )
    r = subprocess.run(
        [sys.executable, "-c", codigo], capture_output=True, text=True, timeout=120,
    )
    assert "OK" in r.stdout, f"stdout={r.stdout!r} stderr={r.stderr[-600:]!r}"
