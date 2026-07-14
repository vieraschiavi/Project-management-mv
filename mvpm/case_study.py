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


def narrar_caso(projects: pd.DataFrame | None = None, tasks: pd.DataFrame | None = None,
                 team: pd.DataFrame | None = None, proyecto_id: str | None = None) -> dict:
    proj_df = projects if projects is not None else demo_data.projects()
    task_df = tasks if tasks is not None else demo_data.tasks()
    team_df = team if team is not None else demo_data.team()

    pid = _elegir_proyecto(proj_df, task_df, team_df, proyecto_id)
    p = proj_df[proj_df["proyecto_id"] == pid].iloc[0]
    pt = task_df[task_df["proyecto_id"] == pid]

    cat = catalog.catalog(proj_df)
    c = cat[cat["proyecto_id"] == pid].iloc[0]
    h = health.project_health(proj_df, task_df, team_df)
    hp = h[h["proyecto_id"] == pid].iloc[0]

    bloqueos = dep_mod.bloqueos_activos(task_df)
    bloqueos_p = bloqueos[bloqueos["proyecto_id"] == pid]

    backlog = prioritizer.prioritized_backlog(proj_df, task_df).reset_index(drop=True)
    backlog["puesto"] = backlog.index + 1
    backlog_p = backlog[backlog["proyecto_id"] == pid]

    copiloto = copilot_mod.answer("¿Qué proyectos están en riesgo?", proj_df, task_df, team_df, use_ai=False)

    pasos = []

    pasos.append({
        "seccion": "Portafolio",
        "titulo": f"1. Así aparece '{p['nombre']}' en el catálogo",
        "texto": (
            f"Sponsor {p['sponsor'] or 'sin definir'}, dueño {p['dueno'] or 'sin asignar'}, "
            f"criticidad {p['criticidad']}. Presupuesto ${p['presupuesto']:,.0f}, ejecutado "
            f"${p['ejecutado']:,.0f} ({c['ejecucion_pct']}%)."
            + (" El catálogo ya lo marca como sobre presupuesto, sin que nadie tenga que revisarlo a mano."
               if bool(c["sobre_presupuesto"]) else "")
        ),
    })

    dims_bajas = sorted(
        [(k.replace("dim_", ""), v) for k, v in hp.items() if k.startswith("dim_")],
        key=lambda kv: kv[1],
    )[:2]
    pasos.append({
        "seccion": "Salud de proyecto",
        "titulo": f"2. El índice de salud explica por qué está '{hp['estado']}'",
        "texto": (
            f"Índice {hp['indice']}/100. Las dimensiones que más pesan son "
            + " y ".join(f"{nombre} ({valor}/100)" for nombre, valor in dims_bajas)
            + " — no es una alarma genérica, apunta directo a dónde está el problema."
        ),
    })

    if not bloqueos_p.empty:
        b = bloqueos_p.iloc[0]
        texto_dep = (
            f"'{b['titulo']}' ({b['tarea_id']}) está bloqueada y frena a "
            f"{b['tareas_impactadas']} tarea(s) más aguas abajo — el grafo de dependencias lo "
            f"detecta solo, no hace falta que alguien lo reporte en una reunión."
        )
    else:
        texto_dep = "Este proyecto no tiene tareas bloqueadas activas en este momento."
    pasos.append({"seccion": "Dependencias", "titulo": "3. Qué está frenando el avance", "texto": texto_dep})

    if not backlog_p.empty:
        top = backlog_p.iloc[0]
        dias = int(top["dias_restantes"])
        plazo = f"vencida hace {abs(dias)} días" if dias < 0 else f"vence en {dias} días"
        texto_backlog = (
            f"Su tarea más urgente ('{top['titulo']}') quedó en el puesto #{int(top['puesto'])} "
            f"de todo el backlog priorizado del portafolio ({plazo}) — el motor la subió solo por "
            f"combinar criticidad alta, vencimiento pasado e impacto en otras tareas, sin que "
            f"nadie la marque como 'urgente' a mano."
        )
    else:
        texto_backlog = "Este proyecto no tiene tareas pendientes en el backlog priorizado."
    pasos.append({"seccion": "Backlog priorizado", "titulo": "4. Dónde queda en la fila de prioridades", "texto": texto_backlog})

    pasos.append({
        "seccion": "Copiloto",
        "titulo": "5. Lo que responde el copiloto si le preguntás por proyectos en riesgo",
        "texto": copiloto["answer"],
    })

    pasos.append({
        "seccion": "Reportes",
        "titulo": "6. Qué le llega a dirección",
        "texto": (
            f"El reporte ejecutivo semanal incluye a '{p['nombre']}' entre los proyectos que "
            f"necesitan atención, con estos mismos números — no una versión suavizada para la "
            f"reunión."
        ),
    })

    return {"proyecto_id": pid, "nombre": p["nombre"], "indice": hp["indice"], "estado": hp["estado"], "pasos": pasos}
