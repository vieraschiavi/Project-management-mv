"""Elección de puerto (mvpm/puertos.py): no pisarle el puerto a otra app.

El programa se abre de cuatro formas —el `.exe`, el `.bat` portable,
`./run.sh app` y la ventana de Electron— y cada una elegía el puerto por su
cuenta. Tres de las cuatro podían chocar con otra aplicación:

* el `.bat` no pasaba puerto (Streamlit tomaba su 8501, el más disputado);
* `run.sh app` tenía 8501 fijo;
* el `.exe` buscaba con `connect_ex()`, que da falsos negativos.

Acá se fija que la decisión sea una sola, que sea correcta, y que las cuatro
formas de arrancar la usen.
"""

import socket
import subprocess
import sys
from pathlib import Path

import pytest

from mvpm import puertos

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture
def puerto_ocupado():
    """Un puerto tomado por 'otra aplicación', con el socket abierto."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    yield s.getsockname()[1], s
    s.close()


# ------------------------------------------------------------- detección

def test_un_puerto_ocupado_no_figura_como_libre(puerto_ocupado):
    puerto, _sock = puerto_ocupado
    assert puertos.esta_libre(puerto) is False


def test_un_puerto_ocupado_sin_listen_tampoco_figura_como_libre(puerto_ocupado):
    """EL BUG ORIGINAL. `connect_ex` sólo detecta puertos que ya ACEPTAN
    conexiones: si otra app reservó el puerto pero todavía no llamó a
    `listen()` —la ventana de arranque de cualquier servidor— devolvía
    "conexión rechazada" y el puerto se daba por libre. Streamlit moría
    después con "Address already in use" y el usuario veía una ventana que se
    cerraba sola.

    El fixture bindea SIN listen() a propósito: es exactamente ese estado.
    """
    puerto, _sock = puerto_ocupado

    # Lo que hacía antes: connect_ex dice "libre" (falso negativo).
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        parecia_libre = s.connect_ex(("127.0.0.1", puerto)) != 0
    assert parecia_libre, "el fixture no reprodujo el estado que causaba el bug"

    # Lo que hace ahora: bindear de verdad, la misma operación que Streamlit.
    assert puertos.esta_libre(puerto) is False


def test_un_puerto_libre_figura_como_libre():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        puerto = s.getsockname()[1]
    # El socket ya se cerró: el puerto quedó disponible.
    assert puertos.esta_libre(puerto) is True


def test_comprobar_no_deja_el_puerto_tomado():
    """Si `esta_libre` se olvidara de cerrar el socket, dejaría ocupado
    justamente el puerto que acaba de declarar libre."""
    puerto = puertos.elegir()
    assert puertos.esta_libre(puerto) is True
    assert puertos.esta_libre(puerto) is True, "quedó tomado tras comprobarlo"


# --------------------------------------------------------------- elección

def test_elegir_prefiere_el_primero_de_la_lista():
    """La URL tiene que ser estable entre sesiones: el usuario puede dejarla
    en favoritos. Sólo se cambia de puerto si el preferido está ocupado."""
    elegido = puertos.elegir()
    if puertos.esta_libre(puertos.PUERTOS_PREFERIDOS[0]):
        assert elegido == puertos.PUERTOS_PREFERIDOS[0]


def test_si_el_preferido_esta_ocupado_salta_al_siguiente():
    ocupador = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ocupador.bind(("127.0.0.1", puertos.PUERTOS_PREFERIDOS[0]))
    try:
        elegido = puertos.elegir()
        assert elegido != puertos.PUERTOS_PREFERIDOS[0]
        assert puertos.esta_libre(elegido)
    finally:
        ocupador.close()


def test_con_todos_los_preferidos_ocupados_cae_a_uno_del_sistema():
    """Cuatro instancias abiertas no pueden dejar al usuario sin abrir la
    quinta: se pide uno efímero en vez de fallar."""
    ocupadores = []
    try:
        for p in puertos.PUERTOS_PREFERIDOS:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.bind(("127.0.0.1", p))
                ocupadores.append(s)
            except OSError:
                s.close()  # ya estaba ocupado por otra cosa: igual sirve
        elegido = puertos.elegir()
        assert elegido not in puertos.PUERTOS_PREFERIDOS
        assert puertos.esta_libre(elegido)
    finally:
        for s in ocupadores:
            s.close()


def test_8501_no_esta_entre_los_preferidos():
    """Es el default de Streamlit: el puerto que con más probabilidad ya tiene
    otra app abierta. Elegirlo era buscarse el choque."""
    assert 8501 not in puertos.PUERTOS_PREFERIDOS


def test_elegir_con_reintento_devuelve_algo_usable():
    puerto = puertos.elegir_con_reintento()
    assert puertos.esta_libre(puerto)


# ------------------------------------------------- puerto pedido por fuera

def test_se_respeta_el_puerto_pedido_si_esta_libre():
    """Electron necesita saber de antemano a qué puerto apuntar su ventana."""
    libre = puertos.elegir()
    assert puertos.desde_entorno(str(libre)) == libre


def test_un_puerto_pedido_pero_ocupado_no_hace_fallar_el_arranque(puerto_ocupado):
    """Más vale abrir en otro puerto que no abrir."""
    ocupado, _sock = puerto_ocupado
    elegido = puertos.desde_entorno(str(ocupado))
    assert elegido != ocupado
    assert puertos.esta_libre(elegido)


@pytest.mark.parametrize("basura", [None, "", "no-es-un-numero", "99999999"])
def test_un_valor_invalido_no_rompe(basura):
    puerto = puertos.desde_entorno(basura)
    assert puertos.esta_libre(puerto)


# --------------------------------- que las 4 formas de arrancar lo usen

def test_se_puede_invocar_como_modulo_para_los_scripts():
    """`run.sh` y el `.bat` lo llaman con `python -m mvpm.puertos` y le pasan
    la salida a Streamlit. Si dejara de imprimir sólo el número, el `.bat`
    armaría un `--server.port` inválido."""
    r = subprocess.run([sys.executable, "-m", "mvpm.puertos"],
                       capture_output=True, text=True, cwd=RAIZ, timeout=30)
    assert r.returncode == 0, r.stderr
    salida = r.stdout.strip()
    assert salida.isdigit(), f"tiene que imprimir sólo el número, imprimió: {salida!r}"
    assert puertos.esta_libre(int(salida))


def _solo_codigo(texto: str, marca_comentario: str = "#") -> str:
    """Descarta comentarios: los de este repo nombran el bug que previenen, y
    harían pasar o fallar un test por el texto en vez de por el código."""
    return "\n".join(linea for linea in texto.splitlines()
                     if not linea.strip().startswith(marca_comentario))


def test_run_sh_no_asume_8501():
    contenido = (RAIZ / "run.sh").read_text(encoding="utf-8")
    assert "mvpm.puertos" in contenido, "run.sh no consulta el módulo de puertos"
    assert "8501" not in _solo_codigo(contenido), "run.sh sigue con el 8501 fijo"


def test_el_bat_portable_pasa_un_puerto_explicito():
    """Sin `--server.port`, Streamlit toma 8501 y choca con cualquier otra app
    de Streamlit abierta — que es el caso que reportó el usuario."""
    contenido = (RAIZ / "MV_ProjectManagement.bat").read_text(encoding="utf-8")
    assert "mvpm.puertos" in contenido
    assert "--server.port" in contenido


def test_el_launcher_del_exe_usa_el_modulo_y_no_connect_ex():
    contenido = (RAIZ / "packaging" / "mvpm_launcher.py").read_text(encoding="utf-8")
    codigo = _solo_codigo(contenido)
    assert "puertos.desde_entorno" in codigo
    assert "connect_ex" not in codigo, (
        "volvió la búsqueda por connect_ex, que da falsos negativos")


def test_electron_usa_el_puerto_que_anuncia_el_launcher():
    """Electron pedía un puerto y esperaba en ESE. Si el launcher elegía otro
    (porque el pedido se ocupó), la ventana se quedaba esperando donde no
    había nadie."""
    contenido = (RAIZ / "desktop" / "main.js").read_text(encoding="utf-8")
    assert "MVPM_READY_PORT" in contenido, (
        "Electron no lee el puerto real que anuncia el launcher")
