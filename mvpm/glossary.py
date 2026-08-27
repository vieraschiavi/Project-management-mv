# © 2026 Martín Viera. Todos los derechos reservados.
"""Glosario compartido: qué significa cada estado, igual para todo el equipo."""

import pandas as pd

# Ya traía "definicion_en" desde antes de que el resto del producto fuera
# trilingüe (quedaba mostrada siempre, junto a la española, en una sola tabla
# bilingüe). Ahora que hay un idioma elegido por sesión, se completa el
# portugués y `glossary(lang)` devuelve una sola columna de definición en el
# idioma pedido — la fila bilingüe de antes ya no tiene sentido si el resto
# de la pantalla está en un solo idioma.
_TERMS = [
    {"clave": "saludable", "termino": {"es": "Saludable", "en": "Healthy", "pt": "Saudável"},
     "definicion": {"es": "Índice de salud ≥ 75. Sin acción requerida esta semana.",
                    "en": "Health index ≥ 75. No action required this week.",
                    "pt": "Índice de saúde ≥ 75. Nenhuma ação necessária esta semana."},
     "dueno": {"es": "PMO", "en": "PMO", "pt": "PMO"}},
    {"clave": "en_observacion", "termino": {"es": "En observación", "en": "Watch", "pt": "Em observação"},
     "definicion": {"es": "Índice entre 55 y 75. Revisar en el próximo standup.",
                    "en": "Index between 55 and 75. Review in the next standup.",
                    "pt": "Índice entre 55 e 75. Revisar no próximo standup."},
     "dueno": {"es": "PMO", "en": "PMO", "pt": "PMO"}},
    {"clave": "en_riesgo", "termino": {"es": "En riesgo", "en": "At risk", "pt": "Em risco"},
     "definicion": {"es": "Índice < 55. Requiere plan de acción del dueño esta semana.",
                    "en": "Index < 55. The owner must present an action plan this week.",
                    "pt": "Índice < 55. Exige plano de ação do responsável esta semana."},
     "dueno": {"es": "PMO", "en": "PMO", "pt": "PMO"}},
    {"clave": "bloqueado", "termino": {"es": "Bloqueado", "en": "Blocked", "pt": "Bloqueado"},
     "definicion": {"es": "La tarea no puede avanzar hasta resolver una dependencia u obstáculo externo.",
                    "en": "The task can't move forward until a dependency or external blocker is resolved.",
                    "pt": "A tarefa não pode avançar até resolver uma dependência ou obstáculo externo."},
     "dueno": {"es": "Equipo", "en": "Team", "pt": "Equipe"}},
    {"clave": "sobre_presupuesto", "termino": {"es": "Sobre presupuesto", "en": "Over budget", "pt": "Acima do orçamento"},
     "definicion": {"es": "Ejecutado > presupuesto asignado al proyecto.",
                    "en": "Spent > the project's assigned budget.",
                    "pt": "Executado > orçamento atribuído ao projeto."},
     "dueno": {"es": "Finanzas", "en": "Finance", "pt": "Financeiro"}},
    {"clave": "tarea_huerfana", "termino": {"es": "Tarea huérfana", "en": "Orphan task", "pt": "Tarefa órfã"},
     "definicion": {"es": "Tarea sin responsable asignado.",
                    "en": "Task with no assignee.",
                    "pt": "Tarefa sem responsável atribuído."},
     "dueno": {"es": "PMO", "en": "PMO", "pt": "PMO"}},
]

def glossary(lang: str = "es") -> pd.DataFrame:
    """Una fila por término, en el idioma pedido — antes era una tabla fija con
    columnas 'definicion_es'/'definicion_en' mostradas siempre juntas; ahora el
    glosario respeta el mismo idioma que el resto de la pantalla. Los NOMBRES
    de columna (termino/definicion/dueno) quedan fijos en las tres versiones
    —son la clave interna, no texto de cara al usuario—; `app/app.py` es quien
    les pone el encabezado traducido al mostrar la tabla."""
    lang = lang if lang in ("es", "en", "pt") else "es"
    filas = [{"termino": t["termino"].get(lang, t["termino"]["es"]),
             "definicion": t["definicion"].get(lang, t["definicion"]["es"]),
             "dueno": t["dueno"].get(lang, t["dueno"]["es"])}
            for t in _TERMS]
    return pd.DataFrame(filas)
