# © 2026 Martín Viera. Todos los derechos reservados.
"""Políticas de gestión verificadas contra evidencia real (no checkboxes manuales)."""

from dataclasses import dataclass

import pandas as pd

from . import demo_data, health


@dataclass
class Policy:
    clave: str
    nombre: dict
    descripcion: dict


_POLICIES = [
    Policy("dueno",
          {"es": "Todo proyecto tiene dueño", "en": "Every project has an owner",
           "pt": "Todo projeto tem responsável"},
          {"es": "Ningún proyecto activo debe estar sin responsable asignado.",
           "en": "No active project should be without an assigned owner.",
           "pt": "Nenhum projeto ativo deve estar sem responsável atribuído."}),
    Policy("fecha_fin",
          {"es": "Todo proyecto tiene fecha de fin", "en": "Every project has an end date",
           "pt": "Todo projeto tem data de término"},
          {"es": "Todo proyecto activo debe tener una fecha de cierre estimada.",
           "en": "Every active project must have an estimated closing date.",
           "pt": "Todo projeto ativo deve ter uma data de encerramento estimada."}),
    Policy("huerfanas",
          {"es": "Sin tareas huérfanas", "en": "No orphan tasks", "pt": "Sem tarefas órfãs"},
          {"es": "Ninguna tarea activa debe estar sin responsable asignado.",
           "en": "No active task should be without an assignee.",
           "pt": "Nenhuma tarefa ativa deve estar sem responsável atribuído."}),
    Policy("dependencias",
          {"es": "Sin dependencias inconsistentes", "en": "No inconsistent dependencies",
           "pt": "Sem dependências inconsistentes"},
          {"es": "Ninguna dependencia debe apuntar a una tarea inexistente.",
           "en": "No dependency should point to a task that doesn't exist.",
           "pt": "Nenhuma dependência deve apontar para uma tarefa inexistente."}),
    Policy("salud",
          {"es": "Índice de salud del portafolio ≥ 70", "en": "Portfolio health index ≥ 70",
           "pt": "Índice de saúde do portfólio ≥ 70"},
          {"es": "El promedio de salud de los proyectos activos debe mantenerse saludable.",
           "en": "The average health of active projects must stay in the healthy range.",
           "pt": "A média de saúde dos projetos ativos deve se manter saudável."}),
    Policy("criticos",
          {"es": "Sin proyectos críticos en riesgo", "en": "No critical projects at risk",
           "pt": "Sem projetos críticos em risco"},
          {"es": "Ningún proyecto de criticidad Alta debe tener índice de salud < 55.",
           "en": "No High-criticality project should have a health index < 55.",
           "pt": "Nenhum projeto de criticidade Alta deve ter índice de saúde < 55."}),
]

_EVIDENCIA = {
    "dueno": {"es": "{n} proyecto(s) sin dueño", "en": "{n} project(s) without an owner",
              "pt": "{n} projeto(s) sem responsável"},
    "fecha_fin": {"es": "{n} proyecto(s) sin fecha de fin", "en": "{n} project(s) without an end date",
                  "pt": "{n} projeto(s) sem data de término"},
    "huerfanas": {"es": "{n} tarea(s) huérfana(s)", "en": "{n} orphan task(s)",
                  "pt": "{n} tarefa(s) órfã(s)"},
    "dependencias": {"es": "{n} dependencia(s) inconsistente(s)", "en": "{n} inconsistent dependency(-ies)",
                      "pt": "{n} dependência(s) inconsistente(s)"},
    "salud": {"es": "Índice promedio actual: {n}", "en": "Current average index: {n}",
              "pt": "Índice médio atual: {n}"},
    "criticos": {"es": "{n} proyecto(s) crítico(s) en riesgo", "en": "{n} critical project(s) at risk",
                 "pt": "{n} projeto(s) crítico(s) em risco"},
}


def evaluate(projects=None, tasks=None, team=None, lang: str = "es") -> pd.DataFrame:
    lang = lang if lang in ("es", "en", "pt") else "es"
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
        ("dueno", sin_dueno == 0, sin_dueno),
        ("fecha_fin", sin_fecha == 0, sin_fecha),
        ("huerfanas", huerfanas == 0, huerfanas),
        ("dependencias", inconsistentes == 0, inconsistentes),
        ("salud", indice_prom >= 70, f"{indice_prom:.1f}"),
        ("criticos", criticos_en_riesgo == 0, criticos_en_riesgo),
    ]

    rows = []
    for policy, (clave, ok, n) in zip(_POLICIES, evals):
        rows.append({
            # "clave" es el identificador ESTABLE (no cambia con el idioma) —
            # quien necesite persistir algo atado a esta política (p. ej. el
            # seguimiento de advisor.py) tiene que usar esto, no "politica":
            # el nombre traducido cambiaría de id cada vez que alguien
            # cambiara de idioma, duplicando el seguimiento.
            "clave": clave,
            "politica": policy.nombre.get(lang, policy.nombre["es"]),
            "descripcion": policy.descripcion.get(lang, policy.descripcion["es"]),
            "estado": "cumple" if ok else "incumple",
            "evidencia": _EVIDENCIA[clave].get(lang, _EVIDENCIA[clave]["es"]).format(n=n),
        })
    return pd.DataFrame(rows)
