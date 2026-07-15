"""API REST local para conectar Power BI/Tableau/Looker u otra herramienta de
BI al mismo motor que usa el dashboard. Corre en la PC/servidor del cliente,
no expone datos fuera de la red local por defecto.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from mvpm import db, demo_pharma, exporters, licensing, reviews

app = FastAPI(title="MV Project Management API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

db.init_db()


def _tables():
    """Se recalcula en cada request (no se cachea): los datos son la base real
    del cliente, que cambia con cada proyecto/tarea que crea o edita desde el
    dashboard — servir una copia vieja rompería la integración de BI."""
    return exporters.portfolio_tables(db.projects(), db.tasks(), db.team())


@app.get("/")
def root():
    return {"app": "MV Project Management API", "status": "ok"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/{table}")
def get_table(table: str, format: str = "json"):
    tables = _tables()
    if table not in tables:
        raise HTTPException(status_code=404, detail=f"Tabla '{table}' no encontrada. Disponibles: {list(tables)}")
    df = tables[table]
    if format == "csv":
        return JSONResponse(content=df.to_csv(index=False), media_type="text/csv")
    return df.to_dict("records")


@app.get("/api/demo/pharma")
def demo_pharma_bi(format: str = "json"):
    """Ensayos clínicos reales (ClinicalTrials.gov) listos para Power BI /
    Tableau — es el endpoint al que apunta el archivo .pbids de la carpeta
    `distribucion/powerbi/`. Un ensayo por fila, con estado, fase, laboratorio
    y criticidad derivada. Dominio público (U.S. NLM / NIH)."""
    df = demo_pharma.tabla_para_bi()
    if format == "csv":
        return JSONResponse(content=df.to_csv(index=False), media_type="text/csv")
    return df.to_dict("records")


@app.get("/api/reviews/summary")
def reviews_summary():
    return reviews.summary()


@app.get("/licencias/planes")
def planes():
    """Planes públicos con su cupo mensual de consultas de IA — el motor de
    reglas (catálogo, salud, dependencias, backlog, políticas) no tiene cupo
    en ningún plan, incluido el demo."""
    return licensing.PLANES


@app.get("/licencias/estado")
def estado_licencia(token: str | None = None):
    """Estado de cupo de IA para el token dado (o del plan demo si no se
    manda token). Emitido por /api/verify-payment en Vercel tras un pago
    aprobado de MercadoPago."""
    payload = licensing.verify_license(token) if token else None
    if token and payload is None:
        raise HTTPException(status_code=401, detail="Token de licencia inválido.")
    plan = payload["plan"] if payload else "demo"
    email = payload["email"] if payload else "demo@local"
    puede, detalle = licensing.puede_usar_ia(token)
    return {
        "plan": plan,
        "email": email,
        "puede_usar_ia": puede,
        "detalle": detalle,
        "consultas_usadas_mes": licensing.consultas_usadas(email),
    }
