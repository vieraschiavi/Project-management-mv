"""Catálogo único de proyectos: dueño, sponsor, criticidad, presupuesto vs. ejecutado."""

import pandas as pd

from . import demo_data


def catalog(projects: pd.DataFrame | None = None) -> pd.DataFrame:
    df = (projects if projects is not None else demo_data.projects()).copy()
    ejecucion = (df["ejecutado"] / df["presupuesto"] * 100).round(1)
    # presupuesto=0 (proyecto recién creado, sin cifra cargada todavía) da
    # división por cero — 0/0 y N/0 devuelven NaN/inf, no un % real. Se deja
    # como NaN explícito en vez de mostrar "nan%" o "inf%" en el dashboard.
    df["ejecucion_pct"] = ejecucion.replace([float("inf"), float("-inf")], float("nan"))
    df["sin_dueno"] = df["dueno"].isna()
    df["sobre_presupuesto"] = df["ejecutado"] > df["presupuesto"]
    return df


def kpis(projects: pd.DataFrame | None = None) -> dict:
    df = catalog(projects)
    ejecucion_validas = df["ejecucion_pct"].dropna()
    ejecucion_prom = float(ejecucion_validas.mean()) if not ejecucion_validas.empty else 0.0
    return {
        "proyectos_activos": int(len(df)),
        "presupuesto_total": float(df["presupuesto"].sum()),
        "ejecutado_total": float(df["ejecutado"].sum()),
        "ejecucion_pct_promedio": round(ejecucion_prom, 1),
        "sin_dueno": int(df["sin_dueno"].sum()),
        "sobre_presupuesto": int(df["sobre_presupuesto"].sum()),
    }


def por_portafolio(projects: pd.DataFrame | None = None) -> pd.DataFrame:
    df = catalog(projects)
    return (
        df.groupby("portafolio")
        .agg(proyectos=("proyecto_id", "count"),
             presupuesto=("presupuesto", "sum"),
             ejecutado=("ejecutado", "sum"))
        .reset_index()
    )
