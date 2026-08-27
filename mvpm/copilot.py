# © 2026 Martín Viera. Todos los derechos reservados.
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

# Palabras clave por idioma: antes sólo reconocía español, así que una
# pregunta en inglés o portugués ("what's blocked?") no matcheaba ningún
# tópico y caía siempre en "resumen" — el motor de reglas funcionaba, pero
# entendía mal la pregunta. Ahora cada idioma tiene su propio set.
_KEYWORDS = {
    "es": {"bloque": "bloqueos", "sobrecarg": "sobrecarga", "riesgo": "riesgo",
          "presupuesto": "presupuesto", "prioridad": "prioridad", "prioriza": "prioridad"},
    "en": {"block": "bloqueos", "overload": "sobrecarga", "risk": "riesgo",
          "budget": "presupuesto", "priorit": "prioridad"},
    "pt": {"bloque": "bloqueos", "sobrecarg": "sobrecarga", "risco": "riesgo",
          "orçamento": "presupuesto", "orcamento": "presupuesto", "priorid": "prioridad",
          "prioriza": "prioridad"},
}


def _route(question: str, lang: str = "es") -> str:
    q = question.lower()
    for kw, topic in _KEYWORDS.get(lang, _KEYWORDS["es"]).items():
        if kw in q:
            return topic
    return "resumen"


_TX = {
    "es": {
        "bloqueos_none": "No hay tareas bloqueadas activas en este momento.",
        "bloqueos": ("Hay {n} tarea(s) bloqueada(s). La de mayor impacto es '{titulo}' "
                    "({tarea_id}): si sigue bloqueada, frena a {impactadas} tarea(s) más "
                    "aguas abajo."),
        "sobrecarga_none": "Nadie está por encima de su capacidad semanal declarada.",
        "sobrecarga": "{n} persona(s) sobrecargada(s) esta semana: {nombres}.",
        "riesgo_none": "Ningún proyecto está en estado de riesgo hoy.",
        "riesgo": "{n} proyecto(s) en riesgo: {nombres}.",
        "presupuesto_none": "Ningún proyecto está sobre presupuesto.",
        "presupuesto": "{n} proyecto(s) sobre presupuesto: {nombres}.",
        "prioridad_none": "No hay tareas pendientes para priorizar.",
        "prioridad": "Las 3 tareas de mayor valor esperado ahora mismo son: {items}.",
        "resumen": "Índice de salud del portafolio: {indice}/100. {riesgo} proyecto(s) en riesgo.",
        "valor": "valor",
    },
    "en": {
        "bloqueos_none": "There are no active blocked tasks right now.",
        "bloqueos": ("There are {n} blocked task(s). The highest-impact one is '{titulo}' "
                    "({tarea_id}): if it stays blocked, it holds back {impactadas} more "
                    "downstream task(s)."),
        "sobrecarga_none": "No one is above their declared weekly capacity.",
        "sobrecarga": "{n} person/people overloaded this week: {nombres}.",
        "riesgo_none": "No project is in an at-risk state today.",
        "riesgo": "{n} project(s) at risk: {nombres}.",
        "presupuesto_none": "No project is over budget.",
        "presupuesto": "{n} project(s) over budget: {nombres}.",
        "prioridad_none": "There are no pending tasks to prioritize.",
        "prioridad": "The 3 tasks with the highest expected value right now are: {items}.",
        "resumen": "Portfolio health index: {indice}/100. {riesgo} project(s) at risk.",
        "valor": "value",
    },
    "pt": {
        "bloqueos_none": "Não há tarefas bloqueadas ativas neste momento.",
        "bloqueos": ("Há {n} tarefa(s) bloqueada(s). A de maior impacto é '{titulo}' "
                    "({tarea_id}): se continuar bloqueada, trava {impactadas} tarefa(s) a "
                    "mais rio abaixo."),
        "sobrecarga_none": "Ninguém está acima da capacidade semanal declarada.",
        "sobrecarga": "{n} pessoa(s) sobrecarregada(s) esta semana: {nombres}.",
        "riesgo_none": "Nenhum projeto está em estado de risco hoje.",
        "riesgo": "{n} projeto(s) em risco: {nombres}.",
        "presupuesto_none": "Nenhum projeto está acima do orçamento.",
        "presupuesto": "{n} projeto(s) acima do orçamento: {nombres}.",
        "prioridad_none": "Não há tarefas pendentes para priorizar.",
        "prioridad": "As 3 tarefas de maior valor esperado agora são: {items}.",
        "resumen": "Índice de saúde do portfólio: {indice}/100. {riesgo} projeto(s) em risco.",
        "valor": "valor",
    },
}


def _respuesta_bloqueos(tasks: pd.DataFrame, tx: dict) -> str:
    bloqueadas = dep_mod.bloqueos_activos(tasks)
    if bloqueadas.empty:
        return tx["bloqueos_none"]
    top = bloqueadas.iloc[0]
    return tx["bloqueos"].format(n=len(bloqueadas), titulo=top["titulo"], tarea_id=top["tarea_id"],
                                 impactadas=top["tareas_impactadas"])


def _respuesta_sobrecarga(team: pd.DataFrame, tx: dict) -> str:
    sobre = team[team["carga_actual_hs"] > team["capacidad_semanal_hs"]]
    if sobre.empty:
        return tx["sobrecarga_none"]
    nombres = ", ".join(f"{r['nombre']} ({r['carga_actual_hs']}/{r['capacidad_semanal_hs']}hs)" for _, r in sobre.iterrows())
    return tx["sobrecarga"].format(n=len(sobre), nombres=nombres)


def _respuesta_riesgo(projects: pd.DataFrame, tasks: pd.DataFrame, team: pd.DataFrame, tx: dict) -> str:
    h = health.project_health(projects, tasks, team)
    riesgo = h[h["estado"] == "riesgo"].sort_values("indice")
    if riesgo.empty:
        return tx["riesgo_none"]
    nombres = ", ".join(f"{r['nombre']} ({r['indice']}/100)" for _, r in riesgo.head(5).iterrows())
    return tx["riesgo"].format(n=len(riesgo), nombres=nombres)


def _respuesta_presupuesto(projects: pd.DataFrame, tx: dict) -> str:
    sobre = projects[projects["ejecutado"] > projects["presupuesto"]]
    if sobre.empty:
        return tx["presupuesto_none"]
    nombres = ", ".join(sobre["nombre"].tolist()[:5])
    return tx["presupuesto"].format(n=len(sobre), nombres=nombres)


def _respuesta_prioridad(projects: pd.DataFrame, tasks: pd.DataFrame, tx: dict) -> str:
    top = prioritizer.top(3, projects, tasks)
    if top.empty:
        return tx["prioridad_none"]
    items = "; ".join(f"{r['titulo']} ({tx['valor']} {r['valor_esperado']})" for _, r in top.iterrows())
    return tx["prioridad"].format(items=items)


def _respuesta_resumen(projects: pd.DataFrame, tasks: pd.DataFrame, team: pd.DataFrame, tx: dict) -> str:
    indice = health.overall_index(projects, tasks, team)
    riesgo = (health.project_health(projects, tasks, team)["estado"] == "riesgo").sum()
    return tx["resumen"].format(indice=indice, riesgo=riesgo)


def answer(question: str, projects=None, tasks=None, team=None, use_ai: bool = True,
           license_token: str | None = None, lang: str = "es") -> dict:
    """Responde una pregunta sobre el portafolio. Devuelve dict con la respuesta
    determinística y, si hay ANTHROPIC_API_KEY configurada, cupo de IA
    disponible en la licencia y use_ai=True, una versión redactada por IA del
    mismo contenido (nunca reemplaza los números). El motor de reglas
    responde siempre, tenga o no cupo — solo el enriquecimiento con IA se mide.
    `lang` decide tanto qué palabras clave reconoce la pregunta como en qué
    idioma sale la respuesta (determinística y, si corresponde, la de IA)."""
    lang = lang if lang in _TX else "es"
    tx = _TX[lang]
    proj_df = projects if projects is not None else demo_data.projects()
    task_df = tasks if tasks is not None else demo_data.tasks()
    team_df = team if team is not None else demo_data.team()

    topic = _route(question, lang)
    handlers = {
        "bloqueos": lambda: _respuesta_bloqueos(task_df, tx),
        "sobrecarga": lambda: _respuesta_sobrecarga(team_df, tx),
        "riesgo": lambda: _respuesta_riesgo(proj_df, task_df, team_df, tx),
        "presupuesto": lambda: _respuesta_presupuesto(proj_df, tx),
        "prioridad": lambda: _respuesta_prioridad(proj_df, task_df, tx),
        "resumen": lambda: _respuesta_resumen(proj_df, task_df, team_df, tx),
    }
    base_answer = handlers[topic]()

    result = {"topic": topic, "answer": base_answer, "ai_enriched": False, "cupo_ia": None}
    if use_ai and os.environ.get("ANTHROPIC_API_KEY"):
        from . import licensing
        puede, detalle = licensing.puede_usar_ia(license_token)
        result["cupo_ia"] = detalle
        if puede:
            enriched = _claude_enrich(question, base_answer, lang)
            if enriched:
                result["answer"] = enriched
                result["ai_enriched"] = True
                payload = licensing.verify_license(license_token) if license_token else None
                licensing.registrar_uso_ia(payload["email"] if payload else "demo@local")
    return result


_SYSTEM_POR_IDIOMA = {
    "es": "Redactás en español rioplatense, tono directo y profesional. "
          "Nunca agregues cifras que no estén en el texto base.",
    "en": "You write in professional, direct English. "
          "Never add figures that aren't already in the base text.",
    "pt": "Você escreve em português (Brasil), tom direto e profissional. "
          "Nunca adicione números que não estejam no texto base.",
}


def _claude_enrich(question: str, base_answer: str, lang: str = "es") -> str | None:
    """Redacta la respuesta base en un tono más natural, EN EL IDIOMA PEDIDO.
    Nunca inventa cifras fuera de `base_answer`; si falla o no hay API key, se
    degrada en silencio al texto determinístico (el producto nunca depende de
    esta capa)."""
    try:
        import anthropic  # type: ignore
    except ImportError:
        return None
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=200,
            system=_SYSTEM_POR_IDIOMA.get(lang, _SYSTEM_POR_IDIOMA["es"]),
            messages=[{
                "role": "user",
                "content": f"Pregunta del usuario: {question}\nDato real calculado por el motor: {base_answer}\n"
                            "Redactá esta respuesta en 1-2 frases naturales, sin inventar números nuevos.",
            }],
        )
        return msg.content[0].text if msg.content else None
    except Exception:
        return None
