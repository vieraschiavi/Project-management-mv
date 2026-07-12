"""Glosario compartido: qué significa cada estado, igual para todo el equipo."""

import pandas as pd

_TERMS = [
    {"termino": "Saludable", "definicion_es": "Índice de salud ≥ 75. Sin acción requerida esta semana.",
     "definicion_en": "Health index ≥ 75. No action required this week.", "dueno": "PMO"},
    {"termino": "En observación", "definicion_es": "Índice entre 55 y 75. Revisar en el próximo standup.",
     "definicion_en": "Index between 55 and 75. Review in next standup.", "dueno": "PMO"},
    {"termino": "En riesgo", "definicion_es": "Índice < 55. Requiere plan de acción del dueño esta semana.",
     "definicion_en": "Index < 55. Owner must present an action plan this week.", "dueno": "PMO"},
    {"termino": "Bloqueado", "definicion_es": "La tarea no puede avanzar hasta resolver una dependencia u obstáculo externo.",
     "definicion_en": "Task cannot progress until a dependency or external blocker is resolved.", "dueno": "Equipo"},
    {"termino": "Sobre presupuesto", "definicion_es": "Ejecutado > presupuesto asignado al proyecto.",
     "definicion_en": "Spent > project's assigned budget.", "dueno": "Finanzas"},
    {"termino": "Tarea huérfana", "definicion_es": "Tarea sin responsable asignado.",
     "definicion_en": "Task with no assignee.", "dueno": "PMO"},
]


def glossary() -> pd.DataFrame:
    return pd.DataFrame(_TERMS)
