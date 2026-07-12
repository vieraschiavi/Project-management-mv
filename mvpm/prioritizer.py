"""Priorización de backlog por valor esperado (impacto × urgencia × riesgo),
no por orden de llegada ni por quién insiste más. Motor de reglas, sin IA.
"""

from datetime import datetime

import pandas as pd

from . import demo_data, dependencies as dep_mod

_TODAY = datetime(2026, 7, 12)

_CRITICALITY_WEIGHT = {"Alta": 1.4, "Media": 1.0, "Baja": 0.6}
_PRIORITY_WEIGHT = {"Alta": 1.3, "Media": 1.0, "Baja": 0.7}


def prioritized_backlog(
    projects: pd.DataFrame | None = None,
    tasks: pd.DataFrame | None = None,
) -> pd.DataFrame:
    proj_df = projects if projects is not None else demo_data.projects()
    task_df = tasks if tasks is not None else demo_data.tasks()

    pending = task_df[task_df["estado"].isin(["todo", "in_progress", "blocked"])].copy()
    proj_map = proj_df.set_index("proyecto_id")

    def score_row(row):
        due = pd.to_datetime(row["vencimiento"])
        dias_restantes = (due - _TODAY).days
        urgencia = 1.0 if dias_restantes < 0 else max(0.3, 1.0 - dias_restantes / 90)
        if dias_restantes < 0:
            urgencia = 1.6  # vencida: máxima urgencia
        criticidad = proj_map.loc[row["proyecto_id"], "criticidad"] if row["proyecto_id"] in proj_map.index else "Media"
        impacto_dependencias = len(dep_mod.impacto_si_se_atrasa(row["tarea_id"], task_df))
        bloqueo_bonus = 1.25 if row["estado"] == "blocked" else 1.0
        valor = (
            _CRITICALITY_WEIGHT.get(criticidad, 1.0)
            * _PRIORITY_WEIGHT.get(row["prioridad"], 1.0)
            * urgencia
            * bloqueo_bonus
            * (1 + impacto_dependencias * 0.15)
        )
        return round(valor, 2), impacto_dependencias, dias_restantes

    scored = pending.apply(score_row, axis=1, result_type="expand")
    pending["valor_esperado"] = scored[0]
    pending["tareas_impactadas"] = scored[1]
    pending["dias_restantes"] = scored[2]
    return pending.sort_values("valor_esperado", ascending=False).reset_index(drop=True)


def top(n: int = 10, projects=None, tasks=None) -> pd.DataFrame:
    return prioritized_backlog(projects, tasks).head(n)
