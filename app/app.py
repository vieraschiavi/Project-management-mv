"""MV Project Management — dashboard operativo (Streamlit).

Un único motor (mvpm/) alimenta este dashboard, la API REST (api/main.py) y
los exportadores — sin lógica de negocio duplicada entre capas.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from mvpm import (
    BRAND,
    catalog,
    demo_data,
    dependencies as dep_mod,
    exporters,
    glossary,
    health,
    help_center,
    i18n,
    licensing,
    policies,
    prioritizer,
    reports,
    reviews,
)
from mvpm import copilot as copilot_mod

st.set_page_config(page_title="MV Project Management", page_icon="📋", layout="wide")

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {BRAND['navy']}; }}
    [data-testid="stMetricValue"] {{ color: {BRAND['amber']}; }}
    h1, h2, h3 {{ color: {BRAND['ink']}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

LANG = st.sidebar.selectbox("Idioma / Language / Idioma", ["es", "en", "pt"], index=0)
LICENSE_TOKEN = st.sidebar.text_input(
    "Token de licencia (opcional)", type="password",
    help="Se emite automáticamente al pagar el plan Professional. Sin token, corrés en plan demo.",
) or None


def T(key: str) -> str:
    return i18n.t(key, LANG)


@st.cache_data
def load_data():
    proj = demo_data.projects()
    tasks = demo_data.tasks()
    team = demo_data.team()
    return proj, tasks, team


proj_df, task_df, team_df = load_data()

st.sidebar.title(T("app_title"))
section = st.sidebar.radio(
    "Sección",
    [
        T("nav_portfolio"), T("nav_health"), T("nav_dependencies"),
        T("nav_backlog"), T("nav_copilot"), T("nav_reports"),
        T("nav_reviews"), T("nav_glossary"), T("nav_policies"), T("nav_import"),
    ],
)

st.title(T("app_title"))

if section == T("nav_portfolio"):
    kpis = catalog.kpis(proj_df)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric(T("kpi_projects"), kpis["proyectos_activos"])
    c2.metric(T("kpi_health"), f"{health.overall_index(proj_df, task_df, team_df)}/100")
    riesgo = int((health.project_health(proj_df, task_df, team_df)["estado"] == "riesgo").sum())
    c3.metric(T("kpi_at_risk"), riesgo)
    c4.metric(T("kpi_budget"), f"{kpis['ejecucion_pct_promedio']}%")
    bloqueadas = int((task_df["estado"] == "blocked").sum())
    c5.metric(T("kpi_blocked"), bloqueadas)
    a_tiempo = int((health.project_health(proj_df, task_df, team_df)["dim_cronograma"] >= 70).sum())
    c6.metric(T("kpi_on_time"), a_tiempo)

    st.subheader(T("nav_portfolio"))
    st.dataframe(catalog.catalog(proj_df), use_container_width=True)

    st.subheader("Por portafolio")
    st.bar_chart(catalog.por_portafolio(proj_df).set_index("portafolio")[["presupuesto", "ejecutado"]])

elif section == T("nav_health"):
    h = health.project_health(proj_df, task_df, team_df)
    st.subheader(f"{T('nav_health')} — índice global: {health.overall_index(proj_df, task_df, team_df)}/100")
    estado_color = {"saludable": "🟢", "observacion": "🟡", "riesgo": "🔴"}
    h_display = h.copy()
    h_display["estado"] = h_display["estado"].map(lambda e: f"{estado_color.get(e,'')} {e}")
    st.dataframe(h_display, use_container_width=True)
    st.subheader("Matriz por dimensión")
    matriz = health.matriz_por_dimension(proj_df, task_df, team_df).set_index("nombre")
    st.dataframe(matriz.style.background_gradient(cmap="RdYlGn", vmin=0, vmax=100), use_container_width=True)

elif section == T("nav_dependencies"):
    st.subheader(T("nav_dependencies"))
    bloqueos = dep_mod.bloqueos_activos(task_df)
    if bloqueos.empty:
        st.success("No hay tareas bloqueadas activas.")
    else:
        st.dataframe(bloqueos[["tarea_id", "titulo", "proyecto_id", "tareas_impactadas"]], use_container_width=True)
    st.subheader("Dependencias inconsistentes")
    orphans = dep_mod.orphan_dependencies(task_df)
    if orphans.empty:
        st.success("Sin dependencias huérfanas.")
    else:
        st.warning(f"{len(orphans)} dependencia(s) apuntan a una tarea inexistente.")
        st.dataframe(orphans, use_container_width=True)

elif section == T("nav_backlog"):
    st.subheader(T("nav_backlog"))
    st.caption("Ordenado por valor esperado = criticidad × prioridad × urgencia × impacto en dependencias.")
    st.dataframe(
        prioritizer.prioritized_backlog(proj_df, task_df)[
            ["tarea_id", "titulo", "proyecto_id", "estado", "valor_esperado", "tareas_impactadas", "dias_restantes"]
        ],
        use_container_width=True,
    )

elif section == T("nav_copilot"):
    st.subheader(T("nav_copilot"))
    st.caption("El motor de reglas responde siempre. Si hay ANTHROPIC_API_KEY configurada y todavía hay cupo de IA en tu plan, Claude pule el lenguaje sin inventar cifras nuevas.")
    puede_ia, detalle_cupo = licensing.puede_usar_ia(LICENSE_TOKEN)
    st.caption(f"Cupo de IA: {detalle_cupo}")
    q = st.text_input("Preguntá sobre el portafolio", "¿Qué está bloqueando los proyectos?")
    if st.button("Preguntar"):
        result = copilot_mod.answer(q, proj_df, task_df, team_df, license_token=LICENSE_TOKEN)
        st.info(result["answer"])
        st.caption("Respuesta enriquecida con IA" if result["ai_enriched"] else "Respuesta del motor de reglas (sin IA)")

elif section == T("nav_reports"):
    st.subheader(T("nav_reports"))
    st.code(reports.as_text(proj_df, task_df, team_df), language=None)
    st.download_button("Descargar JSON del portafolio", exporters.to_json_bundle(), file_name="portafolio_mvpm.json")
    st.download_button("Descargar Excel del portafolio", exporters.to_excel_bytes(), file_name="portafolio_mvpm.xlsx")

elif section == T("nav_reviews"):
    st.subheader(T("nav_reviews"))
    s = reviews.summary()
    if s["es_beta_sin_resenas"]:
        st.info(f"⭐ {T('reviews_empty_title')} — {T('reviews_empty_body')}")
    else:
        st.metric("Calificación promedio", f"{s['promedio']} / 5 ({s['total']} reseñas)")
        for r in reviews.list_reviews():
            st.markdown(f"**{'⭐' * r['calificacion']}** — *{r['autor']}, {r['rol']} en {r['empresa']}*")
            st.write(r["comentario"])
            st.divider()
    with st.expander("Dejar una reseña"):
        with st.form("nueva_resena"):
            autor = st.text_input("Tu nombre")
            empresa = st.text_input("Empresa")
            rol = st.text_input("Rol")
            calificacion = st.slider("Calificación", 1, 5, 5)
            comentario = st.text_area("Comentario")
            enviado = st.form_submit_button("Enviar reseña")
            if enviado and autor and comentario:
                reviews.add_review(autor, empresa, rol, calificacion, comentario, verificado=False)
                st.success("¡Gracias! Tu reseña queda pendiente de verificación antes de publicarse.")

elif section == T("nav_glossary"):
    st.subheader(T("nav_glossary"))
    st.dataframe(glossary.glossary(), use_container_width=True)

elif section == T("nav_policies"):
    st.subheader(T("nav_policies"))
    pol = policies.evaluate(proj_df, task_df, team_df)
    for _, row in pol.iterrows():
        icon = "✅" if row["estado"] == "cumple" else "⚠️"
        st.markdown(f"{icon} **{row['politica']}** — {row['evidencia']}")
    st.divider()
    st.subheader("Matriz de automatización y adopción")
    for row in help_center.automation_rows():
        nivel_icon = {"auto": "🟢 automático", "parcial": "🟡 parcial", "humano": "🔴 humano"}[row["nivel"]]
        st.markdown(f"**{row['area']}** — {nivel_icon}")
        st.caption(row["detalle"])

elif section == T("nav_import"):
    st.subheader(T("nav_import"))
    uploaded = st.file_uploader("Subí un CSV/Excel de tareas existente", type=["csv", "xlsx"])
    if uploaded is not None:
        df = pd.read_csv(uploaded) if uploaded.name.endswith("csv") else pd.read_excel(uploaded)
        st.write(f"{len(df)} filas, {len(df.columns)} columnas detectadas.")
        st.dataframe(df.head(20), use_container_width=True)
        nulos = df.isna().sum()
        st.write("Columnas con datos faltantes:")
        st.dataframe(nulos[nulos > 0].rename("valores_nulos"))
