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

from mvpm import exporters, reviews

app = FastAPI(title="MV Project Management API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

_TABLES = None


def _tables():
    global _TABLES
    if _TABLES is None:
        _TABLES = exporters.portfolio_tables()
    return _TABLES


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


@app.get("/api/reviews/summary")
def reviews_summary():
    return reviews.summary()
