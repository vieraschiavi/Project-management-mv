"""Regresión de mvpm/seguro.py — el punto de escape antes de insertar texto
externo (reseñas, notas de gobernanza, organigrama importado) en un
st.markdown/st.write.

Los payloads acá son los mismos que se probaron en vivo contra
http://localhost:8501 con Playwright (login real + navegación a Reseñas):
antes de aplicar seguro.escapar(), Streamlit YA neutralizaba estos vectores
por su cuenta (raw HTML → texto escapado; link markdown con esquema
`javascript:` → `href="#"`, cero flags JS disparados). Este test fija ese
comportamiento a nivel de la función propia, para no depender solo de que
la librería siga haciéndolo bien en el futuro.
"""

from mvpm import seguro

PAYLOAD_IMG = "<img src=x onerror=window.__xss_html=1>"
PAYLOAD_SCRIPT = "**bold** `code` <script>window.__xss_script=1</script>"
PAYLOAD_MDLINK = "[click](javascript:window.__xss_mdlink=1)"
PAYLOAD_MIXTO = "Comentario <b>html</b> y [link](javascript:alert(1))"


def test_tag_html_crudo_queda_escapado():
    salida = seguro.escapar(PAYLOAD_IMG)
    # ninguna '<' o '>' cruda sobrevive: no puede formarse ningún tag real,
    # sin importar qué texto lleve adentro (onerror=, nombre de atributo, etc.)
    assert "<" not in salida
    assert ">" not in salida
    assert "&lt;img" in salida
    assert "&gt;" in salida


def test_script_crudo_queda_escapado():
    salida = seguro.escapar(PAYLOAD_SCRIPT)
    assert "<script>" not in salida
    assert "&lt;script&gt;" in salida


def test_negrita_e_inline_code_markdown_quedan_neutralizados():
    """`**bold**` y `` `code` `` son sintaxis markdown real: si no se
    escapan, un autor de reseña podría formatear texto arbitrario (o, con
    otros parsers, abrir vectores más allá de lo que Streamlit filtra)."""
    salida = seguro.escapar(PAYLOAD_SCRIPT)
    assert "**bold**" not in salida
    assert "\\*\\*bold\\*\\*" in salida
    assert "`code`" not in salida
    assert "\\`code\\`" in salida


def test_link_markdown_con_esquema_javascript_no_forma_un_link():
    """CommonMark solo reconoce `[texto](url)` con corchetes LITERALES.
    Escapando `[` y `]` con backslash, el parser nunca ve la sintaxis de
    link — no hay forma de que se genere un <a href="javascript:...">."""
    salida = seguro.escapar(PAYLOAD_MDLINK)
    assert "[click](javascript:" not in salida
    assert "\\[click\\]" in salida
    # el '(' y ')' quedan literales (no son sintaxis markdown por sí solos);
    # lo que importa es que ya no pueden emparejarse con un '[...]' real
    assert "(javascript:window." in salida


def test_payload_mixto_html_y_mdlink_ambos_neutralizados():
    salida = seguro.escapar(PAYLOAD_MIXTO)
    assert "<b>html</b>" not in salida
    assert "&lt;b&gt;html&lt;/b&gt;" in salida
    assert "[link](javascript:" not in salida
    assert "\\[link\\]" in salida


def test_comillas_quedan_escapadas_para_contexto_de_atributo_html():
    salida = seguro.escapar('nombre="valor" y \'otro\'')
    assert '"' not in salida
    assert "'" not in salida
    assert "&quot;" in salida
    assert "&#x27;" in salida


def test_entidad_html_generada_no_se_corrompe_con_el_escape_de_markdown():
    """Bug real durante el desarrollo: si el orden fuera html.escape primero
    y el escape de markdown después, el '#' de la entidad &#x27; se
    escaparía de nuevo (&\\#x27;) y quedaría rota. El orden correcto es
    markdown primero, html.escape al final."""
    salida = seguro.escapar("'")
    assert salida == "&#x27;"
    assert "\\#" not in salida


def test_texto_normal_sin_caracteres_especiales_no_cambia():
    assert seguro.escapar("Juan Pérez, Gerente de Operaciones") == "Juan Pérez, Gerente de Operaciones"


def test_none_no_rompe():
    assert seguro.escapar(None) == ""


def test_numero_se_convierte_a_texto():
    assert seguro.escapar(5) == "5"
