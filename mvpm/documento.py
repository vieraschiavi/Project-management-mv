# © 2026 Martín Viera. Todos los derechos reservados.
"""La bitácora técnica, exportada a HTML, Word y PDF.

**Sin dependencias nuevas, y es una decisión, no una limitación.** Un `.docx`
es un ZIP con XML adentro y un PDF es texto con una tabla de offsets al final:
las dos cosas se arman con la biblioteca estándar. La alternativa era sumar
`python-docx` y `reportlab` —unos 20 MB entre las dos— a un producto que se
distribuye como instalador de escritorio y como ZIP portable, para generar dos
documentos de texto. No vale.

Qué significa "real" acá, para no prometer de más:

  · **HTML** — un solo archivo, sin CSS externo ni fuentes remotas: se abre
    igual en una máquina sin internet, que es donde suele estar el cliente.
  · **Word** — `.docx` de verdad (OOXML mínimo pero válido), no un HTML con
    la extensión cambiada. Word lo abre y lo deja editar como cualquier otro.
  · **PDF** — PDF 1.4 con las fuentes base-14 (Helvetica), que TODO lector
    trae incorporadas. No se embeben fuentes, así que el archivo pesa poco;
    a cambio, el texto se codifica en Latin-1 y lo que no entra en esa tabla
    se translitera en vez de romper el archivo.

Todo lo que se exporta sale de `mvpm/bitacora.py`. Este módulo no tiene una
sola frase de contenido propio: si dijera algo distinto del programa, sería un
folleto, no una bitácora.
"""

from __future__ import annotations

import io
import unicodedata
import zipfile
from datetime import date, timezone
from xml.sax.saxutils import escape

from mvpm import APP_NAME, VERSION, bitacora

#: Encabezados de las cuatro secciones de cada etapa. Van acá y no en
#: `bitacora.py` porque son etiquetas del documento, no contenido.
_ETIQUETAS = {
    "es": {"tecnico": "En términos técnicos", "criollo": "En criollo",
           "porque": "Por qué se hizo así", "repercusion": "Cómo repercute",
           "modulo": "Implementado en", "titulo": "Bitácora técnica del pipeline",
           "bajada": "Qué le pasa al dato desde que entra hasta que sale, etapa por "
                     "etapa: la versión técnica y la versión en criollo de cada "
                     "transformación, por qué se hizo así y qué cambia aguas abajo.",
           "generado": "Generado el"},
    "en": {"tecnico": "In technical terms", "criollo": "In plain words",
           "porque": "Why it was built this way", "repercusion": "What it affects",
           "modulo": "Implemented in", "titulo": "Technical pipeline log",
           "bajada": "What happens to the data from the moment it comes in until it "
                     "goes out, stage by stage: the technical version and the plain "
                     "version of each transformation, why it was built that way and "
                     "what changes downstream.",
           "generado": "Generated on"},
    "pt": {"tecnico": "Em termos técnicos", "criollo": "Em linguagem simples",
           "porque": "Por que foi feito assim", "repercusion": "Como repercute",
           "modulo": "Implementado em", "titulo": "Registro técnico do pipeline",
           "bajada": "O que acontece com o dado desde que entra até sair, etapa por "
                     "etapa: a versão técnica e a versão em linguagem simples de cada "
                     "transformação, por que foi feito assim e o que muda rio abaixo.",
           "generado": "Gerado em"},
}

_CUERPO = ("tecnico", "criollo", "porque", "repercusion")


def _etiquetas(lang: str) -> dict:
    return _ETIQUETAS.get(lang, _ETIQUETAS["es"])


def _hoy() -> str:
    from datetime import datetime
    return datetime.now(timezone.utc).date().isoformat()


# ------------------------------------------------------------------- HTML

def a_html(lang: str = "es", hoy: str | None = None) -> str:
    """Un solo archivo, con el CSS embebido: se abre sin internet."""
    t = _etiquetas(lang)
    partes = [
        "<!DOCTYPE html>",
        f'<html lang="{escape(lang)}"><head><meta charset="utf-8">',
        f"<title>{escape(t['titulo'])} — {escape(APP_NAME)}</title>",
        "<style>",
        "body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;",
        "max-width:52em;margin:0 auto;padding:2.5rem 1.5rem;line-height:1.6;",
        "color:#16202e;background:#fff;}",
        "h1{font-size:1.9rem;margin-bottom:.25rem;}",
        ".bajada{color:#5a6675;margin-top:0;}",
        ".meta{color:#8a94a2;font-size:.85rem;border-bottom:1px solid #e3e8ee;",
        "padding-bottom:1.25rem;margin-bottom:2rem;}",
        "section{border-left:3px solid #f2b441;padding-left:1.25rem;margin:2.5rem 0;}",
        "h2{font-size:1.25rem;margin:0 0 .2rem;}",
        ".modulo{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;",
        "font-size:.8rem;color:#8a94a2;margin:0 0 1rem;}",
        "h3{font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;",
        "color:#2f74c0;margin:1.1rem 0 .3rem;}",
        "p{margin:.3rem 0;}",
        "@media print{section{break-inside:avoid;}}",
        "</style></head><body>",
        f"<h1>{escape(t['titulo'])}</h1>",
        f'<p class="bajada">{escape(t["bajada"])}</p>',
        f'<p class="meta">{escape(APP_NAME)} v{escape(VERSION)} · '
        f'{escape(t["generado"])} {escape(hoy or _hoy())}</p>',
    ]
    for e in bitacora.etapas(lang):
        partes.append("<section>")
        partes.append(f"<h2>{escape(e['titulo'])}</h2>")
        partes.append(f'<p class="modulo">{escape(t["modulo"])}: {escape(e["modulo"])}</p>')
        for campo in _CUERPO:
            partes.append(f"<h3>{escape(t[campo])}</h3>")
            partes.append(f"<p>{escape(e[campo])}</p>")
        partes.append("</section>")
    partes.append("</body></html>")
    return "\n".join(partes)


# ------------------------------------------------------------------- Word

def _p(texto: str, *, size: int = 22, bold: bool = False,
       color: str | None = None, space_before: int = 0) -> str:
    """Un párrafo de OOXML. `size` va en medios puntos, que es como lo mide
    Word: 22 = 11pt."""
    rpr = [f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>']
    if bold:
        rpr.append("<w:b/>")
    if color:
        rpr.append(f'<w:color w:val="{color}"/>')
    ppr = f'<w:spacing w:before="{space_before}"/>' if space_before else ""
    return (f"<w:p><w:pPr>{ppr}</w:pPr>"
            f"<w:r><w:rPr>{''.join(rpr)}</w:rPr>"
            f'<w:t xml:space="preserve">{escape(texto)}</w:t></w:r></w:p>')


def a_docx_bytes(lang: str = "es", hoy: str | None = None) -> bytes:
    """Un `.docx` real: ZIP + OOXML mínimo, abierto por Word sin conversión.

    Las cuatro partes son las que exige el formato: el mapa de tipos de
    contenido, la relación raíz que dice cuál es el documento principal, el
    documento en sí y sus propias relaciones (vacías acá: no hay imágenes ni
    hipervínculos). Sacar cualquiera de las cuatro da un archivo que Word
    rechaza como dañado."""
    t = _etiquetas(lang)
    cuerpo = [
        _p(t["titulo"], size=36, bold=True),
        _p(t["bajada"], size=20, color="5A6675"),
        _p(f"{APP_NAME} v{VERSION} · {t['generado']} {hoy or _hoy()}",
           size=16, color="8A94A2"),
    ]
    for e in bitacora.etapas(lang):
        cuerpo.append(_p(e["titulo"], size=28, bold=True, space_before=360))
        cuerpo.append(_p(f"{t['modulo']}: {e['modulo']}", size=16, color="8A94A2"))
        for campo in _CUERPO:
            cuerpo.append(_p(t[campo], size=18, bold=True, color="2F74C0",
                             space_before=160))
            cuerpo.append(_p(e[campo]))

    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(cuerpo)}</w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/></Relationships>'
    )
    doc_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)
        z.writestr("word/_rels/document.xml.rels", doc_rels)
    return buf.getvalue()


# -------------------------------------------------------------------- PDF

_ANCHO, _ALTO = 595, 842          # A4 en puntos
_MARGEN = 56
_BASE = _ANCHO - 2 * _MARGEN

# Anchos por carácter de Helvetica, en milésimas de punto. No es la tabla
# completa de métricas: es un promedio por clase de carácter, suficiente para
# cortar renglones que entren en el ancho útil. Errar por ancho de más es
# inofensivo (corta antes); errar por menos escribiría fuera del margen.
_ANCHO_CAR = 0.52


def _latin1(texto: str) -> str:
    """Lo que no entra en Latin-1 se translitera en vez de romper el archivo.

    Sin esto, un solo carácter fuera de la tabla —la comilla tipográfica, el
    guión largo, el `·` de los títulos— tira una excepción y no se genera
    ningún PDF. Un documento con "..." en vez de "…" es infinitamente mejor
    que un botón de descarga que falla."""
    reemplazos = {"…": "...", "—": "-", "–": "-", "·": "-",
                  "“": '"', "”": '"', "‘": "'", "’": "'", "«": '"', "»": '"'}
    for viejo, nuevo in reemplazos.items():
        texto = texto.replace(viejo, nuevo)
    try:
        texto.encode("latin-1")
        return texto
    except UnicodeEncodeError:
        # Descompone los acentos y descarta lo que siga sin entrar.
        normal = unicodedata.normalize("NFKD", texto)
        return normal.encode("latin-1", "ignore").decode("latin-1")


def _escapar_pdf(texto: str) -> str:
    return texto.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _wrap(texto: str, size: float, ancho: float = _BASE) -> list[str]:
    max_car = max(8, int(ancho / (size * _ANCHO_CAR)))
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if len(prueba) <= max_car or not actual:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas or [""]


def a_pdf_bytes(lang: str = "es", hoy: str | None = None) -> bytes:
    """PDF 1.4 con fuentes base-14: sin embeber nada, lo abre cualquier lector."""
    t = _etiquetas(lang)

    # 1) El documento como lista de renglones (texto, tamaño, negrita, salto).
    renglones: list[tuple[str, float, bool, float]] = []

    def escribir(texto: str, size: float, bold: bool, antes: float = 0.0) -> None:
        for i, linea in enumerate(_wrap(texto, size)):
            renglones.append((_latin1(linea), size, bold, antes if i == 0 else 0.0))

    escribir(t["titulo"], 19, True)
    escribir(t["bajada"], 9.5, False, 6)
    escribir(f"{APP_NAME} v{VERSION} - {t['generado']} {hoy or _hoy()}", 8, False, 6)
    for e in bitacora.etapas(lang):
        escribir(e["titulo"], 13, True, 22)
        escribir(f"{t['modulo']}: {e['modulo']}", 8, False, 2)
        for campo in _CUERPO:
            escribir(t[campo].upper(), 8, True, 10)
            escribir(e[campo], 10, False, 2)

    # 2) Paginado: se corta cuando el cursor pasa el margen inferior.
    paginas: list[list[tuple[str, float, bool, float, float]]] = [[]]
    y = _ALTO - _MARGEN
    for texto, size, bold, antes in renglones:
        alto = size * 1.32
        if y - (alto + antes) < _MARGEN:
            paginas.append([])
            y = _ALTO - _MARGEN
        y -= alto + antes
        paginas[-1].append((texto, size, bold, antes, y))

    # 3) Objetos PDF. El orden importa: los offsets de la xref se calculan
    #    sobre el archivo ya serializado.
    n_pag = len(paginas)
    obj: dict[int, bytes] = {}
    id_content = 5
    ids_pagina = [id_content + n_pag + i for i in range(n_pag)]

    obj[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids = " ".join(f"{i} 0 R" for i in ids_pagina)
    obj[2] = f"<< /Type /Pages /Kids [{kids}] /Count {n_pag} >>".encode("latin-1")
    obj[3] = (b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
              b"/Encoding /WinAnsiEncoding >>")
    obj[4] = (b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold "
              b"/Encoding /WinAnsiEncoding >>")

    for p, contenido in enumerate(paginas):
        trozos = ["BT"]
        for texto, size, bold, _antes, yy in contenido:
            fuente = "/F2" if bold else "/F1"
            trozos.append(f"1 0 0 1 {_MARGEN} {yy:.1f} Tm")
            trozos.append(f"{fuente} {size:.1f} Tf")
            trozos.append(f"({_escapar_pdf(texto)}) Tj")
        trozos.append("ET")
        flujo = "\n".join(trozos).encode("latin-1")
        obj[id_content + p] = (
            f"<< /Length {len(flujo)} >>\nstream\n".encode("latin-1")
            + flujo + b"\nendstream")
        obj[ids_pagina[p]] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {_ANCHO} {_ALTO}] "
            f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
            f"/Contents {id_content + p} 0 R >>".encode("latin-1"))

    salida = bytearray(b"%PDF-1.4\n")
    offsets: dict[int, int] = {}
    for num in sorted(obj):
        offsets[num] = len(salida)
        salida += f"{num} 0 obj\n".encode("latin-1") + obj[num] + b"\nendobj\n"

    inicio_xref = len(salida)
    total = max(obj) + 1
    salida += f"xref\n0 {total}\n".encode("latin-1")
    salida += b"0000000000 65535 f \n"
    for num in range(1, total):
        salida += f"{offsets.get(num, 0):010d} 00000 n \n".encode("latin-1")
    salida += (f"trailer\n<< /Size {total} /Root 1 0 R >>\n"
               f"startxref\n{inicio_xref}\n%%EOF\n").encode("latin-1")
    return bytes(salida)


def nombre_archivo(lang: str, extension: str, hoy: str | None = None) -> str:
    """Nombre estable y fechado, para que dos exportaciones del mismo día no
    se pisen en la carpeta de descargas con nombres distintos."""
    return f"bitacora_tecnica_{lang}_{hoy or date.today().isoformat()}.{extension}"
