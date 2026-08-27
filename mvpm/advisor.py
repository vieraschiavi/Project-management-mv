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
    "es": {
        "bloqueo": "Desbloqueá '{titulo}' antes que nada: frena a {impacto} tarea(s) más — "
                   "confirmá con el responsable qué falta para destrabarla.",
        "dependencia_huerfana": "'{titulo}' depende de una tarea que ya no existe — corregí o "
                                "quitá esa dependencia desde la ficha de la tarea para que el "
                                "backlog no se distorsione.",
        "proyecto_en_riesgo": "'{titulo}' está en riesgo (índice {indice}/100) — pedile a su "
                              "dueño un plan de acción esta semana, como marca el glosario "
                              "compartido.",
        "sobre_presupuesto": "'{titulo}' ya ejecutó más presupuesto del asignado — revisá con "
                             "finanzas si corresponde ampliar la partida o frenar gasto.",
        "sobrecarga_equipo": "{titulo} está por encima de su capacidad semanal declarada — "
                             "redistribuí alguna tarea activa antes de sumarle más.",
        "politica_incumplida": "'{titulo}' no cumple la política de gestión — revisá la "
                               "evidencia y corregí lo que falta para que deje de aparecer acá.",
    },
    "en": {
        "bloqueo": "Unblock '{titulo}' first: it's holding back {impacto} more task(s) — check "
                   "with the assignee what's needed to clear it.",
        "dependencia_huerfana": "'{titulo}' depends on a task that no longer exists — fix or "
                                "remove that dependency from the task's record so the backlog "
                                "isn't distorted.",
        "proyecto_en_riesgo": "'{titulo}' is at risk (index {indice}/100) — ask its owner for an "
                              "action plan this week, as the shared glossary calls for.",
        "sobre_presupuesto": "'{titulo}' has already spent more than its assigned budget — check "
                             "with finance whether to expand the allocation or cut spending.",
        "sobrecarga_equipo": "{titulo} is above their declared weekly capacity — redistribute "
                             "an active task before adding more.",
        "politica_incumplida": "'{titulo}' doesn't meet the management policy — review the "
                               "evidence and fix what's missing so it stops showing up here.",
    },
    "pt": {
        "bloqueo": "Desbloqueie '{titulo}' antes de tudo: trava {impacto} tarefa(s) a mais — "
                   "confirme com o responsável o que falta para destravá-la.",
        "dependencia_huerfana": "'{titulo}' depende de uma tarefa que já não existe — corrija ou "
                                "remova essa dependência na ficha da tarefa para o backlog não "
                                "distorcer.",
        "proyecto_en_riesgo": "'{titulo}' está em risco (índice {indice}/100) — peça ao "
                              "responsável um plano de ação esta semana, como marca o glossário "
                              "compartilhado.",
        "sobre_presupuesto": "'{titulo}' já executou mais orçamento do que o atribuído — revise "
                             "com o financeiro se é o caso de ampliar a verba ou cortar gastos.",
        "sobrecarga_equipo": "{titulo} está acima da capacidade semanal declarada — redistribua "
                             "alguma tarefa ativa antes de somar mais.",
        "politica_incumplida": "'{titulo}' não cumpre a política de gestão — revise a evidência "
                               "e corrija o que falta para deixar de aparecer aqui.",
    },
}


def detectar_problemas(projects: pd.DataFrame, tasks: pd.DataFrame, team: pd.DataFrame,
                       lang: str = "es") -> list[dict]:
    """Cada problema tiene un id estable ('tipo:entidad') para poder
    persistir su seguimiento sin duplicarlo si se vuelve a detectar."""
    lang = lang if lang in _SUGERENCIAS else "es"
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

    pol = policies.evaluate(projects, tasks, team, lang=lang)
    for _, r in pol[pol["estado"] != "cumple"].iterrows():
        # El id usa "clave" (estable, no cambia con el idioma) — no "politica"
        # (el nombre ya traducido): si usara el nombre, cambiar de idioma
        # crearía un seguimiento nuevo para el MISMO incumplimiento en vez de
        # seguir el que ya existía.
        problemas.append({
            "id": f"politica_incumplida:{r['clave']}", "tipo": "politica_incumplida",
            "titulo": r["politica"], "severidad": "baja", "contexto": {},
        })

    return problemas


def _texto_base(problema: dict, lang: str = "es") -> str:
    lang = lang if lang in _SUGERENCIAS else "es"
    return _SUGERENCIAS[lang][problema["tipo"]].format(titulo=problema["titulo"], **problema["contexto"])


# El pedido de redacción es idéntico para todos los proveedores: lo único que
# cambiaba entre las tres versiones que había acá era el dialecto del SDK, y de
# eso ahora se encarga ai.completar(). La instrucción de no inventar cifras va
# en el mensaje de sistema, no como sugerencia: es la regla de honestidad de
# datos del producto aplicada a la capa de IA. `lang` decide en qué idioma se
# le pide a la IA que redacte — antes siempre le pedía español.
_SISTEMA = {
    "es": "Redactás en español rioplatense, tono directo y profesional. "
          "Nunca agregues cifras que no estén en el texto base.",
    "en": "You write in professional, direct English. "
          "Never add figures that aren't already in the base text.",
    "pt": "Você escreve em português (Brasil), tom direto e profissional. "
          "Nunca adicione números que não estejam no texto base.",
}

_PEDIDO = {
    "es": "Sugerencia del motor de reglas: {texto}\n"
          "Redactala en 1-2 frases más naturales, sin inventar números nuevos.",
    "en": "Rules-engine suggestion: {texto}\n"
          "Rewrite it in 1-2 more natural sentences, without inventing new numbers.",
    "pt": "Sugestão do motor de regras: {texto}\n"
          "Redija em 1-2 frases mais naturais, sem inventar números novos.",
}

# Se derivan de la capa genérica para que agregar un proveedor allá alcance:
# antes este módulo tenía su propia lista y su propia implementación por
# proveedor, y cualquier alta había que hacerla dos veces.
_PROVEEDORES = dict(ai._ENV_KEYS)


def _enriquecer(texto: str, proveedor: str, lang: str = "es") -> str | None:
    sistema = _SISTEMA.get(lang, _SISTEMA["es"])
    pedido = _PEDIDO.get(lang, _PEDIDO["es"]).format(texto=texto)
    return ai.completar(sistema, pedido, proveedor, max_tokens=200)


def proveedores_disponibles() -> list[str]:
    """Sólo lista proveedores con su clave configurada — nunca se ofrece uno
    que vaya a fallar en silencio.

    Más laxo que `ai.proveedores_disponibles()`, que además exige tener un
    modelo resuelto: acá alcanza con la clave porque si falta el modelo la
    sugerencia igual sale del motor de reglas, que es el comportamiento
    correcto y no un error."""
    return [nombre for nombre, env_key in _PROVEEDORES.items() if os.environ.get(env_key)]


def sugerir(problema: dict, proveedor: str | None = None, lang: str = "es") -> dict:
    """Devuelve {sugerencia, ai_enriched, proveedor}. El motor de reglas
    responde siempre — la IA es una capa de redacción opcional que nunca
    reemplaza el texto base si no está disponible o falla.

    El modelo lo decide `mvpm/modelos.py` (lo elegido en Configuración, o la
    variable de entorno del proveedor). `lang` decide el idioma tanto del
    texto base como, si corresponde, de la redacción con IA."""
    base = _texto_base(problema, lang)
    resultado = {"sugerencia": base, "ai_enriched": False, "proveedor": None}
    if proveedor and proveedor in _PROVEEDORES:
        if os.environ.get(_PROVEEDORES[proveedor]):
            enriched = _enriquecer(base, proveedor, lang)
            if enriched:
                resultado = {"sugerencia": enriched, "ai_enriched": True, "proveedor": proveedor}
    return resultado
