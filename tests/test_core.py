import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from mvpm import (
    catalog,
    demo_data,
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
