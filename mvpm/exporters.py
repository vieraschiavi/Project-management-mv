"""Exportación uniforme a CSV/Excel/JSON — mismo dato para dashboard, API y BI."""

import io
import json

import pandas as pd

from . import catalog, demo_data, health, policies, prioritizer, reviews


def portfolio_tables(proj: pd.DataFrame | None = None, tasks: pd.DataFrame | None = None,
                      team: pd.DataFrame | None = None) -> dict:
    """Si no se pasan DataFrames, exporta los datos demo — pero el dashboard y
    la API le pasan siempre los datos reales de `mvpm/db.py` cuando existen,
    para que lo descargado sea lo mismo que ve el cliente, no la demo."""
    if proj is None:
        proj = demo_data.projects()
    if tasks is None:
        tasks = demo_data.tasks()
    if team is None:
        team = demo_data.team()
    return {
        "proyectos": catalog.catalog(proj),
        "tareas": tasks,
        "equipo": team,
        "salud": health.project_health(proj, tasks, team),
        "backlog_priorizado": prioritizer.prioritized_backlog(proj, tasks),
        "politicas": policies.evaluate(proj, tasks, team),
    }


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def to_json_bundle(proj: pd.DataFrame | None = None, tasks: pd.DataFrame | None = None,
                    team: pd.DataFrame | None = None) -> str:
    tables = portfolio_tables(proj, tasks, team)
    bundle = {name: df.to_dict("records") for name, df in tables.items()}
    bundle["resenas"] = reviews.summary()
    return json.dumps(bundle, ensure_ascii=False, indent=2, default=str)


def to_excel_bytes(proj: pd.DataFrame | None = None, tasks: pd.DataFrame | None = None,
                    team: pd.DataFrame | None = None) -> bytes:
    tables = portfolio_tables(proj, tasks, team)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for name, df in tables.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    return buf.getvalue()
