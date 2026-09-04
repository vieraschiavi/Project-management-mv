# © 2026 Martín Viera. Todos los derechos reservados.
"""El video corto de antes/después de la landing.

Lo que se fija acá es lo que falla en silencio y sale caro:

 1. **Que ninguna cifra esté escrita a mano.** Es el riesgo real de un video
    de ventas: alguien pone "ahorrás 40 horas" en el guion, la fuente cambia
    y el video sigue prometiendo un número que el producto ya no respalda.
    Acá los números salen de `mvpm.demo_real` en tiempo de build, y este test
    lo verifica sustituyendo la fuente por otra y exigiendo que el texto
    cambie con ella.
 2. **Que el supuesto se declare.** Las horas del "antes" NO son una
    medición: son 15 minutos por proyecto multiplicados por la cantidad de
    proyectos. Si el video muestra el número sin decir eso, es una cifra
    inventada con cara de dato.
 3. **La paridad ES/EN/PT**, misma regla que el resto del producto: el texto
    en pantalla y la narración existen en los tres idiomas o no se publica.
 4. **Que la landing apunte a los tres archivos** y no quede un idioma
    sirviendo el video de otro.
"""

import re
from pathlib import Path

import pytest

from assets.video import build_antes_despues as ad

RAIZ = Path(__file__).resolve().parent.parent
LANDING = RAIZ / "landing" / "index.html"


# ----------------------------------------------------- los números son datos

def test_las_cifras_salen_del_motor_y_no_estan_escritas_a_mano(monkeypatch):
    """El test que importa. Se le cambia la fuente por un portafolio
    inventado y se exige que el texto del video cambie con ella: si alguien
    hardcodeara "132 proyectos" en la traducción, este test lo agarra."""
    import pandas as pd

    falso = {
        "total_proyectos": 7,
        "sobre_presupuesto": 3,
        "minutos_por_revision_manual_supuesto": 20,
        "horas_ahorradas_estimadas": 2.0,
        "proyectos_sobre_presupuesto_detalle": pd.DataFrame(
            [{"nombre": "PROYECTO FALSO", "presupuesto": 1.0,
              "ejecutado": 9.0, "ejecucion_pct": 900.0}]),
    }
    monkeypatch.setattr(ad.demo_real, "resumen_portafolio", lambda *a, **k: falso)
    d = ad.datos()
    assert d["total"] == 7 and d["sobre"] == 3 and d["minutos"] == 20
    assert d["peor_pct"] == 900.0

    # Y el texto renderizado con esos datos tiene que hablar de 7, no de 132.
    for lang in ad.LANGS:
        texto = " ".join(ad.TEXTS[lang][k].format(**d) for k in ad.TEXTS[lang])
        assert "7" in texto, f"[{lang}] el total del motor no llegó al texto"
        assert "132" not in texto, (
            f"[{lang}] aparece 132 con otra fuente de datos: hay una cifra "
            "escrita a mano en la traducción")


def test_el_supuesto_de_las_horas_esta_declarado_en_pantalla():
    """Las horas del "antes" son 15 min × proyecto, no una medición. El video
    tiene que decirlo en el mismo cuadro donde muestra el número."""
    for lang in ad.LANGS:
        pie = ad.T(lang, "antes_pie").lower()
        assert str(ad.D["minutos"]) in pie, f"[{lang}] el pie no dice los minutos"
        assert any(p in pie for p in ("supuesto", "suposição", "assumption")), (
            f"[{lang}] el pie no declara que es un supuesto: {pie!r}")
        assert any(p in pie for p in ("no es una medición", "não é uma medição",
                                      "not a measurement")), (
            f"[{lang}] el pie no aclara que no es una medición: {pie!r}")


def test_la_fuente_publica_se_cita_en_el_cierre():
    """Un número sin fuente es una promesa. El cierre nombra el organismo y la
    licencia con la que ese dato se puede republicar."""
    for lang in ad.LANGS:
        cierre = ad.T(lang, "cierre_b")
        assert "Cabinet Office" in cierre, f"[{lang}] no cita el organismo"
        assert "Open Government Licence" in cierre, f"[{lang}] no cita la licencia"


# --------------------------------------------------------------- trilingüe

def test_las_tres_versiones_tienen_las_mismas_claves_en_pantalla():
    es = set(ad.TEXTS["es"])
    for lang in ("en", "pt"):
        assert set(ad.TEXTS[lang]) == es, (
            f"TEXTS[{lang!r}] no tiene las mismas claves que el español")


def test_la_narracion_va_una_por_escena_en_los_tres_idiomas():
    for lang in ad.LANGS:
        assert len(ad.NARRATIONS[lang]) == len(ad.SCENES), (
            f"[{lang}] {len(ad.NARRATIONS[lang])} narraciones para "
            f"{len(ad.SCENES)} escenas")
        assert all(t.strip() for t in ad.narracion(lang)), f"[{lang}] narración vacía"


#: Claves que coinciden con el español a propósito y por qué. El portugués
#: comparte varias palabras exactas con el español; exigir que difieran sería
#: pedir una traducción peor. La lista es explícita para que agregar una
#: excepción sea una decisión y no un descuido.
IGUALES_A_PROPOSITO = {
    "en": {"cierre_cta"},                       # la URL del sitio
    "pt": {"cierre_cta",
           "antes_t",                           # "ANTES" es igual en portugués
           "comp_izq_v",                        # "{horas} horas"
           "comp_der_v"},                       # "segundos"
}


@pytest.mark.parametrize("lang", ["en", "pt"])
def test_ninguna_traduccion_quedo_igual_al_español(lang):
    """Una traducción idéntica al español es, casi siempre, una traducción que
    no se hizo. Las excepciones reales están declaradas arriba."""
    iguales = [k for k in ad.TEXTS["es"]
               if k not in IGUALES_A_PROPOSITO[lang]
               and ad.TEXTS[lang][k] == ad.TEXTS["es"][k]]
    assert not iguales, f"sin traducir al {lang}: {iguales}"


@pytest.mark.skipif(not LANDING.exists(), reason="landing/ es del repositorio")
def test_la_cifra_que_promete_la_landing_es_la_que_calcula_el_motor():
    """En el video la cifra se interpola; en el HTML de la landing es texto
    estático y puede quedar vieja. Este test la ata al motor: el copy de la
    sección antes/después, en los tres idiomas, tiene que decir el total real
    del portafolio y ningún otro número de proyectos."""
    html = LANDING.read_text(encoding="utf-8")
    copys = re.findall(r'data-i="(ad_lead|ad_h2)"[^>]*>([^<]+)<', html)
    copys += re.findall(r'\bad_(?:lead|h2):"([^"]+)"', html)
    textos = [c[1] if isinstance(c, tuple) else c for c in copys]
    assert textos, "no se encontró el copy de la sección antes/después"
    total = str(ad.D["total"])
    con_numero = [t for t in textos if re.search(r"\b\d{2,}\b", t)]
    assert con_numero, "ningún copy de la landing menciona la cantidad de proyectos"
    for t in con_numero:
        nums = re.findall(r"\b\d{2,}\b", t)
        assert nums == [total], (
            f"la landing promete {nums} proyectos y el motor calcula {total}: "
            f"{t!r}")


# ------------------------------------------------------- texto que sí entra

def test_ningun_texto_se_sale_de_su_caja_en_ningun_idioma():
    """Las escenas se dibujan de verdad en los 3 idiomas. No comprueba
    estética; comprueba que ninguna llamada de dibujo reviente y que el cuadro
    salga del tamaño correcto — que es donde aparecen los errores de tipo
    "esta traducción no entra y el helper explota"."""
    for lang in ad.LANGS:
        for escena, _ in ad.SCENES:
            for p in (0.0, 0.5, 1.0):
                img = escena(p, lang)
                assert img.size == (ad.W, ad.H), (
                    f"[{lang}] {escena.__name__} devolvió {img.size}")


# ------------------------------------------------------------- en la landing

@pytest.mark.skipif(not LANDING.exists(),
                    reason="landing/ no viaja en el paquete: es del repositorio")
def test_la_landing_sirve_el_video_del_idioma_elegido():
    """El bug que esto tapa: agregar el video en español y que al cambiar a
    inglés se siga viendo el español, que fue exactamente lo que pasó con el
    demo largo antes de renderizarlo por idioma."""
    html = LANDING.read_text(encoding="utf-8")
    assert 'id="adVideo"' in html, "la landing no tiene el video antes/después"
    for archivo in ("antes_despues.mp4", "antes_despues_en.mp4",
                    "antes_despues_pt.mp4"):
        assert archivo in html, f"la landing no referencia {archivo}"
    # El switcher tiene que conocer el video por su id, o cambiar de idioma no
    # lo toca.
    bloque = re.search(r"const VIDEO_SRC = \{.*?\n\};", html, re.S)
    assert bloque and "adVideo" in bloque.group(0), (
        "VIDEO_SRC no incluye adVideo: el video no cambia con el idioma")


@pytest.mark.skipif(not LANDING.exists(), reason="landing/ es del repositorio")
def test_los_tres_videos_y_la_portada_estan_publicados():
    faltan = [n for n in ("antes_despues.mp4", "antes_despues_en.mp4",
                          "antes_despues_pt.mp4", "poster_antes_despues.jpg")
              if not (RAIZ / "landing" / "video" / n).exists()]
    assert not faltan, f"faltan en landing/video/: {faltan}"


#: `imageio_ffmpeg` trae el binario con el que se mide la duración, pero es
#: una dependencia sólo del render (no está en requirements.txt: un cliente no
#: la necesita para usar el producto, y CI no la instala). El test que la
#: precisa se saltea donde no está, en vez de exigirle a todo el mundo el
#: stack de video para poder correr la suite.
try:
    from imageio_ffmpeg import get_ffmpeg_exe
    HAY_FFMPEG = True
except ImportError:  # pragma: no cover - depende del entorno
    HAY_FFMPEG = False


@pytest.mark.skipif(not LANDING.exists(), reason="landing/ es del repositorio")
@pytest.mark.skipif(not HAY_FFMPEG,
                    reason="imageio_ffmpeg es del entorno de render, no del producto")
def test_el_video_de_ventas_es_breve():
    """"Breve" es el requisito, no un adorno: un gerente no mira tres minutos.
    Techo de 90 segundos por idioma, medido sobre el archivo publicado."""
    import subprocess
    for nombre in ("antes_despues.mp4", "antes_despues_en.mp4",
                   "antes_despues_pt.mp4"):
        ruta = RAIZ / "landing" / "video" / nombre
        salida = subprocess.run([get_ffmpeg_exe(), "-i", str(ruta)],
                                capture_output=True, text=True).stderr
        m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", salida)
        assert m, f"no se pudo leer la duración de {nombre}"
        segundos = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        assert segundos <= 90, f"{nombre} dura {segundos:.0f}s (techo: 90s)"
        assert "Audio:" in salida, f"{nombre} salió sin pista de audio"
