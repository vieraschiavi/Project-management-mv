# © 2026 Martín Viera. Todos los derechos reservados.
"""Video corto "antes / después" para la landing — el que mira un gerente.

Por qué existe además de `build_video.py`: ese es el recorrido del producto,
escena por escena, y dura minuto y medio. Un gerente que entra a decidir si
contrata no mira minuto y medio de recorrido: quiere ver, en menos de un
minuto, qué cambia el lunes a la mañana. Este video hace UNA sola cosa —
poner el mismo portafolio dos veces, antes y después— y termina.

**Los números NO se escriben acá.** Se leen del motor en tiempo de build
(`mvpm.demo_real`), sobre el portafolio público del gobierno del Reino Unido.
Si el dato de origen cambia, el video cambia con él; nadie puede dejar
hardcodeado un "ahorrás 40 horas" que la fuente no respalde. Lo cubre
`tests/test_video_antes_despues.py`.

Las 33 horas del "antes" son un SUPUESTO declarado, no una medición: 15
minutos de revisión manual por proyecto, que es el mismo supuesto que la app
muestra en pantalla (`minutos_por_revision_manual_supuesto`). Va escrito en el
propio cuadro para que nadie lo lea como un número medido.

Uso (mismas voces Piper que el demo largo; sin ellas sale mudo, no falla):

    MVPM_VOICE_ONNX_ES=./es_AR-daniela-high.onnx \\
    MVPM_VOICE_ONNX_EN=./en_US-amy-medium.onnx \\
    MVPM_VOICE_ONNX_PT=./pt_BR-faber-medium.onnx \\
    python assets/video/build_antes_despues.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

# `imageio` va DENTRO de build() (ver el comentario equivalente en
# build_video.py): importar este módulo para leer sus cifras o dibujar una
# escena no tiene por qué exigir el stack de render, que no está en
# requirements.txt.

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from assets.video.build_video import (  # noqa: E402
    AMBER, FADE, FPS, GREEN, H, INK, MUTED, NAVY, RED, VOICE_LEAD, VOICE_TAIL,
    W, _mix_audio_track, _synth_narrations_de, _wav_duration, base_frame,
    center_text_fit, ease, fit_font, fit_paragraph, font,
)
from mvpm import demo_real  # noqa: E402

_SUFFIX = {"es": "", "en": "_en", "pt": "_pt"}
LANGS = ("es", "en", "pt")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _out_path(lang: str) -> str:
    return os.path.join(ROOT, "assets", "video", f"antes_despues{_SUFFIX[lang]}.mp4")


def _landing_path(lang: str) -> str:
    return os.path.join(ROOT, "landing", "video", f"antes_despues{_SUFFIX[lang]}.mp4")


# --------------------------------------------------------------- los números
#
# Una sola lectura del motor, al importar. Todo lo que se dibuja y se narra
# sale de acá: no hay una segunda copia del número en el texto de pantalla ni
# en la narración.

def datos() -> dict:
    """Las cifras del video, calculadas por el motor sobre el portafolio real
    del gobierno del Reino Unido (IPA / Cabinet Office, OGL v3.0)."""
    r = demo_real.resumen_portafolio()
    peor = r["proyectos_sobre_presupuesto_detalle"].iloc[0]
    return {
        "total": int(r["total_proyectos"]),
        "sobre": int(r["sobre_presupuesto"]),
        "minutos": int(r["minutos_por_revision_manual_supuesto"]),
        "horas": float(r["horas_ahorradas_estimadas"]),
        "peor_nombre": str(peor["nombre"]),
        "peor_pct": float(peor["ejecucion_pct"]),
    }


D = datos()


# -------------------------------------------------------- texto en pantalla
#
# Cada idioma trae las MISMAS claves (lo verifica el assert de abajo) y usa
# {} para los números, que vienen de `D`. Así una traducción no puede quedar
# con una cifra vieja: la cifra no está escrita en la traducción.

TEXTS = {
    "es": {
        "kicker": "Antes / después",
        "titulo": "El mismo portafolio. Dos lunes distintos.",
        "sub": "{total} proyectos públicos reales del gobierno británico.",
        "antes_t": "ANTES",
        "antes_h": "Abrir {total} proyectos, uno por uno",
        "antes_b1": "{minutos} minutos de revisión manual por proyecto",
        "antes_b2": "{horas:.0f} horas hasta saber cuáles están en rojo",
        "antes_b3": "Los desvíos aparecen cuando la plata ya se gastó",
        "antes_pie": "Supuesto declarado: {minutos} minutos por proyecto. No es una medición.",
        "desp_t": "DESPUÉS",
        "desp_h": "El motor los ordena solo",
        "desp_b1": "{sobre} proyectos sobre presupuesto, con nombre y porcentaje",
        "desp_b2": "Salud en 6 dimensiones, calculada, no estimada a ojo",
        "desp_b3": "Qué tarea bloquea a cuántas otras, antes de la reunión",
        "desp_pie": "El peor del portafolio: {peor_pct:.1f}% de lo presupuestado.",
        "comp_t": "Lo que cambia para quien firma",
        "comp_izq_l": "Enterarse",
        "comp_izq_v": "{horas:.0f} horas",
        "comp_der_l": "Enterarse",
        "comp_der_v": "segundos",
        "comp_pie": "Mismo dato. Misma gente. Otro momento del mes para enterarse.",
        "cierre_h": "Probalo con tus propios proyectos",
        "cierre_b": "Siete días completos, todo desbloqueado. Los números de este "
                    "video salen de datos públicos verificables: IPA / Cabinet "
                    "Office, Open Government Licence v3.0.",
        "cierre_cta": "mv-project-management.vercel.app",
    },
    "en": {
        "kicker": "Before / after",
        "titulo": "The same portfolio. Two very different Mondays.",
        "sub": "{total} real public projects from the UK government.",
        "antes_t": "BEFORE",
        "antes_h": "Open {total} projects, one by one",
        "antes_b1": "{minutos} minutes of manual review per project",
        "antes_b2": "{horas:.0f} hours before you know which ones are red",
        "antes_b3": "Overruns surface once the money is already spent",
        "antes_pie": "Stated assumption: {minutos} minutes per project. Not a measurement.",
        "desp_t": "AFTER",
        "desp_h": "The engine ranks them for you",
        "desp_b1": "{sobre} projects over budget, by name and percentage",
        "desp_b2": "Health across 6 dimensions, computed, not eyeballed",
        "desp_b3": "Which task blocks how many others, before the meeting",
        "desp_pie": "Worst in the portfolio: {peor_pct:.1f}% of its budget.",
        "comp_t": "What changes for whoever signs",
        "comp_izq_l": "Time to know",
        "comp_izq_v": "{horas:.0f} hours",
        "comp_der_l": "Time to know",
        "comp_der_v": "seconds",
        "comp_pie": "Same data. Same people. A different point in the month to find out.",
        "cierre_h": "Try it on your own projects",
        "cierre_b": "Seven full days, everything unlocked. The numbers in this "
                    "video come from verifiable public data: IPA / Cabinet "
                    "Office, Open Government Licence v3.0.",
        "cierre_cta": "mv-project-management.vercel.app",
    },
    "pt": {
        "kicker": "Antes / depois",
        "titulo": "O mesmo portfólio. Duas segundas-feiras diferentes.",
        "sub": "{total} projetos públicos reais do governo britânico.",
        "antes_t": "ANTES",
        "antes_h": "Abrir {total} projetos, um por um",
        "antes_b1": "{minutos} minutos de revisão manual por projeto",
        "antes_b2": "{horas:.0f} horas até saber quais estão em vermelho",
        "antes_b3": "Os desvios aparecem quando o dinheiro já foi gasto",
        "antes_pie": "Suposição declarada: {minutos} minutos por projeto. Não é uma medição.",
        "desp_t": "DEPOIS",
        "desp_h": "O motor ordena sozinho",
        "desp_b1": "{sobre} projetos acima do orçamento, com nome e percentual",
        "desp_b2": "Saúde em 6 dimensões, calculada, não estimada a olho",
        "desp_b3": "Qual tarefa bloqueia quantas outras, antes da reunião",
        "desp_pie": "O pior do portfólio: {peor_pct:.1f}% do orçamento previsto.",
        "comp_t": "O que muda para quem assina",
        "comp_izq_l": "Descobrir",
        "comp_izq_v": "{horas:.0f} horas",
        "comp_der_l": "Descobrir",
        "comp_der_v": "segundos",
        "comp_pie": "Mesmo dado. Mesma equipe. Outro momento do mês para descobrir.",
        "cierre_h": "Teste com os seus próprios projetos",
        "cierre_b": "Sete dias completos, tudo desbloqueado. Os números deste "
                    "vídeo vêm de dados públicos verificáveis: IPA / Cabinet "
                    "Office, Open Government Licence v3.0.",
        "cierre_cta": "mv-project-management.vercel.app",
    },
}

_CLAVES = set(TEXTS["es"])
for _l, _t in TEXTS.items():
    assert set(_t) == _CLAVES, (
        f"TEXTS[{_l!r}] no tiene las mismas claves que el español: "
        f"faltan {_CLAVES - set(_t)}, sobran {set(_t) - _CLAVES}")


def T(lang: str, clave: str) -> str:
    """El texto del idioma, con los números del motor ya sustituidos."""
    return TEXTS[lang][clave].format(**D)


# ------------------------------------------------------------------ escenas
#
# Ninguna escena fija un tamaño de fuente para una traducción puntual: todo
# pasa por fit_font / center_text_fit / fit_paragraph, que miden el texto real
# contra su caja y achican hasta que entra. El inglés y el portugués suelen
# ser más largos que el español y no se salen del marco.

def _panel(d: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int,
           borde, relleno=(11, 27, 48)) -> None:
    d.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=relleno,
                        outline=borde, width=2)


def _vinetas(d: ImageDraw.ImageDraw, x: int, y: int, ancho: int,
             textos: list[str], color_punto, f) -> int:
    """Dibuja las viñetas una debajo de otra devolviendo la y final. Cada
    línea se envuelve dentro de `ancho`, así que nunca pisa el borde del
    panel ni la viñeta de al lado."""
    from assets.video.build_video import wrap_lines
    for texto in textos:
        lineas = wrap_lines(d, texto, f, ancho - 34)
        d.ellipse([x + 4, y + 8, x + 14, y + 18], fill=color_punto)
        for i, linea in enumerate(lineas):
            d.text((x + 30, y + (i * (f.size + 6))), linea, font=f, fill=INK)
        y += len(lineas) * (f.size + 6) + 16
    return y


def scene_intro(p: float, lang: str) -> Image.Image:
    img = base_frame()
    d = ImageDraw.Draw(img)
    a = ease(min(1.0, p * 2.2))
    y = int(250 - 30 * a)
    center_text_fit(d, y - 70, T(lang, "kicker"), 26, W - 300, AMBER, bold=True)
    center_text_fit(d, y, T(lang, "titulo"), 54, W - 200, INK, bold=True)
    center_text_fit(d, y + 100, T(lang, "sub"), 27, W - 320, MUTED, bold=False)
    # La barra que separa los dos mundos, creciendo desde el centro.
    ancho = int((W - 420) * ease(min(1.0, max(0.0, p * 1.6 - 0.35))))
    if ancho > 4:
        d.rounded_rectangle([W // 2 - ancho // 2, y + 178,
                             W // 2 + ancho // 2, y + 184], radius=3, fill=AMBER)
    return img


def _lado(img: Image.Image, lang: str, cual: str, prog: float) -> None:
    """Dibuja uno de los dos paneles. `cual` es 'antes' o 'desp'."""
    d = ImageDraw.Draw(img)
    rojo = cual == "antes"
    color = RED if rojo else GREEN
    x0, x1 = 90, W - 90
    _panel(d, x0, 130, x1, H - 96, color)

    f_tag = font(24, True)
    tag = T(lang, f"{cual}_t")
    w_tag = d.textlength(tag, font=f_tag)
    d.rounded_rectangle([x0 + 34, 158, x0 + 34 + w_tag + 34, 200],
                        radius=21, fill=color)
    d.text((x0 + 51, 165), tag, font=f_tag, fill=NAVY)

    f_h = fit_font(d, T(lang, f"{cual}_h"), x1 - x0 - 90, 42, 22, True)
    d.text((x0 + 40, 226), T(lang, f"{cual}_h"), font=f_h, fill=color)

    # Las viñetas entran de a una, al ritmo de la escena.
    todas = [T(lang, f"{cual}_b{i}") for i in (1, 2, 3)]
    cuantas = max(1, min(len(todas), int(prog * (len(todas) + 0.6)) + 1))
    _vinetas(d, x0 + 40, 300, x1 - x0 - 80, todas[:cuantas], color, font(25, False))

    pie = T(lang, f"{cual}_pie")
    f_pie = fit_font(d, pie, x1 - x0 - 80, 20, 13, False)
    d.text((x0 + 40, H - 152), pie, font=f_pie, fill=MUTED)


def scene_antes(p: float, lang: str) -> Image.Image:
    img = base_frame()
    _lado(img, lang, "antes", p)
    return img


def scene_despues(p: float, lang: str) -> Image.Image:
    img = base_frame()
    _lado(img, lang, "desp", p)
    return img


def scene_comparativa(p: float, lang: str) -> Image.Image:
    img = base_frame()
    d = ImageDraw.Draw(img)
    center_text_fit(d, 96, T(lang, "comp_t"), 42, W - 220, INK, bold=True)

    cajas = [(120, RED, T(lang, "comp_izq_l"), T(lang, "comp_izq_v"), T(lang, "antes_t")),
             (W // 2 + 30, GREEN, T(lang, "comp_der_l"), T(lang, "comp_der_v"),
              T(lang, "desp_t"))]
    ancho = W // 2 - 150
    for i, (x, col, label, valor, tag) in enumerate(cajas):
        # La segunda caja aparece después, para que se lea como un antes→después.
        a = ease(min(1.0, max(0.0, p * 2.0 - i * 0.5)))
        if a <= 0.02:
            continue
        y0 = int(200 + 26 * (1 - a))
        _panel(d, x, y0, x + ancho, y0 + 250, col)
        f_tag = font(19, True)
        d.text((x + 28, y0 + 24), tag, font=f_tag, fill=col)
        f_l = fit_font(d, label, ancho - 56, 24, 14, False)
        d.text((x + 28, y0 + 62), label, font=f_l, fill=MUTED)
        f_v = fit_font(d, valor, ancho - 56, 74, 30, True)
        d.text((x + 28, y0 + 108), valor, font=f_v, fill=col)

    if p > 0.55:
        center_text_fit(d, H - 118, T(lang, "comp_pie"), 24, W - 260, MUTED,
                        bold=False)
    return img


def scene_cierre(p: float, lang: str) -> Image.Image:
    img = base_frame()
    d = ImageDraw.Draw(img)
    a = ease(min(1.0, p * 2.0))
    center_text_fit(d, int(196 - 22 * a), T(lang, "cierre_h"), 50, W - 220,
                    INK, bold=True)
    # El párrafo se achica hasta entrar en su caja y se dibuja centrado línea
    # a línea: ninguna traducción puede desbordar ni pisar el botón de abajo.
    f, lineas, line_h = fit_paragraph(d, T(lang, "cierre_b"), W - 420, 150, 25,
                                      15, bold=False)
    for i, linea in enumerate(lineas):
        w = d.textlength(linea, font=f)
        d.text(((W - w) / 2, 290 + i * line_h), linea, font=f, fill=MUTED)
    if p > 0.35:
        cta = T(lang, "cierre_cta")
        f = fit_font(d, cta, W - 420, 30, 18, True)
        w = d.textlength(cta, font=f)
        d.rounded_rectangle([W / 2 - w / 2 - 30, H - 150, W / 2 + w / 2 + 30,
                             H - 150 + f.size + 30], radius=25,
                            fill=(24, 22, 12), outline=AMBER, width=2)
        d.text((W / 2 - w / 2, H - 136), cta, font=f, fill=AMBER)
    return img


SCENES = [
    (scene_intro, 5.0),
    (scene_antes, 9.0),
    (scene_despues, 9.5),
    (scene_comparativa, 7.0),
    (scene_cierre, 6.0),
]

# La narración también sale de `D`: los números se interpolan, no se escriben.
NARRATIONS = {
    "es": [
        "El mismo portafolio, dos lunes distintos. {total} proyectos "
        "públicos reales del gobierno británico.",
        "Antes: abrir los {total} proyectos uno por uno. A {minutos} minutos de "
        "revisión cada uno, son {horas:.0f} horas hasta saber cuáles están en rojo. "
        "Para entonces, el desvío ya se gastó.",
        "Después: el motor los ordena solo. {sobre} proyectos sobre presupuesto, "
        "con nombre y porcentaje. La salud sale en seis dimensiones, calculada, y "
        "el motor te dice qué tarea bloquea a cuántas otras.",
        "Para quien firma, lo que cambia no es el dato: es cuándo se entera. "
        "{horas:.0f} horas de trabajo manual, o segundos.",
        "Probalo con tus propios proyectos: siete días completos, todo "
        "desbloqueado. Los números de este video salen de datos públicos "
        "verificables.",
    ],
    "en": [
        "The same portfolio, two very different Mondays. {total} real public "
        "projects from the UK government.",
        "Before: opening all {total} projects one by one. At {minutos} minutes of "
        "review each, that is {horas:.0f} hours before you know which ones are red. "
        "By then, the overrun is already spent.",
        "After: the engine ranks them for you. {sobre} projects over budget, by "
        "name and percentage. Health comes out across six dimensions, computed, and "
        "the engine tells you which task blocks how many others.",
        "For whoever signs, what changes is not the data: it is when they find out. "
        "{horas:.0f} hours of manual work, or seconds.",
        "Try it on your own projects: seven full days, everything unlocked. The "
        "numbers in this video come from verifiable public data.",
    ],
    "pt": [
        "O mesmo portfólio, duas segundas-feiras diferentes. {total} projetos "
        "públicos reais do governo britânico.",
        "Antes: abrir os {total} projetos um por um. A {minutos} minutos de revisão "
        "cada um, são {horas:.0f} horas até saber quais estão em vermelho. A essa "
        "altura, o desvio já foi gasto.",
        "Depois: o motor ordena sozinho. {sobre} projetos acima do orçamento, com "
        "nome e percentual. A saúde sai em seis dimensões, calculada, e o motor diz "
        "qual tarefa bloqueia quantas outras.",
        "Para quem assina, o que muda não é o dado: é quando fica sabendo. "
        "{horas:.0f} horas de trabalho manual, ou segundos.",
        "Teste com os seus próprios projetos: sete dias completos, tudo "
        "desbloqueado. Os números deste vídeo vêm de dados públicos verificáveis.",
    ],
}

for _lang, _textos in NARRATIONS.items():
    assert len(_textos) == len(SCENES), (
        f"NARRATIONS[{_lang!r}] tiene {len(_textos)} textos y SCENES tiene "
        f"{len(SCENES)} escenas — van 1 a 1.")


def narracion(lang: str) -> list[str]:
    return [t.format(**D) for t in NARRATIONS[lang]]


def _scene_seconds(narrations: list[str] | None) -> list[float]:
    return [max(min_s, VOICE_LEAD + _wav_duration(narrations[i]) + VOICE_TAIL)
            if narrations else min_s
            for i, (_, min_s) in enumerate(SCENES)]


def build(lang: str) -> str:
    out, landing_copy = _out_path(lang), _landing_path(lang)
    tmpdir = tempfile.mkdtemp(prefix=f"mvpm_ad_{lang}_")
    narrations = _synth_narrations_de(narracion(lang), lang, tmpdir)
    secs_list = _scene_seconds(narrations)

    import imageio.v2 as imageio  # sólo para escribir el .mp4

    os.makedirs(os.path.dirname(out), exist_ok=True)
    video_only = os.path.join(tmpdir, "sin_audio.mp4") if narrations else out
    writer = imageio.get_writer(video_only, fps=FPS, codec="libx264",
                                quality=7, macro_block_size=16,
                                ffmpeg_params=["-pix_fmt", "yuv420p"])
    black = Image.new("RGB", (W, H), (0, 0, 0))
    for (scene, _), secs in zip(SCENES, secs_list):
        n = int(round(secs * FPS))
        for f_i in range(n):
            p = f_i / max(1, n - 1)
            frame = scene(p, lang)
            t, rem = f_i / FPS, secs - f_i / FPS
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
                        "-shortest", out], check=True, capture_output=True)

    os.makedirs(os.path.dirname(landing_copy), exist_ok=True)
    shutil.copyfile(out, landing_copy)
    shutil.rmtree(tmpdir, ignore_errors=True)
    return out


def build_all() -> dict[str, str]:
    return {lang: build(lang) for lang in LANGS}


if __name__ == "__main__":
    for lang, ruta in build_all().items():
        print(f"[{lang}] {ruta}  ({os.path.getsize(ruta) / 1e6:.1f} MB)")
