"""Asistente de sugerencias: detecta problemas reales del portafolio (motor de
reglas, siempre disponible) y redacta una sugerencia de acción — con un motor
de reglas por defecto, o pulida por el proveedor de IA que el usuario elija
(Claude, ChatGPT o Gemini, según qué clave tenga configurada). Mismo
principio que `copilot.py`: la IA nunca inventa el problema ni el número que
lo sustenta, sólo redacta mejor la acción sugerida sobre el dato real.

Las sugerencias se pueden marcar en seguimiento y cambiar de estado — quedan
persistidas en `mvpm/db.py` (tabla `seguimientos`), no se pierden al recargar.
"""

import os

import pandas as pd

from . import catalog, dependencies as dep_mod, health, policies

_SUGERENCIAS = {
    "bloqueo": "Desbloqueá '{titulo}' antes que nada: frena a {impacto} tarea(s) más — "
               "confirmá con el responsable qué falta para destrabarla.",
    "dependencia_huerfana": "'{titulo}' depende de una tarea que ya no existe — corregí o quitá "
                             "esa dependencia desde la ficha de la tarea para que el backlog no se distorsione.",
    "proyecto_en_riesgo": "'{titulo}' está en riesgo (índice {indice}/100) — pedile a su dueño un "
                           "plan de acción esta semana, como marca el glosario compartido.",
    "sobre_presupuesto": "'{titulo}' ya ejecutó más presupuesto del asignado — revisá con "
                          "finanzas si corresponde ampliar la partida o frenar gasto.",
    "sobrecarga_equipo": "{titulo} está por encima de su capacidad semanal declarada — "
                          "redistribuí alguna tarea activa antes de sumarle más.",
    "politica_incumplida": "'{titulo}' no cumple la política de gestión — revisá la evidencia y "
                            "corregí lo que falta para que deje de aparecer acá.",
}


def detectar_problemas(projects: pd.DataFrame, tasks: pd.DataFrame, team: pd.DataFrame) -> list[dict]:
    """Cada problema tiene un id estable ('tipo:entidad') para poder
    persistir su seguimiento sin duplicarlo si se vuelve a detectar."""
    problemas = []

    for _, b in dep_mod.bloqueos_activos(tasks).iterrows():
        problemas.append({
            "id": f"bloqueo:{b['tarea_id']}", "tipo": "bloqueo", "titulo": b["titulo"],
            "severidad": "alta", "contexto": {"impacto": int(b["tareas_impactadas"])},
        })

    for _, o in dep_mod.orphan_dependencies(tasks).iterrows():
        problemas.append({
            "id": f"dependencia_huerfana:{o['tarea_id']}", "tipo": "dependencia_huerfana",
            "titulo": o["titulo"], "severidad": "media", "contexto": {},
        })

    for _, p in health.project_health(projects, tasks, team).iterrows():
        if p["estado"] == "riesgo":
            problemas.append({
                "id": f"proyecto_en_riesgo:{p['proyecto_id']}", "tipo": "proyecto_en_riesgo",
                "titulo": p["nombre"], "severidad": "alta", "contexto": {"indice": p["indice"]},
            })

    cat = catalog.catalog(projects)
    for _, c in cat[cat["sobre_presupuesto"]].iterrows():
        problemas.append({
            "id": f"sobre_presupuesto:{c['proyecto_id']}", "tipo": "sobre_presupuesto",
            "titulo": c["nombre"], "severidad": "media", "contexto": {},
        })

    for _, m in team[team["carga_actual_hs"] > team["capacidad_semanal_hs"]].iterrows():
        problemas.append({
            "id": f"sobrecarga_equipo:{m['nombre']}", "tipo": "sobrecarga_equipo",
            "titulo": m["nombre"], "severidad": "media",
            "contexto": {"carga": int(m["carga_actual_hs"]), "capacidad": int(m["capacidad_semanal_hs"])},
        })

    pol = policies.evaluate(projects, tasks, team)
    for _, r in pol[pol["estado"] != "cumple"].iterrows():
        problemas.append({
            "id": f"politica_incumplida:{r['politica']}", "tipo": "politica_incumplida",
            "titulo": r["politica"], "severidad": "baja", "contexto": {},
        })

    return problemas


def _texto_base(problema: dict) -> str:
    return _SUGERENCIAS[problema["tipo"]].format(titulo=problema["titulo"], **problema["contexto"])


def _enrich_claude(texto: str) -> str | None:
    try:
        import anthropic  # type: ignore
    except ImportError:
        return None
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=200,
            output_config={"effort": "low"},
            system="Redactás en español rioplatense, tono directo y profesional. "
                   "Nunca agregues cifras que no estén en el texto base.",
            messages=[{"role": "user", "content":
                       f"Sugerencia del motor de reglas: {texto}\n"
                       "Redactala en 1-2 frases más naturales, sin inventar números nuevos."}],
        )
        return msg.content[0].text if msg.content else None
    except Exception:
        return None


def _enrich_openai(texto: str) -> str | None:
    model = os.environ.get("OPENAI_MODEL")
    if not model:
        return None
    try:
        import openai  # type: ignore
    except ImportError:
        return None
    try:
        client = openai.OpenAI()
        resp = client.chat.completions.create(
            model=model,
            max_tokens=200,
            messages=[
                {"role": "system", "content": "Redactás en español rioplatense, tono directo y "
                                               "profesional. Nunca agregues cifras que no estén en el texto base."},
                {"role": "user", "content": f"Sugerencia del motor de reglas: {texto}\n"
                                             "Redactala en 1-2 frases más naturales, sin inventar números nuevos."},
            ],
        )
        return resp.choices[0].message.content if resp.choices else None
    except Exception:
        return None


def _enrich_gemini(texto: str) -> str | None:
    model = os.environ.get("GEMINI_MODEL")
    if not model:
        return None
    try:
        import google.generativeai as genai  # type: ignore
    except ImportError:
        return None
    try:
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        client = genai.GenerativeModel(model)
        resp = client.generate_content(
            "Redactá en español rioplatense, tono directo y profesional, sin inventar cifras nuevas.\n"
            f"Sugerencia del motor de reglas: {texto}\nRedactala en 1-2 frases más naturales.")
        return resp.text if getattr(resp, "text", None) else None
    except Exception:
        return None


_PROVEEDORES = {
    "claude": (_enrich_claude, "ANTHROPIC_API_KEY"),
    "chatgpt": (_enrich_openai, "OPENAI_API_KEY"),
    "gemini": (_enrich_gemini, "GEMINI_API_KEY"),
}


def proveedores_disponibles() -> list[str]:
    """Sólo lista proveedores con su clave configurada — nunca se ofrece uno
    que vaya a fallar en silencio."""
    return [nombre for nombre, (_, env_key) in _PROVEEDORES.items() if os.environ.get(env_key)]


def sugerir(problema: dict, proveedor: str | None = None) -> dict:
    """Devuelve {sugerencia, ai_enriched, proveedor}. El motor de reglas
    responde siempre — la IA es una capa de redacción opcional que nunca
    reemplaza el texto base si no está disponible o falla."""
    base = _texto_base(problema)
    resultado = {"sugerencia": base, "ai_enriched": False, "proveedor": None}
    if proveedor and proveedor in _PROVEEDORES:
        fn, env_key = _PROVEEDORES[proveedor]
        if os.environ.get(env_key):
            enriched = fn(base)
            if enriched:
                resultado = {"sugerencia": enriched, "ai_enriched": True, "proveedor": proveedor}
    return resultado
