# © 2026 Martín Viera. Todos los derechos reservados.
"""El recorrido largo de la landing (`assets/video/build_video.py`).

El video corto de antes/después tenía suite desde que se hizo; éste, que es
el que de verdad muestra el producto entero, no tenía ninguna. La diferencia
importa porque es el archivo que más crece: cada función nueva del producto le
agrega una escena, y son justo esos agregados los que rompen en silencio.

Lo que se fija acá:

 1. **Que escena y narración vayan 1 a 1.** El módulo ya tiene un `assert` de
    import que lo exige, pero un `assert` sólo protege a quien importe el
    módulo. Acá queda como test para que CI lo reporte con nombre propio en
    vez de "error al importar".
 2. **La paridad ES/EN/PT**, la misma regla que `mvpm/i18n.py`: si una clave
    existe en español y falta en otro idioma, esa versión del video muestra un
    hueco o revienta al dibujar.
 3. **Que ninguna traducción haya quedado en español.** Es la forma más común
    de "traducir" sin traducir, y en un video no se nota hasta que alguien lo
    mira entero en inglés.
 4. **Que ningún texto reviente su caja en ningún idioma.** Las escenas se
    dibujan de verdad, en los 3 idiomas: el alemán del pobre es el portugués,
    que suele ser más largo que el español y es donde primero explota un
    helper de ajuste.
 5. **Que las escenas nuevas realmente estén en el video**, y no sólo
    definidas como función suelta que nadie agregó a `SCENES` — que es el
    olvido natural al sumar una escena.
"""

from pathlib import Path

import pytest

from assets.video import build_video as bv

LANGS = ("es", "en", "pt")

RAIZ = Path(__file__).resolve().parent.parent
LANDING = RAIZ / "landing"

#: Techo de duración, en segundos, que promete el copy de la landing
#: («menos de 3 minutos» / «under 3 minutes» / «em menos de 3 minutos»).
TECHO_SEGUNDOS = 180


# ----------------------------------------------------------------- estructura

def test_cada_escena_tiene_su_narracion_en_los_tres_idiomas():
    for lang in LANGS:
        assert len(bv.NARRATIONS[lang]) == len(bv.SCENES), (
            f"[{lang}] {len(bv.NARRATIONS[lang])} narraciones para "
            f"{len(bv.SCENES)} escenas — tienen que ir 1 a 1")
        vacias = [i for i, t in enumerate(bv.NARRATIONS[lang]) if not t.strip()]
        assert not vacias, f"[{lang}] narración vacía en las escenas {vacias}"


@pytest.mark.parametrize("lang", ["en", "pt"])
def test_las_tres_versiones_tienen_las_mismas_claves_en_pantalla(lang):
    faltan = sorted(set(bv.TEXTS["es"]) - set(bv.TEXTS[lang]))
    sobran = sorted(set(bv.TEXTS[lang]) - set(bv.TEXTS["es"]))
    assert not faltan, f"TEXTS[{lang!r}] no tiene: {faltan}"
    assert not sobran, f"TEXTS[{lang!r}] tiene de más: {sobran}"


#: Claves que coinciden con el español a propósito, y por qué. Se listan una
#: por una para que sumar una excepción sea una decisión explícita y no la
#: forma cómoda de hacer pasar un test.
IGUALES_A_PROPOSITO = {
    "en": {
        "bit_formatos",       # "HTML · WORD · PDF" — nombres de formato
        "ins_modo1_host",     # 127.0.0.1 — una dirección IP no se traduce
        "ins_modo2_host",     # 0.0.0.0
    },
    "pt": {
        "bit_formatos",
        "ins_modo1_host",
        "ins_modo2_host",
        # El portugués comparte estas palabras exactas con el español; exigir
        # que difieran sería pedir una traducción peor. Que la clave vecina
        # `pmbok_tag_criollo` SÍ esté traducida es la prueba de que acá no hubo
        # descuido: son coincidencias del idioma.
        "intro_badge",        # "IA ADITIVA" se escribe igual en portugués
        "org_cols",           # nombres de columna de un archivo: cargos · áreas · reporta_a
        "org_arrow",          # "→  IA  →": símbolos y una sigla
        "pmbok_tag_tec",      # "TÉCNICO" es la misma palabra
    },
}


@pytest.mark.parametrize("lang", ["en", "pt"])
def test_ninguna_traduccion_quedo_igual_al_español(lang):
    """Una traducción idéntica al español es, casi siempre, una traducción que
    nadie hizo. Sólo se comparan los textos: las listas de tuplas con color
    (los pasos de gobernanza, la minuta) se revisan aparte."""
    iguales = [k for k, v in bv.TEXTS["es"].items()
               if isinstance(v, str)
               and k not in IGUALES_A_PROPOSITO[lang]
               and bv.TEXTS[lang][k] == v]
    assert not iguales, f"sin traducir al {lang}: {iguales}"


# -------------------------------------------------------------------- dibujo

def test_ningun_texto_se_sale_de_su_caja_en_ningun_idioma():
    """Dibuja cada escena de verdad, en los 3 idiomas y en 3 momentos de su
    animación. No juzga estética: verifica que ninguna llamada de dibujo
    reviente y que el cuadro salga del tamaño correcto — que es donde aparece
    el error de "esta traducción no entra y el helper de ajuste explota"."""
    for lang in LANGS:
        for escena, _ in bv.SCENES:
            for p in (0.0, 0.5, 1.0):
                img = escena(p, lang)
                assert img.size == (bv.W, bv.H), (
                    f"[{lang}] {escena.__name__} en p={p} devolvió {img.size}")


def test_toda_escena_definida_esta_en_el_video():
    """Definir la función y olvidarse de agregarla a SCENES es el olvido
    natural al sumar una escena: no falla nada, simplemente no se ve."""
    definidas = {n for n in dir(bv) if n.startswith("scene_")}
    en_el_video = {e.__name__ for e, _ in bv.SCENES}
    huerfanas = sorted(definidas - en_el_video)
    assert not huerfanas, (
        f"escenas definidas que no están en SCENES (no se ven en el video): "
        f"{huerfanas}")


# ------------------------------------- las funciones nuevas están en el video

#: Cada función del producto que el video promete, con una clave suya. Si
#: alguien saca una escena, el video deja de mostrar algo que la landing sigue
#: vendiendo — y eso no lo detecta ningún otro test.
PROMESAS = {
    "reuniones y minutas": "reu_minuta",
    "relevamiento por área": "rel_areas",
    "bitácora técnica / criollo": "bit_criollo",
    "modos de instalación": "ins_modo2_host",
}


@pytest.mark.parametrize("que,clave", sorted(PROMESAS.items()))
def test_el_video_muestra_cada_funcion_que_la_landing_vende(que, clave):
    for lang in LANGS:
        assert bv.TEXTS[lang].get(clave), f"[{lang}] falta «{que}» ({clave})"


def test_el_relevamiento_muestra_sus_nueve_areas():
    """Las 9 áreas son las de `mvpm/relevamiento_preguntas.py`. Si el motor
    gana o pierde un área y el video sigue diciendo nueve, el video miente."""
    from mvpm import relevamiento_preguntas as rp
    reales = len(rp.AREAS)
    for lang in LANGS:
        en_pantalla = len(bv.TEXTS[lang]["rel_areas"])
        assert en_pantalla == reales, (
            f"[{lang}] el video muestra {en_pantalla} áreas y el motor tiene "
            f"{reales}")


# ------------------------------------------- lo que la landing promete y dura

VIDEOS = ("demo.mp4", "demo_en.mp4", "demo_pt.mp4")


# --------------------------------------------------- leer el .mp4 sin ffmpeg
#
# Estos dos tests son los únicos que miran el ARCHIVO publicado, así que tienen
# que correr donde importa: en CI. La primera versión llamaba a ffmpeg vía
# `imageio_ffmpeg`, que está en mi entorno de desarrollo pero NO en
# `requirements.txt` — la suite local pasaba y CI se caía con
# ModuleNotFoundError. Saltear el test cuando falta el módulo lo habría puesto
# verde dejándolo sin correr nunca en CI, que es exactamente donde tiene que
# proteger.
#
# Un .mp4 es un árbol de cajas [tamaño uint32][tipo 4 bytes][contenido]. Las
# dos cosas que hace falta saber están ahí y se leen con la biblioteca
# estándar, igual que el .docx y el PDF de la bitácora:
#   · la duración, en la caja `mvhd` (duración / escala de tiempo);
#   · si hay audio, en alguna caja `hdlr` con manejador `soun`.

def _cajas(datos: bytes, ini: int = 0, fin: int | None = None):
    """Itera (tipo, inicio_contenido, fin_contenido) de las cajas de un nivel."""
    fin = len(datos) if fin is None else fin
    pos = ini
    while pos + 8 <= fin:
        tam = int.from_bytes(datos[pos:pos + 4], "big")
        tipo = datos[pos + 4:pos + 8]
        cuerpo = pos + 8
        if tam == 1:  # tamaño de 64 bits, guardado justo después del tipo
            tam = int.from_bytes(datos[pos + 8:pos + 16], "big")
            cuerpo = pos + 16
        elif tam == 0:  # "hasta el final del archivo"
            tam = fin - pos
        if tam < 8:
            return
        yield tipo, cuerpo, min(pos + tam, fin)
        pos += tam


def _buscar(datos: bytes, tipo: bytes, ini: int = 0, fin: int | None = None):
    """Busca una caja por tipo, recursivamente. Devuelve (inicio, fin) o None."""
    for t, cuerpo, tope in _cajas(datos, ini, fin):
        if t == tipo:
            return cuerpo, tope
        # Sólo bajar por los contenedores: una caja de datos puede contener
        # cualquier byte y parecer una caja anidada.
        if t in (b"moov", b"trak", b"mdia", b"minf", b"stbl", b"udta"):
            hallado = _buscar(datos, tipo, cuerpo, tope)
            if hallado:
                return hallado
    return None


def _duracion_mp4(ruta: Path) -> float:
    datos = ruta.read_bytes()
    caja = _buscar(datos, b"mvhd")
    assert caja, f"{ruta.name} no tiene caja mvhd: ¿es un .mp4 válido?"
    ini, _ = caja
    version = datos[ini]
    # v0: creación y modificación de 32 bits; v1: de 64. Después van siempre
    # la escala de tiempo y la duración.
    desp = ini + 4 + (16 if version == 1 else 8)
    escala = int.from_bytes(datos[desp:desp + 4], "big")
    largo = 8 if version == 1 else 4
    duracion = int.from_bytes(datos[desp + 4:desp + 4 + largo], "big")
    assert escala, f"{ruta.name} declara escala de tiempo 0"
    return duracion / escala


def _tiene_pista_de_audio(ruta: Path) -> bool:
    datos = ruta.read_bytes()
    moov = _buscar(datos, b"moov")
    if not moov:
        return False
    for tipo, cuerpo, tope in _cajas(datos, *moov):
        if tipo != b"trak":
            continue
        hdlr = _buscar(datos, b"hdlr", cuerpo, tope)
        # hdlr: versión+banderas (4) · predefinido (4) · tipo de manejador (4)
        if hdlr and datos[hdlr[0] + 8:hdlr[0] + 12] == b"soun":
            return True
    return False


@pytest.mark.skipif(not (LANDING / "video").exists(),
                    reason="landing/ no viaja en el paquete: es del repositorio")
@pytest.mark.parametrize("nombre", VIDEOS)
def test_el_video_publicado_dura_lo_que_promete_la_landing(nombre):
    """El copy de la landing dice «menos de 3 minutos» en los 3 idiomas. Ese
    número es texto estático y el video crece cada vez que el producto suma una
    función: el claim se vuelve mentira sin que falle nada.

    Ya pasó una vez. El copy decía «90 segundos» y era cierto —el video duraba
    91,6 s— hasta que cuatro escenas nuevas lo llevaron a 2:25. No lo detectó
    ningún test porque no había ninguno: se vio midiendo el archivo a mano.
    Este test lo mide sobre el archivo PUBLICADO, que es el que mira el
    visitante, no sobre el guion."""
    ruta = LANDING / "video" / nombre
    assert ruta.exists(), f"{nombre} no está publicado en landing/video/"
    segundos = _duracion_mp4(ruta)
    assert segundos <= TECHO_SEGUNDOS, (
        f"{nombre} dura {segundos:.0f}s y la landing promete menos de "
        f"{TECHO_SEGUNDOS}s — corregí el copy en los 3 idiomas o acortá el video")


@pytest.mark.skipif(not (LANDING / "video").exists(),
                    reason="landing/ no viaja en el paquete: es del repositorio")
@pytest.mark.parametrize("nombre", VIDEOS)
def test_el_video_publicado_tiene_voz(nombre):
    """Renderizar sin los modelos de voz configurados NO falla: sale un video
    mudo. Es el error más fácil de commitear sin notarlo, porque el archivo se
    ve perfecto — hasta que alguien le da play delante de un cliente."""
    assert _tiene_pista_de_audio(LANDING / "video" / nombre), (
        f"{nombre} salió sin pista de audio (¿render sin los modelos de voz?)")


def test_los_dos_modos_de_instalacion_dicen_los_hosts_reales():
    """Los hosts en pantalla salen de `mvpm/instalacion.py`. Escribirlos a
    mano en el video es la forma de que queden viejos sin que nadie se entere."""
    from mvpm import instalacion
    for lang in LANGS:
        assert bv.TEXTS[lang]["ins_modo1_host"] == instalacion.HOST_LOCAL
        assert bv.TEXTS[lang]["ins_modo2_host"] == instalacion.HOST_TODAS
