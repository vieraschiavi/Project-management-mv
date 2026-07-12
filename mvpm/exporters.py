"""Exportación uniforme a CSV/Excel/JSON — mismo dato para dashboard, API y BI."""

import io
import json

import pandas as pd

from . import catalog, demo_data, health, policies, prioritizer, reviews


def portfolio_tables() -> dict:
    proj = demo_data.projects()
    tasks = demo_data.tasks()
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


def to_json_bundle() -> str:
    tables = portfolio_tables()
    bundle = {name: df.to_dict("records") for name, df in tables.items()}
    bundle["resenas"] = reviews.summary()
    return json.dumps(bundle, ensure_ascii=False, indent=2, default=str)


def to_excel_bytes() -> bytes:
    tables = portfolio_tables()
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for name, df in tables.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    return buf.getvalue()
