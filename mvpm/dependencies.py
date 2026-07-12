"""Grafo de dependencias entre tareas: qué bloquea a qué, y simulación de impacto
si una tarea se atrasa. Grafo dirigido simple (tarea -> depende_de).
"""

from collections import defaultdict

import pandas as pd

from . import demo_data


def build_graph(tasks: pd.DataFrame | None = None) -> dict:
    df = tasks if tasks is not None else demo_data.tasks()
    downstream = defaultdict(list)  # quién depende de mí (se bloquea si yo me atraso)
    for _, row in df.iterrows():
        dep = row["depende_de"]
        if pd.notna(dep):
            downstream[dep].append(row["tarea_id"])
    return dict(downstream)


def orphan_dependencies(tasks: pd.DataFrame | None = None) -> pd.DataFrame:
    """Dependencias que apuntan a una tarea que no existe (dato inconsistente)."""
    df = tasks if tasks is not None else demo_data.tasks()
    ids = set(df["tarea_id"])
    deps = df[df["depende_de"].notna()]
    return deps[~deps["depende_de"].isin(ids)]


def impacto_si_se_atrasa(tarea_id: str, tasks: pd.DataFrame | None = None) -> list[str]:
    """Devuelve, recursivamente, todas las tareas que se bloquean si `tarea_id` se atrasa."""
    graph = build_graph(tasks)
    seen: list[str] = []
    stack = list(graph.get(tarea_id, []))
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.append(current)
        stack.extend(graph.get(current, []))
    return seen


def bloqueos_activos(tasks: pd.DataFrame | None = None) -> pd.DataFrame:
    df = tasks if tasks is not None else demo_data.tasks()
    blocked = df[df["estado"] == "blocked"].copy()
    blocked["tareas_impactadas"] = blocked["tarea_id"].apply(lambda t: len(impacto_si_se_atrasa(t, df)))
    return blocked.sort_values("tareas_impactadas", ascending=False)
