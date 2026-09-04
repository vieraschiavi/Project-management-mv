# © 2026 Martín Viera. Todos los derechos reservados.
"""
MV Project Management · Generador del video demo (PIL + imageio-ffmpeg) con
contenido en pantalla Y narración en los 3 idiomas del producto (Piper TTS:
es_AR "daniela", en_US "amy", pt_BR "faber").

Produce un ``demo.mp4`` por idioma (1280×720): el mismo recorrido animado del
producto, pero renderizado ENTERO en ese idioma —texto en pantalla y voz en
off, no sólo la voz— con la duración de cada escena ajustada a su narración,
sin desfases. Es una animación explicativa del producto —no un screencast— y
así se declara en la landing.

Por qué el texto en pantalla también se traduce (y no sólo el audio, como en
la versión anterior de este script): una persona viendo el video en inglés
que lee "Portafolio con salud en 6 dimensiones" en pantalla mientras escucha
"Portfolio health across 6 dimensions" en el audio no experimenta un producto
en inglés — experimenta una traducción a medias. El texto de cada escena vive
en ``TEXTS[lang]``, con la misma clave en los tres idiomas.

Ningún tamaño de fuente ni ancho de caja está fijo a mano por idioma: todo
texto que entra en una caja (tarjeta, pastilla, párrafo) pasa por
``fit_font``/``fit_paragraph``, que reducen el tamaño hasta que el texto
entra en el ancho/alto disponible. Sin esto, una traducción más larga que el
español original (frecuente en inglés y portugués) se saldría de su caja o se
superpondría con el elemento de al lado — el tamaño se ajusta al marco del
contenido, no al revés.

Ejecutar desde la raíz del repo:
    python assets/video/build_video.py

Voz (opcional pero recomendada): descargar los modelos una vez y exportar
cada ruta en su variable. El idioma que no tenga modelo configurado sale sin
narración (silencioso, no se salta).
    pip install piper-tts
    curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_AR/daniela/high/es_AR-daniela-high.onnx{,.json}
    curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx{,.json}
    curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx{,.json}
    MVPM_VOICE_ONNX_ES=./es_AR-daniela-high.onnx \\
    MVPM_VOICE_ONNX_EN=./en_US-amy-medium.onnx \\
    MVPM_VOICE_ONNX_PT=./pt_BR-faber-medium.onnx \\
    python assets/video/build_video.py

Compatibilidad: MVPM_VOICE_ONNX (sin sufijo) sigue funcionando como alias de
MVPM_VOICE_ONNX_ES, para no romper el flujo anterior de un solo idioma.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import wave

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 720
FPS = 24
NAVY = (8, 21, 39)
NAVY2 = (13, 36, 64)
AMBER = (242, 180, 65)
BLUE = (47, 116, 192)
GREEN = (0, 200, 150)
RED = (224, 92, 92)
PURPLE = (196, 121, 232)
INK = (234, 241, 251)
MUTED = (157, 176, 200)
FAINT = (108, 127, 153)

_FONT_DIR = "/usr/share/fonts/truetype/dejavu"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# "es" mantiene el nombre de archivo histórico (demo.mp4) porque la landing
# ya apunta ahí por defecto; en/pt suman el sufijo de idioma.
_SUFFIX = {"es": "", "en": "_en", "pt": "_pt"}
LANGS = ("es", "en", "pt")


def _out_path(lang: str) -> str:
    return os.path.join(ROOT, "assets", "video", f"demo{_SUFFIX[lang]}.mp4")


def _landing_path(lang: str) -> str:
    return os.path.join(ROOT, "landing", "video", f"demo{_SUFFIX[lang]}.mp4")


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(os.path.join(_FONT_DIR, name), size)
    except OSError:
        return ImageFont.load_default()


def base_frame() -> Image.Image:
    img = Image.new("RGB", (W, H), NAVY)
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W * 0.62, -H * 0.35, W * 1.25, H * 0.45], fill=(36, 27, 8))
    gd.ellipse([-W * 0.2, -H * 0.1, W * 0.38, H * 0.55], fill=(9, 23, 40))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    return Image.blend(img, Image.blend(img, glow, 0.9), 0.55)


def ease(p: float) -> float:
    p = max(0.0, min(1.0, p))
    return 3 * p * p - 2 * p * p * p


def center_text(d: ImageDraw.ImageDraw, y: int, text: str,
                f: ImageFont.FreeTypeFont, fill):
    w = d.textlength(text, font=f)
    d.text(((W - w) / 2, y), text, font=f, fill=fill)


def badge(d: ImageDraw.ImageDraw, cx: int, y: int, text: str, f):
    w = d.textlength(text, font=f)
    pad = 16
    d.rounded_rectangle([cx - w / 2 - pad, y - 8, cx + w / 2 + pad, y + 30],
                        radius=19, outline=AMBER, width=2, fill=(24, 22, 12))
    d.text((cx - w / 2, y - 1), text, font=f, fill=AMBER)


# ------------------------------------------------------------ texto que cabe
#
# Nada de lo que sigue fija un tamaño de fuente "a ojo" para una traducción en
# particular: cada función mide el texto real contra el ancho/alto de SU caja
# y reduce el tamaño hasta que entra. Así una traducción más larga (el inglés
# y el portugués suelen serlo frente al español) nunca se sale de su marco ni
# pisa al elemento de al lado — el tamaño se adapta al contenido, no al revés.


def fit_font(d: ImageDraw.ImageDraw, text: str, max_width: float,
             max_size: int, min_size: int = 13, bold: bool = True) -> ImageFont.FreeTypeFont:
    size = max_size
    while size > min_size:
        f = font(size, bold)
        if d.textlength(text, font=f) <= max_width:
            return f
        size -= 1
    return font(min_size, bold)


def center_text_fit(d: ImageDraw.ImageDraw, y: int, text: str, max_size: int,
                    max_width: float, fill, bold: bool = True, min_size: int = 15):
    f = fit_font(d, text, max_width, max_size, min_size, bold)
    center_text(d, y, text, f, fill)


def wrap_lines(d: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont,
              max_width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if not cur or d.textlength(trial, font=f) <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_paragraph(d: ImageDraw.ImageDraw, text: str, max_width: float, max_height: float,
                  max_size: int, min_size: int = 14, bold: bool = False,
                  line_gap: float = 1.35) -> tuple[ImageFont.FreeTypeFont, list[str], float]:
    """Reduce el tamaño hasta que el párrafo entero —ya wrappeado a
    ``max_width``— entra en ``max_height``. Devuelve la fuente, las líneas y
    el alto de línea a usar para dibujarlas."""
    size = max_size
    while size >= min_size:
        f = font(size, bold)
        lines = wrap_lines(d, text, f, max_width)
        line_h = size * line_gap
        if line_h * len(lines) <= max_height:
            return f, lines, line_h
        size -= 1
    f = font(min_size, bold)
    lines = wrap_lines(d, text, f, max_width)
    return f, lines, min_size * line_gap


def _kpi_card(d, x, y, w, h, label, value, vcolor):
    d.rounded_rectangle([x, y, x + w, y + h], radius=14,
                        fill=(15, 33, 53), outline=(29, 49, 73), width=2)
    lf = fit_font(d, label, w - 36, 14, 10, bold=False)
    d.text((x + 18, y + 14), label, font=lf, fill=MUTED)
    vf = fit_font(d, value, w - 36, 32, 20, bold=True)
    d.text((x + 18, y + 38), value, font=vf, fill=vcolor)


def _pill(d, x, y, text, col, f):
    pw = d.textlength(text, font=f)
    d.rounded_rectangle([x - 8, y - 2, x + pw + 10, y + 24], radius=12,
                        outline=col, width=2)
    d.text((x + 1, y), text, font=f, fill=col)
    return pw + 18


# -------------------------------------------------------- texto en pantalla
#
# Misma clave en los 3 idiomas — cada escena la lee con TEXTS[lang]["clave"].
# Los nombres propios (laboratorios reales, "Ana Pérez", el endpoint técnico
# de la API) no se traducen a propósito: son datos o código, no prosa.

TEXTS = {
    "es": {
        "intro_tagline": "Portafolio con salud medible, no reuniones de estado",
        "intro_badge": "100% WEB + PC · ES / EN / PT · IA ADITIVA",
        "portfolio_h": "Portafolio con salud en 6 dimensiones",
        "portfolio_sub": "Alcance · cronograma · presupuesto · riesgo · dependencias · equipo",
        "portfolio_kpi1": "PROYECTOS", "portfolio_kpi2": "ÍNDICE DE SALUD",
        "portfolio_kpi3": "TAREAS BLOQUEADAS",
        "portfolio_proyectos": ["Migración de facturación", "Expansión Paraguay",
                                "Migración de CRM", "Portal de clientes"],
        "pharma_h": "Dataset real de laboratorio → Power BI",
        "pharma_sub": "474 ensayos clínicos reales · ClinicalTrials.gov (NIH) · dominio público",
        "pharma_crit": "Estado clínico → criticidad de portafolio:",
        "pharma_pill1": "135 completados → Baja", "pharma_pill2": "120 reclutando → Media",
        "pharma_pill3": "9 suspendidos → Alta",
        "pharma_connector": "Conector .pbids de un clic → Power BI",
        "pharma_honest": "Honesto: ClinicalTrials.gov no publica presupuesto → queda en 0 con nota",
        "gov_h": "La IA propone, el responsable valida",
        "gov_sub": "Definiciones preestablecidas · validadas por el data owner · versionadas",
        "gov_steps": [
            ("1 · IA RECOMIENDA", "Alcance: trabajo incluido y excluido que define el límite del proyecto.", BLUE),
            ("2 · EL DUEÑO VALIDA", "Ana Pérez (Data Owner) revisa, ajusta el texto y lo guarda.", AMBER),
            ("3 · QUEDA VERSIONADO", "Historial por empresa: quién, cuándo, nombre y cargo.", GREEN),
        ],
        "org_h": "Organigrama → responsables por etapa",
        "org_sub": "Subís Excel, CSV o base SQL · la IA autocompleta áreas y responsables",
        "org_file": "▤ organigrama.xlsx", "org_cols": "cargos · áreas · reporta_a",
        "org_arrow": "→  IA  →",
        "org_etapas": [("Inicio", "M. Rodríguez · PMO"),
                       ("Planificación", "L. Fernández · Jefa de Proyectos"),
                       ("Ejecución", "C. Gómez · Líder Técnico"),
                       ("Seguimiento", "A. Pérez · Data Owner"),
                       ("Cierre", "R. Silva · Sponsor")],
        "pmbok_h": "PMBOK técnico y \"en criollo\"",
        "pmbok_sub": "10 áreas de conocimiento + 5 grupos de proceso · con nota editable por empresa",
        "pmbok_tag_tec": "TÉCNICO", "pmbok_tag_criollo": "EN CRIOLLO",
        "pmbok_tecnico": "Gestión del Cronograma: procesos para administrar la terminación en plazo "
                        "del proyecto — secuenciar actividades, estimar duraciones, controlar la "
                        "línea base del cronograma.",
        "pmbok_criollo": "Que las tareas estén en orden y que sepas si vas a llegar con los tiempos. "
                         "Si algo se atrasa, cuánto te corre todo lo demás — antes de que te "
                         "explote encima.",
        "pmbok_footer": "Cada etapa no automatizable se anota a mano y se guarda por empresa",
        "trial_h": "Prueba completa de 7 días",
        "trial_sub": "Descargás el programa completo — todo desbloqueado, sin recortes",
        "trial_line1": "Al día 8 se bloquea — pero tus datos NO se borran.",
        "trial_line2": "Cargás tu licencia Professional y seguís exactamente donde estabas.",
        "trial_badge": "US$9 / usuario / mes · se cobra en pesos al cambio del día",
        "outro_tagline": "Tu portafolio, gobernado de punta a punta.",
        "outro_badge": "DESCARGA COMPLETA · PROBALA 7 DÍAS · SIN RECORTES",
        "outro_footer": "Descargá el programa completo y conservá todo lo que cargues",
    },
    "en": {
        "intro_tagline": "A project portfolio with measurable health, not status meetings",
        "intro_badge": "100% WEB + DESKTOP · ES / EN / PT · ADDITIVE AI",
        "portfolio_h": "Portfolio health across 6 dimensions",
        "portfolio_sub": "Scope · schedule · budget · risk · dependencies · team",
        "portfolio_kpi1": "PROJECTS", "portfolio_kpi2": "HEALTH INDEX",
        "portfolio_kpi3": "BLOCKED TASKS",
        "portfolio_proyectos": ["Billing migration", "Paraguay expansion",
                                "CRM migration", "Customer portal"],
        "pharma_h": "Real lab dataset → Power BI",
        "pharma_sub": "474 real clinical trials · ClinicalTrials.gov (NIH) · public domain",
        "pharma_crit": "Clinical status → portfolio criticality:",
        "pharma_pill1": "135 completed → Low", "pharma_pill2": "120 recruiting → Medium",
        "pharma_pill3": "9 suspended → High",
        "pharma_connector": "One-click .pbids connector → Power BI",
        "pharma_honest": "Honest by design: ClinicalTrials.gov has no budget field → stays 0, with a note",
        "gov_h": "AI proposes, the owner validates",
        "gov_sub": "Preset definitions · validated by the data owner · versioned",
        "gov_steps": [
            ("1 · AI RECOMMENDS", "Scope: work included and excluded, defining the project's boundary.", BLUE),
            ("2 · THE OWNER VALIDATES", "Ana Pérez (Data Owner) reviews, edits the text and saves it.", AMBER),
            ("3 · IT STAYS VERSIONED", "History per company: who, when, full name and role.", GREEN),
        ],
        "org_h": "Org chart → owners per stage",
        "org_sub": "Upload Excel, CSV or a SQL database · AI auto-fills areas and owners",
        "org_file": "▤ org_chart.xlsx", "org_cols": "roles · areas · reports_to",
        "org_arrow": "→  AI  →",
        "org_etapas": [("Initiation", "M. Rodríguez · PMO"),
                       ("Planning", "L. Fernández · Project Lead"),
                       ("Execution", "C. Gómez · Tech Lead"),
                       ("Monitoring", "A. Pérez · Data Owner"),
                       ("Closing", "R. Silva · Sponsor")],
        "pmbok_h": "PMBOK: technical & plain-spoken",
        "pmbok_sub": "10 knowledge areas + 5 process groups · with an editable note per company",
        "pmbok_tag_tec": "TECHNICAL", "pmbok_tag_criollo": "PLAIN ENGLISH",
        "pmbok_tecnico": "Schedule Management: the processes to manage timely completion of the "
                        "project — sequencing activities, estimating durations, controlling the "
                        "schedule baseline.",
        "pmbok_criollo": "Whether your tasks are in order and whether you'll hit your dates. If "
                         "something slips, how much it drags everything else — before it blows "
                         "up on you.",
        "pmbok_footer": "Any stage that can't be automated gets noted by hand and saved per company",
        "trial_h": "A full 7-day trial",
        "trial_sub": "You download the complete program — everything unlocked, no cuts",
        "trial_line1": "On day 8 it locks — but your data is NEVER deleted.",
        "trial_line2": "Load your Professional license and pick up exactly where you left off.",
        "trial_badge": "US$9 / user / month · charged in local currency at the day's rate",
        "outro_tagline": "Your portfolio, governed end to end.",
        "outro_badge": "FULL DOWNLOAD · TRY IT 7 DAYS · NO CUTS",
        "outro_footer": "Download the complete program and keep everything you load",
    },
    "pt": {
        "intro_tagline": "Portfólio de projetos com saúde mensurável, não reuniões de status",
        "intro_badge": "100% WEB + PC · ES / EN / PT · IA ADITIVA",
        "portfolio_h": "Saúde do portfólio em 6 dimensões",
        "portfolio_sub": "Escopo · cronograma · orçamento · risco · dependências · equipe",
        "portfolio_kpi1": "PROJETOS", "portfolio_kpi2": "ÍNDICE DE SAÚDE",
        "portfolio_kpi3": "TAREFAS BLOQUEADAS",
        "portfolio_proyectos": ["Migração de faturamento", "Expansão Paraguai",
                                "Migração de CRM", "Portal de clientes"],
        "pharma_h": "Dataset real de laboratório → Power BI",
        "pharma_sub": "474 ensaios clínicos reais · ClinicalTrials.gov (NIH) · domínio público",
        "pharma_crit": "Status clínico → criticidade de portfólio:",
        "pharma_pill1": "135 concluídos → Baixa", "pharma_pill2": "120 recrutando → Média",
        "pharma_pill3": "9 suspensos → Alta",
        "pharma_connector": "Conector .pbids de um clique → Power BI",
        "pharma_honest": "Honesto: ClinicalTrials.gov não publica orçamento → fica em 0, com nota",
        "gov_h": "A IA propõe, o responsável valida",
        "gov_sub": "Definições preestabelecidas · validadas pelo data owner · versionadas",
        "gov_steps": [
            ("1 · A IA RECOMENDA", "Escopo: trabalho incluído e excluído que define o limite do projeto.", BLUE),
            ("2 · O DONO VALIDA", "Ana Pérez (Data Owner) revisa, ajusta o texto e salva.", AMBER),
            ("3 · FICA VERSIONADO", "Histórico por empresa: quem, quando, nome e cargo.", GREEN),
        ],
        "org_h": "Organograma → responsáveis por etapa",
        "org_sub": "Envie Excel, CSV ou base SQL · a IA autocompleta áreas e responsáveis",
        "org_file": "▤ organograma.xlsx", "org_cols": "cargos · áreas · reporta_a",
        "org_arrow": "→  IA  →",
        "org_etapas": [("Início", "M. Rodríguez · PMO"),
                       ("Planejamento", "L. Fernández · Líder de Projetos"),
                       ("Execução", "C. Gómez · Líder Técnico"),
                       ("Monitoramento", "A. Pérez · Data Owner"),
                       ("Encerramento", "R. Silva · Sponsor")],
        "pmbok_h": "PMBOK técnico e em linguagem simples",
        "pmbok_sub": "10 áreas de conhecimento + 5 grupos de processo · com nota editável por empresa",
        "pmbok_tag_tec": "TÉCNICO", "pmbok_tag_criollo": "LINGUAGEM SIMPLES",
        "pmbok_tecnico": "Gestão do Cronograma: processos para administrar a conclusão no prazo do "
                        "projeto — sequenciar atividades, estimar durações, controlar a linha de "
                        "base do cronograma.",
        "pmbok_criollo": "Se as tarefas estão em ordem e se você vai chegar nos prazos. Se algo "
                         "atrasa, o quanto isso empurra tudo o resto — antes que exploda em cima "
                         "de você.",
        "pmbok_footer": "Toda etapa não automatizável é anotada à mão e fica salva por empresa",
        "trial_h": "Teste completo de 7 dias",
        "trial_sub": "Você baixa o programa completo — tudo desbloqueado, sem cortes",
        "trial_line1": "No dia 8, bloqueia — mas seus dados NÃO são apagados.",
        "trial_line2": "Você carrega sua licença Professional e continua exatamente de onde parou.",
        "trial_badge": "US$9 / usuário / mês · cobrado em moeda local à cotação do dia",
        "outro_tagline": "Seu portfólio, governado de ponta a ponta.",
        "outro_badge": "DOWNLOAD COMPLETO · TESTE 7 DIAS · SEM CORTES",
        "outro_footer": "Baixe o programa completo e mantenha tudo o que você carregar",
    },
}

for _lang, _dict in TEXTS.items():
    assert set(_dict) == set(TEXTS["es"]), (
        f"TEXTS[{_lang!r}] no tiene las mismas claves que TEXTS['es'] — "
        f"faltan: {set(TEXTS['es']) - set(_dict)}, sobran: {set(_dict) - set(TEXTS['es'])}")


def _others(lang: str) -> str:
    """Las taglines de los OTROS dos idiomas, para el guiño trilingüe de
    intro/outro — en vez de repetir la misma frase, cada versión muestra en
    qué otros dos idiomas también existe el producto."""
    keys = [k for k in LANGS if k != lang]
    return " · ".join(TEXTS[k]["intro_tagline"] for k in keys)


# ------------------------------------------------------------------- escenas
#
# Cada escena recibe (p, lang): p es el progreso 0-1 de ESA escena (para la
# animación), lang decide qué texto de TEXTS mostrar. El dibujo (posiciones,
# colores, curvas de aparición) es el mismo entre idiomas; lo que cambia es
# el string y, cuando ese string es más largo, el tamaño de fuente que
# fit_font/fit_paragraph calculan para que siga entrando en su caja.

def scene_intro(p: float, lang: str) -> Image.Image:
    t = TEXTS[lang]
    img = base_frame()
    d = ImageDraw.Draw(img)
    size = 66
    d.rounded_rectangle([W / 2 - size, 140, W / 2 + size, 140 + size * 2],
                        radius=26, fill=(15, 33, 53), outline=AMBER, width=3)
    f_logo = font(58)
    lw = d.textlength("MV", font=f_logo)
    d.text((W / 2 - lw / 2, 140 + size - 36), "MV", font=f_logo, fill=AMBER)
    if p > 0.18:
        center_text(d, 310, "MV Project Management", font(52), INK)
    if p > 0.38:
        center_text_fit(d, 388, t["intro_tagline"], 24, 1080, MUTED, bold=False)
    if p > 0.55:
        center_text_fit(d, 428, _others(lang), 19, 1080, FAINT, bold=False, min_size=14)
    if p > 0.72:
        badge(d, W // 2, 505, t["intro_badge"], fit_font(d, t["intro_badge"], 1080, 18, 14))
    return img


def scene_portfolio(p: float, lang: str) -> Image.Image:
    t = TEXTS[lang]
    img = base_frame()
    d = ImageDraw.Draw(img)
    center_text_fit(d, 40, t["portfolio_h"], 32, 1080, INK)
    center_text_fit(d, 86, t["portfolio_sub"], 17, 1080, MUTED, bold=False, min_size=13)
    a = ease(p * 1.6)
    _kpi_card(d, 120, 140, 300, 86, t["portfolio_kpi1"], f"{int(round(20 * a))}", INK)
    _kpi_card(d, 445, 140, 300, 86, t["portfolio_kpi2"], f"{76.8 * a:.1f}/100", GREEN)
    _kpi_card(d, 770, 140, 300, 86, t["portfolio_kpi3"], f"{int(round(22 * a))}/211", AMBER)
    proyectos = list(zip(t["portfolio_proyectos"], [88, 64, 41, 79], [GREEN, AMBER, RED, GREEN]))
    y = 285
    for i, (name, score, col) in enumerate(proyectos):
        pa = ease(p * 2.2 - i * 0.16)
        if pa <= 0:
            continue
        bx0, bx1 = 470, 1040
        nf = fit_font(d, name, bx0 - 130 - 20, 18, 13, bold=False)
        d.text((130, y + 2), name, font=nf, fill=INK)
        d.rounded_rectangle([bx0, y + 2, bx1, y + 22], radius=10, fill=(20, 39, 60))
        fill_w = (bx1 - bx0) * (score / 100) * pa
        if fill_w > 16:
            d.rounded_rectangle([bx0, y + 2, bx0 + fill_w, y + 22], radius=10, fill=col)
        d.text((1058, y), f"{int(score * pa)}", font=font(17), fill=MUTED)
        y += 68
    return img


def scene_pharma(p: float, lang: str) -> Image.Image:
    t = TEXTS[lang]
    img = base_frame()
    d = ImageDraw.Draw(img)
    center_text_fit(d, 40, t["pharma_h"], 32, 1080, INK)
    center_text_fit(d, 86, t["pharma_sub"], 17, 1080, MUTED, bold=False, min_size=13)
    labs = [("AstraZeneca", 163), ("Novartis", 156), ("Pfizer", 155)]
    y = 150
    maxv = 170
    for i, (name, v) in enumerate(labs):
        pa = ease(p * 2.2 - i * 0.18)
        if pa <= 0:
            continue
        d.text((130, y + 2), name, font=font(18, False), fill=INK)
        bx0, bx1 = 360, 1000
        d.rounded_rectangle([bx0, y + 2, bx1, y + 26], radius=10, fill=(20, 39, 60))
        fill_w = (bx1 - bx0) * (v / maxv) * pa
        if fill_w > 16:
            d.rounded_rectangle([bx0, y + 2, bx0 + fill_w, y + 26], radius=10, fill=BLUE)
        d.text((1015, y + 2), f"{int(v * pa)}", font=font(18), fill=MUTED)
        y += 62
    # estados → criticidad
    if p > 0.4:
        cf = fit_font(d, t["pharma_crit"], 1020, 18, 14)
        d.text((130, 360), t["pharma_crit"], font=cf, fill=AMBER)
        pf = fit_font(d, max((t["pharma_pill1"], t["pharma_pill2"], t["pharma_pill3"]), key=len),
                     320, 15, 11, bold=True)
        x = 130
        x += _pill(d, x, 400, t["pharma_pill1"], GREEN, pf) + 14
        x += _pill(d, x, 400, t["pharma_pill2"], AMBER, pf) + 14
        _pill(d, x, 400, t["pharma_pill3"], RED, pf)
    if p > 0.62:
        d.rounded_rectangle([120, 470, 1160, 590], radius=14, fill=(9, 20, 35),
                            outline=(42, 65, 96), width=2)
        d.text((150, 492), "GET  http://127.0.0.1:8600/api/demo/pharma   (JSON · CSV)",
               font=fit_font(d, "GET  http://127.0.0.1:8600/api/demo/pharma   (JSON · CSV)",
                            980, 21, 15), fill=(127, 212, 168))
        cf2 = fit_font(d, t["pharma_connector"], 980, 21, 15)
        d.text((150, 536), t["pharma_connector"], font=cf2, fill=AMBER)
    if p > 0.85:
        center_text_fit(d, 622, t["pharma_honest"], 15, 1080, FAINT, bold=False, min_size=11)
    return img


def scene_governance(p: float, lang: str) -> Image.Image:
    t = TEXTS[lang]
    img = base_frame()
    d = ImageDraw.Draw(img)
    center_text_fit(d, 40, t["gov_h"], 32, 1080, INK)
    center_text_fit(d, 86, t["gov_sub"], 17, 1080, MUTED, bold=False, min_size=13)
    y = 150
    for i, (tag, body, col) in enumerate(t["gov_steps"]):
        pa = ease(p * 2.0 - i * 0.24)
        if pa <= 0:
            continue
        d.rounded_rectangle([130, y, 1150, y + 128], radius=14, fill=(13, 30, 51),
                            outline=col, width=2)
        tf = fit_font(d, tag, 970, 17, 13)
        d.text((155, y + 18), tag, font=tf, fill=col)
        bf, lines, line_h = fit_paragraph(d, body, 970, 68, 19, min_size=14, bold=False)
        for li, line in enumerate(lines[:3]):
            d.text((155, y + 52 + li * line_h), line, font=bf, fill=INK)
        y += 150
    return img


def scene_organigrama(p: float, lang: str) -> Image.Image:
    t = TEXTS[lang]
    img = base_frame()
    d = ImageDraw.Draw(img)
    center_text_fit(d, 40, t["org_h"], 32, 1080, INK)
    center_text_fit(d, 86, t["org_sub"], 17, 1080, MUTED, bold=False, min_size=13)
    if p > 0.15:
        d.rounded_rectangle([130, 150, 470, 250], radius=14, fill=(9, 20, 35),
                            outline=(42, 65, 96), width=2)
        ff = fit_font(d, t["org_file"], 300, 20, 15)
        d.text((155, 172), t["org_file"], font=ff, fill=INK)
        cf = fit_font(d, t["org_cols"], 300, 15, 11, bold=False)
        d.text((155, 206), t["org_cols"], font=cf, fill=MUTED)
    if p > 0.3:
        d.text((500, 190), t["org_arrow"], font=font(26), fill=AMBER)
    y = 285
    for i, (etapa, resp) in enumerate(t["org_etapas"]):
        pa = ease(p * 2.4 - i * 0.2)
        if pa <= 0:
            continue
        d.rounded_rectangle([130, y, 1150, y + 58], radius=12, fill=(13, 30, 51),
                            outline=(29, 49, 73), width=1)
        ef = fit_font(d, etapa, 300, 19, 14)
        d.text((155, y + 16), etapa, font=ef, fill=AMBER)
        rf = fit_font(d, resp, 660, 18, 13, bold=False)
        d.text((470, y + 16), resp, font=rf, fill=INK)
        y += 70
    return img


def scene_pmbok(p: float, lang: str) -> Image.Image:
    t = TEXTS[lang]
    img = base_frame()
    d = ImageDraw.Draw(img)
    center_text_fit(d, 40, t["pmbok_h"], 32, 1080, INK)
    center_text_fit(d, 86, t["pmbok_sub"], 17, 1080, MUTED, bold=False, min_size=13)
    if p > 0.2:
        d.rounded_rectangle([130, 150, 630, 470], radius=14, fill=(13, 30, 51),
                            outline=BLUE, width=2)
        d.text((155, 170), t["pmbok_tag_tec"], font=fit_font(d, t["pmbok_tag_tec"], 450, 18, 14), fill=BLUE)
        tf, lines, lh = fit_paragraph(d, t["pmbok_tecnico"], 450, 250, 18, min_size=14, bold=False)
        for li, line in enumerate(lines):
            d.text((155, 210 + li * lh), line, font=tf, fill=INK)
    if p > 0.45:
        d.rounded_rectangle([650, 150, 1150, 470], radius=14, fill=(13, 30, 51),
                            outline=AMBER, width=2)
        d.text((675, 170), t["pmbok_tag_criollo"],
              font=fit_font(d, t["pmbok_tag_criollo"], 450, 18, 14), fill=AMBER)
        cf, lines, lh = fit_paragraph(d, t["pmbok_criollo"], 450, 250, 18, min_size=14, bold=False)
        for li, line in enumerate(lines):
            d.text((675, 210 + li * lh), line, font=cf, fill=INK)
    if p > 0.7:
        center_text_fit(d, 510, t["pmbok_footer"], 17, 1080, FAINT, bold=False, min_size=12)
    return img


def scene_trial(p: float, lang: str) -> Image.Image:
    t = TEXTS[lang]
    img = base_frame()
    d = ImageDraw.Draw(img)
    center_text_fit(d, 60, t["trial_h"], 38, 1080, INK, min_size=26)
    center_text_fit(d, 120, t["trial_sub"], 20, 1080, MUTED, bold=False, min_size=14)
    # timeline 7 días
    if p > 0.2:
        x0, x1, yb = 180, 1100, 260
        d.rounded_rectangle([x0, yb, x1, yb + 14], radius=7, fill=(20, 39, 60))
        prog = ease(min(1.0, p * 1.6))
        d.rounded_rectangle([x0, yb, x0 + (x1 - x0) * prog, yb + 14], radius=7, fill=AMBER)
        for dday in range(8):
            dx = x0 + (x1 - x0) * dday / 7
            d.ellipse([dx - 5, yb + 2, dx + 5, yb + 12], fill=INK)
            d.text((dx - 6, yb + 22), f"{dday}", font=font(14, False), fill=FAINT)
    if p > 0.5:
        d.text((180, 330), t["trial_line1"], font=fit_font(d, t["trial_line1"], 920, 21, 15), fill=INK)
    if p > 0.68:
        d.text((180, 372), t["trial_line2"], font=fit_font(d, t["trial_line2"], 920, 21, 15), fill=GREEN)
    if p > 0.82:
        badge(d, W // 2, 450, t["trial_badge"], fit_font(d, t["trial_badge"], 1080, 18, 13))
    return img


def scene_outro(p: float, lang: str) -> Image.Image:
    t = TEXTS[lang]
    img = base_frame()
    d = ImageDraw.Draw(img)
    center_text(d, 200, "MV Project Management", font(50), INK)
    center_text_fit(d, 280, t["outro_tagline"], 23, 1080, MUTED, bold=False, min_size=16)
    center_text_fit(d, 318, _others(lang), 19, 1080, FAINT, bold=False, min_size=14)
    if p > 0.35:
        badge(d, W // 2, 400, t["outro_badge"], fit_font(d, t["outro_badge"], 1080, 18, 13))
    if p > 0.6:
        center_text_fit(d, 480, t["outro_footer"], 19, 1080, MUTED, bold=False, min_size=13)
    return img


# (función de escena, duración mínima visual) — igual en los 3 idiomas: lo
# que cambia entre versiones es el texto en pantalla y la narración, no la
# composición ni el timing base de cada escena.
SCENES = [
    (scene_intro, 6.0),
    (scene_portfolio, 8.0),
    (scene_pharma, 9.5),
    (scene_governance, 9.0),
    (scene_organigrama, 8.5),
    (scene_pmbok, 8.5),
    (scene_trial, 9.0),
    (scene_outro, 5.0),
]

# Narración por idioma, escena por escena — mismo orden que SCENES. El
# español es la voz rioplatense original; inglés y portugués son traducción
# directa, no resumen, para que la duración de cada escena quede pareja entre
# versiones (el largo del texto es lo que fija cuánto dura la escena).
NARRATIONS = {
    "es": [
        "MV Proyect Management: tu portafolio de proyectos con salud medible, "
        "en vez de reuniones de estado. Cien por ciento web y PC, en español, "
        "inglés y portugués.",
        "Cada proyecto tiene un índice de salud en seis dimensiones: alcance, "
        "cronograma, presupuesto, riesgo, dependencias y equipo. El motor detecta "
        "qué tarea bloquea a cuántas otras, calculado, no estimado a ojo.",
        "Podés trabajar de punta a punta con datos públicos reales: cuatrocientos "
        "setenta y cuatro ensayos clínicos de laboratorios multinacionales, desde "
        "ClinicalTrials.gov. El estado clínico se traduce a criticidad, y todo "
        "sale a Power BI con un conector de un clic. Y somos honestos: si el dato "
        "no trae presupuesto, no lo inventamos.",
        "Todo lo manual aparece primero recomendado por inteligencia artificial. "
        "Después, el data owner lo valida o lo corrige y lo guarda. Nada se "
        "sobrescribe: queda el historial completo por empresa, con quién lo validó, "
        "su nombre y su cargo.",
        "Subís el organigrama de la empresa en Excel, CSV o base de datos, y la "
        "inteligencia artificial autocompleta las áreas y los responsables de cada "
        "etapa. Después lo editás y lo guardás cuando quieras.",
        "Y para demostrar conocimiento, cada área del PMBOK viene con su definición "
        "técnica y su explicación en criollo. Cualquier etapa que no sea "
        "automatizable, la anotás a mano y queda guardada por empresa.",
        "Lo descargás completo y funciona cien por ciento durante siete días, con "
        "todo desbloqueado. Al vencer se bloquea, pero tus datos no se borran: "
        "cargás tu licencia Professional y seguís exactamente donde estabas.",
        "MV Proyect Management. Tu portafolio, gobernado de punta a punta. "
        "Descargalo hoy y probalo completo, siete días.",
    ],
    "en": [
        "MV Project Management: your project portfolio with measurable health, "
        "instead of status meetings. One hundred percent web and desktop, in "
        "Spanish, English, and Portuguese.",
        "Every project has a health index across six dimensions: scope, "
        "schedule, budget, risk, dependencies, and team. The engine detects "
        "which task blocks how many others — calculated, not eyeballed.",
        "You can work end to end with real public data: four hundred "
        "seventy-four clinical trials from multinational labs, sourced from "
        "ClinicalTrials.gov. Clinical status maps straight to criticality, and "
        "everything flows to Power BI with a one-click connector. And we're "
        "honest about it: if the data has no budget field, we don't make one up.",
        "Every manual field shows up first as an AI-recommended suggestion. "
        "Then the data owner validates or corrects it and saves. Nothing gets "
        "overwritten: the full history stays per company, with who validated "
        "it, their name, and their role.",
        "Upload the company's org chart from Excel, CSV, or a database, and the "
        "AI auto-fills the areas and owners for each stage. Then you edit it "
        "and save whenever you want.",
        "And to show real methodology knowledge, every PMBOK area comes with "
        "its technical definition and a plain-language explanation. Any stage "
        "that can't be automated, you note by hand, and it's saved per company.",
        "You download it in full, and it runs one hundred percent for seven "
        "days, everything unlocked. When it expires, it locks — but your data "
        "is never deleted: load your Professional license and you're right "
        "back where you left off.",
        "MV Project Management. Your portfolio, governed end to end. Download "
        "it today and try the full version, free for seven days.",
    ],
    "pt": [
        "MV Project Management: seu portfólio de projetos com saúde mensurável, "
        "em vez de reuniões de status. Cem por cento web e PC, em espanhol, "
        "inglês e português.",
        "Cada projeto tem um índice de saúde em seis dimensões: escopo, "
        "cronograma, orçamento, risco, dependências e equipe. O motor detecta "
        "qual tarefa bloqueia quantas outras — calculado, não estimado no "
        "olhômetro.",
        "Você pode trabalhar de ponta a ponta com dados públicos reais: "
        "quatrocentos e setenta e quatro ensaios clínicos de laboratórios "
        "multinacionais, do ClinicalTrials.gov. O status clínico se traduz em "
        "criticidade, e tudo vai para o Power BI com um conector de um clique. "
        "E somos honestos: se o dado não traz orçamento, não inventamos.",
        "Todo campo manual aparece primeiro recomendado por inteligência "
        "artificial. Depois, o data owner valida ou corrige e salva. Nada é "
        "sobrescrito: fica o histórico completo por empresa, com quem validou, "
        "nome e cargo.",
        "Você envia o organograma da empresa em Excel, CSV ou banco de dados, e "
        "a inteligência artificial autocompleta as áreas e os responsáveis de "
        "cada etapa. Depois você edita e salva quando quiser.",
        "E para demonstrar conhecimento, cada área do PMBOK vem com sua "
        "definição técnica e sua explicação em linguagem simples. Qualquer "
        "etapa que não seja automatizável, você anota à mão e fica salva por "
        "empresa.",
        "Você baixa completo e funciona cem por cento durante sete dias, com "
        "tudo desbloqueado. Ao vencer, bloqueia — mas seus dados não são "
        "apagados: você carrega sua licença Professional e continua exatamente "
        "de onde parou.",
        "MV Project Management. Seu portfólio, governado de ponta a ponta. "
        "Baixe hoje e experimente completo, sete dias.",
    ],
}

for _lang, _texts in NARRATIONS.items():
    assert len(_texts) == len(SCENES), (
        f"NARRATIONS[{_lang!r}] tiene {len(_texts)} textos, pero SCENES tiene "
        f"{len(SCENES)} escenas — tienen que ir 1 a 1.")

FADE = 0.5
VOICE_LEAD = 0.4
VOICE_TAIL = 0.9

# Alias por compatibilidad: el flujo anterior de un solo idioma exportaba
# MVPM_VOICE_ONNX (sin sufijo) para la voz española.
_VOICE_ENV = {"es": ("MVPM_VOICE_ONNX_ES", "MVPM_VOICE_ONNX"),
              "en": ("MVPM_VOICE_ONNX_EN",), "pt": ("MVPM_VOICE_ONNX_PT",)}


def _voice_model_path(lang: str) -> str:
    for var in _VOICE_ENV[lang]:
        val = os.environ.get(var, "")
        if val:
            return val
    return ""


def _synth_narrations_de(textos: list[str], lang: str, tmpdir: str) -> list[str] | None:
    """Sintetiza una lista cualquiera de textos con la voz de `lang`.

    Está separado de `_synth_narrations` porque el video corto de
    antes/después (`build_antes_despues.py`) usa las MISMAS voces y el mismo
    criterio —sin modelo configurado se devuelve None y el video sale mudo en
    vez de fallar— pero con su propio guion. Duplicar esto era garantizar que
    los dos videos se fueran separando con el tiempo."""
    model = _voice_model_path(lang)
    if not model or not os.path.exists(model):
        return None
    try:
        from piper import PiperVoice
    except ImportError:
        return None
    voice = PiperVoice.load(model)
    paths = []
    for i, text in enumerate(textos):
        path = os.path.join(tmpdir, f"nar_{lang}_{i}.wav")
        with wave.open(path, "wb") as w:
            voice.synthesize_wav(text, w)
        paths.append(path)
    return paths


def _synth_narrations(lang: str, tmpdir: str) -> list[str] | None:
    return _synth_narrations_de(NARRATIONS[lang], lang, tmpdir)


def _wav_duration(path: str) -> float:
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def _scene_seconds(narrations: list[str] | None) -> list[float]:
    secs = []
    for i, (_, min_secs) in enumerate(SCENES):
        if narrations:
            secs.append(max(min_secs, VOICE_LEAD + _wav_duration(narrations[i]) + VOICE_TAIL))
        else:
            secs.append(min_secs)
    return secs


def _mix_audio_track(narrations: list[str], secs: list[float], out_wav: str) -> None:
    with wave.open(narrations[0]) as w:
        rate, width, channels = w.getframerate(), w.getsampwidth(), w.getnchannels()
    total = np.zeros(int(sum(secs) * rate) + rate, dtype=np.int16)
    start = 0.0
    for i, nar in enumerate(narrations):
        with wave.open(nar) as w:
            data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        at = int((start + VOICE_LEAD) * rate)
        total[at:at + len(data)] = data
        start += secs[i]
    total = total[:int(sum(secs) * rate)]
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(width)
        w.setframerate(rate)
        w.writeframes(total.tobytes())


def build(lang: str) -> str:
    """Genera el demo de un idioma. La duración de cada escena depende de lo
    que dure SU narración, así que el video se renderiza entero por idioma —
    no se puede reusar el mismo video mudo entre idiomas porque el largo de
    "the AI auto-fills the areas" no dura lo mismo que su traducción, y el
    texto en pantalla tampoco es el mismo dibujo: es el de ESE idioma."""
    out, landing_copy = _out_path(lang), _landing_path(lang)
    tmpdir = tempfile.mkdtemp(prefix=f"mvpm_video_{lang}_")
    narrations = _synth_narrations(lang, tmpdir)
    secs_list = _scene_seconds(narrations)

    os.makedirs(os.path.dirname(out), exist_ok=True)
    video_only = os.path.join(tmpdir, "video_sin_audio.mp4") if narrations else out
    writer = imageio.get_writer(video_only, fps=FPS, codec="libx264",
                                quality=7, macro_block_size=16,
                                ffmpeg_params=["-pix_fmt", "yuv420p"])
    black = Image.new("RGB", (W, H), (0, 0, 0))
    for (scene, _), secs in zip(SCENES, secs_list):
        n = int(round(secs * FPS))
        for f_i in range(n):
            p = f_i / max(1, n - 1)
            frame = scene(p, lang)
            t = f_i / FPS
            rem = secs - t
            if t < FADE:
                frame = Image.blend(black, frame, ease(t / FADE))
            elif rem < FADE:
                frame = Image.blend(black, frame, ease(max(0.0, rem) / FADE))
            writer.append_data(np.asarray(frame))
    writer.close()

    if narrations:
        track = os.path.join(tmpdir, "narracion.wav")
        _mix_audio_track(narrations, secs_list, track)
        from imageio_ffmpeg import get_ffmpeg_exe
        subprocess.run([get_ffmpeg_exe(), "-y", "-i", video_only, "-i", track,
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                        "-shortest", out],
                       check=True, capture_output=True)

    os.makedirs(os.path.dirname(landing_copy), exist_ok=True)
    shutil.copyfile(out, landing_copy)
    shutil.rmtree(tmpdir, ignore_errors=True)
    return out


def build_all() -> dict[str, str]:
    """Genera los 3 idiomas. El idioma sin voz configurada sale silencioso
    (no se salta) — mejor un video mudo que no producirlo."""
    return {lang: build(lang) for lang in LANGS}


if __name__ == "__main__":
    LANG_NOMBRE = {"es": "es_AR", "en": "en_US", "pt": "pt_BR"}
    paths = build_all()
    for lang, path in paths.items():
        size_mb = os.path.getsize(path) / 1e6
        voz = f"con voz {LANG_NOMBRE[lang]}" if _voice_model_path(lang) else "SIN VOZ"
        print(f"[{lang}] {voz}: {path} ({size_mb:.1f} MB)")
    print("Copiados a landing/video/ (demo.mp4, demo_en.mp4, demo_pt.mp4)")
