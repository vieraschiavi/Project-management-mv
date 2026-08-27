# © 2026 Martín Viera. Todos los derechos reservados.
"""Caso de uso completo: recorre las herramientas del programa sobre UN
proyecto real (o el más comprometido del portafolio, si no se elige uno),
para que alguien nuevo vea el flujo completo de punta a punta — no una
lista de features sueltas. Cada paso muestra el resultado real de correr el
motor, nunca un número inventado para la demo.
"""

import pandas as pd

from . import catalog, demo_data, dependencies as dep_mod, health, prioritizer
from . import copilot as copilot_mod


def _elegir_proyecto(proj_df: pd.DataFrame, task_df: pd.DataFrame, team_df: pd.DataFrame,
                      proyecto_id: str | None) -> str:
    if proyecto_id:
        return proyecto_id
    h = health.project_health(proj_df, task_df, team_df)
    if h.empty:
        raise ValueError("No hay proyectos para armar un caso de uso.")
    return h.sort_values("indice").iloc[0]["proyecto_id"]


_ESTADO_DISPLAY = {
    "saludable": {"es": "saludable", "en": "healthy", "pt": "saudável"},
    "observacion": {"es": "en observación", "en": "under watch", "pt": "em observação"},
    "riesgo": {"es": "en riesgo", "en": "at risk", "pt": "em risco"},
}
_DIM_DISPLAY = {
    "alcance": {"es": "Alcance", "en": "Scope", "pt": "Escopo"},
    "cronograma": {"es": "Cronograma", "en": "Schedule", "pt": "Cronograma"},
    "presupuesto": {"es": "Presupuesto", "en": "Budget", "pt": "Orçamento"},
    "riesgo": {"es": "Riesgo", "en": "Risk", "pt": "Risco"},
    "dependencias": {"es": "Dependencias", "en": "Dependencies", "pt": "Dependências"},
    "equipo": {"es": "Equipo", "en": "Team", "pt": "Equipe"},
}
_SIN_DEFINIR = {"es": "sin definir", "en": "not set", "pt": "não definido"}
_SIN_ASIGNAR = {"es": "sin asignar", "en": "unassigned", "pt": "não atribuído"}

# Plantillas de cada paso: seccion (clave nav_* de mvpm/i18n.py, sin
# traducirla acá — la resuelve quien llame T() con esa clave), titulo y texto
# por idioma. El contenido dinámico (números reales del motor) se interpola
# después con .format(), nunca traducido — son datos, no texto de producto.
_PASOS_TXT = {
    "es": {
        "portafolio_titulo": "1. Así aparece '{nombre}' en el catálogo",
        "portafolio_texto": ("Sponsor {sponsor}, dueño {dueno}, criticidad {criticidad}. "
                             "Presupuesto ${presupuesto:,.0f}, ejecutado ${ejecutado:,.0f} "
                             "({pct}%).{sobre}"),
        "portafolio_sobre": (" El catálogo ya lo marca como sobre presupuesto, sin que nadie "
                             "tenga que revisarlo a mano."),
        "salud_titulo": "2. El índice de salud explica por qué está '{estado}'",
        "salud_texto": ("Índice {indice}/100. Las dimensiones que más pesan son {dims} — no es "
                        "una alarma genérica, apunta directo a dónde está el problema."),
        "dep_titulo": "3. Qué está frenando el avance",
        "dep_bloqueada": ("'{titulo}' ({tarea_id}) está bloqueada y frena a {n} tarea(s) más "
                          "aguas abajo — el grafo de dependencias lo detecta solo, no hace "
                          "falta que alguien lo reporte en una reunión."),
        "dep_libre": "Este proyecto no tiene tareas bloqueadas activas en este momento.",
        "backlog_titulo": "4. Dónde queda en la fila de prioridades",
        "backlog_con": ("Su tarea más urgente ('{titulo}') quedó en el puesto #{puesto} de todo "
                        "el backlog priorizado del portafolio ({plazo}) — el motor la subió "
                        "solo por combinar criticidad alta, vencimiento pasado e impacto en "
                        "otras tareas, sin que nadie la marque como 'urgente' a mano."),
        "backlog_sin": "Este proyecto no tiene tareas pendientes en el backlog priorizado.",
        "backlog_vencida": "vencida hace {dias} días", "backlog_vence": "vence en {dias} días",
        "copiloto_titulo": "5. Lo que responde el copiloto si le preguntás por proyectos en riesgo",
        "reportes_titulo": "6. Qué le llega a dirección",
        "reportes_texto": ("El reporte ejecutivo semanal incluye a '{nombre}' entre los "
                           "proyectos que necesitan atención, con estos mismos números — no una "
                           "versión suavizada para la reunión."),
        "pregunta_riesgo": "¿Qué proyectos están en riesgo?",
    },
    "en": {
        "portafolio_titulo": "1. How '{nombre}' shows up in the catalog",
        "portafolio_texto": ("Sponsor {sponsor}, owner {dueno}, criticality {criticidad}. "
                             "Budget ${presupuesto:,.0f}, spent ${ejecutado:,.0f} ({pct}%).{sobre}"),
        "portafolio_sobre": (" The catalog already flags it as over budget, with no one having "
                             "to check by hand."),
        "salud_titulo": "2. The health index explains why it's '{estado}'",
        "salud_texto": ("Index {indice}/100. The heaviest-weighing dimensions are {dims} — it's "
                        "not a generic alarm, it points straight at where the problem is."),
        "dep_titulo": "3. What's holding progress back",
        "dep_bloqueada": ("'{titulo}' ({tarea_id}) is blocked and is holding back {n} more "
                          "downstream task(s) — the dependency graph detects it on its own, no "
                          "one has to report it in a meeting."),
        "dep_libre": "This project has no active blocked tasks right now.",
        "backlog_titulo": "4. Where it lands in the priority line",
        "backlog_con": ("Its most urgent task ('{titulo}') landed at spot #{puesto} of the "
                        "entire portfolio's prioritized backlog ({plazo}) — the engine bumped "
                        "it up on its own by combining high criticality, a past due date and "
                        "impact on other tasks, with no one flagging it 'urgent' by hand."),
        "backlog_sin": "This project has no pending tasks in the prioritized backlog.",
        "backlog_vencida": "overdue by {dias} day(s)", "backlog_vence": "due in {dias} day(s)",
        "copiloto_titulo": "5. What the copilot answers when asked about projects at risk",
        "reportes_titulo": "6. What reaches leadership",
        "reportes_texto": ("The weekly executive report includes '{nombre}' among the projects "
                           "that need attention, with these same numbers — not a softened "
                           "version for the meeting."),
        "pregunta_riesgo": "Which projects are at risk?",
    },
    "pt": {
        "portafolio_titulo": "1. Assim aparece '{nombre}' no catálogo",
        "portafolio_texto": ("Sponsor {sponsor}, responsável {dueno}, criticidade {criticidad}. "
                             "Orçamento ${presupuesto:,.0f}, executado ${ejecutado:,.0f} "
                             "({pct}%).{sobre}"),
        "portafolio_sobre": (" O catálogo já o marca como acima do orçamento, sem que ninguém "
                             "precise revisar à mão."),
        "salud_titulo": "2. O índice de saúde explica por que está '{estado}'",
        "salud_texto": ("Índice {indice}/100. As dimensões que mais pesam são {dims} — não é um "
                        "alarme genérico, aponta direto para onde está o problema."),
        "dep_titulo": "3. O que está travando o avanço",
        "dep_bloqueada": ("'{titulo}' ({tarea_id}) está bloqueada e trava {n} tarefa(s) a mais "
                          "rio abaixo — o grafo de dependências detecta sozinho, sem que "
                          "ninguém precise reportar em reunião."),
        "dep_libre": "Este projeto não tem tarefas bloqueadas ativas neste momento.",
        "backlog_titulo": "4. Onde fica na fila de prioridades",
        "backlog_con": ("Sua tarefa mais urgente ('{titulo}') ficou na posição #{puesto} de todo "
                        "o backlog priorizado do portfólio ({plazo}) — o motor a subiu sozinho "
                        "combinando criticidade alta, vencimento passado e impacto em outras "
                        "tarefas, sem que ninguém a marque como 'urgente' à mão."),
        "backlog_sin": "Este projeto não tem tarefas pendentes no backlog priorizado.",
        "backlog_vencida": "vencida há {dias} dia(s)", "backlog_vence": "vence em {dias} dia(s)",
        "copiloto_titulo": "5. O que o copiloto responde se você perguntar sobre projetos em risco",
        "reportes_titulo": "6. O que chega à diretoria",
        "reportes_texto": ("O relatório executivo semanal inclui '{nombre}' entre os projetos "
                           "que precisam de atenção, com estes mesmos números — não uma versão "
                           "suavizada para a reunião."),
        "pregunta_riesgo": "Quais projetos estão em risco?",
    },
}

# Nombre de la sección tal como se ve en pantalla (para que el paso quede
# etiquetado igual que el nav real) — mismo texto que mvpm/i18n.py nav_*.
_SECCION = {
    "es": {"portafolio": "Portafolio", "salud": "Salud de proyecto", "dependencias": "Dependencias",
          "backlog": "Backlog priorizado", "copiloto": "Copiloto", "reportes": "Reportes"},
    "en": {"portafolio": "Portfolio", "salud": "Project health", "dependencias": "Dependencies",
          "backlog": "Prioritized backlog", "copiloto": "Copilot", "reportes": "Reports"},
    "pt": {"portafolio": "Portfólio", "salud": "Saúde do projeto", "dependencias": "Dependências",
          "backlog": "Backlog priorizado", "copiloto": "Copiloto", "reportes": "Relatórios"},
}


def narrar_caso(projects: pd.DataFrame | None = None, tasks: pd.DataFrame | None = None,
                 team: pd.DataFrame | None = None, proyecto_id: str | None = None,
                 lang: str = "es") -> dict:
    lang = lang if lang in _PASOS_TXT else "es"
    tx, sec = _PASOS_TXT[lang], _SECCION[lang]
    proj_df = projects if projects is not None else demo_data.projects()
    task_df = tasks if tasks is not None else demo_data.tasks()
    team_df = team if team is not None else demo_data.team()

    pid = _elegir_proyecto(proj_df, task_df, team_df, proyecto_id)
    p = proj_df[proj_df["proyecto_id"] == pid].iloc[0]

    cat = catalog.catalog(proj_df)
    c = cat[cat["proyecto_id"] == pid].iloc[0]
    h = health.project_health(proj_df, task_df, team_df)
    hp = h[h["proyecto_id"] == pid].iloc[0]

    bloqueos = dep_mod.bloqueos_activos(task_df)
    bloqueos_p = bloqueos[bloqueos["proyecto_id"] == pid]

    backlog = prioritizer.prioritized_backlog(proj_df, task_df).reset_index(drop=True)
    backlog["puesto"] = backlog.index + 1
    backlog_p = backlog[backlog["proyecto_id"] == pid]

    copiloto = copilot_mod.answer(tx["pregunta_riesgo"], proj_df, task_df, team_df, use_ai=False)

    pasos = []

    pasos.append({
        "seccion": sec["portafolio"],
        "titulo": tx["portafolio_titulo"].format(nombre=p["nombre"]),
        "texto": tx["portafolio_texto"].format(
            sponsor=p["sponsor"] or _SIN_DEFINIR[lang], dueno=p["dueno"] or _SIN_ASIGNAR[lang],
            criticidad=p["criticidad"], presupuesto=p["presupuesto"], ejecutado=p["ejecutado"],
            pct=c["ejecucion_pct"],
            sobre=tx["portafolio_sobre"] if bool(c["sobre_presupuesto"]) else ""),
    })

    dims_bajas = sorted(
        [(k.replace("dim_", ""), v) for k, v in hp.items() if k.startswith("dim_")],
        key=lambda kv: kv[1],
    )[:2]
    dims_texto = " y ".join(
        f"{_DIM_DISPLAY.get(nombre, {}).get(lang, nombre)} ({valor}/100)" for nombre, valor in dims_bajas)
    pasos.append({
        "seccion": sec["salud"],
        "titulo": tx["salud_titulo"].format(estado=_ESTADO_DISPLAY.get(hp["estado"], {}).get(lang, hp["estado"])),
        "texto": tx["salud_texto"].format(indice=hp["indice"], dims=dims_texto),
    })

    if not bloqueos_p.empty:
        b = bloqueos_p.iloc[0]
        texto_dep = tx["dep_bloqueada"].format(titulo=b["titulo"], tarea_id=b["tarea_id"],
                                               n=b["tareas_impactadas"])
    else:
        texto_dep = tx["dep_libre"]
    pasos.append({"seccion": sec["dependencias"], "titulo": tx["dep_titulo"], "texto": texto_dep})

    if not backlog_p.empty:
        top = backlog_p.iloc[0]
        dias = int(top["dias_restantes"])
        plazo = (tx["backlog_vencida"].format(dias=abs(dias)) if dias < 0
                 else tx["backlog_vence"].format(dias=dias))
        texto_backlog = tx["backlog_con"].format(titulo=top["titulo"], puesto=int(top["puesto"]), plazo=plazo)
    else:
        texto_backlog = tx["backlog_sin"]
    pasos.append({"seccion": sec["backlog"], "titulo": tx["backlog_titulo"], "texto": texto_backlog})

    pasos.append({"seccion": sec["copiloto"], "titulo": tx["copiloto_titulo"], "texto": copiloto["answer"]})

    pasos.append({
        "seccion": sec["reportes"],
        "titulo": tx["reportes_titulo"],
        "texto": tx["reportes_texto"].format(nombre=p["nombre"]),
    })

    return {"proyecto_id": pid, "nombre": p["nombre"], "indice": hp["indice"], "estado": hp["estado"], "pasos": pasos}
