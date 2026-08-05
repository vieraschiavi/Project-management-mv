"""API REST local para conectar Power BI/Tableau/Looker u otra herramienta de
BI al mismo motor que usa el dashboard. Corre en la PC/servidor del cliente.

Seguridad — esta API sirve el portafolio COMPLETO del cliente (proyectos,
presupuestos, equipo), así que por defecto es de uso local:

* `run.sh api` la levanta escuchando en 127.0.0.1 (sólo esta máquina).
* Para que la consuma un Power BI en OTRA máquina hay que abrirla a propósito
  con MVPM_API_HOST=0.0.0.0, y en ese caso se EXIGE una clave (MVPM_API_KEY):
  sin clave, la API se niega a servir datos fuera de loopback en vez de
  quedar abierta a toda la red.
* La clave se manda en el header `X-API-Key` (Power BI: Origen de datos web →
  Avanzadas → encabezado).
"""

import math
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from mvpm import db, demo_pharma, exporters, licensing, puertos, reviews

app = FastAPI(title="MV Project Management API", version="0.1.0")

API_KEY = os.environ.get("MVPM_API_KEY") or ""
# Orígenes permitidos para CORS. Antes era "*", lo que dejaba que cualquier
# página web que la víctima tuviera abierta leyera su portafolio entero desde
# el navegador. Por defecto ahora sólo se permite el propio host local; se
# amplía con MVPM_API_ORIGINS (lista separada por comas) si hace falta.
#
# Los puertos por defecto salen de mvpm/puertos.py y no están escritos a mano.
# Estaban: la lista decía 8501, que es exactamente el puerto que el dashboard
# YA NO usa —puertos.py lo excluye a propósito por ser el default de Streamlit
# y el más disputado—. O sea que el único origen permitido era uno donde la app
# nunca escucha, y cualquier pedido del dashboard real moría en el navegador
# por CORS sin que nada lo dijera.
_origins_env = os.environ.get("MVPM_API_ORIGINS", "").strip()
ALLOWED_ORIGINS = ([o.strip() for o in _origins_env.split(",") if o.strip()]
                   if _origins_env else
                   [f"http://{host}:{puerto}"
                    for puerto in puertos.PUERTOS_PREFERIDOS
                    for host in ("localhost", "127.0.0.1")])

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)

_LOOPBACK = {"127.0.0.1", "::1", "localhost", "testclient"}


def requiere_acceso(request: Request) -> None:
    """Autorización de los endpoints que exponen datos del cliente.

    Se aplica en CADA endpoint de datos, no sólo en el arranque: el chequeo
    tiene que estar donde se sirve el dato, porque el mismo `app` lo puede
    levantar cualquiera (uvicorn a mano, un test, un import) sin pasar por
    run.sh.

    Regla: desde la propia máquina se permite sin clave (es el caso normal,
    Power BI y el dashboard corriendo al lado). Desde cualquier otra IP hay
    que presentar MVPM_API_KEY.
    """
    host = (request.client.host if request.client else "") or ""
    if host in _LOOPBACK:
        return
    if not API_KEY:
        raise HTTPException(
            status_code=403,
            detail=("Esta API sólo atiende pedidos locales. Para consultarla desde "
                    "otra máquina, configurá la variable de entorno MVPM_API_KEY "
                    "en el servidor y mandá esa clave en el header X-API-Key."),
        )
    enviada = request.headers.get("x-api-key", "")
    # compare_digest evita filtrar la clave por diferencia de tiempos.
    if not enviada or not secrets.compare_digest(enviada, API_KEY):
        raise HTTPException(status_code=401, detail="Clave de API inválida o ausente (header X-API-Key).")


db.init_db()


def _tables():
    """Se recalcula en cada request (no se cachea): los datos son la base real
    del cliente, que cambia con cada proyecto/tarea que crea o edita desde el
    dashboard — servir una copia vieja rompería la integración de BI."""
    return exporters.portfolio_tables(db.projects(), db.tasks(), db.team())


def _registros(df):
    """DataFrame -> lista de dicts serializable a JSON.

    NaN e infinito no son JSON válido: `json.dumps` los rechaza y el endpoint
    respondía 500. Y no es un caso raro — un proyecto recién creado, sin
    presupuesto cargado todavía, da ejecucion_pct = NaN (catalog.py lo deja
    así a propósito, para no mostrar "inf%"). O sea que al primer proyecto que
    cargaba el cliente se le caía la conexión de Power BI.

    Se convierten a null, que es como se representa "sin dato" en JSON y lo
    que las herramientas de BI esperan para una celda vacía.

    Se recorre el resultado en vez de usar `df.where(notna, None)`: sobre una
    columna float, pandas mantiene el dtype y vuelve a convertir ese None en
    NaN, así que el reemplazo por DataFrame no sirve para este caso.
    """
    registros = df.to_dict("records")
    for fila in registros:
        for clave, valor in fila.items():
            if isinstance(valor, float) and not math.isfinite(valor):
                fila[clave] = None
    return registros


def _csv(df):
    """DataFrame -> CSV crudo (`?format=csv`).

    Iba por JSONResponse, que serializa el texto COMO JSON: la respuesta salía
    entre comillas y con los saltos de línea escapados (`\\n` literal), pero
    rotulada `text/csv`. O sea que Tableau/Excel/pandas leían una sola columna
    gigante y cero filas — el formato que el README ofrece para "si tu
    herramienta prefiere CSV" no servía para ninguna herramienta.

    PlainTextResponse manda el texto tal cual, que es lo que un parser de CSV
    espera.
    """
    return PlainTextResponse(content=df.to_csv(index=False), media_type="text/csv")


@app.get("/")
def root():
    return {"app": "MV Project Management API", "status": "ok"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/{table}", dependencies=[Depends(requiere_acceso)])
def get_table(table: str, format: str = "json"):
    tables = _tables()
    if table not in tables:
        raise HTTPException(status_code=404, detail=f"Tabla '{table}' no encontrada. Disponibles: {list(tables)}")
    df = tables[table]
    if format == "csv":
        return _csv(df)
    return _registros(df)


@app.get("/api/demo/pharma", dependencies=[Depends(requiere_acceso)])
def demo_pharma_bi(format: str = "json"):
    """Ensayos clínicos reales (ClinicalTrials.gov) listos para Power BI /
    Tableau — es el endpoint al que apunta el archivo .pbids de la carpeta
    `distribucion/powerbi/`. Un ensayo por fila, con estado, fase, laboratorio
    y criticidad derivada. Dominio público (U.S. NLM / NIH)."""
    df = demo_pharma.tabla_para_bi()
    if format == "csv":
        return _csv(df)
    return _registros(df)


@app.get("/api/reviews/summary", dependencies=[Depends(requiere_acceso)])
def reviews_summary():
    return reviews.summary()


@app.get("/licencias/planes")
def planes():
    """Planes públicos con su cupo mensual de consultas de IA — el motor de
    reglas (catálogo, salud, dependencias, backlog, políticas) no tiene cupo
    en ningún plan, incluido el demo."""
    return licensing.PLANES


@app.get("/licencias/estado", dependencies=[Depends(requiere_acceso)])
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
