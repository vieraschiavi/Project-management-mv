"""Salud de proyecto en 6 dimensiones (alcance, cronograma, presupuesto, riesgo,
dependencias, equipo) — motor de reglas determinístico, sin dependencia de IA.
Cada dimensión devuelve un score 0-100; el índice de salud es el promedio.
"""

from datetime import datetime

import pandas as pd

from . import demo_data

DIMENSIONS = ["alcance", "cronograma", "presupuesto", "riesgo", "dependencias", "equipo"]

_TODAY = datetime(2026, 7, 12)


def _schedule_score(proj_tasks: pd.DataFrame) -> float:
    if proj_tasks.empty:
        return 100.0
    due = pd.to_datetime(proj_tasks["vencimiento"])
    overdue = ((due < _TODAY) & (proj_tasks["estado"] != "done")).sum()
    return max(0.0, 100.0 - (overdue / len(proj_tasks)) * 140)


def _budget_score(row: pd.Series) -> float:
    pct = row["ejecutado"] / row["presupuesto"] if row["presupuesto"] else 0
    if pct <= 1.0:
        return 100.0 - max(0, pct - 0.85) * 200
    return max(0.0, 100.0 - (pct - 1.0) * 250)


def _risk_score(proj_tasks: pd.DataFrame) -> float:
    if proj_tasks.empty:
        return 100.0
    blocked = (proj_tasks["estado"] == "blocked").sum()
    return max(0.0, 100.0 - (blocked / len(proj_tasks)) * 260)


def _dependency_score(proj_tasks: pd.DataFrame, all_task_ids: set) -> float:
    deps = proj_tasks["depende_de"].dropna()
    if deps.empty:
        return 100.0
    orphan = sum(1 for d in deps if d not in all_task_ids)
    return max(0.0, 100.0 - (orphan / len(deps)) * 100)


def _scope_score(proj_tasks: pd.DataFrame) -> float:
    if proj_tasks.empty:
        return 100.0
    orphan_owner = proj_tasks["responsable"].isna().sum()
    return max(0.0, 100.0 - (orphan_owner / len(proj_tasks)) * 130)


def _team_score(project_owner: str | None, team_df: pd.DataFrame) -> float:
    if project_owner is None:
        return 55.0
    row = team_df[team_df["nombre"] == project_owner]
    if row.empty:
        return 80.0
    r = row.iloc[0]
    overload = max(0.0, (r["carga_actual_hs"] - r["capacidad_semanal_hs"]) / r["capacidad_semanal_hs"])
    return max(0.0, 100.0 - overload * 180)


def project_health(
    projects: pd.DataFrame | None = None,
    tasks: pd.DataFrame | None = None,
    team: pd.DataFrame | None = None,
) -> pd.DataFrame:
    proj_df = projects if projects is not None else demo_data.projects()
    task_df = tasks if tasks is not None else demo_data.tasks()
    team_df = team if team is not None else demo_data.team()
    all_task_ids = set(task_df["tarea_id"])

    rows = []
    for _, p in proj_df.iterrows():
        pt = task_df[task_df["proyecto_id"] == p["proyecto_id"]]
        scores = {
            "alcance": _scope_score(pt),
            "cronograma": _schedule_score(pt),
            "presupuesto": _budget_score(p),
            "riesgo": _risk_score(pt),
            "dependencias": _dependency_score(pt, all_task_ids),
            "equipo": _team_score(p["dueno"], team_df),
        }
        indice = round(sum(scores.values()) / len(scores), 1)
        estado = "riesgo" if indice < 55 else ("observacion" if indice < 75 else "saludable")
        rows.append({"proyecto_id": p["proyecto_id"], "nombre": p["nombre"], "indice": indice,
                      "estado": estado, **{f"dim_{k}": round(v, 1) for k, v in scores.items()}})
    return pd.DataFrame(rows)


def overall_index(projects=None, tasks=None, team=None) -> float:
    df = project_health(projects, tasks, team)
    return round(float(df["indice"].mean()), 1) if not df.empty else 0.0


def matriz_por_dimension(projects=None, tasks=None, team=None) -> pd.DataFrame:
    df = project_health(projects, tasks, team)
    cols = [f"dim_{d}" for d in DIMENSIONS]
    return df[["proyecto_id", "nombre"] + cols]
