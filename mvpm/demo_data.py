"""Datos sintéticos deterministas para demo — con defectos inyectados a propósito
(tareas sin dueño, hitos vencidos, dependencias huérfanas) para que el motor de
salud tenga algo real que detectar. Ningún dato corresponde a una persona u
organización real.
"""

import random
from datetime import datetime, timedelta

import pandas as pd

_SEED = 42
_TODAY = datetime(2026, 7, 12)

_PORTFOLIOS = ["Producto Core", "Expansión LatAm", "Operaciones Internas"]
_SPONSORS = ["G. Suárez", "L. Fernández", "M. Casaravilla", "P. Bentancor"]
_SEGMENTS = ["Cliente externo", "Interno", "Regulatorio"]
_MEMBERS = [
    "A. Rodríguez", "B. Silva", "C. Pereyra", "D. Machado", "E. Cabrera",
    "F. Gómez", "G. Núñez", "H. Larrosa", "I. Techera", "J. Olivera",
]


def _rng():
    return random.Random(_SEED)


def projects() -> pd.DataFrame:
    rng = _rng()
    rows = []
    names = [
        "Migración de facturación", "Rediseño de onboarding", "Portal de clientes",
        "Integración ERP", "App móvil v2", "Automatización de soporte",
        "Panel de KPIs gerenciales", "Expansión Paraguay", "Expansión Chile",
        "Cumplimiento Ley 18.331", "Renovación de infraestructura", "Programa de referidos",
        "Rediseño de checkout", "Plan de capacitación interna", "Optimización de costos cloud",
        "Nuevo módulo de reportes", "Piloto de IA en soporte", "Alianza con partner regional",
        "Migración de CRM", "Auditoría de seguridad anual",
    ]
    for i, name in enumerate(names):
        start = _TODAY - timedelta(days=rng.randint(20, 220))
        due = start + timedelta(days=rng.randint(60, 260))
        budget = rng.choice([8000, 15000, 25000, 40000, 60000, 90000])
        spent_ratio = rng.uniform(0.15, 1.35)
        owner = rng.choice(_MEMBERS + [None, None])  # ~15% sin dueño (defecto a propósito)
        rows.append({
            "proyecto_id": f"PRJ-{i+1:03d}",
            "nombre": name,
            "portafolio": rng.choice(_PORTFOLIOS),
            "sponsor": rng.choice(_SPONSORS),
            "dueno": owner,
            "segmento": rng.choice(_SEGMENTS),
            "fecha_inicio": start.date().isoformat(),
            "fecha_fin": due.date().isoformat(),
            "presupuesto": budget,
            "ejecutado": round(budget * spent_ratio, 2),
            "criticidad": rng.choice(["Alta", "Media", "Baja"]),
        })
    return pd.DataFrame(rows)


def tasks() -> pd.DataFrame:
    rng = _rng()
    proj = projects()
    rows = []
    task_id = 1
    for _, p in proj.iterrows():
        n_tasks = rng.randint(6, 16)
        for _ in range(n_tasks):
            due = datetime.fromisoformat(p["fecha_fin"]) - timedelta(days=rng.randint(-30, 120))
            status = rng.choices(
                ["done", "in_progress", "blocked", "todo"],
                weights=[0.42, 0.28, 0.1, 0.2],
            )[0]
            assignee = rng.choice(_MEMBERS + [None])  # tareas huérfanas a propósito
            rows.append({
                "tarea_id": f"T-{task_id:04d}",
                "proyecto_id": p["proyecto_id"],
                "titulo": f"Tarea {task_id} — {p['nombre'][:24]}",
                "responsable": assignee,
                "estado": status,
                "vencimiento": due.date().isoformat(),
                "prioridad": rng.choice(["Alta", "Media", "Baja"]),
                "depende_de": None,
            })
            task_id += 1
    df = pd.DataFrame(rows)
    # Inyecta dependencias, incluida al menos una huérfana a propósito.
    rng2 = _rng()
    ids = df["tarea_id"].tolist()
    for i in range(len(df)):
        if rng2.random() < 0.22 and i > 0:
            df.at[i, "depende_de"] = rng2.choice(ids[max(0, i - 8):i] or [ids[0]])
    df.at[3, "depende_de"] = "T-9999"  # dependencia huérfana (defecto a propósito)
    return df


def team() -> pd.DataFrame:
    rng = _rng()
    rows = []
    for m in _MEMBERS:
        rows.append({
            "nombre": m,
            "rol": rng.choice(["PM", "Dev", "Diseño", "QA", "Datos"]),
            "capacidad_semanal_hs": rng.choice([20, 30, 40]),
            "carga_actual_hs": rng.randint(10, 46),
        })
    return pd.DataFrame(rows)
