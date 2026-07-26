"""Tests de las plantillas de gobernanza por rubro.

Buena parte son tests de integridad del contenido. Puede parecer poco, pero es
lo que evita el peor resultado posible acá: una plantilla que parece completa,
se lleva a la reunión con el cliente, y tiene una etapa sin criterio de salida o
un riesgo apuntando a un área de PMBOK que no existe.
"""

import pytest

from mvpm import plantillas as pl
from mvpm import pmbok


def test_estan_todos_los_rubros_esperados():
    claves = set(pl.PLANTILLAS)
    esperados = {"construccion", "software", "farma", "manufactura", "servicios",
                 "energia", "salud", "financiero", "agro", "publico", "retail",
                 "educacion", "logistica", "telecom"}
    assert esperados <= claves


def test_rubro_desconocido():
    with pytest.raises(ValueError, match="Rubro desconocido"):
        pl.obtener("mineria_espacial")


# --------------------------------------------------- integridad del contenido

@pytest.mark.parametrize("clave", sorted(pl.PLANTILLAS))
def test_la_plantilla_esta_completa(clave):
    p = pl.obtener(clave)
    assert p.rubro and len(p.resumen) > 40
    assert len(p.etapas) >= 4, "una gobernanza con menos de 4 etapas no gobierna nada"
    assert p.roles and p.riesgos and p.indicadores and p.normativa
    assert p.portafolios_sugeridos and p.areas_criticas


@pytest.mark.parametrize("clave", sorted(pl.PLANTILLAS))
def test_toda_etapa_tiene_puerta_de_salida(clave):
    """Una etapa sin criterio de salida ni responsable no es una puerta."""
    for e in pl.obtener(clave).etapas:
        assert e.nombre and e.objetivo
        assert e.entregables, f"{clave}/{e.clave} sin entregables"
        assert e.criterio_salida, f"{clave}/{e.clave} sin criterio de salida"
        assert e.aprueba, f"{clave}/{e.clave} no dice quién aprueba"


@pytest.mark.parametrize("clave", sorted(pl.PLANTILLAS))
def test_las_etapas_usan_grupos_de_proceso_reales(clave):
    validos = {g["clave"] for g in pmbok.GRUPOS_PROCESO}
    for e in pl.obtener(clave).etapas:
        assert e.grupo_pmbok in validos, f"{clave}/{e.clave}: grupo {e.grupo_pmbok!r}"


@pytest.mark.parametrize("clave", sorted(pl.PLANTILLAS))
def test_los_riesgos_apuntan_a_areas_de_pmbok_reales(clave):
    validas = {a["clave"] for a in pmbok.AREAS}
    for r in pl.obtener(clave).riesgos:
        assert r.area_pmbok in validas, f"{clave}: área {r.area_pmbok!r} no existe"
        assert r.senal_temprana and r.mitigacion


@pytest.mark.parametrize("clave", sorted(pl.PLANTILLAS))
def test_las_areas_criticas_existen(clave):
    validas = {a["clave"] for a in pmbok.AREAS}
    assert set(pl.obtener(clave).areas_criticas) <= validas


@pytest.mark.parametrize("clave", sorted(pl.PLANTILLAS))
def test_toda_plantilla_arranca_y_cierra(clave):
    """Sin etapa de inicio no hay autorización; sin cierre, el proyecto no termina."""
    grupos = {e.grupo_pmbok for e in pl.obtener(clave).etapas}
    assert "inicio" in grupos, f"{clave} no tiene etapa de inicio"
    assert "cierre" in grupos, f"{clave} no tiene etapa de cierre"


@pytest.mark.parametrize("clave", sorted(pl.PLANTILLAS))
def test_las_claves_de_etapa_no_se_repiten(clave):
    claves = [e.clave for e in pl.obtener(clave).etapas]
    assert len(claves) == len(set(claves))


def test_los_rubros_regulados_nombran_su_normativa():
    """En estos rubros una plantilla sin normativa concreta no sirve de nada."""
    for clave, esperado in [("farma", "GMP"), ("publico", "TOCAF"),
                            ("financiero", "Banco Central"), ("telecom", "URSEC")]:
        texto = " ".join(pl.obtener(clave).normativa)
        assert esperado in texto, f"{clave} no menciona {esperado}"


def test_cada_rubro_tiene_riesgos_propios_no_genericos():
    """Si dos rubros comparten los mismos riesgos, la plantilla no aporta nada."""
    por_rubro = {c: {r.titulo for r in pl.obtener(c).riesgos} for c in pl.PLANTILLAS}
    claves = sorted(por_rubro)
    for i, a in enumerate(claves):
        for b in claves[i + 1:]:
            comunes = por_rubro[a] & por_rubro[b]
            assert not comunes, f"{a} y {b} repiten riesgos: {comunes}"


# ------------------------------------------------------------------ derivados

def test_areas_criticas_explicadas_trae_las_definiciones():
    areas = pl.areas_criticas_explicadas("construccion")
    assert len(areas) == len(pl.obtener("construccion").areas_criticas)
    assert all("definicion_tecnica" in a and "criollo" in a for a in areas)


def test_checklist_aplana_todos_los_entregables():
    p = pl.obtener("farma")
    ch = pl.checklist("farma")
    assert len(ch) == sum(len(e.entregables) for e in p.etapas)
    assert all(f["aprueba"] and f["criterio_salida"] for f in ch)


def test_texto_imprimible_trae_lo_importante():
    txt = pl.como_texto("construccion")
    assert "Construcción" in txt
    assert "Recepción provisoria" in txt
    assert "Puerta de salida" in txt
    assert "Ley 16.074" in txt
    # La aclaración de que no es asesoramiento legal no puede faltar.
    assert "asesoramiento legal" in txt


@pytest.mark.parametrize("clave", sorted(pl.PLANTILLAS))
def test_el_texto_imprimible_no_se_rompe_en_ningun_rubro(clave):
    txt = pl.como_texto(clave)
    assert txt.startswith("# Gobernanza de proyectos")
    assert "{" not in txt and "}" not in txt          # sin formato sin resolver


# --------------------------------------------------------------- persistencia

@pytest.fixture
def empresa(tmp_path, monkeypatch):
    from mvpm import db
    monkeypatch.setattr(db, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(db, "_DB_FILE", tmp_path / "plantillas.db")
    db.init_db()
    return db.obtener_o_crear_empresa("Constructora del Este")


def test_sin_adoptar_no_hay_plantilla(empresa):
    assert pl.aplicada(empresa) is None


def test_adoptar_y_recuperar(empresa):
    pl.adoptar(empresa, "construccion", "Ana Pérez", "Directora de obra")
    activa = pl.aplicada(empresa)
    assert activa["clave"] == "construccion"
    assert activa["plantilla"].rubro.startswith("Construcción")
    assert activa["version"]["validado_por_nombre"] == "Ana Pérez"
    assert activa["version"]["estado"] == "validado"


def test_adoptar_sin_validar_queda_en_borrador(empresa):
    pl.adoptar(empresa, "software")
    assert pl.aplicada(empresa)["version"]["estado"] == "borrador"


def test_cambiar_de_rubro_no_pierde_la_historia(empresa):
    from mvpm import db
    pl.adoptar(empresa, "software")
    pl.adoptar(empresa, "servicios", "Juan Gómez", "Socio")
    assert pl.aplicada(empresa)["clave"] == "servicios"
    historial = db.historial_versiones(empresa, pl.ENTIDAD, "rubro")
    assert len(historial) == 2


def test_no_se_puede_adoptar_un_rubro_inventado(empresa):
    with pytest.raises(ValueError):
        pl.adoptar(empresa, "no_existe")
    assert pl.aplicada(empresa) is None       # y no queda nada guardado
