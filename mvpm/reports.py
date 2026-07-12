"""Reporte ejecutivo del portafolio — texto plano estructurado, listo para
convertir a PDF o pegar en un email gerencial. Generado del dato real, no
armado a mano."""

from datetime import datetime

from . import catalog, demo_data, health, policies

_TODAY = datetime(2026, 7, 12)


def executive_summary(projects=None, tasks=None, team=None) -> dict:
    proj_df = projects if projects is not None else demo_data.projects()
    task_df = tasks if tasks is not None else demo_data.tasks()
    team_df = team if team is not None else demo_data.team()

    kpis = catalog.kpis(proj_df)
    h = health.project_health(proj_df, task_df, team_df)
    pol = policies.evaluate(proj_df, task_df, team_df)

    riesgo = h[h["estado"] == "riesgo"].sort_values("indice")
    incumplidas = pol[pol["estado"] == "incumple"]

    return {
        "generado_en": _TODAY.date().isoformat(),
        "indice_portafolio": health.overall_index(proj_df, task_df, team_df),
        "kpis": kpis,
        "proyectos_en_riesgo": riesgo[["proyecto_id", "nombre", "indice"]].to_dict("records"),
        "politicas_incumplidas": incumplidas[["politica", "evidencia"]].to_dict("records"),
        "top_hallazgo": (
            f"{len(riesgo)} proyecto(s) en riesgo de un total de {kpis['proyectos_activos']}"
            if len(riesgo) else "Ningún proyecto en riesgo esta semana."
        ),
    }


def as_text(projects=None, tasks=None, team=None) -> str:
    s = executive_summary(projects, tasks, team)
    lines = [
        f"Reporte ejecutivo — {s['generado_en']}",
        f"Índice de salud del portafolio: {s['indice_portafolio']}/100",
        f"Proyectos activos: {s['kpis']['proyectos_activos']} · "
        f"Presupuesto ejecutado: {s['kpis']['ejecucion_pct_promedio']}% promedio",
        s["top_hallazgo"],
    ]
    if s["proyectos_en_riesgo"]:
        lines.append("Proyectos en riesgo:")
        lines += [f"  - {p['nombre']} ({p['indice']}/100)" for p in s["proyectos_en_riesgo"]]
    if s["politicas_incumplidas"]:
        lines.append("Políticas incumplidas:")
        lines += [f"  - {p['politica']}: {p['evidencia']}" for p in s["politicas_incumplidas"]]
    return "\n".join(lines)
