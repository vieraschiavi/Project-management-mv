# © 2026 Martín Viera. Todos los derechos reservados.
"""Asistente de sugerencias: detecta problemas reales del portafolio (motor de
reglas, siempre disponible) y redacta una sugerencia de acción — con un motor
de reglas por defecto, o pulida por el proveedor de IA que el usuario elija
(Claude, ChatGPT, Gemini, Grok o Copilot, según qué clave tenga configurada, y
con el modelo que haya elegido en Configuración). Mismo
principio que `copilot.py`: la IA nunca inventa el problema ni el número que
lo sustenta, sólo redacta mejor la acción sugerida sobre el dato real.

Las sugerencias se pueden marcar en seguimiento y cambiar de estado — quedan
persistidas en `mvpm/db.py` (tabla `seguimientos`), no se pierden al recargar.
"""

import os

import pandas as pd

from . import ai, catalog, dependencies as dep_mod, health, policies

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


# El pedido de redacción es idéntico para todos los proveedores: lo único que
# cambiaba entre las tres versiones que había acá era el dialecto del SDK, y de
# eso ahora se encarga ai.completar(). La instrucción de no inventar cifras va
# en el mensaje de sistema, no como sugerencia: es la regla de honestidad de
# datos del producto aplicada a la capa de IA.
_SISTEMA = ("Redactás en español rioplatense, tono directo y profesional. "
            "Nunca agregues cifras que no estén en el texto base.")

_PEDIDO = ("Sugerencia del motor de reglas: {texto}\n"
           "Redactala en 1-2 frases más naturales, sin inventar números nuevos.")

# Se derivan de la capa genérica para que agregar un proveedor allá alcance:
# antes este módulo tenía su propia lista y su propia implementación por
# proveedor, y cualquier alta había que hacerla dos veces.
_PROVEEDORES = dict(ai._ENV_KEYS)


def _enriquecer(texto: str, proveedor: str) -> str | None:
    return ai.completar(_SISTEMA, _PEDIDO.format(texto=texto), proveedor, max_tokens=200)


def proveedores_disponibles() -> list[str]:
    """Sólo lista proveedores con su clave configurada — nunca se ofrece uno
    que vaya a fallar en silencio.

    Más laxo que `ai.proveedores_disponibles()`, que además exige tener un
    modelo resuelto: acá alcanza con la clave porque si falta el modelo la
    sugerencia igual sale del motor de reglas, que es el comportamiento
    correcto y no un error."""
    return [nombre for nombre, env_key in _PROVEEDORES.items() if os.environ.get(env_key)]


def sugerir(problema: dict, proveedor: str | None = None) -> dict:
    """Devuelve {sugerencia, ai_enriched, proveedor}. El motor de reglas
    responde siempre — la IA es una capa de redacción opcional que nunca
    reemplaza el texto base si no está disponible o falla.

    El modelo lo decide `mvpm/modelos.py` (lo elegido en Configuración, o la
    variable de entorno del proveedor)."""
    base = _texto_base(problema)
    resultado = {"sugerencia": base, "ai_enriched": False, "proveedor": None}
    if proveedor and proveedor in _PROVEEDORES:
        if os.environ.get(_PROVEEDORES[proveedor]):
            enriched = _enriquecer(base, proveedor)
            if enriched:
                resultado = {"sugerencia": enriched, "ai_enriched": True, "proveedor": proveedor}
    return resultado
