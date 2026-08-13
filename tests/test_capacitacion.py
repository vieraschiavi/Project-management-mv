# © 2026 Martín Viera. Todos los derechos reservados.
"""Tests de la capacitación por rol."""

import pytest

from mvpm import capacitacion as cap


def test_estan_los_roles_del_producto():
    assert set(cap.CURRICULAS) == {"sponsor", "pm", "miembro", "pmo", "admin", "datos"}


def test_rol_desconocido():
    with pytest.raises(ValueError, match="desconocido"):
        cap.obtener("gerente_general")


@pytest.mark.parametrize("clave", sorted(cap.CURRICULAS))
def test_la_curricula_esta_completa(clave):
    c = cap.obtener(clave)
    assert c.rol and c.para_quien and c.promesa
    assert c.modulos, f"{clave} sin módulos"
    assert c.minutos == sum(m.minutos for m in c.modulos)


@pytest.mark.parametrize("clave", sorted(cap.CURRICULAS))
def test_todo_modulo_tiene_guion_practica_y_verificacion(clave):
    """Sin verificación la capacitación no puede fallar, y entonces no mide nada."""
    for m in cap.obtener(clave).modulos:
        assert m.titulo and m.objetivo and m.seccion_app
        assert m.minutos > 0
        assert len(m.guion) >= 2, f"{clave}/{m.clave}: guion demasiado corto"
        assert m.practica, f"{clave}/{m.clave} sin práctica"
        assert m.verificacion, f"{clave}/{m.clave} sin verificación"
        assert all(p.strip().endswith("?") for p in m.verificacion), \
            f"{clave}/{m.clave}: la verificación tiene que ser preguntas"


@pytest.mark.parametrize("clave", sorted(cap.CURRICULAS))
def test_las_claves_de_modulo_no_se_repiten(clave):
    claves = [m.clave for m in cap.obtener(clave).modulos]
    assert len(claves) == len(set(claves))


def test_no_hay_claves_de_modulo_repetidas_entre_roles():
    vistas = {}
    for c in cap.catalogo():
        for m in c.modulos:
            assert m.clave not in vistas or vistas[m.clave] == m, \
                f"{m.clave} definido distinto en dos roles"
            vistas[m.clave] = m


def test_el_sponsor_es_corto_a_proposito():
    """Un sponsor no mira una hora de video; si se le exige, no mira nada."""
    assert cap.obtener("sponsor").minutos <= 20


def test_el_pm_es_la_curricula_mas_completa():
    pm = cap.obtener("pm").minutos
    assert pm > cap.obtener("sponsor").minutos
    assert pm > cap.obtener("miembro").minutos


def test_ninguna_curricula_es_maratonica():
    """Más de dos horas seguidas no lo termina nadie."""
    for c in cap.catalogo():
        assert c.minutos <= 120, f"{c.clave} dura {c.minutos} minutos"


# ------------------------------------------------------------------ rutas

def test_ruta_incluye_los_requisitos_primero():
    ruta = cap.ruta_completa("pmo")
    assert [c.clave for c in ruta] == ["pm", "pmo"]


def test_ruta_de_datos_pasa_por_admin():
    assert [c.clave for c in cap.ruta_completa("datos")] == ["admin", "datos"]


def test_ruta_sin_requisitos_es_solo_ella():
    assert [c.clave for c in cap.ruta_completa("sponsor")] == ["sponsor"]


def test_todos_los_requisitos_apuntan_a_roles_existentes():
    for c in cap.catalogo():
        for r in c.requiere:
            assert r in cap.CURRICULAS, f"{c.clave} requiere {r!r}, que no existe"


def test_no_hay_requisitos_circulares():
    for clave in cap.CURRICULAS:
        ruta = cap.ruta_completa(clave)          # explotaría por recursión si los hubiera
        assert ruta[-1].clave == clave


# --------------------------------------------------------- plan de grabación

def test_el_plan_de_grabacion_no_repite_modulos():
    plan = cap.plan_de_grabacion()
    claves = [m["clave"] for m in plan]
    assert len(claves) == len(set(claves))


def test_el_plan_cubre_todos_los_modulos():
    total = {m.clave for c in cap.catalogo() for m in c.modulos}
    assert {m["clave"] for m in cap.plan_de_grabacion()} == total


def test_el_plan_dice_que_roles_usan_cada_modulo():
    for m in cap.plan_de_grabacion():
        assert m["roles"], f"{m['clave']} no lo usa ningún rol"


def test_grabar_todo_es_una_tarde_no_una_semana():
    """Si grabar todo llevara días, nadie lo graba y volvemos a las sesiones en vivo."""
    assert cap.minutos_totales_a_grabar() <= 300


# ------------------------------------------------------------------ salidas

@pytest.mark.parametrize("clave", sorted(cap.CURRICULAS))
def test_el_guion_imprimible_no_se_rompe(clave):
    txt = cap.guion_de(clave)
    assert txt.startswith("# Capacitación")
    assert "Práctica:" in txt and "Verificación:" in txt
    assert "{" not in txt and "}" not in txt


def test_el_guion_del_pmo_avisa_de_los_requisitos():
    assert "Antes de esto" in cap.guion_de("pmo")


def test_checklist_de_verificacion_acumula_toda_la_ruta():
    solo_pm = cap.checklist_de_verificacion("pm")
    con_pmo = cap.checklist_de_verificacion("pmo")
    assert len(con_pmo) > len(solo_pm)
    assert {f["rol"] for f in con_pmo} == {"Dueño de proyecto / Project Manager",
                                           "PMO / Responsable de metodología"}


def test_las_preguntas_del_admin_cubren_lo_riesgoso():
    """Respaldo y solo-lectura del ERP son las dos que no pueden faltar."""
    preguntas = " ".join(f["pregunta"].lower()
                         for f in cap.checklist_de_verificacion("admin"))
    assert "respald" in preguntas
    assert "modificar" in preguntas or "solo lectura" in preguntas


def test_la_capacitacion_de_conectores_advierte_del_sondeo():
    guion = cap.guion_de("admin").lower()
    assert "sondeo" in guion or "sondear" in guion
    assert "solo lectura" in guion
