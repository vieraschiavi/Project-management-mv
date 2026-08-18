# © 2026 Martín Viera. Todos los derechos reservados.
"""La iconografía de la interfaz: iconos de sistema, no emojis decorativos.

Los emojis sueltos al principio de cada botón y cada título —📂 💾 🗑️ 🌱 🤖—
se ven como los de un chat, no como los de un producto. Streamlit tiene desde
1.34 un parámetro `icon=` que renderiza Material Symbols de verdad, con la
fuente EMBEBIDA en el paquete (`MaterialSymbols-Rounded...woff2`), así que
funcionan también en el instalador de escritorio, que corre sin internet.

Lo que estos tests NO verifican: cómo se ve. Eso se miró con el navegador.
Lo que sí: que no vuelvan los emojis decorativos, que todo `icon=` use un
nombre que Streamlit acepte, y que sólo se use en widgets que lo soportan —
Streamlit ignora en silencio un `icon=` puesto donde no va.
"""

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

RAIZ = Path(__file__).resolve().parent.parent
APP = RAIZ / "app" / "app.py"
I18N = RAIZ / "mvpm" / "i18n.py"

#: Widgets de Streamlit que aceptan `icon=`. En el resto, el parámetro no
#: existe y la llamada revienta (o peor: lo ignora).
SOPORTAN_ICON = {
    "button", "form_submit_button", "download_button", "expander",
    "info", "success", "warning", "error", "metric", "page_link",
}

#: Widgets cuyo primer argumento es el texto que lee el usuario. Un emoji ahí
#: es decoración, sin excepción — para eso está `icon=`.
CON_ETIQUETA = SOPORTAN_ICON | {
    "title", "header", "subheader", "caption", "markdown", "write",
    "text_input", "text_area", "selectbox", "radio", "checkbox", "multiselect",
    "number_input", "date_input", "slider", "file_uploader", "toggle",
}

_EMOJI = re.compile("[\U0001F300-\U0001FAFF\U0001F1E6-\U0001F1FF☀-➿⬀-⯿]")


def _textos_de(nodo: ast.AST) -> list[str]:
    """Los literales de un argumento, sea un string suelto o una f-string."""
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
        return [nodo.value]
    if isinstance(nodo, ast.JoinedStr):
        return [t.value for t in nodo.values
                if isinstance(t, ast.Constant) and isinstance(t.value, str)]
    return []


def test_ninguna_etiqueta_de_la_interfaz_lleva_un_emoji():
    """EL test de esto. Si vuelve un `st.button("💾 Guardar")` o un
    `st.title("📋 ...")`, acá se cae.

    Se mira el ARGUMENTO de la llamada y no la línea entera a propósito: los
    semáforos RAG (🔴🟡🟢) y el ✅/⚠️ de las políticas sí llevan información y
    viven en diccionarios de estado, no en etiquetas. Un test por línea o los
    prohibía a ellos también, o —si se los ponía en una lista de permitidos—
    dejaba pasar un 📋 decorativo en un título. Lo probé: pasaba.
    """
    arbol = ast.parse(APP.read_text(encoding="utf-8"))
    sobrantes = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        nombre = getattr(nodo.func, "attr", None) or getattr(nodo.func, "id", None)
        if nombre not in CON_ETIQUETA or not nodo.args:
            continue
        for texto in _textos_de(nodo.args[0]):
            hallados = set(_EMOJI.findall(texto))
            if hallados:
                sobrantes.append((nodo.lineno, nombre, sorted(hallados), texto[:60]))
    assert not sobrantes, (
        'Emojis dentro de etiquetas — van en `icon=":material/...:"`:\n'
        + "\n".join(map(str, sobrantes)))


def test_los_semaforos_de_estado_siguen_estando():
    """El complemento del test de arriba: sacar los emojis no puede haberse
    llevado puesto el semáforo RAG, que es información y no decoración."""
    texto = APP.read_text(encoding="utf-8")
    # Se verifica CADA mapa por su nombre y no que el glifo esté en algún lado
    # del archivo: con el chequeo global, vaciar `estado_color` pasaba
    # inadvertido porque los mismos círculos seguían en los otros dos mapas.
    # Lo probé mutando: pasaba.
    for mapa, glifos in [("estado_color", "🟢🟡🔴"),
                         ("icon_severidad", "🔴🟡⚪"),
                         ("nivel_icon", "🟢🟡🔴")]:
        assert mapa in texto, f"desapareció el mapa de estado `{mapa}`"
        linea = next(ln for ln in texto.splitlines() if mapa in ln and "{" in ln)
        faltan = [g for g in glifos if g not in linea]
        assert not faltan, f"`{mapa}` se quedó sin {faltan}: {linea.strip()[:80]}"


def test_los_textos_traducidos_no_llevan_emojis():
    """Un emoji dentro de `i18n.py` se multiplica por tres idiomas y encima
    viaja pegado al texto, donde no se puede reemplazar por un icono."""
    sobrantes = set(_EMOJI.findall(I18N.read_text(encoding="utf-8")))
    assert not sobrantes, f"emojis en i18n.py: {sorted(sobrantes)}"


@pytest.fixture(scope="module")
def llamadas_con_icono():
    arbol = ast.parse(APP.read_text(encoding="utf-8"))
    encontradas = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        for clave in nodo.keywords:
            if clave.arg == "icon":
                nombre = getattr(nodo.func, "attr", None) or getattr(nodo.func, "id", None)
                valor = (clave.value.value
                         if isinstance(clave.value, ast.Constant) else None)
                encontradas.append((nombre, valor, nodo.lineno))
    return encontradas


def test_hay_iconos_declarados(llamadas_con_icono):
    assert len(llamadas_con_icono) > 20, (
        f"sólo {len(llamadas_con_icono)} widgets con icono: el test de arriba "
        "pasaría igual con una interfaz sin ningún icono")


def test_todo_icono_esta_en_un_widget_que_lo_soporta(llamadas_con_icono):
    intrusos = [(w, ln) for w, _, ln in llamadas_con_icono if w not in SOPORTAN_ICON]
    assert not intrusos, f"`icon=` en widgets que no lo aceptan: {intrusos}"


def test_todo_icono_es_uno_que_streamlit_conoce(llamadas_con_icono):
    """Un nombre inventado (`:material/guardar:`) no falla al importar: revienta
    recién cuando el usuario abre esa pantalla. Se valida con el mismo
    validador que usa Streamlit en tiempo de ejecución."""
    from streamlit.string_util import validate_icon_or_emoji

    malos = []
    for widget, valor, linea in llamadas_con_icono:
        if valor is None:
            continue
        try:
            validate_icon_or_emoji(valor)
        except Exception as e:  # noqa: BLE001
            malos.append((valor, linea, str(e)[:60]))
    assert not malos, f"iconos que Streamlit rechaza: {malos}"


def test_la_fuente_de_iconos_viaja_en_el_paquete():
    """El instalador de escritorio corre sin internet. Si Streamlit bajara la
    fuente de un CDN, cada icono se vería como su nombre en texto
    ('upload_file') en la PC del cliente."""
    import streamlit

    estaticos = Path(streamlit.__file__).parent / "static"
    fuentes = list(estaticos.rglob("*aterial*.woff2"))
    assert fuentes, (
        "no se encontró la fuente Material embebida en Streamlit: los iconos "
        "dependerían de internet")
