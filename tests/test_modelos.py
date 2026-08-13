# © 2026 Martín Viera. Todos los derechos reservados.
"""Tests del selector de modelos de IA (mvpm/modelos.py) y de su efecto real
sobre la capa de IA (mvpm/ai.py, mvpm/advisor.py).

Nada acá sale a internet: el catálogo se sirve desde un doble de `urllib` para
poder probar respuestas 401, JSON roto y catálogos vacíos, que son justamente
los casos donde una capa de IA mal hecha rompe la aplicación entera.
"""

import json
import pathlib
import urllib.error

import pytest

from mvpm import advisor, ai, modelos


@pytest.fixture(autouse=True)
def _sin_claves_ni_seleccion(monkeypatch):
    """Cada test arranca sin ninguna clave de proveedor y sin nada elegido.

    Importa que sea automático: la máquina de quien corre la suite puede tener
    OPENAI_API_KEY o XAI_API_KEY exportada para otra cosa, y sin esto los tests
    pasarían o fallarían según el entorno en vez de según el código.
    """
    for cfg in modelos.PROVEEDORES.values():
        monkeypatch.delenv(cfg["env_clave"], raising=False)
        monkeypatch.delenv(cfg["env_modelo"], raising=False)
    modelos.aplicar_seleccion(None)
    yield
    modelos.aplicar_seleccion(None)


def _respuesta(payload):
    """Reemplaza a modelos._pedir con una respuesta fija."""
    return lambda url, cabeceras, timeout: payload


# ---------------------------------------------------------------- precedencia

def test_lo_elegido_en_configuracion_le_gana_a_la_variable_de_entorno(monkeypatch):
    """La elección hecha con el mouse es lo último que pidió el usuario. Si una
    variable de entorno vieja se la pisara, la pantalla mostraría un modelo y
    se cobraría otro."""
    monkeypatch.setenv("OPENAI_MODEL", "el-de-la-variable")
    assert modelos.modelo_actual("chatgpt") == "el-de-la-variable"

    modelos.fijar_modelo("chatgpt", "el-que-elegi")
    assert modelos.modelo_actual("chatgpt") == "el-que-elegi"


def test_sin_eleccion_se_respeta_la_variable_de_entorno(monkeypatch):
    """Quien automatiza el arranque (Electron, el .bat, un servidor) sigue
    pudiendo fijar el modelo por entorno sin abrir la pantalla."""
    monkeypatch.setenv("GEMINI_MODEL", "gemini-de-entorno")
    assert modelos.modelo_actual("gemini") == "gemini-de-entorno"


def test_sin_eleccion_ni_variable_no_se_inventa_ningun_modelo():
    """El módulo no trae ninguna lista de modelos escrita a mano: un catálogo
    hardcodeado envejece y además miente, porque no todas las claves tienen
    habilitados los mismos modelos."""
    for proveedor in modelos.PROVEEDORES:
        assert modelos.modelo_actual(proveedor) is None


def test_borrar_la_eleccion_vuelve_a_la_variable_de_entorno(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "el-de-la-variable")
    modelos.fijar_modelo("chatgpt", "el-que-elegi")
    modelos.fijar_modelo("chatgpt", None)
    assert modelos.modelo_actual("chatgpt") == "el-de-la-variable"


def test_no_se_puede_elegir_para_un_proveedor_inexistente():
    with pytest.raises(ValueError):
        modelos.fijar_modelo("proveedor-que-no-existe", "algo")


# ------------------------------------------------------------- disponibilidad

def test_solo_se_ofrecen_proveedores_con_clave(monkeypatch):
    assert modelos.con_clave() == []
    monkeypatch.setenv("XAI_API_KEY", "xai-test")
    assert modelos.con_clave() == ["grok"]


def test_copilot_no_se_activa_con_el_github_token_de_cualquier_entorno(monkeypatch):
    """GITHUB_TOKEN está seteada por defecto en cualquier runner de Actions y en
    muchas máquinas de desarrollo, para cosas que no tienen nada que ver con IA.
    Si fuera la clave de Copilot, el producto ofrecería un proveedor que el
    usuario nunca configuró y que devolvería 403 al primer uso."""
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_de_otra_cosa")
    assert "copilot" not in modelos.con_clave()

    monkeypatch.setenv("GITHUB_MODELS_TOKEN", "ghp_para_ia")
    assert "copilot" in modelos.con_clave()


def test_la_capa_de_ia_no_ofrece_un_proveedor_sin_modelo_resuelto(monkeypatch):
    """Con clave pero sin modelo, el pedido no se puede armar. Ofrecerlo sería
    prometer algo que falla en silencio."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert "chatgpt" not in ai.proveedores_disponibles()

    modelos.fijar_modelo("chatgpt", "un-modelo")
    assert "chatgpt" in ai.proveedores_disponibles()


def test_claude_tiene_modelo_por_defecto_y_los_demas_no(monkeypatch):
    """Quien ya venía usando Claude sin configurar nada no tiene que elegir un
    modelo para que siga andando igual que antes."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    assert ai.proveedores_disponibles() == ["claude"]


# ------------------------------------------------------------- persistencia

def test_la_seleccion_va_y_vuelve_por_json():
    modelos.fijar_modelo("chatgpt", "modelo-a")
    modelos.fijar_modelo("grok", "modelo-b")
    guardado = modelos.serializar_seleccion()

    modelos.aplicar_seleccion(None)
    assert modelos.seleccion() == {}

    modelos.aplicar_seleccion(guardado)
    assert modelos.seleccion() == {"chatgpt": "modelo-a", "grok": "modelo-b"}


@pytest.mark.parametrize("basura", [
    "no soy json", "[1, 2, 3]", '{"proveedor_inventado": "x"}',
    '{"chatgpt": 42}', '{"chatgpt": "   "}', "",
])
def test_una_seleccion_corrupta_no_rompe_el_arranque(basura):
    """La elección se lee al abrir la aplicación. Si un JSON roto levantara una
    excepción ahí, el programa no abriría — y por una preferencia de modelo,
    que es lo menos importante que hay guardado."""
    assert modelos.aplicar_seleccion(basura) == {}


def test_la_seleccion_no_se_comparte_entre_hilos():
    """Streamlit atiende todas las sesiones en un solo proceso, cada script en
    su hilo. Con estado de módulo compartido, el modelo que elige una empresa
    se lo comería la sesión de otra — cobrado a la clave de la otra."""
    import threading

    modelos.fijar_modelo("chatgpt", "el-de-la-sesion-1")
    visto = {}

    def otra_sesion():
        visto["antes"] = modelos.modelo_actual("chatgpt")
        modelos.fijar_modelo("chatgpt", "el-de-la-sesion-2")
        visto["propio"] = modelos.modelo_actual("chatgpt")

    hilo = threading.Thread(target=otra_sesion)
    hilo.start()
    hilo.join()

    assert visto["antes"] is None      # no ve lo de la sesión 1
    assert visto["propio"] == "el-de-la-sesion-2"
    assert modelos.modelo_actual("chatgpt") == "el-de-la-sesion-1"  # ni la pisa


# --------------------------------------------------------- catálogo de la API

def test_sin_clave_no_se_consulta_el_catalogo():
    with pytest.raises(modelos.ErrorDeProveedor, match="ANTHROPIC_API_KEY"):
        modelos.listar_desde_api("claude")


def test_anthropic_manda_la_clave_por_encabezado_y_su_version(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    visto = {}

    def espia(url, cabeceras, timeout):
        visto["url"], visto["cabeceras"] = url, cabeceras
        return {"data": [{"id": "modelo-b"}, {"id": "modelo-a"}]}

    monkeypatch.setattr(modelos, "_pedir", espia)
    assert modelos.listar_desde_api("claude") == ["modelo-a", "modelo-b"]
    assert visto["cabeceras"]["x-api-key"] == "sk-ant-test"
    assert "anthropic-version" in visto["cabeceras"]
    assert "sk-ant-test" not in visto["url"]


def test_gemini_manda_la_clave_por_url_y_filtra_lo_que_no_genera_texto(monkeypatch):
    """Gemini lista también modelos de embeddings, que no sirven para redactar:
    ofrecerlos sería mandar al cliente a un error garantizado."""
    monkeypatch.setenv("GEMINI_API_KEY", "g-test")
    visto = {}

    def espia(url, cabeceras, timeout):
        visto["url"] = url
        return {"models": [
            {"name": "models/gemini-que-sirve",
             "supportedGenerationMethods": ["generateContent"]},
            {"name": "models/embedding-que-no",
             "supportedGenerationMethods": ["embedContent"]},
        ]}

    monkeypatch.setattr(modelos, "_pedir", espia)
    assert modelos.listar_desde_api("gemini") == ["gemini-que-sirve"]
    assert "key=g-test" in visto["url"]


def test_el_catalogo_de_github_models_viene_como_lista_pelada(monkeypatch):
    """OpenAI y xAI envuelven en {"data": [...]}; GitHub devuelve la lista
    directamente. Las dos formas tienen que funcionar."""
    monkeypatch.setenv("GITHUB_MODELS_TOKEN", "ghp-test")
    monkeypatch.setattr(modelos, "_pedir",
                        _respuesta([{"id": "openai/gpt-x"}, {"id": "meta/llama-y"}]))
    assert modelos.listar_desde_api("copilot") == ["meta/llama-y", "openai/gpt-x"]


def test_una_clave_rechazada_dice_que_clave_revisar(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "xai-vencida")

    def rechaza(url, cabeceras, timeout):
        raise urllib.error.HTTPError(url, 401, "Unauthorized", {}, None)

    monkeypatch.setattr(modelos, "_pedir", rechaza)
    with pytest.raises(modelos.ErrorDeProveedor, match="XAI_API_KEY"):
        modelos.listar_desde_api("grok")


def test_un_catalogo_vacio_se_reporta_en_vez_de_dejar_la_lista_en_blanco(monkeypatch):
    """Sin esto, una clave sin modelos habilitados se vería igual que "todavía
    no actualizaste": el usuario apretaría el botón para siempre."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(modelos, "_pedir", _respuesta({"data": []}))
    with pytest.raises(modelos.ErrorDeProveedor, match="ningún modelo"):
        modelos.listar_desde_api("chatgpt")


def test_una_respuesta_ilegible_no_se_propaga_como_error_de_red(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    def rompe(url, cabeceras, timeout):
        raise ValueError("Expecting value")

    monkeypatch.setattr(modelos, "_pedir", rompe)
    with pytest.raises(modelos.ErrorDeProveedor, match="JSON"):
        modelos.listar_desde_api("chatgpt")


def test_una_caida_de_red_no_levanta_urlerror_crudo(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    def cae(url, cabeceras, timeout):
        raise urllib.error.URLError("sin red")

    monkeypatch.setattr(modelos, "_pedir", cae)
    with pytest.raises(modelos.ErrorDeProveedor):
        modelos.listar_desde_api("chatgpt")


# ------------------------------------------------- el modelo elegido se usa

def test_el_modelo_elegido_es_el_que_se_le_pide_al_proveedor(monkeypatch):
    """Sin esto el selector sería decorativo: mostraría una elección que no
    llega al pedido."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    modelos.fijar_modelo("chatgpt", "el-barato-que-elegi")
    pedido = {}

    class _Respuesta:
        choices = [type("C", (), {"message": type("M", (), {"content": "ok"})()})()]

    class _FalsoOpenAI:
        def __init__(self, **kwargs):
            pedido["base_url"] = kwargs.get("base_url")

        @property
        def chat(self):
            class _Completions:
                def create(self, **kwargs):
                    pedido.update(kwargs)
                    return _Respuesta()

            return type("Chat", (), {"completions": _Completions()})()

    monkeypatch.setitem(__import__("sys").modules, "openai",
                        type("M", (), {"OpenAI": _FalsoOpenAI}))
    assert ai.completar("sys", "user", "chatgpt") == "ok"
    assert pedido["model"] == "el-barato-que-elegi"


def test_grok_y_copilot_pegan_a_su_propia_url_base(monkeypatch):
    """Los tres hablan el dialecto de OpenAI; si no se cambiara la URL base,
    elegir Grok le mandaría el pedido —y el gasto— a OpenAI."""
    assert ai._BASE_URL_OPENAI["grok"] == "https://api.x.ai/v1"
    assert ai._BASE_URL_OPENAI["copilot"] == "https://models.github.ai/inference"
    assert ai._BASE_URL_OPENAI["chatgpt"] is None


def test_el_asistente_degrada_al_motor_de_reglas_sin_ia(monkeypatch):
    """La regla que no se negocia: sin clave, sin modelo o con el proveedor
    caído, la sugerencia igual sale — del motor de reglas."""
    from mvpm import demo_data

    problema = advisor.detectar_problemas(
        demo_data.projects(), demo_data.tasks(), demo_data.team())[0]
    resultado = advisor.sugerir(problema, proveedor="grok")
    assert resultado["ai_enriched"] is False
    assert resultado["sugerencia"]


def test_el_asistente_usa_la_capa_generica_y_no_su_propia_copia():
    """advisor.py tenía una implementación por proveedor duplicada de ai.py:
    agregar Grok o Copilot había que hacerlo dos veces, y el modelo elegido en
    Configuración no llegaba a la pantalla de Asistente IA."""
    assert advisor._PROVEEDORES == ai._ENV_KEYS
    assert set(advisor._PROVEEDORES) == set(modelos.PROVEEDORES)


def test_todo_proveedor_declarado_sabe_completar_y_listar():
    """Un proveedor a medias —que se ofrece en la pantalla pero no sabe
    responder, o al revés— es peor que no tenerlo."""
    for proveedor, cfg in modelos.PROVEEDORES.items():
        assert proveedor in ai._FUNCS, f"{proveedor} no sabe completar"
        assert cfg["estilo"] in ("anthropic", "openai", "gemini")
        assert cfg["url"].startswith("https://")


def test_la_seleccion_serializada_es_json_valido_para_la_tabla_versiones():
    """Se guarda con db.guardar_version(), que espera texto: si no fuera JSON
    estable, el historial por empresa quedaría ilegible."""
    modelos.fijar_modelo("claude", "un-modelo")
    assert json.loads(modelos.serializar_seleccion()) == {"claude": "un-modelo"}


# ------------------------------------------------------ la pantalla, de punta a punta

def test_la_pantalla_de_configuracion_hace_el_recorrido_completo(monkeypatch, tmp_path):
    """Corre el dashboard de verdad y hace lo que haría un cliente: entrar,
    ir a Configuración de IA, actualizar el catálogo contra su API, elegir el
    modelo barato, guardar y volver a abrir.

    Es el único test que cruza el motor con la interfaz. Sin él, todo lo de
    arriba puede estar verde con la pantalla desconectada: el selector
    mostrando una elección que nunca llega ni al pedido ni a la base.
    """
    from streamlit.testing.v1 import AppTest

    from mvpm import db

    # Base aislada. No alcanza con MVPM_DATA_DIR: mvpm/db.py resuelve su ruta
    # UNA vez, al importarse, y para cuando este test corre el módulo ya está
    # importado. Sin parchear los dos atributos, el test crea su usuario y sus
    # versiones en la base real del perfil del usuario que corre la suite — y
    # a partir de la segunda corrida ya no ve la pantalla de "crear cuenta de
    # administrador" que necesita, así que se rompe solo.
    monkeypatch.setenv("MVPM_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(db, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(db, "_DB_FILE", tmp_path / "datos.db")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-de-prueba")

    # La API del cliente, doblada. El catálogo sale de acá y no de internet:
    # la suite tiene que correr igual en una máquina sin red.
    monkeypatch.setattr(modelos, "_pedir", _respuesta(
        {"data": [{"id": "gpt-caro"}, {"id": "gpt-barato"}]}))

    raiz = pathlib.Path(__file__).resolve().parent.parent
    at = AppTest.from_file(str(raiz / "app" / "app.py"), default_timeout=120)
    at.run()

    # Primera cuenta del servidor: la pantalla de administrador.
    at.text_input[0].set_value("Tester")
    at.text_input[1].set_value("tester@ejemplo.com")
    at.text_input[2].set_value("contrasena123")
    [b for b in at.button if "administrador" in b.label][0].click().run()
    assert not at.exception

    at.radio[0].set_value("Configuración de IA").run()
    assert not at.exception

    def _selectores_de_modelo():
        return [s for s in at.selectbox if s.label == "Modelo"]

    # Antes de preguntarle a la API no se ofrece ningún modelo: el programa no
    # trae catálogo precargado, y decir "sin elegir" es lo único cierto.
    assert _selectores_de_modelo()[0].options == ["sin elegir"]

    [b for b in at.button if b.label.startswith("🔄")][0].click().run()
    assert not at.exception
    assert _selectores_de_modelo()[0].options == ["sin elegir", "gpt-barato", "gpt-caro"]

    _selectores_de_modelo()[0].set_value("gpt-barato")
    [b for b in at.button if b.label.startswith("💾")][0].click().run()
    assert not at.exception

    # Quedó como una versión más, con autor — igual que gobernanza y organigrama.
    fila = db.obtener_version_actual(1, "config_ia", "modelos")
    assert json.loads(fila["contenido"]) == {"chatgpt": "gpt-barato"}
    assert fila["recomendado_por"] == "Tester"

    # Y lo lee la corrida siguiente, que es lo que hace que sobreviva a cerrar
    # el programa.
    at.run()
    assert any("gpt-barato" in c.value for c in at.caption if "En uso ahora" in c.value)
