"""La ventana del programa (mvpm/ventana.py).

Lo que se fija acá es una promesa de producto, no un detalle técnico: quien
compra el programa lo instala, le queda un icono en el escritorio y espera algo
que se comporte como Excel o como cualquier otro programa de escritorio. Antes
se abría con `webbrowser.open()`, o sea una pestaña más en el navegador que ya
tenía abierto — sin entrada propia en la barra de tareas, perdida entre otras
veinte pestañas, y con la barra de direcciones mostrando `localhost:8731`.
"""

import subprocess
import sys

import pytest

from mvpm import puertos, ventana


def test_el_comando_abre_en_modo_aplicacion_y_no_como_pestana():
    """`--app=` es lo único que convierte la ventana del navegador en algo que
    no parece un navegador: sin barra de direcciones, sin pestañas, con su
    propio icono en la barra de tareas."""
    cmd = ventana.comando("http://127.0.0.1:8731", "/usr/bin/chromium")
    assert cmd[0] == "/usr/bin/chromium"
    assert "--app=http://127.0.0.1:8731" in cmd


def test_la_ventana_usa_un_perfil_propio():
    """Sin `--user-data-dir` propio, Chromium reutiliza el proceso del
    navegador que el usuario ya tiene abierto: la ventana hereda sus
    extensiones y sus cookies, y vuelve a colgarse de su icono en la barra de
    tareas en vez de tener el suyo."""
    cmd = ventana.comando("http://127.0.0.1:8731", "/usr/bin/chromium")
    perfil = [a for a in cmd if a.startswith("--user-data-dir=")]
    assert len(perfil) == 1
    assert perfil[0].split("=", 1)[1].endswith("ventana")


def test_no_se_le_pasa_ninguna_url_ajena_al_navegador():
    """La URL va sólo dentro de --app=. Si además se pasara suelta como
    argumento posicional, Chromium abriría una segunda ventana normal."""
    cmd = ventana.comando("http://127.0.0.1:8731", "/usr/bin/chromium")
    sueltos = [a for a in cmd[1:] if not a.startswith("--")]
    assert sueltos == []


def test_sin_navegador_chromium_se_cae_a_la_pestana_comun(monkeypatch):
    """Peor estéticamente, pero el programa abre igual: no abrir nada sería
    mucho peor que abrir una pestaña."""
    monkeypatch.setattr(ventana, "buscar_navegador", lambda: None)
    abiertas = []
    monkeypatch.setattr(ventana.webbrowser, "open", lambda url: abiertas.append(url))

    assert ventana.abrir("http://127.0.0.1:8731") is False
    assert abiertas == ["http://127.0.0.1:8731"]


def test_un_navegador_que_no_se_puede_lanzar_tampoco_deja_sin_ventana(monkeypatch):
    """El ejecutable existe pero falla al arrancar (permisos, ruta rota). Sin
    este fallback el usuario se queda mirando una consola sin nada abierto."""
    monkeypatch.setattr(ventana, "buscar_navegador", lambda: "/no/existe/chrome")

    def explota(*a, **k):
        raise OSError("no se pudo lanzar")

    monkeypatch.setattr(subprocess, "Popen", explota)
    abiertas = []
    monkeypatch.setattr(ventana.webbrowser, "open", lambda url: abiertas.append(url))

    assert ventana.abrir("http://127.0.0.1:8731") is False
    assert abiertas == ["http://127.0.0.1:8731"]


def test_se_puede_volver_a_la_pestana_comun_por_variable(monkeypatch):
    """Salida de emergencia si el modo aplicación fallara en alguna máquina."""
    monkeypatch.delenv("MVPM_SIN_VENTANA", raising=False)
    assert ventana.esta_deshabilitada() is False
    monkeypatch.setenv("MVPM_SIN_VENTANA", "1")
    assert ventana.esta_deshabilitada() is True
    monkeypatch.setenv("MVPM_SIN_VENTANA", "0")
    assert ventana.esta_deshabilitada() is False


def test_no_se_lanza_ningun_proceso_al_importar():
    """Importar el módulo no puede abrir ventanas: lo importa la API, los tests
    y el launcher antes de que haya nada que mostrar."""
    assert callable(ventana.abrir)


@pytest.mark.skipif(sys.platform == "win32", reason="rutas de Windows")
def test_buscar_navegador_no_explota_sin_ninguno_instalado(monkeypatch):
    monkeypatch.setattr(ventana.shutil, "which", lambda _: None)
    assert ventana.buscar_navegador() is None


# ------------------------------------------------- que no se vea Streamlit

def test_la_app_oculta_la_barra_de_herramientas_de_streamlit():
    """El botón Deploy es el peor de los tres: le ofrece al cliente publicar su
    portafolio —proyectos, presupuestos, equipo— en la nube pública de
    Streamlit, desde un programa que se vende como local."""
    from pathlib import Path

    codigo = (Path(__file__).resolve().parent.parent / "app" / "app.py").read_text(
        encoding="utf-8")
    for selector in ('[data-testid="stToolbar"]',
                     '[data-testid="stAppDeployButton"]',
                     '[data-testid="stDecoration"]',
                     "#MainMenu",
                     "footer"):
        assert selector in codigo, f"falta ocultar {selector}"


def test_la_app_no_esconde_el_header_entero():
    """La flecha para plegar y desplegar la barra lateral vive en el header:
    ocultarlo completo deja al usuario sin forma de recuperar la barra si la
    cierra, que es peor que ver una franja de color."""
    from pathlib import Path

    codigo = (Path(__file__).resolve().parent.parent / "app" / "app.py").read_text(
        encoding="utf-8")
    assert '[data-testid="stHeader"] {{ background: transparent; }}' in codigo
    assert '[data-testid="stHeader"] {{ display: none' not in codigo


def test_el_menu_no_ofrece_las_opciones_de_streamlit():
    """"Report a bug" y "About Streamlit" le cuentan al cliente con qué está
    hecho el producto que compró, y no le sirven para nada."""
    from pathlib import Path

    codigo = (Path(__file__).resolve().parent.parent / "app" / "app.py").read_text(
        encoding="utf-8")
    assert "menu_items=" in codigo
    assert '"Report a Bug": None' in codigo


# ------------------------------------------------------------------ puertos

def test_la_api_no_compite_por_el_puerto_del_dashboard():
    """Dashboard y API arrancan juntos. Con una sola lista, el que arrancara
    segundo se encontraba el puerto tomado por el primero."""
    assert not set(puertos.PUERTOS_PREFERIDOS) & set(puertos.PUERTOS_API_PREFERIDOS)


def test_la_api_sigue_prefiriendo_8600():
    """Los `.pbids` ya repartidos apuntan a 8600: si dejara de ser la primera
    opción, las conexiones de Power BI que el cliente ya tiene guardadas
    dejarían de encontrar la API."""
    assert puertos.PUERTOS_API_PREFERIDOS[0] == 8600


def test_el_puerto_de_la_api_se_elige_libre(monkeypatch):
    """8600 ocupado por otra cosa (otro servicio local, un túnel, un
    contenedor) no puede matar la API: antes uvicorn moría con `Address
    already in use` y Power BI se quedaba sin origen sin explicación."""
    monkeypatch.setattr(puertos, "esta_libre",
                        lambda p, host=puertos.HOST: p != 8600)
    elegido = puertos.elegir_con_reintento_api()
    assert elegido != 8600
    assert elegido in puertos.PUERTOS_API_PREFERIDOS


def test_el_cors_de_la_api_apunta_a_los_puertos_donde_la_app_escucha():
    """Regresión. La lista decía 8501, que es justo el puerto que puertos.py
    excluye a propósito por ser el default de Streamlit: el único origen
    permitido era uno donde la app nunca escucha, así que todo pedido del
    dashboard real moría por CORS en el navegador, en silencio."""
    from api.main import ALLOWED_ORIGINS

    assert not any(":8501" in o for o in ALLOWED_ORIGINS)
    for puerto in puertos.PUERTOS_PREFERIDOS:
        assert f"http://localhost:{puerto}" in ALLOWED_ORIGINS
        assert f"http://127.0.0.1:{puerto}" in ALLOWED_ORIGINS
