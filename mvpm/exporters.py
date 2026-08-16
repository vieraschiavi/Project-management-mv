# © 2026 Martín Viera. Todos los derechos reservados.
"""Exportación uniforme a CSV/Excel/JSON — mismo dato para dashboard, API y BI."""

import datetime
import io
import json
import math

import pandas as pd

from . import catalog, demo_data, health, policies, prioritizer, reviews


def registros_json(df: pd.DataFrame) -> list[dict]:
    """DataFrame -> lista de dicts que `json.dumps` acepta sin romperse.

    NaN e infinito no son JSON válido. Y no es un caso raro: un proyecto recién
    creado, sin presupuesto cargado, da `ejecucion_pct = NaN` (catalog.py lo
    deja así a propósito para no mostrar "inf%"). Se convierten a null, que es
    como se representa "sin dato" en JSON y lo que las herramientas de BI
    esperan para una celda vacía.

    Se recorre el resultado en vez de usar `df.where(notna, None)`: sobre una
    columna float pandas mantiene el dtype y vuelve a convertir ese None en
    NaN, así que el reemplazo por DataFrame no sirve para este caso.

    Vive en el motor porque hoy lo necesitan dos consumidores —la API REST y el
    servidor MCP— y los dos tienen que serializar igual: si uno arregla los NaN
    y el otro no, la misma tabla se rompe según por dónde se la pida.

    Además de los NaN se normalizan los tipos que pandas devuelve y que
    `json.dumps` rechaza: escalares de numpy (`int64`, `bool_`) y fechas
    (`Timestamp`). Las tablas de la demo hoy salen con tipos nativos, pero una
    cargada desde Excel con `mvpm/importer.py` trae `Timestamp` en las columnas
    de fecha — sin esto, esa instalación rompe el endpoint en vez de la demo,
    que es justo el caso que nadie prueba antes de entregar.
    """
    registros = df.to_dict("records")
    for fila in registros:
        for clave, valor in fila.items():
            fila[clave] = _valor_json(valor)
    return registros


def _valor_json(valor):
    """Un valor de celda -> algo que `json.dumps` acepta."""
    if valor is None or valor is pd.NaT:
        # NaT NO es instancia de Timestamp (es su propio tipo), así que si no
        # se lo nombra acá se escapa de todos los chequeos de abajo.
        return None
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, float) and not math.isfinite(valor):
        return None
    if isinstance(valor, (pd.Timestamp, datetime.datetime, datetime.date)):
        return valor.isoformat()
    if type(valor).__module__ == "numpy" and hasattr(valor, "item"):
        nativo = valor.item()
        if isinstance(nativo, float) and not math.isfinite(nativo):
            return None
        return nativo
    return valor


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
