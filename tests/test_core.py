import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import pytest

from mvpm import (
    advisor,
    case_study,
    catalog,
    demo_data,
    demo_pharma,
    demo_real,
    dependencies as dep_mod,
    exporters,
    glossary,
    health,
    help_center,
    i18n,
    licensing,
    pmbok,
    policies,
    prioritizer,
    reports,
    reviews,
    tutorial,
)
from mvpm import copilot as copilot_mod


# ---- i18n ----

def test_i18n_parity_all_languages():
    for key in i18n.all_keys():
        for lang in ("es", "en", "pt"):
            assert i18n.t(key, lang).strip() != ""


def test_i18n_fallback_to_spanish():
    assert i18n.t("app_title", "fr") == i18n.t("app_title", "es")


# ---- demo data ----

def test_demo_data_deterministic():
    assert demo_data.projects().equals(demo_data.projects())
    assert demo_data.tasks().equals(demo_data.tasks())


def test_demo_data_has_injected_defects():
    proj = demo_data.projects()
    tasks = demo_data.tasks()
    assert proj["dueno"].isna().sum() > 0
    assert tasks["responsable"].isna().sum() > 0
    assert (tasks["depende_de"] == "T-9999").sum() >= 1


# ---- catalog ----

def test_catalog_kpis_consistent():
    proj = demo_data.projects()
    k = catalog.kpis(proj)
    assert k["proyectos_activos"] == len(proj)
    assert k["ejecutado_total"] >= 0


def test_catalog_kpis_presupuesto_cero_no_muestra_nan():
    """Un proyecto recién creado con el formulario por defecto (presupuesto
    0, ejecutado 0) no debe mostrar 'nan%' en el KPI — es el primer proyecto
    real de cualquier cuenta nueva."""
    proj = demo_data.projects().head(1).copy()
    proj["presupuesto"] = 0
    proj["ejecutado"] = 0
    k = catalog.kpis(proj)
    assert k["ejecucion_pct_promedio"] == 0.0
    assert not pd.isna(k["ejecucion_pct_promedio"])

    cat = catalog.catalog(proj)
    assert pd.isna(cat.iloc[0]["ejecucion_pct"])  # el valor por fila sigue siendo indefinido...
    assert not cat.iloc[0]["sobre_presupuesto"]    # ...pero no se marca como sobre presupuesto

    # presupuesto 0 con gasto real sí debe marcarse sobre presupuesto,
    # y seguir sin romper el promedio (antes daba inf%, no nan%, pero
    # tampoco es un porcentaje real)
    proj2 = proj.copy()
    proj2["ejecutado"] = 500
    k2 = catalog.kpis(proj2)
    assert not pd.isna(k2["ejecucion_pct_promedio"])
    assert catalog.catalog(proj2).iloc[0]["sobre_presupuesto"]


def test_catalog_kpis_no_rompe_con_portafolio_vacio():
    """Primera pantalla real de cualquier cuenta nueva: cero proyectos
    todavía. Regresión: mean() sobre una Serie vacía devuelve un float
    Python plano sin .round(), no un escalar numpy — kpis() encadenaba
    .round(1) directo sobre ese mean() y reventaba con AttributeError."""
    vacio = demo_data.projects().iloc[0:0]
    k = catalog.kpis(vacio)
    assert k == {
        "proyectos_activos": 0, "presupuesto_total": 0.0, "ejecutado_total": 0.0,
        "ejecucion_pct_promedio": 0.0, "sin_dueno": 0, "sobre_presupuesto": 0,
    }


# ---- health ----

def test_health_scores_bounded():
    h = health.project_health()
    assert not h.empty
    for col in [c for c in h.columns if c.startswith("dim_")]:
        assert h[col].between(0, 100).all()
    assert h["indice"].between(0, 100).all()
    assert set(h["estado"].unique()) <= {"saludable", "observacion", "riesgo"}


def test_health_overall_index_is_mean():
    h = health.project_health()
    assert health.overall_index() == pytest.approx(round(h["indice"].mean(), 1))


# ---- dependencies ----

def test_orphan_dependency_detected():
    orphans = dep_mod.orphan_dependencies()
    assert len(orphans) >= 1
    assert "T-9999" in orphans["depende_de"].values


def test_impacto_no_infinite_loop():
    tasks = demo_data.tasks()
    tid = tasks["tarea_id"].iloc[0]
    result = dep_mod.impacto_si_se_atrasa(tid, tasks)
    assert isinstance(result, list)


# ---- prioritizer ----

def test_backlog_sorted_descending():
    backlog = prioritizer.prioritized_backlog()
    values = backlog["valor_esperado"].tolist()
    assert values == sorted(values, reverse=True)


def test_backlog_excludes_done_tasks():
    backlog = prioritizer.prioritized_backlog()
    assert "done" not in backlog["estado"].unique()


def test_backlog_vacio_no_rompe_con_cero_tareas_pendientes():
    """Un proyecto recién creado en el dashboard real no tiene tareas todavía
    — el backlog debe devolver un DataFrame vacío con las columnas
    esperadas, no reventar (regresión: pending.apply()[0] con 0 filas)."""
    proj = demo_data.projects().head(1)
    tasks_vacias = demo_data.tasks().iloc[0:0]
    backlog = prioritizer.prioritized_backlog(proj, tasks_vacias)
    assert backlog.empty
    for col in ("valor_esperado", "tareas_impactadas", "dias_restantes"):
        assert col in backlog.columns


# ---- policies ----

def test_policies_have_valid_states():
    pol = policies.evaluate()
    assert set(pol["estado"].unique()) <= {"cumple", "incumple"}
    assert len(pol) == 6


# ---- glossary ----

def test_glossary_not_empty():
    g = glossary.glossary()
    assert len(g) > 0
    assert g["definicion_es"].str.len().gt(0).all()


# ---- reviews (honestidad de reseñas) ----

def test_reviews_start_empty_and_marked_beta(tmp_path, monkeypatch):
    monkeypatch.setattr(reviews, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(reviews, "_STORE_FILE", tmp_path / "resenas.json")
    s = reviews.summary()
    assert s["total"] == 0
    assert s["es_beta_sin_resenas"] is True
    assert s["promedio"] is None


def test_reviews_unverified_not_shown_by_default(tmp_path, monkeypatch):
    monkeypatch.setattr(reviews, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(reviews, "_STORE_FILE", tmp_path / "resenas.json")
    reviews.add_review("Ana", "Acme", "PM", 5, "Excelente", verificado=False)
    assert reviews.list_reviews(only_verified=True) == []
    assert len(reviews.list_reviews(only_verified=False)) == 1


def test_reviews_rejects_invalid_rating(tmp_path, monkeypatch):
    monkeypatch.setattr(reviews, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(reviews, "_STORE_FILE", tmp_path / "resenas.json")
    with pytest.raises(ValueError):
        reviews.add_review("Ana", "Acme", "PM", 7, "Excelente")


# ---- copilot ----

def test_copilot_answers_without_ai_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = copilot_mod.answer("¿Qué está bloqueando los proyectos?")
    assert result["ai_enriched"] is False
    assert isinstance(result["answer"], str) and result["answer"]


# ---- licensing (plan de créditos de IA) ----

def test_issue_and_verify_license_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(licensing, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(licensing, "_SECRET_FILE", tmp_path / "secret.txt")
    token = licensing.issue_license("professional", "cliente@empresa.com", payment_id="PAY-123")
    payload = licensing.verify_license(token)
    assert payload["plan"] == "professional"
    assert payload["email"] == "cliente@empresa.com"
    assert payload["payment_id"] == "PAY-123"


def test_verify_license_rejects_tampered_token(tmp_path, monkeypatch):
    monkeypatch.setattr(licensing, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(licensing, "_SECRET_FILE", tmp_path / "secret.txt")
    token = licensing.issue_license("professional", "cliente@empresa.com")
    prefix, payload_b64, sig = token.split(".")
    tampered = f"{prefix}.{payload_b64}X.{sig}"
    assert licensing.verify_license(tampered) is None


def test_verify_license_rejects_unknown_plan():
    with pytest.raises(ValueError):
        licensing.issue_license("plan_inexistente", "cliente@empresa.com")


def test_demo_quota_enforced(tmp_path, monkeypatch):
    monkeypatch.setattr(licensing, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(licensing, "_SECRET_FILE", tmp_path / "secret.txt")
    monkeypatch.setattr(licensing, "_USAGE_FILE", tmp_path / "uso.json")
    cupo = licensing.PLANES["demo"]["cupo_mensual_ia"]
    for _ in range(cupo):
        licensing.registrar_uso_ia("demo@local")
    puede, _ = licensing.puede_usar_ia(None)
    assert puede is False


def test_enterprise_quota_unlimited(tmp_path, monkeypatch):
    monkeypatch.setattr(licensing, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(licensing, "_SECRET_FILE", tmp_path / "secret.txt")
    monkeypatch.setattr(licensing, "_USAGE_FILE", tmp_path / "uso.json")
    token = licensing.issue_license("enterprise", "grande@empresa.com")
    for _ in range(500):
        licensing.registrar_uso_ia("grande@empresa.com")
    puede, detalle = licensing.puede_usar_ia(token)
    assert puede is True
    assert detalle == "ilimitado"


def test_rules_engine_never_blocked_by_quota(tmp_path, monkeypatch):
    """El motor de reglas responde siempre, tenga o no cupo de IA."""
    monkeypatch.setattr(licensing, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(licensing, "_SECRET_FILE", tmp_path / "secret.txt")
    monkeypatch.setattr(licensing, "_USAGE_FILE", tmp_path / "uso.json")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    for _ in range(licensing.PLANES["demo"]["cupo_mensual_ia"] + 5):
        licensing.registrar_uso_ia("demo@local")
    result = copilot_mod.answer("¿Qué está bloqueando los proyectos?", use_ai=False)
    assert isinstance(result["answer"], str) and result["answer"]


# ---- reports ----

def test_executive_summary_has_expected_keys():
    s = reports.executive_summary()
    assert {"indice_portafolio", "kpis", "proyectos_en_riesgo", "top_hallazgo"} <= s.keys()


# ---- help center ----

def test_automation_matrix_links_to_existing_speeches():
    speeches = help_center.speeches()
    for row in help_center.automation_rows():
        if "speech_id" in row:
            assert row["speech_id"] in speeches


# ---- pmbok ----

_PMBOK_AREAS_ESTANDAR = 10  # las 10 áreas de conocimiento de la guía PMBOK del PMI


def test_pmbok_cubre_las_diez_areas_de_conocimiento():
    assert len(pmbok.areas()) == _PMBOK_AREAS_ESTANDAR


def test_pmbok_cobertura_es_honesta_no_todo_completo():
    """Si todas las áreas dijeran 'completa' sería marketing, no una referencia
    honesta — el producto tiene huecos reales (adquisiciones, comunicaciones)
    y este test los obliga a seguir declarados."""
    coberturas = {a["cobertura"] for a in pmbok.areas()}
    assert coberturas == {"completa", "parcial", "no_cubierta"}


def test_pmbok_areas_sin_cobertura_completa_explican_que_falta():
    for a in pmbok.areas():
        if a["cobertura"] != "completa":
            assert a["lo_que_falta"], f"'{a['area']}' no explica qué falta"


def test_pmbok_resumen_suma_el_total():
    r = pmbok.resumen()
    assert r["completa"] + r["parcial"] + r["no_cubierta"] == r["total_areas"] == _PMBOK_AREAS_ESTANDAR


# ---- tutorial ----

def test_tutorial_cubre_todas_las_secciones_del_nav():
    """Si se agrega una sección nueva al dashboard (una nav_* en i18n) y nadie
    le suma su entrada acá, el tutorial queda incompleto sin que ningún test
    lo note — este chequeo lo detecta."""
    ids_tutorial = {s["id"] for s in tutorial.sections()}
    nav_keys = [k for k in i18n.all_keys() if k.startswith("nav_") and k != "nav_tutorial"]
    faltantes = [k for k in nav_keys if k not in ids_tutorial]
    assert not faltantes, f"Faltan en el tutorial: {faltantes}"


def test_tutorial_secciones_tienen_contenido_real():
    for s in tutorial.sections():
        assert s["titulo"].strip()
        assert s["resumen"].strip()
        assert len(s["pasos"]) >= 1
        assert all(p.strip() for p in s["pasos"])


# ---- case_study ----

def test_narrar_caso_elige_el_proyecto_de_peor_salud():
    caso = case_study.narrar_caso()
    peor = health.project_health().sort_values("indice").iloc[0]
    assert caso["proyecto_id"] == peor["proyecto_id"]
    assert caso["indice"] == peor["indice"]


def test_narrar_caso_tiene_los_seis_pasos_con_contenido_real():
    caso = case_study.narrar_caso()
    secciones = [p["seccion"] for p in caso["pasos"]]
    assert secciones == ["Portafolio", "Salud de proyecto", "Dependencias",
                          "Backlog priorizado", "Copiloto", "Reportes"]
    for p in caso["pasos"]:
        assert p["texto"].strip()
        assert caso["proyecto_id"] not in p["texto"]  # el texto narra con el nombre, no el código


def test_narrar_caso_admite_elegir_proyecto_explicito():
    proj = demo_data.projects()
    otro_id = proj.iloc[5]["proyecto_id"]
    caso = case_study.narrar_caso(proyecto_id=otro_id)
    assert caso["proyecto_id"] == otro_id


def test_narrar_caso_funciona_con_portafolio_de_un_solo_proyecto_sin_tareas():
    proj = demo_data.projects().head(1).copy()
    tasks_vacias = demo_data.tasks().iloc[0:0]
    team = demo_data.team()
    caso = case_study.narrar_caso(proj, tasks_vacias, team)
    assert caso["proyecto_id"] == proj.iloc[0]["proyecto_id"]
    assert len(caso["pasos"]) == 6


# ---- advisor ----

def test_detectar_problemas_encuentra_los_del_dato_demo():
    proj, tasks, team = demo_data.projects(), demo_data.tasks(), demo_data.team()
    problemas = advisor.detectar_problemas(proj, tasks, team)
    assert len(problemas) > 0
    tipos = {p["tipo"] for p in problemas}
    assert tipos <= set(advisor._SUGERENCIAS.keys())
    ids = [p["id"] for p in problemas]
    assert len(ids) == len(set(ids))  # sin duplicados


def test_detectar_problemas_vacio_sin_datos_no_rompe():
    vacio = demo_data.projects().iloc[0:0]
    problemas = advisor.detectar_problemas(vacio, demo_data.tasks().iloc[0:0], demo_data.team().iloc[0:0])
    # sin proyectos no hay bloqueos, sobrepresupuesto, riesgo ni sobrecarga que detectar
    tipos = {p["tipo"] for p in problemas}
    assert tipos <= {"politica_incumplida"}


def test_sugerir_sin_proveedor_usa_motor_de_reglas():
    proj, tasks, team = demo_data.projects(), demo_data.tasks(), demo_data.team()
    problema = advisor.detectar_problemas(proj, tasks, team)[0]
    resultado = advisor.sugerir(problema)
    assert resultado["ai_enriched"] is False
    assert resultado["proveedor"] is None
    assert resultado["sugerencia"].strip()


def test_sugerir_con_proveedor_sin_clave_configurada_no_falla(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    proj, tasks, team = demo_data.projects(), demo_data.tasks(), demo_data.team()
    problema = advisor.detectar_problemas(proj, tasks, team)[0]
    resultado = advisor.sugerir(problema, proveedor="claude")
    assert resultado["ai_enriched"] is False  # se degrada al motor de reglas, no rompe


def test_proveedores_disponibles_solo_lista_los_configurados(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert advisor.proveedores_disponibles() == []
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert advisor.proveedores_disponibles() == ["chatgpt"]


# ---- demo_pharma ----

def test_pharma_tiene_el_esquema_de_demo_data():
    proj = demo_pharma.cargar_portafolio_pharma()
    assert list(proj.columns) == list(demo_data.projects().columns)
    assert len(proj) > 0
    assert proj["criticidad"].isin(["Alta", "Media", "Baja"]).all()


def test_pharma_criticidad_deriva_del_estado_real():
    r = demo_pharma.resumen_portafolio()
    assert r["total_ensayos"] > 0
    # terminados/suspendidos existen y se marcan en riesgo (dato real, no inventado)
    assert r["en_riesgo"] > 0
    assert len(r["por_sponsor"]) == 3  # AstraZeneca, Pfizer, Novartis


def test_pharma_no_inventa_presupuesto():
    proj = demo_pharma.cargar_portafolio_pharma()
    # la fuente no publica presupuesto — se deja en 0, no se fabrica
    assert (proj["presupuesto"] == 0).all()
    assert (proj["ejecutado"] == 0).all()


def test_pharma_tabla_bi_lista_para_powerbi():
    bi = demo_pharma.tabla_para_bi()
    for col in ("nct", "titulo", "laboratorio", "estado", "criticidad", "fase"):
        assert col in bi.columns
    assert not bi.empty
    assert catalog.kpis(demo_pharma.cargar_portafolio_pharma())["proyectos_activos"] == len(bi)


# ---- pmbok grupos de procesos ----

def test_pmbok_tiene_cinco_grupos_de_procesos_tecnico_y_criollo():
    grupos = pmbok.grupos_proceso()
    assert len(grupos) == 5
    for g in grupos:
        assert g["definicion_tecnica"].strip() and g["criollo"].strip()
    assert pmbok.resumen()["grupos_proceso"] == 5


def test_pmbok_cada_area_tiene_tecnico_y_criollo():
    for a in pmbok.areas():
        assert a["definicion_tecnica"].strip()
        assert a["criollo"].strip()
        assert a["clave"]


# ---- demo_real ----

def test_cargar_portafolio_real_tiene_el_esquema_de_demo_data():
    proj = demo_real.cargar_portafolio_real()
    assert list(proj.columns) == list(demo_data.projects().columns)
    assert len(proj) > 0
    assert proj["nombre"].notna().all()
    assert proj["presupuesto"].notna().all()
    assert proj["ejecutado"].notna().all()


def test_resumen_portafolio_real_es_consistente():
    r = demo_real.resumen_portafolio()
    assert r["total_proyectos"] > 0
    assert 0 <= r["sobre_presupuesto"] <= r["total_proyectos"]
    assert r["horas_ahorradas_estimadas"] > 0
    assert not r["proyectos_sobre_presupuesto_detalle"].empty


def test_caso_real_trae_los_dos_casos_narrados():
    for nombre in ["Social Housing Decarbonisation Fund", "Borders & Trade Programme"]:
        c = demo_real.caso(nombre)
        assert c["nombre"] == nombre
        assert c["narrativa_real"].strip()
        assert c["revision_real"].strip()
        assert c["rag"] in {"Red", "Amber", "Green"}


def test_caso_real_sobre_presupuesto_coincide_con_los_numeros_reales():
    c = demo_real.caso("Social Housing Decarbonisation Fund")
    assert c["sobre_presupuesto"] is True  # £65.33M base vs £184.77M ejecutado, dato real
    c2 = demo_real.caso("Borders & Trade Programme")
    assert c2["sobre_presupuesto"] is False  # £410.2M base vs £379.12M ejecutado, dato real


# ---- exporters ----

def test_exporters_produce_valid_json_bundle():
    import json
    bundle = json.loads(exporters.to_json_bundle())
    assert "proyectos" in bundle
    assert "resenas" in bundle


# ---- empaquetado portable ----

def test_build_release_portable_zip(monkeypatch):
    import zipfile
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent / "packaging"))
    import build_release

    zip_path = build_release.build_portable_zip(version="test")
    try:
        assert zip_path.exists()
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            assert any(n.endswith("MV_ProjectManagement.bat") for n in names)
            assert any(n.startswith("mvpm/") for n in names)
            assert any(n.startswith("app/") for n in names)
            assert not any(".venv" in n or "__pycache__" in n for n in names)
    finally:
        zip_path.unlink(missing_ok=True)
