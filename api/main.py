# © 2026 Martín Viera. Todos los derechos reservados.
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

import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from mvpm import db, demo_pharma, exporters, licensing, owner, puertos, reviews

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

    Dos candados independientes, los dos tienen que abrir:

    1. Licencia/prueba — igual que el dashboard: el dueño entra siempre: sin
       eso, el reloj de 7 días. Va PRIMERO y sin excepción de loopback: es la
       instalación la que tiene o no tiene acceso, no la red desde la que se
       pregunta — antes esta API servía el portafolio completo para siempre
       aunque la prueba del dashboard ya hubiera vencido, porque nunca
       consultaba nada de licencias.

       El token sale de `licensing.token_guardado()`: el archivo que el
       dashboard escribe cuando el cliente pega su licencia. Este proceso no
       puede ver la sesión de Streamlit —es otro proceso—, y mientras el token
       vivió sólo ahí, un cliente que YA HABÍA PAGADO recibía 402 de esta API
       para siempre pasados los 7 días. Pagaba por los conectores de BI y no
       los podía usar, que es de las dos formas de fallar la peor: silenciosa
       y después de cobrar.

       `token_guardado()` devuelve None si el archivo no está o si dejó de
       verificar, así que esto no es una puerta nueva: sin licencia válida el
       402 sigue igual.

    2. Red — desde la propia máquina se permite sin clave (es el caso normal,
       Power BI y el dashboard corriendo al lado). Desde cualquier otra IP hay
       que presentar MVPM_API_KEY.
    """
    if not owner.es_owner():
        token = licensing.token_guardado()
        acceso = licensing.estado_acceso(token)
        if not acceso["acceso"]:
            raise HTTPException(status_code=402, detail=acceso["mensaje"])
        # Esta API ES la feature "integraciones" del plan: los .pbids de Power
        # BI y el exportador de Tableau consumen exactamente estos endpoints.
        # Durante la prueba de 7 días `tiene_feature` dice que sí a todo, así
        # que esto no le saca nada a nadie hoy; lo que hace es que el día que
        # se venda un plan sin integraciones, el plan lo signifique de verdad
        # en vez de ser una línea decorativa en una tabla de precios.
        if not licensing.tiene_feature(token, "integraciones"):
            raise HTTPException(
                status_code=402,
                detail="Tu plan no incluye los conectores de BI (integraciones). "
                       "El plan Professional sí los incluye.")

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

    La conversión vive en el motor (`exporters.registros_json`) porque el
    servidor MCP tiene que serializar exactamente igual que esta API.
    """
    return exporters.registros_json(df)


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


def solo_local(request: Request) -> None:
    """Sólo desde esta misma máquina. Sin licencia de por medio.

    Es la mitad de red de `requiere_acceso`, aislada para los endpoints que
    tienen que funcionar CON la prueba vencida. Sigue exigiendo MVPM_API_KEY
    desde otra IP: que un endpoint no mire la licencia no lo vuelve público.
    """
    host = (request.client.host if request.client else "") or ""
    if host in _LOOPBACK:
        return
    if not API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Esta API sólo atiende pedidos locales.")
    enviada = request.headers.get("x-api-key", "")
    if not enviada or not secrets.compare_digest(enviada, API_KEY):
        raise HTTPException(status_code=401, detail="Clave de API inválida o ausente.")


class ActivacionLicencia(BaseModel):
    token: str


@app.post("/licencias/activar", dependencies=[Depends(solo_local)])
def activar_licencia(cuerpo: ActivacionLicencia):
    """Guarda la licencia del cliente en esta instalación.

    Existe para la interfaz de escritorio (React): sin este endpoint, la única
    forma de cargar una licencia era el campo de texto de la barra lateral de
    Streamlit, y la versión .exe no tiene Streamlit.

    Va detrás de `solo_local` y NO de `requiere_acceso`, por el mismo motivo
    que el endpoint de abajo: pedir licencia para poder cargar la licencia es
    un candado sin llave adentro.
    """
    if licensing.verify_license(cuerpo.token) is None:
        raise HTTPException(status_code=400, detail="Token de licencia inválido.")
    if not licensing.guardar_token(cuerpo.token):
        raise HTTPException(
            status_code=507,
            detail="La licencia es válida pero no se pudo guardar en el disco.")
    return licensing.estado_acceso(licensing.token_guardado())


@app.delete("/licencias/activar", dependencies=[Depends(solo_local)])
def desactivar_licencia():
    """Borra la licencia guardada — para dejar limpia una máquina prestada."""
    return {"borrada": licensing.olvidar_token()}


@app.get("/licencias/acceso", dependencies=[Depends(solo_local)])
def acceso_actual():
    """Si esta instalación puede usar el programa, y por qué.

    Es lo PRIMERO que consulta la interfaz de escritorio al abrir: decide si
    muestra el portafolio o la pantalla de licencia. Por eso no puede estar
    detrás de `requiere_acceso` — un cliente con la prueba vencida recibiría
    402 acá también y la aplicación no tendría forma de decirle qué le pasa ni
    de ofrecerle cargar su licencia. Se quedaría en una pantalla de error sin
    salida, que es exactamente el momento en que estaba por pagar.

    No devuelve ningún dato del portafolio: sólo el estado del candado.
    """
    if owner.es_owner():
        return {**owner.estado_acceso(), "es_owner": True}
    return {**licensing.estado_acceso(licensing.token_guardado()), "es_owner": False}


@app.get("/licencias/estado", dependencies=[Depends(solo_local)])
def estado_licencia(token: str | None = None):
    """Estado de cupo de IA para el token dado (o del plan demo si no se
    manda token). Emitido por /api/verify-payment en Vercel tras un pago
    aprobado de MercadoPago.

    Antes estaba detrás de `requiere_acceso`: con la prueba vencida devolvía
    402, o sea que quien más necesitaba saber en qué estado estaba su licencia
    era justamente quien no lo podía consultar."""
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


def _dir_ui() -> str | None:
    """Carpeta con la interfaz de escritorio (React) ya empaquetada.

    La sirve ESTE servidor, en `/app`, a propósito: así la UI y la API quedan
    en el mismo origen. Las dos alternativas son peores — abrirla por `file://`
    obliga a aflojar CORS y a hardcodear el puerto, y servirla desde otro
    proceso duplica el arranque para nada.

    Orden: `MVPM_UI_DIR` primero, porque en el empaquetado de electron-builder
    la carpeta NO queda al lado de `api/`; la heurística relativa sirve para el
    repositorio y no para el `.exe` instalado, y el síntoma sería un 404 en
    `/app` recién después de instalar.

    Si no hay bundle no se monta nada y la API sigue igual para Power BI y
    Tableau, que es su trabajo principal.
    """
    candidatas = []
    env = os.environ.get("MVPM_UI_DIR", "").strip()
    if env:
        candidatas.append(Path(env))
    candidatas.append(Path(__file__).resolve().parent.parent / "desktop" / "ui" / "dist")
    for c in candidatas:
        if (c / "index.html").is_file():
            return str(c)
    return None


_UI = _dir_ui()
if _UI:
    from fastapi.staticfiles import StaticFiles

    # html=True hace que /app sirva index.html en la raíz de la carpeta.
    app.mount("/app", StaticFiles(directory=_UI, html=True), name="ui")
