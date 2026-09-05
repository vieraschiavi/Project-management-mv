# © 2026 Martín Viera. Todos los derechos reservados.
"""La bitácora técnica y sus tres exportaciones.

Lo que se fija acá, en orden de qué tan caro sale si falla:

 1. **Que la bitácora no describa un producto que no existe.** Cada etapa
    nombra el archivo que la implementa; si ese archivo se renombra o se
    borra, el documento pasa a mentirle a un comité. Un archivo inexistente
    citado en un informe firmado es peor que no tener informe.
 2. **Que los tres formatos se abran de verdad.** Un `.docx` inválido no
    avisa: pesa lo mismo, se descarga igual y recién falla en la máquina de
    quien lo iba a leer. Se verifica la estructura que exige cada formato, no
    que el archivo "parezca" correcto.
 3. **La paridad ES/EN/PT**, misma regla que el resto del producto.
 4. **Que la pantalla y el documento digan lo mismo** — si divergen, el
    exportable deja de servir para lo único que existe.

Sobre los validadores: `python-docx` y `pypdf` NO están en requirements.txt a
propósito (el producto no los necesita, y son ~20 MB en un instalador de
escritorio). Los tests que los usan se saltean donde no están, y quedan los
que verifican la estructura con la biblioteca estándar — que corren siempre,
también en CI.
"""

import re
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

from mvpm import bitacora, documento, i18n

RAIZ = Path(__file__).resolve().parent.parent


# ------------------------------------------------ el contenido es honesto

def test_cada_etapa_nombra_un_archivo_que_existe():
    """EL test de este módulo. Una bitácora que cita `mvpm/loquesea.py` y ese
    módulo no está, es un informe que no se puede defender."""
    faltan = [(e["clave"], e["modulo"]) for e in bitacora.etapas()
              if not (RAIZ / e["modulo"]).exists()]
    assert not faltan, f"etapas que citan archivos inexistentes: {faltan}"


def test_las_etapas_estan_numeradas_en_orden():
    """El pedido era "en orden secuencial del pipeline": si alguien inserta una
    etapa en el medio y no renumera, el documento se lee salteado."""
    numeros = []
    for e in bitacora.etapas():
        m = re.match(r"^(\d+)\s*·", e["titulo"])
        assert m, f"la etapa {e['clave']!r} no empieza con su número: {e['titulo']!r}"
        numeros.append(int(m.group(1)))
    assert numeros == list(range(1, len(numeros) + 1)), (
        f"la numeración no es correlativa: {numeros}")


def test_ninguna_etapa_llega_vacia_en_ningun_idioma():
    for lang in bitacora.LANGS:
        for e in bitacora.etapas(lang):
            for campo in bitacora.CAMPOS:
                assert e[campo].strip(), f"[{lang}] {e['clave']}.{campo} vacío"


def test_la_clave_y_el_modulo_no_se_traducen():
    """`clave` ordena y la usan los tests; `modulo` es una ruta real. Si alguna
    de las dos se tradujera, la etapa dejaría de ser la misma entre idiomas."""
    base = {(e["clave"], e["modulo"]) for e in bitacora.etapas("es")}
    for lang in ("en", "pt"):
        assert {(e["clave"], e["modulo"]) for e in bitacora.etapas(lang)} == base


@pytest.mark.parametrize("lang", ["en", "pt"])
def test_ninguna_traduccion_quedo_igual_al_español(lang):
    """Una traducción idéntica al español es, casi siempre, una que no se hizo."""
    iguales = [
        f"{e['clave']}.{campo}"
        for e, o in zip(bitacora.etapas("es"), bitacora.etapas(lang))
        for campo in ("tecnico", "criollo", "porque", "repercusion")
        if e[campo] == o[campo]
    ]
    assert not iguales, f"sin traducir al {lang}: {iguales}"


def test_el_criollo_no_es_el_texto_tecnico_otra_vez():
    """El punto entero de la pestaña es que haya DOS registros. Si el criollo
    repite el técnico, se pierde el gerente, que es para quien se escribió."""
    for lang in bitacora.LANGS:
        for e in bitacora.etapas(lang):
            assert e["criollo"] != e["tecnico"], (
                f"[{lang}] {e['clave']}: el criollo es una copia del técnico")


# ------------------------------------------------------ los tres formatos

def test_el_html_es_autocontenido():
    """Sin CSS ni fuentes remotas: se abre en una máquina sin internet, que es
    donde suele estar el cliente cuando lo abre."""
    html = documento.a_html("es")
    assert html.startswith("<!DOCTYPE html>")
    assert "<style>" in html, "el CSS dejó de ir embebido"
    for remoto in ("http://", "https://", "<script"):
        assert remoto not in html, f"el HTML dejó de ser autocontenido: {remoto!r}"


def test_el_html_trae_todas_las_etapas_en_los_tres_idiomas():
    for lang in bitacora.LANGS:
        html = documento.a_html(lang)
        for e in bitacora.etapas(lang):
            assert e["clave"] in html or e["titulo"].split("·")[-1].strip()[:20] in html


def test_el_docx_tiene_las_cuatro_partes_que_exige_el_formato():
    """Un .docx sin cualquiera de estas cuatro es un archivo que Word declara
    dañado. Se verifica con `zipfile` de la biblioteca estándar, así que este
    test corre también donde no está python-docx."""
    with zipfile.ZipFile(BytesIO(documento.a_docx_bytes("es"))) as z:
        partes = set(z.namelist())
        assert z.testzip() is None, "el ZIP del .docx está corrupto"
        for obligatoria in ("[Content_Types].xml", "_rels/.rels",
                            "word/document.xml", "word/_rels/document.xml.rels"):
            assert obligatoria in partes, f"al .docx le falta {obligatoria}"
        doc = z.read("word/document.xml").decode("utf-8")
    assert doc.startswith("<?xml"), "document.xml sin declaración XML"
    assert "<w:body>" in doc and "</w:document>" in doc


def test_el_docx_escapa_el_xml():
    """Un `&` o un `<` sin escapar rompe el documento entero, y el contenido
    real trae comillas y símbolos. Se verifica que el XML parsee."""
    from xml.etree import ElementTree

    for lang in bitacora.LANGS:
        with zipfile.ZipFile(BytesIO(documento.a_docx_bytes(lang))) as z:
            ElementTree.fromstring(z.read("word/document.xml"))


def test_el_pdf_tiene_la_estructura_minima():
    pdf = documento.a_pdf_bytes("es")
    assert pdf.startswith(b"%PDF-1.4"), "no declara versión de PDF"
    assert pdf.rstrip().endswith(b"%%EOF"), "el PDF quedó sin cerrar"
    assert b"xref" in pdf and b"startxref" in pdf, "sin tabla de referencias"
    assert b"/Type /Catalog" in pdf and b"/Type /Pages" in pdf
    assert pdf.count(b"/Type /Page ") >= 1, "el PDF no tiene ni una página"


def test_el_offset_de_la_xref_apunta_donde_dice():
    """El error clásico de un PDF armado a mano: la tabla de offsets queda
    desfasada y el lector abre un archivo vacío sin decir por qué."""
    pdf = documento.a_pdf_bytes("es")
    inicio = int(pdf.split(b"startxref")[-1].split(b"%%EOF")[0].strip())
    assert pdf[inicio:inicio + 4] == b"xref", (
        f"startxref apunta a {inicio}, donde no empieza la xref")


def test_el_pdf_no_revienta_con_caracteres_fuera_de_latin1():
    """Las fuentes base-14 son Latin-1. Un solo carácter fuera de tabla tiraba
    una excepción y no se generaba NINGÚN PDF — mejor transliterar."""
    assert documento._latin1("guión — y comillas “así” y puntos…") == (
        "guión - y comillas \"así\" y puntos...")
    raro = documento._latin1("emoji 🚀 y chino 中文")
    raro.encode("latin-1")  # no debe lanzar


def test_los_tres_formatos_salen_en_los_tres_idiomas():
    for lang in bitacora.LANGS:
        assert len(documento.a_html(lang)) > 2000
        assert len(documento.a_docx_bytes(lang)) > 2000
        assert len(documento.a_pdf_bytes(lang)) > 2000


def test_el_nombre_de_archivo_lleva_idioma_y_fecha():
    n = documento.nombre_archivo("en", "pdf", hoy="2026-09-05")
    assert n == "bitacora_tecnica_en_2026-09-05.pdf"


# ------------------------------------- la pantalla y el documento coinciden

def test_la_pestaña_y_el_documento_usan_las_mismas_etiquetas():
    """Si la pantalla dijera "En criollo" y el PDF otra cosa, el exportable
    dejaría de ser el mismo informe que se revisó antes de mandarlo."""
    for lang in bitacora.LANGS:
        for campo in ("tecnico", "criollo", "porque", "repercusion", "modulo"):
            assert i18n.t(f"bit_{campo}", lang) == documento._etiquetas(lang)[campo], (
                f"[{lang}] la etiqueta {campo!r} difiere entre la app y el documento")


def test_la_pestaña_esta_enganchada_al_nav():
    app = (RAIZ / "app" / "app.py").read_text(encoding="utf-8")
    assert 'T("nav_bitacora")' in app, "la sección no está en el nav"
    assert 'elif section == T("nav_bitacora")' in app, "el nav apunta a una sección vacía"
    # Y baja los tres formatos, no uno.
    for fn in ("a_html", "a_docx_bytes", "a_pdf_bytes"):
        assert f"documento.{fn}" in app, f"la pestaña no ofrece {fn}"


# ----------------------------- validación con parsers reales (si están)

def test_word_puede_abrir_el_docx():
    """Con el parser que usa Word. Se saltea donde no está python-docx: es una
    dependencia de verificación, no del producto."""
    docx = pytest.importorskip("docx", reason="python-docx es sólo para verificar")
    for lang in bitacora.LANGS:
        doc = docx.Document(BytesIO(documento.a_docx_bytes(lang)))
        textos = [p.text for p in doc.paragraphs]
        for e in bitacora.etapas(lang):
            assert e["titulo"] in textos, f"[{lang}] falta la etapa {e['clave']}"


def test_un_lector_de_pdf_extrae_el_texto():
    pypdf = pytest.importorskip("pypdf", reason="pypdf es sólo para verificar")
    for lang in bitacora.LANGS:
        lector = pypdf.PdfReader(BytesIO(documento.a_pdf_bytes(lang)))
        assert len(lector.pages) >= 2
        texto = "\n".join(p.extract_text() or "" for p in lector.pages)
        for e in bitacora.etapas(lang):
            esperado = documento._latin1(e["titulo"])
            assert esperado in texto, f"[{lang}] {e['clave']} no aparece en el PDF"
