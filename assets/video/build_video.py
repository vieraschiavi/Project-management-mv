"""
MV Project Management · Generador del video demo (PIL + imageio-ffmpeg) con
narración en los 3 idiomas del producto (Piper TTS: es_AR "daniela",
en_US "amy", pt_BR "faber").

Produce un ``demo.mp4`` por idioma (1280×720): el mismo recorrido animado del
producto con la voz en off sincronizada escena por escena (la duración de cada
escena se ajusta a su narración, sin desfases). Es una animación explicativa
del producto —no un screencast— y así se declara en la landing. Las escenas
(lo que se dibuja en pantalla) son las mismas para los tres idiomas; lo que
cambia es sólo el audio — la landing ya declara "100% WEB + PC · ES / EN / PT"
en pantalla, en las tres versiones.

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


def _kpi_card(d, x, y, w, h, label, value, vcolor):
    d.rounded_rectangle([x, y, x + w, y + h], radius=14,
                        fill=(15, 33, 53), outline=(29, 49, 73), width=2)
    d.text((x + 18, y + 14), label, font=font(14, False), fill=MUTED)
    d.text((x + 18, y + 38), value, font=font(32), fill=vcolor)


def _pill(d, x, y, text, col, f):
    pw = d.textlength(text, font=f)
    d.rounded_rectangle([x - 8, y - 2, x + pw + 10, y + 24], radius=12,
                        outline=col, width=2)
    d.text((x + 1, y), text, font=f, fill=col)
    return pw + 18


# ------------------------------------------------------------------- escenas

def scene_intro(p: float) -> Image.Image:
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
        center_text(d, 388, "Portafolio con salud medible, no reuniones de estado", font(24, False), MUTED)
    if p > 0.55:
        center_text(d, 428, "Measurable portfolio health · Saúde de portfólio mensurável", font(19, False), FAINT)
    if p > 0.72:
        badge(d, W // 2, 505, "100% WEB + PC · ES / EN / PT · IA ADITIVA", font(18))
    return img


def scene_portfolio(p: float) -> Image.Image:
    img = base_frame()
    d = ImageDraw.Draw(img)
    center_text(d, 40, "Portafolio con salud en 6 dimensiones", font(32), INK)
    center_text(d, 86, "Alcance · cronograma · presupuesto · riesgo · dependencias · equipo",
                font(17, False), MUTED)
    a = ease(p * 1.6)
    _kpi_card(d, 120, 140, 300, 86, "PROYECTOS", f"{int(round(20 * a))}", INK)
    _kpi_card(d, 445, 140, 300, 86, "ÍNDICE DE SALUD", f"{76.8 * a:.1f}/100", GREEN)
    _kpi_card(d, 770, 140, 300, 86, "TAREAS BLOQUEADAS", f"{int(round(22 * a))}/211", AMBER)
    proyectos = [("Migración de facturación", 88, GREEN),
                 ("Expansión Paraguay", 64, AMBER),
                 ("Migración de CRM", 41, RED),
                 ("Portal de clientes", 79, GREEN)]
    y = 285
    for i, (name, score, col) in enumerate(proyectos):
        pa = ease(p * 2.2 - i * 0.16)
        if pa <= 0:
            continue
        d.text((130, y + 2), name, font=font(18, False), fill=INK)
        bx0, bx1 = 470, 1040
        d.rounded_rectangle([bx0, y + 2, bx1, y + 22], radius=10, fill=(20, 39, 60))
        fill_w = (bx1 - bx0) * (score / 100) * pa
        if fill_w > 16:
            d.rounded_rectangle([bx0, y + 2, bx0 + fill_w, y + 22], radius=10, fill=col)
        d.text((1058, y), f"{int(score * pa)}", font=font(17), fill=MUTED)
        y += 68
    return img


def scene_pharma(p: float) -> Image.Image:
    img = base_frame()
    d = ImageDraw.Draw(img)
    center_text(d, 40, "Dataset real de laboratorio → Power BI", font(32), INK)
    center_text(d, 86, "474 ensayos clínicos reales · ClinicalTrials.gov (NIH) · dominio público",
                font(17, False), MUTED)
    a = ease(p * 1.6)
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
        d.text((130, 360), "Estado clínico → criticidad de portafolio:", font=font(18), fill=AMBER)
        x = 130
        x += _pill(d, x, 400, "135 completados → Baja", GREEN, font(15)) + 14
        x += _pill(d, x, 400, "120 reclutando → Media", AMBER, font(15)) + 14
        _pill(d, x, 400, "9 suspendidos → Alta", RED, font(15))
    if p > 0.62:
        d.rounded_rectangle([120, 470, 1160, 590], radius=14, fill=(9, 20, 35),
                            outline=(42, 65, 96), width=2)
        d.text((150, 492), "GET  http://127.0.0.1:8600/api/demo/pharma   (JSON · CSV)",
               font=font(21), fill=(127, 212, 168))
        d.text((150, 536), "Conector .pbids de un clic → Power BI", font=font(21), fill=AMBER)
    if p > 0.85:
        center_text(d, 622, "Honesto: ClinicalTrials.gov no publica presupuesto → queda en 0 con nota",
                    font(15, False), FAINT)
    return img


def scene_governance(p: float) -> Image.Image:
    img = base_frame()
    d = ImageDraw.Draw(img)
    center_text(d, 40, "La IA propone, el responsable valida", font(32), INK)
    center_text(d, 86, "Definiciones preestablecidas · validadas por el data owner · versionadas",
                font(17, False), MUTED)
    steps = [("1 · IA RECOMIENDA", "Alcance: trabajo incluido y excluido\nque define el límite del proyecto.", BLUE),
             ("2 · EL DUEÑO VALIDA", "Ana Pérez (Data Owner) revisa,\najusta el texto y lo guarda.", AMBER),
             ("3 · QUEDA VERSIONADO", "Historial por empresa: quién,\ncuándo, nombre y cargo.", GREEN)]
    y = 150
    for i, (tag, body, col) in enumerate(steps):
        pa = ease(p * 2.0 - i * 0.24)
        if pa <= 0:
            continue
        d.rounded_rectangle([130, y, 1150, y + 128], radius=14, fill=(13, 30, 51),
                            outline=col, width=2)
        d.text((155, y + 18), tag, font=font(17), fill=col)
        for li, line in enumerate(body.split("\n")):
            d.text((155, y + 52 + li * 30), line, font=font(19, False), fill=INK)
        y += 150
    return img


def scene_organigrama(p: float) -> Image.Image:
    img = base_frame()
    d = ImageDraw.Draw(img)
    center_text(d, 40, "Organigrama → responsables por etapa", font(32), INK)
    center_text(d, 86, "Subís Excel, CSV o base SQL · la IA autocompleta áreas y responsables",
                font(17, False), MUTED)
    if p > 0.15:
        d.rounded_rectangle([130, 150, 470, 250], radius=14, fill=(9, 20, 35),
                            outline=(42, 65, 96), width=2)
        d.text((155, 172), "📄 organigrama.xlsx", font=font(20), fill=INK)
        d.text((155, 206), "cargos · áreas · reporta_a", font=font(15, False), fill=MUTED)
    if p > 0.3:
        d.text((500, 190), "→  IA  →", font=font(26), fill=AMBER)
    etapas = [("Inicio", "M. Rodríguez · PMO"),
              ("Planificación", "L. Fernández · Jefa de Proyectos"),
              ("Ejecución", "C. Gómez · Líder Técnico"),
              ("Seguimiento", "A. Pérez · Data Owner"),
              ("Cierre", "R. Silva · Sponsor")]
    y = 285
    for i, (etapa, resp) in enumerate(etapas):
        pa = ease(p * 2.4 - i * 0.2)
        if pa <= 0:
            continue
        d.rounded_rectangle([130, y, 1150, y + 58], radius=12, fill=(13, 30, 51),
                            outline=(29, 49, 73), width=1)
        d.text((155, y + 16), etapa, font=font(19), fill=AMBER)
        d.text((470, y + 16), resp, font=font(18, False), fill=INK)
        y += 70
    return img


def scene_pmbok(p: float) -> Image.Image:
    img = base_frame()
    d = ImageDraw.Draw(img)
    center_text(d, 40, "PMBOK técnico y \"en criollo\"", font(32), INK)
    center_text(d, 86, "10 áreas de conocimiento + 5 grupos de proceso · con nota editable por empresa",
                font(17, False), MUTED)
    if p > 0.2:
        d.rounded_rectangle([130, 150, 630, 470], radius=14, fill=(13, 30, 51),
                            outline=BLUE, width=2)
        d.text((155, 170), "TÉCNICO", font=font(18), fill=BLUE)
        tecnico = ("Gestión del Cronograma:\nprocesos para administrar la\nterminación en plazo del\nproyecto (secuenciar, estimar\nduraciones, controlar la línea\nbase del cronograma).")
        for li, line in enumerate(tecnico.split("\n")):
            d.text((155, 210 + li * 34), line, font=font(18, False), fill=INK)
    if p > 0.45:
        d.rounded_rectangle([650, 150, 1150, 470], radius=14, fill=(13, 30, 51),
                            outline=AMBER, width=2)
        d.text((675, 170), "EN CRIOLLO", font=font(18), fill=AMBER)
        criollo = ("Que las tareas estén en orden\ny que sepas si vas a llegar\ncon los tiempos. Si algo se\natrasa, cuánto te corre todo\nlo demás — antes de que\nte explote encima.")
        for li, line in enumerate(criollo.split("\n")):
            d.text((675, 210 + li * 34), line, font=font(18, False), fill=INK)
    if p > 0.7:
        center_text(d, 510, "Cada etapa no automatizable se anota a mano y se guarda por empresa",
                    font(17, False), FAINT)
    return img


def scene_trial(p: float) -> Image.Image:
    img = base_frame()
    d = ImageDraw.Draw(img)
    center_text(d, 60, "Prueba completa de 7 días", font(38), INK)
    center_text(d, 120, "Descargás el programa completo — todo desbloqueado, sin recortes",
                font(20, False), MUTED)
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
        d.text((180, 330), "Al día 8 se bloquea — pero tus datos NO se borran.",
               font=font(21), fill=INK)
    if p > 0.68:
        d.text((180, 372), "Cargás tu licencia Professional y seguís exactamente donde estabas.",
               font=font(21), fill=GREEN)
    if p > 0.82:
        badge(d, W // 2, 450, "US$9 / usuario / mes · se cobra en pesos al cambio del día", font(18))
    return img


def scene_outro(p: float) -> Image.Image:
    img = base_frame()
    d = ImageDraw.Draw(img)
    center_text(d, 200, "MV Project Management", font(50), INK)
    center_text(d, 280, "Tu portafolio, gobernado de punta a punta.", font(23, False), MUTED)
    center_text(d, 318, "Your portfolio, governed end to end.", font(19, False), FAINT)
    if p > 0.35:
        badge(d, W // 2, 400, "DESCARGA COMPLETA · PROBALA 7 DÍAS · SIN RECORTES", font(18))
    if p > 0.6:
        center_text(d, 480, "Descargá el programa completo y conservá todo lo que cargues", font(19, False), MUTED)
    return img


# (función de escena, duración mínima visual) — igual en los 3 idiomas: lo
# que cambia entre versiones es sólo la narración, no el dibujo.
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


def _synth_narrations(lang: str, tmpdir: str) -> list[str] | None:
    model = _voice_model_path(lang)
    if not model or not os.path.exists(model):
        return None
    try:
        from piper import PiperVoice
    except ImportError:
        return None
    voice = PiperVoice.load(model)
    paths = []
    for i, text in enumerate(NARRATIONS[lang]):
        path = os.path.join(tmpdir, f"nar_{lang}_{i}.wav")
        with wave.open(path, "wb") as w:
            voice.synthesize_wav(text, w)
        paths.append(path)
    return paths


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
    "the AI auto-fills the areas" no dura lo mismo que su traducción."""
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
            frame = scene(p)
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
    return {lang: build(lang) for lang in ("es", "en", "pt")}


if __name__ == "__main__":
    LANG_NOMBRE = {"es": "es_AR", "en": "en_US", "pt": "pt_BR"}
    paths = build_all()
    for lang, path in paths.items():
        size_mb = os.path.getsize(path) / 1e6
        voz = f"con voz {LANG_NOMBRE[lang]}" if _voice_model_path(lang) else "SIN VOZ"
        print(f"[{lang}] {voz}: {path} ({size_mb:.1f} MB)")
    print("Copiados a landing/video/ (demo.mp4, demo_en.mp4, demo_pt.mp4)")
