"""Políticas de gestión verificadas contra evidencia real (no checkboxes manuales)."""

from dataclasses import dataclass

import pandas as pd

from . import demo_data, health


@dataclass
class Policy:
    nombre: str
    descripcion: str


_POLICIES = [
    Policy("Todo proyecto tiene dueño", "Ningún proyecto activo debe estar sin responsable asignado."),
    Policy("Todo proyecto tiene fecha de fin", "Todo proyecto activo debe tener una fecha de cierre estimada."),
    Policy("Sin tareas huérfanas", "Ninguna tarea activa debe estar sin responsable asignado."),
    Policy("Sin dependencias inconsistentes", "Ninguna dependencia debe apuntar a una tarea inexistente."),
    Policy("Índice de salud del portafolio ≥ 70", "El promedio de salud de los proyectos activos debe mantenerse saludable."),
    Policy("Sin proyectos críticos en riesgo", "Ningún proyecto de criticidad Alta debe tener índice de salud < 55."),
]


def evaluate(projects=None, tasks=None, team=None) -> pd.DataFrame:
    proj_df = projects if projects is not None else demo_data.projects()
    task_df = tasks if tasks is not None else demo_data.tasks()
    h = health.project_health(proj_df, task_df, team)

    sin_dueno = int(proj_df["dueno"].isna().sum())
    sin_fecha = int(proj_df["fecha_fin"].isna().sum())
    huerfanas = int(task_df["responsable"].isna().sum())
    from . import dependencies as dep_mod
    inconsistentes = len(dep_mod.orphan_dependencies(task_df))
    indice_prom = float(h["indice"].mean()) if not h.empty else 0.0
    criticos = proj_df[proj_df["criticidad"] == "Alta"].merge(h, on="proyecto_id", how="left")
    criticos_en_riesgo = int((criticos["indice"] < 55).sum())

    evals = [
        (sin_dueno == 0, f"{sin_dueno} proyecto(s) sin dueño"),
        (sin_fecha == 0, f"{sin_fecha} proyecto(s) sin fecha de fin"),
        (huerfanas == 0, f"{huerfanas} tarea(s) huérfana(s)"),
        (inconsistentes == 0, f"{inconsistentes} dependencia(s) inconsistente(s)"),
        (indice_prom >= 70, f"Índice promedio actual: {indice_prom:.1f}"),
        (criticos_en_riesgo == 0, f"{criticos_en_riesgo} proyecto(s) crítico(s) en riesgo"),
    ]

    rows = []
    for policy, (ok, evidencia) in zip(_POLICIES, evals):
        rows.append({
            "politica": policy.nombre,
            "descripcion": policy.descripcion,
            "estado": "cumple" if ok else "incumple",
            "evidencia": evidencia,
        })
    return pd.DataFrame(rows)
