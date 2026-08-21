# © 2026 Martín Viera. Todos los derechos reservados.
"""La landing: paridad de idiomas y qué se ofrece descargar.

Dos cosas que fallan en silencio y esta suite fija:

**Las claves duplicadas.** Los diccionarios EN/PT son objetos literales de
JavaScript. Si una clave aparece dos veces, gana la ÚLTIMA y la primera se
ignora sin ningún error — ni en consola, ni en el build (no hay build). Me
pasó reescribiendo las tarjetas de la sección de demo: quedaron las nuevas
arriba y las viejas abajo, y en inglés se seguía leyendo el texto viejo.
Nadie lo hubiera notado sin cambiar el idioma y leer.

**La paridad.** `mvpm/i18n.py` tiene su test de paridad desde siempre; la
landing no tenía ninguno, aunque es la página donde alguien decide pagar. Una
clave que existe en el HTML y falta en el diccionario deja ese texto en
español dentro de la versión en inglés.
"""

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
LANDING = RAIZ / "landing" / "index.html"

if not LANDING.exists():
    pytest.skip("landing/ no viaja en el paquete: es del repositorio",
                allow_module_level=True)

HTML = LANDING.read_text(encoding="utf-8")


def _bloque_idioma(lang: str) -> str:
    """El texto del diccionario de un idioma dentro de I18N."""
    ini = HTML.index(f"  {lang}: {{")
    # Hasta el cierre del bloque: la línea que tiene sólo "  },"
    fin = HTML.index("\n  },", ini)
    return HTML[ini:fin]


def _claves(bloque: str) -> list[str]:
    """Las claves declaradas, EN ORDEN y con repetidos — que es el punto."""
    return re.findall(r'(?:^|[{,]\s*)([a-z][a-z0-9_]*)\s*:\s*"', bloque, re.MULTILINE)


@pytest.mark.parametrize("lang", ["en", "pt"])
def test_ninguna_clave_esta_declarada_dos_veces(lang):
    """En un objeto literal de JS, la segunda declaración pisa a la primera y
    no hay ningún aviso. Es la forma más silenciosa de dejar texto viejo
    publicado."""
    claves = _claves(_bloque_idioma(lang))
    repetidas = sorted({c for c in claves if claves.count(c) > 1})
    assert not repetidas, (
        f"claves duplicadas en el diccionario '{lang}': {repetidas}. "
        "Gana la última declarada, así que la primera nunca se muestra.")


@pytest.mark.parametrize("lang", ["en", "pt"])
def test_todo_texto_del_html_tiene_traduccion(lang):
    """Cada `data-i` / `data-i-ph` del HTML tiene que existir en los dos
    diccionarios, o ese texto queda en español para quien eligió otro idioma."""
    del_html = set(re.findall(r'data-i(?:-ph)?="([^"]+)"', HTML))
    del_dict = set(_claves(_bloque_idioma(lang)))
    faltan = sorted(del_html - del_dict)
    assert not faltan, f"sin traducir al '{lang}': {faltan}"


@pytest.mark.parametrize("lang", ["en", "pt"])
def test_no_sobran_traducciones_de_textos_que_ya_no_existen(lang):
    """El complemento: una clave que quedó en el diccionario y ya no está en
    el HTML es texto muerto que confunde al próximo que edite. Acá aparecieron
    `dl_btn`, `dl_req` y `dl_installer` después de sacar la descarga."""
    del_html = set(re.findall(r'data-i(?:-ph)?="([^"]+)"', HTML))
    # Las claves que el JS usa a mano (mensajes del formulario) no están en el
    # HTML y son legítimas: se listan para que la excepción sea explícita.
    solo_js = {c for c in _claves(_bloque_idioma(lang)) if c.startswith("demo_")
               and not c.startswith("demo_ph_")}
    sobran = sorted(set(_claves(_bloque_idioma(lang))) - del_html - solo_js)
    assert not sobran, (
        f"traducciones al '{lang}' de textos que ya no existen en el HTML: {sobran}")


# ------------------------------------------------- qué se ofrece descargar

def test_la_landing_no_ofrece_bajar_el_programa():
    """El cambio de criterio: la demo se muestra en vivo y no se descarga.

    Antes había un botón a un ZIP con 39 módulos de `mvpm/` en texto plano —
    el artefacto de ingeniería regalado, sin saber siquiera a quién. Este test
    impide que vuelva por descuido: cualquier enlace a un `.zip`/`.exe` acá es
    una regresión de la decisión comercial, no un detalle.
    """
    enlaces = re.findall(r'href="([^"]+)"', HTML)
    descargables = [h for h in enlaces
                    if re.search(r"\.(zip|exe|7z|msi|dmg)(\?|$)", h, re.I)]
    assert not descargables, f"la landing ofrece descargas directas: {descargables}"


def test_la_descarga_del_instalador_siempre_lleva_licencia():
    """`/api/download-installer` exige un token. Un enlace sin él le daría al
    cliente un 401 justo después de pagar, que es el peor momento posible."""
    sueltos = [h for h in re.findall(r'href="([^"]+)"', HTML)
               if "download-installer" in h and "token=" not in h]
    assert not sueltos, (
        f"enlaces a la descarga sin token: {sueltos}. El endpoint responde 401.")


def test_el_formulario_pide_los_cuatro_datos():
    """Nombre completo, empresa, país y email: sin los cuatro, un pedido de
    demo no distingue a un prospecto de alguien mirando."""
    seccion = HTML[HTML.index('id="form-demo"'):HTML.index("</form>",
                                                            HTML.index('id="form-demo"'))]
    for campo in ["d_nombre", "d_empresa", "d_pais", "d_email"]:
        assert f'id="{campo}"' in seccion, f"falta el campo {campo}"
        # `required` es la primera barrera; el servidor vuelve a validar.
        bloque = seccion[seccion.index(f'id="{campo}"'):]
        assert "required" in bloque[:220], f"{campo} no es obligatorio en el HTML"
    assert "/api/solicitar-demo" in HTML, "el formulario no apunta al endpoint"


def test_el_formulario_manda_los_mismos_nombres_que_espera_el_servidor():
    """El acuerdo entre las dos puntas. Si el HTML manda `nombre_completo` y
    el servidor lee `nombre`, el pedido se rechaza siempre y nada lo explica."""
    servidor = (RAIZ / "api" / "solicitar-demo.js").read_text(encoding="utf-8")
    cuerpo = HTML[HTML.index("function solicitarDemo"):]
    cuerpo = cuerpo[:cuerpo.index("return false;")]
    enviados = set(re.findall(r"^\s+(\w+): document\.getElementById",
                              cuerpo, re.MULTILINE))
    assert enviados == {"nombre", "empresa", "pais", "email", "mensaje"}, enviados
    for campo in enviados:
        assert f"body.{campo}" in servidor, (
            f"la landing manda '{campo}' y solicitar-demo.js no lo lee")


def test_los_mensajes_de_error_del_formulario_cubren_los_del_servidor():
    """Un código de error sin mensaje cae en el genérico "escribime al mail",
    que en el caso de un nombre incompleto es una respuesta inútil."""
    servidor = (RAIZ / "api" / "solicitar-demo.js").read_text(encoding="utf-8")
    codigos = set(re.findall(r"error: '(\w+)'", servidor)) | set(
        re.findall(r"return \{ error: `?(\w+)", servidor))
    # `falta_${campo}` se arma dinámicamente; se expande a mano.
    codigos.discard("falta")
    codigos |= {f"falta_{c}" for c in ("nombre", "email", "empresa", "pais")}
    # Estos no son errores de validación del formulario.
    codigos -= {"method", "no_registrado", "sin_proveedor"}
    js = HTML[HTML.index("function solicitarDemo"):]
    faltan = sorted(c for c in codigos if c not in js)
    assert not faltan, f"el formulario no explica estos errores: {faltan}"
