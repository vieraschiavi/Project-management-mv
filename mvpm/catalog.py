"""Catálogo único de proyectos: dueño, sponsor, criticidad, presupuesto vs. ejecutado."""

import pandas as pd

from . import demo_data


def catalog(projects: pd.DataFrame | None = None) -> pd.DataFrame:
    df = (projects if projects is not None else demo_data.projects()).copy()
    df["ejecucion_pct"] = (df["ejecutado"] / df["presupuesto"] * 100).round(1)
    df["sin_dueno"] = df["dueno"].isna()
    df["sobre_presupuesto"] = df["ejecutado"] > df["presupuesto"]
    return df


def kpis(projects: pd.DataFrame | None = None) -> dict:
    df = catalog(projects)
    return {
        "proyectos_activos": int(len(df)),
        "presupuesto_total": float(df["presupuesto"].sum()),
        "ejecutado_total": float(df["ejecutado"].sum()),
        "ejecucion_pct_promedio": float(df["ejecucion_pct"].mean().round(1)),
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
