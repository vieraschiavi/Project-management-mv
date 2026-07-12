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
    policies,
    prioritizer,
    reports,
    reviews,
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


# ---- exporters ----

def test_exporters_produce_valid_json_bundle():
    import json
    bundle = json.loads(exporters.to_json_bundle())
    assert "proyectos" in bundle
    assert "resenas" in bundle
