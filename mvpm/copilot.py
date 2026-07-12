"""Copiloto de portafolio: responde preguntas en lenguaje natural sobre el
estado real de los proyectos.

Mismo principio que el copiloto de Kobra: el núcleo funciona 100% con reglas
sobre el dato ya calculado por `health`/`dependencies`/`prioritizer` — Claude
es un enriquecimiento opcional que solo pule el lenguaje de una respuesta que
el motor de reglas ya construyó, nunca inventa números nuevos.
"""

import os

import pandas as pd

from . import dependencies as dep_mod
from . import demo_data, health, prioritizer

_KEYWORDS = {
    "bloque": "bloqueos",
    "sobrecarg": "sobrecarga",
    "riesgo": "riesgo",
    "presupuesto": "presupuesto",
    "prioridad": "prioridad",
    "prioriza": "prioridad",
}


def _route(question: str) -> str:
    q = question.lower()
    for kw, topic in _KEYWORDS.items():
        if kw in q:
            return topic
    return "resumen"


def _respuesta_bloqueos(tasks: pd.DataFrame) -> str:
    bloqueadas = dep_mod.bloqueos_activos(tasks)
    if bloqueadas.empty:
        return "No hay tareas bloqueadas activas en este momento."
    top = bloqueadas.iloc[0]
    return (
        f"Hay {len(bloqueadas)} tarea(s) bloqueada(s). La de mayor impacto es "
        f"'{top['titulo']}' ({top['tarea_id']}): si sigue bloqueada, frena a "
        f"{top['tareas_impactadas']} tarea(s) más aguas abajo."
    )


def _respuesta_sobrecarga(team: pd.DataFrame) -> str:
    sobre = team[team["carga_actual_hs"] > team["capacidad_semanal_hs"]]
    if sobre.empty:
        return "Nadie está por encima de su capacidad semanal declarada."
    nombres = ", ".join(f"{r['nombre']} ({r['carga_actual_hs']}/{r['capacidad_semanal_hs']}hs)" for _, r in sobre.iterrows())
    return f"{len(sobre)} persona(s) sobrecargada(s) esta semana: {nombres}."


def _respuesta_riesgo(projects: pd.DataFrame, tasks: pd.DataFrame, team: pd.DataFrame) -> str:
    h = health.project_health(projects, tasks, team)
    riesgo = h[h["estado"] == "riesgo"].sort_values("indice")
    if riesgo.empty:
        return "Ningún proyecto está en estado de riesgo hoy."
    nombres = ", ".join(f"{r['nombre']} ({r['indice']}/100)" for _, r in riesgo.head(5).iterrows())
    return f"{len(riesgo)} proyecto(s) en riesgo: {nombres}."


def _respuesta_presupuesto(projects: pd.DataFrame) -> str:
    sobre = projects[projects["ejecutado"] > projects["presupuesto"]]
    if sobre.empty:
        return "Ningún proyecto está sobre presupuesto."
    nombres = ", ".join(sobre["nombre"].tolist()[:5])
    return f"{len(sobre)} proyecto(s) sobre presupuesto: {nombres}."


def _respuesta_prioridad(projects: pd.DataFrame, tasks: pd.DataFrame) -> str:
    top = prioritizer.top(3, projects, tasks)
    if top.empty:
        return "No hay tareas pendientes para priorizar."
    items = "; ".join(f"{r['titulo']} (valor {r['valor_esperado']})" for _, r in top.iterrows())
    return f"Las 3 tareas de mayor valor esperado ahora mismo son: {items}."


def _respuesta_resumen(projects: pd.DataFrame, tasks: pd.DataFrame, team: pd.DataFrame) -> str:
    indice = health.overall_index(projects, tasks, team)
    riesgo = (health.project_health(projects, tasks, team)["estado"] == "riesgo").sum()
    return f"Índice de salud del portafolio: {indice}/100. {riesgo} proyecto(s) en riesgo."


def answer(question: str, projects=None, tasks=None, team=None, use_ai: bool = True) -> dict:
    """Responde una pregunta sobre el portafolio. Devuelve dict con la respuesta
    determinística y, si hay ANTHROPIC_API_KEY configurada y use_ai=True, una
    versión redactada por IA del mismo contenido (nunca reemplaza los números)."""
    proj_df = projects if projects is not None else demo_data.projects()
    task_df = tasks if tasks is not None else demo_data.tasks()
    team_df = team if team is not None else demo_data.team()

    topic = _route(question)
    handlers = {
        "bloqueos": lambda: _respuesta_bloqueos(task_df),
        "sobrecarga": lambda: _respuesta_sobrecarga(team_df),
        "riesgo": lambda: _respuesta_riesgo(proj_df, task_df, team_df),
        "presupuesto": lambda: _respuesta_presupuesto(proj_df),
        "prioridad": lambda: _respuesta_prioridad(proj_df, task_df),
        "resumen": lambda: _respuesta_resumen(proj_df, task_df, team_df),
    }
    base_answer = handlers[topic]()

    result = {"topic": topic, "answer": base_answer, "ai_enriched": False}
    if use_ai and os.environ.get("ANTHROPIC_API_KEY"):
        enriched = _claude_enrich(question, base_answer)
        if enriched:
            result["answer"] = enriched
            result["ai_enriched"] = True
    return result


def _claude_enrich(question: str, base_answer: str) -> str | None:
    """Redacta la respuesta base en un tono más natural. Nunca inventa cifras
    fuera de `base_answer`; si falla o no hay API key, se degrada en silencio
    al texto determinístico (el producto nunca depende de esta capa)."""
    try:
        import anthropic  # type: ignore
    except ImportError:
        return None
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=200,
            system=(
                "Redactás en español rioplatense, tono directo y profesional. "
                "Nunca agregues cifras que no estén en el texto base."
            ),
            messages=[{
                "role": "user",
                "content": f"Pregunta del usuario: {question}\nDato real calculado por el motor: {base_answer}\n"
                            "Redactá esta respuesta en 1-2 frases naturales, sin inventar números nuevos.",
            }],
        )
        return msg.content[0].text if msg.content else None
    except Exception:
        return None
