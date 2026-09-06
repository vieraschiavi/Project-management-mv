# © 2026 Martín Viera. Todos los derechos reservados.
"""Reuniones (transcripción → minuta) y relevamiento del cliente.

Lo que se fija acá, en orden de qué tan caro sale si falla:

 1. **Que la minuta no invente.** Cada punto tiene que ser una CITA TEXTUAL
    presente en la transcripción y atribuida a quien realmente la dijo. Una
    minuta que parafrasea mal una decisión de directorio, o que se la
    adjudica a otra persona, se cobra caro en la reunión siguiente — y nadie
    la revisa contra el audio hasta que ya es tarde.
 2. **Que el parser aguante los cuatro formatos reales.** Zoom, Teams, Meet y
    WebEx exportan distinto; que ande con uno y falle con otro se descubre
    frente al cliente.
 3. **Que las respuestas del relevamiento se versionen.** Corregir una no
    puede borrar la anterior: qué contestaron PRIMERO suele ser la mitad del
    hallazgo.
 4. **Que el relevamiento funcione sin IA.** La repregunta por reglas existe
    siempre; la IA sólo redacta.
"""

import json

import pytest

from mvpm import db, relevamiento as rv, reuniones as r

# --------------------------------------------- transcripciones de muestra
#
# Un formato por plataforma, con las particularidades reales de cada una:
# Zoom parte la frase en varios subtítulos, Teams envuelve al orador en <v>,
# Meet exporta texto plano y WebEx usa SRT con coma decimal.

ZOOM_VTT = """WEBVTT

1
00:00:03.120 --> 00:00:07.400
Ana Pereyra: El maestro de artículos vive en SAP.

2
00:00:07.400 --> 00:00:12.000
Ana Pereyra: El problema es que logística mantiene una planilla aparte.

3
00:00:12.500 --> 00:00:18.000
Diego Silva: Decidimos que la fuente única va a ser SAP.
"""

TEAMS_VTT = """WEBVTT

00:00:02.000 --> 00:00:06.500
<v Ana Pereyra>No sé si el histórico está completo, tengo que consultar.</v>

00:00:06.500 --> 00:00:11.000
<v Diego Silva>Me encargo yo de traer el detalle para el lunes.</v>
"""

MEET_TXT = """Martín Viera: ¿Cada cuánto se actualiza el stock?
Ana Pereyra: Todas las noches. Falta el corte de la planta de Rivera.
"""

WEBEX_SRT = """1
00:00:01,000 --> 00:00:04,000
Diego Silva: Acordamos que el reporte sale semanal.
"""

TODAS = {"zoom": ZOOM_VTT, "teams": TEAMS_VTT, "meet": MEET_TXT, "webex": WEBEX_SRT}


# --------------------------------------------------------------- el parser

@pytest.mark.parametrize("plataforma", sorted(TODAS))
def test_las_cuatro_plataformas_se_parsean(plataforma):
    ints = r.parsear(TODAS[plataforma])
    assert ints, f"{plataforma}: no se extrajo ni una intervención"
    assert all(i.texto.strip() for i in ints)
    assert all(i.orador != r.SIN_ORADOR for i in ints), (
        f"{plataforma}: se perdió el nombre del orador, que es lo único que "
        "hace útil a la transcripción de la plataforma")


def test_detecta_el_formato_por_contenido_y_no_por_extension():
    """El usuario renombra archivos. Un WebVTT guardado como .txt es frecuente
    y tiene que parsearse igual."""
    assert r.detectar_formato(ZOOM_VTT) == "vtt"
    assert r.detectar_formato(WEBEX_SRT) == "srt"
    assert r.detectar_formato(MEET_TXT) == "txt"


def test_une_los_tramos_partidos_del_mismo_orador():
    """Zoom corta una frase en subtítulos de cinco segundos. Sin unirlos, la
    minuta muestra a la misma persona ocho veces seguidas y no la lee nadie."""
    ints = r.parsear(ZOOM_VTT)
    assert len(ints) == 2, f"no se unieron los tramos: {[i.texto for i in ints]}"
    assert ints[0].orador == "Ana Pereyra"
    assert "SAP" in ints[0].texto and "planilla aparte" in ints[0].texto


def test_los_dos_puntos_de_una_frase_no_se_confunden_con_un_orador():
    """"Entonces hicimos esto: lo otro" no puede partirse en un orador llamado
    "Entonces hicimos esto"."""
    ints = r.parsear("Ana Pereyra: Hicimos lo siguiente: cargamos todo de nuevo.")
    assert len(ints) == 1
    assert ints[0].orador == "Ana Pereyra"
    assert "lo siguiente: cargamos" in ints[0].texto


def test_el_minuto_sale_del_archivo_y_no_se_estima():
    ints = r.parsear(ZOOM_VTT)
    assert ints[0].marca == "0:03"
    # El texto plano no trae tiempos: se deja vacío en vez de inventar uno.
    assert r.parsear(MEET_TXT)[0].marca == ""


# ---------------------------------------------------------- la minuta

def test_cada_punto_de_la_minuta_es_una_cita_textual_de_la_transcripcion():
    """EL test de este módulo. Si un punto no está literalmente en lo que se
    dijo, el motor lo inventó."""
    for plataforma, contenido in TODAS.items():
        ints = r.parsear(contenido)
        dicho = " ".join(i.texto for i in ints)
        for punto in r.minuta(ints):
            assert punto["cita"] in dicho, (
                f"{plataforma}: la minuta trae una frase que nadie dijo: "
                f"{punto['cita']!r}")


def test_cada_punto_se_atribuye_a_quien_lo_dijo():
    """Adjudicarle a una persona algo que dijo otra es peor que no tener
    minuta: se cita en la reunión siguiente y hay que desdecirse."""
    ints = r.parsear(ZOOM_VTT)
    por_orador = {i.orador: i.texto for i in ints}
    for punto in r.minuta(ints):
        assert punto["cita"] in por_orador[punto["orador"]], (
            f"«{punto['cita']}» se le adjudicó a {punto['orador']}, que no lo dijo")


def test_clasifica_decision_compromiso_riesgo_y_pendiente():
    ints = r.parsear(ZOOM_VTT + TEAMS_VTT)
    puntos = r.minuta(ints)
    tipos = {t for p in puntos for t in p["tipos"]}
    assert {"decision", "compromiso", "riesgo", "pregunta_abierta"} <= tipos, (
        f"faltaron tipos: {tipos}")


def test_la_cita_es_la_oracion_y_no_la_intervencion_entera():
    """Una intervención de dos minutos citada completa no es una minuta, es la
    transcripción otra vez."""
    ints = r.parsear(ZOOM_VTT)
    larga = max(len(i.texto) for i in ints)
    assert all(len(p["cita"]) < larga for p in r.minuta(ints))


def test_una_frase_puede_ser_riesgo_y_compromiso_a_la_vez():
    tipos = r.clasificar("El problema es que no llegamos, así que me encargo yo.")
    assert "riesgo" in tipos and "compromiso" in tipos


def test_participantes_cuenta_lo_que_hay_y_no_estima_duracion():
    """El archivo trae el segundo de INICIO, no cuánto duró cada intervención.
    Estimar minutos hablados sería inventar un número que después alguien cita
    en un informe."""
    ints = r.parsear(ZOOM_VTT)
    ps = r.participantes(ints)
    assert [p["orador"] for p in ps] == ["Ana Pereyra", "Diego Silva"]
    assert all("minutos" not in p and "duracion" not in p for p in ps)
    assert ps[0]["palabras"] > 0


def test_una_transcripcion_vacia_no_revienta():
    assert r.parsear("") == []
    assert r.minuta([]) == []


# ------------------------------------------------------- el relevamiento

def test_hay_preguntas_en_todas_las_areas():
    for area in rv.areas():
        assert area["preguntas"] > 0, f"el área {area['clave']} quedó sin preguntas"


def test_las_claves_de_pregunta_no_se_repiten_ni_se_traducen():
    claves_es = [p["clave"] for p in rv.preguntas(lang="es")]
    assert len(claves_es) == len(set(claves_es))
    for lang in ("en", "pt"):
        assert [p["clave"] for p in rv.preguntas(lang=lang)] == claves_es


@pytest.mark.parametrize("lang", ["en", "pt"])
def test_todo_el_banco_esta_traducido(lang):
    iguales = [p["clave"] for p, o in zip(rv.preguntas(lang="es"), rv.preguntas(lang=lang))
               if p["pregunta"] == o["pregunta"] or p["por_que"] == o["por_que"]]
    assert not iguales, f"sin traducir al {lang}: {iguales}"


def test_cada_pregunta_dice_que_esta_buscando():
    """Sin el por qué, un consultor nuevo la hace de memoria y no escucha la
    respuesta. Es lo que separa un relevamiento de un cuestionario."""
    for lang in rv.LANGS:
        for p in rv.preguntas(lang=lang):
            assert len(p["por_que"].split()) >= 8, (
                f"[{lang}] {p['clave']} no explica qué busca")


@pytest.fixture
def base_aislada(tmp_path, monkeypatch):
    """Una base vacía por test, con el mismo mecanismo que usa el resto de la
    suite (`monkeypatch.setattr` sobre las rutas del módulo).

    NO se recarga `mvpm.db` con importlib: recargar el módulo lo deja apuntando
    al temporal para TODO lo que corra después, y eso rompía
    `test_rutas.py::test_db_licensing_reviews_y_owner_usan_el_mismo_directorio`
    varios archivos más adelante — un fallo que sólo aparece en la suite
    completa y no al correr este archivo solo, que es la peor clase de fallo."""
    monkeypatch.setattr(db, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(db, "_DB_FILE", tmp_path / "datos.db")
    db.init_db()
    return db.obtener_o_crear_empresa("Conaprole")


def test_guardar_una_respuesta_no_borra_la_anterior(base_aislada):
    """La regla de versionado del repo, donde más importa: qué contestaron
    primero suele ser la mitad del hallazgo."""
    emp = base_aislada

    rv.guardar_respuesta(emp, "fuentes_maestro", "Está en SAP", "Ana", "Sistemas")
    rv.guardar_respuesta(emp, "fuentes_maestro",
                         "Está en SAP pero logística tiene su planilla",
                         "Ana", "Sistemas", estado="validado")

    actual = rv.respuesta_de(emp, "fuentes_maestro")
    assert "planilla" in actual["respuesta"]
    assert actual["responsable"] == "Ana"
    assert actual["estado"] == "validado"
    assert len(rv.historial(emp, "fuentes_maestro")) == 2, (
        "la respuesta anterior se perdió")


def test_no_se_puede_guardar_una_respuesta_a_una_pregunta_que_no_existe(base_aislada):
    """Una respuesta huérfana no se puede mostrar en ninguna pantalla: se
    guardaría en la base y no la vería nadie nunca."""
    with pytest.raises(KeyError):
        rv.guardar_respuesta(base_aislada, "pregunta_inventada", "algo")


def test_la_respuesta_se_guarda_como_json_legible():
    """Se lee desde la base en un informe, y un JSON con los acentos escapados
    es ilegible para quien lo abre con un visor de SQLite."""
    contenido = json.dumps({"respuesta": "canción", "responsable": "",
                            "area_responsable": ""}, ensure_ascii=False)
    assert "canción" in contenido


# ------------------------------------------------ la repregunta sin IA

def test_las_repreguntas_funcionan_sin_ningun_proveedor_configurado():
    """El relevamiento no puede depender de que alguien haya puesto una clave."""
    for respuesta, esperado in (
        ("Depende del área", "depende"),
        ("Creo que sí", "confirmar"),
        ("Lo llevamos en un Excel a mano", "planilla"),
    ):
        sug = rv.repreguntas_sugeridas("calidad_reglas", respuesta)
        assert sug, f"sin sugerencia para {respuesta!r}"
        assert any(esperado in s.lower() for s in sug), (
            f"{respuesta!r} -> {sug}")


def test_una_respuesta_completa_no_dispara_repregunta_boba():
    completa = ("El maestro de artículos está en SAP, lo mantiene Compras, y "
                "se sincroniza con el resto todas las noches a las dos.")
    assert rv.repreguntas_sugeridas("fuentes_maestro", completa) == []


def test_sin_respuesta_no_hay_nada_que_repreguntar():
    assert rv.repreguntas_sugeridas("fuentes_maestro", "") == []
    assert rv.repreguntas_sugeridas("fuentes_maestro", "   ") == []


@pytest.mark.parametrize("lang", ["es", "en", "pt"])
def test_las_repreguntas_salen_en_el_idioma_elegido(lang):
    sug = rv.repreguntas_sugeridas("calidad_reglas", "Depende", lang)
    assert sug and all(s.strip() for s in sug)


def test_el_prompt_de_ia_pide_repreguntar_y_no_resumir():
    """Si el prompt pidiera un resumen, la IA reescribiría lo que dijo el
    cliente — que es exactamente lo que este módulo evita."""
    for lang in rv.LANGS:
        system, user = rv.prompt_de_repregunta("calidad_reglas", "Depende", lang)
        bajo = system.lower()
        assert any(p in bajo for p in ("no resumas", "do not summarise",
                                       "não resuma"))
        assert "Depende" in user


# ------------------------------- el puente entre la reunión y el relevamiento

def test_la_reunion_marca_que_areas_del_pipeline_se_tocaron():
    ints = r.parsear(ZOOM_VTT)
    tocadas = {a["clave"]: a["menciones"] for a in rv.areas_tocadas(ints)}
    assert tocadas["fuentes"] > 0, "no detectó que se habló de fuentes (SAP, planilla)"
    assert tocadas["consumo"] == 0, "marcó un área de la que nadie habló"


def test_las_areas_tocadas_salen_en_los_tres_idiomas():
    ints = r.parsear(ZOOM_VTT)
    for lang in rv.LANGS:
        assert len(rv.areas_tocadas(ints, lang)) == len(rv.areas(lang))
