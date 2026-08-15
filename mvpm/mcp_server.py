# © 2026 Martín Viera. Todos los derechos reservados.
"""Servidor MCP del portafolio — expone el motor a Claude y a cualquier agente.

Es la tercera boca del MISMO motor, al lado del dashboard (`app/app.py`) y de
la API REST para BI (`api/main.py`): las tres leen `mvpm/`, ninguna recalcula
nada por su cuenta. Un agente conectado acá puede preguntar "¿qué proyectos
están en rojo y por qué?" y recibir los números que el reloj de salud ya
calculó, en vez de inventarlos leyendo el código.

Se habla MCP sobre stdio (JSON-RPC 2.0, un mensaje por línea). Se implementa
con la biblioteca estándar en vez del SDK oficial de MCP a propósito:

* El motor tiene que poder importarse y testearse sin dependencias nuevas —es
  regla del repo—, y el SDK arrastra su propio stack.
* El paquete portable y el build de PyInstaller cargan con cada dependencia que
  se agrega.
* La parte del protocolo que este servidor necesita (`initialize`,
  `tools/list`, `tools/call`, `ping`) son unas pocas decenas de líneas, y
  `tests/test_mcp_server.py` las verifica hablando el protocolo de verdad
  contra el proceso, no simulándolo.

TODAS las herramientas son de sólo lectura: no hay ninguna que escriba, borre
ni modifique datos del cliente. Un agente conectado acá no puede tocar el
portafolio, sólo consultarlo.

Se levanta solo (lo hace el cliente MCP):

    python -m mvpm.mcp_server
"""

from __future__ import annotations

import json
import sys
import traceback

# El motor se importa ACÁ y no adentro de cada herramienta a propósito. Con
# imports perezosos, un cliente MCP que arranque este servidor con el Python
# equivocado (el del sistema, sin pandas) lo ve conectar bien y recién falla
# cuando el agente llama una herramienta, con un ModuleNotFoundError adentro de
# la respuesta. Importando arriba, ese caso muere en el arranque y el cliente
# muestra el servidor como caído, que es la verdad.
from mvpm import (catalog, db, dependencies, exporters, glossary, health,
                  policies, prioritizer)

# Versiones del protocolo que este servidor sabe hablar. Se responde con la que
# pidió el cliente si está acá; si pide una desconocida se contesta la propia y
# el cliente decide, que es lo que manda la especificación.
VERSIONES = ("2025-06-18", "2025-03-26", "2024-11-05")
VERSION_POR_DEFECTO = VERSIONES[0]

LIMITE_POR_DEFECTO = 50
LIMITE_MAXIMO = 500


# --------------------------------------------------------------------------
# Datos: exactamente la misma fuente que la API REST
# --------------------------------------------------------------------------

def _tablas() -> dict:
    """Las tablas del portafolio, recalculadas en cada llamada.

    No se cachean por la misma razón que en `api/main.py`: son los datos vivos
    del cliente y cambian con cada tarea que edita en el dashboard. Un agente
    que lee una copia vieja da consejos sobre un portafolio que ya no existe.
    """
    db.init_db()
    return exporters.portfolio_tables(db.projects(), db.tasks(), db.team())


def _recorte(df, limite: int, orden: str | None = None, descendente: bool = False):
    """Ordena y recorta, y dice cuánto quedó afuera.

    El recorte es obligatorio: `tareas` tiene 211 filas en la demo sola y
    devolverlas enteras en cada consulta llena la ventana de contexto del
    agente con datos que no pidió.
    """
    total = len(df)
    if orden:
        if orden not in df.columns:
            raise _ErrorDeUso(
                f"No existe la columna '{orden}'. Columnas: {list(df.columns)}")
        df = df.sort_values(orden, ascending=not descendente, kind="stable")
    limite = max(1, min(int(limite), LIMITE_MAXIMO))
    recortado = df.head(limite)
    return {
        "filas_totales": total,
        "filas_devueltas": len(recortado),
        "truncado": total > len(recortado),
        "columnas": list(df.columns),
        "datos": exporters.registros_json(recortado),
    }


def _aviso_si_vacio() -> str | None:
    """Aviso cuando la instalación todavía no tiene datos.

    La base arranca vacía a propósito: el dashboard le ofrece al usuario cargar
    el portafolio de ejemplo, y hasta que no lo haga no hay nada. Sin este
    aviso, un agente que pregunta por la salud recibe `indice_general: 0` y
    concluye que el portafolio está en cero, cuando lo que pasa es que no hay
    portafolio. Se avisa en vez de rellenar con la demo: inventar datos que el
    cliente no cargó es exactamente lo que este producto promete no hacer.
    """
    db.init_db()
    if db.projects().empty and db.tasks().empty:
        return ("Esta instalación todavía no tiene proyectos ni tareas cargados, "
                "así que los números vienen en cero: no es un portafolio en mal "
                "estado, es uno vacío. Se cargan desde el dashboard con "
                "'Cargar datos de ejemplo para explorar', o importando los "
                "propios.")
    return None


class _ErrorDeUso(Exception):
    """El agente llamó mal a la herramienta. Se le devuelve el motivo para que
    corrija, en vez de un stack trace que no le sirve."""


# --------------------------------------------------------------------------
# Herramientas
# --------------------------------------------------------------------------

def _listar_tablas() -> dict:
    tablas = _tablas()
    return {"tablas": [
        {"nombre": n, "filas": len(df), "columnas": list(df.columns)}
        for n, df in tablas.items()
    ]}


def _consultar_tabla(tabla: str, limite: int = LIMITE_POR_DEFECTO,
                     orden: str | None = None, descendente: bool = False,
                     filtro_columna: str | None = None,
                     filtro_valor: str | None = None) -> dict:
    tablas = _tablas()
    if tabla not in tablas:
        raise _ErrorDeUso(
            f"No existe la tabla '{tabla}'. Disponibles: {list(tablas)}")
    df = tablas[tabla]
    if filtro_columna:
        if filtro_columna not in df.columns:
            raise _ErrorDeUso(
                f"No existe la columna '{filtro_columna}' en '{tabla}'. "
                f"Columnas: {list(df.columns)}")
        if filtro_valor is None:
            raise _ErrorDeUso("filtro_columna necesita también filtro_valor.")
        # Coincidencia por texto y sin distinguir mayúsculas: el agente escribe
        # "En riesgo" o "en riesgo" indistintamente y las dos tienen que andar.
        serie = df[filtro_columna].astype(str).str.lower()
        df = df[serie.str.contains(str(filtro_valor).lower(), regex=False, na=False)]
    return _recorte(df, limite, orden, descendente)


def _salud_portafolio() -> dict:
    db.init_db()
    proyectos, tareas, equipo = db.projects(), db.tasks(), db.team()
    detalle = health.project_health(proyectos, tareas, equipo)
    # `matriz_por_dimension` devuelve una fila POR PROYECTO, igual que
    # `project_health`: incluirla entera sería mandar las mismas filas dos
    # veces con otro nombre. Lo que no está en ningún lado y es lo que un
    # agente necesita para responder "¿qué dimensión arrastra al portafolio?"
    # es el promedio de cada dimensión, así que se calcula acá.
    matriz = health.matriz_por_dimension(proyectos, tareas, equipo)
    columnas_dim = [c for c in matriz.columns if c.startswith("dim_")]
    promedios = ({c: round(float(matriz[c].mean()), 1) for c in columnas_dim}
                 if not matriz.empty else {})
    return {
        "indice_general": round(float(health.overall_index(proyectos, tareas, equipo)), 2),
        "promedio_por_dimension": promedios,
        "peor_dimension": min(promedios, key=promedios.get) if promedios else None,
        "por_proyecto": exporters.registros_json(detalle),
    }


def _bloqueos_y_dependencias(limite: int = LIMITE_POR_DEFECTO) -> dict:
    db.init_db()
    tareas = db.tasks()
    bloqueos = dependencies.bloqueos_activos(tareas)
    huerfanas = dependencies.orphan_dependencies(tareas)
    return {
        "bloqueos_activos": _recorte(bloqueos, limite),
        # Dependencias que apuntan a una tarea que no existe: son un defecto de
        # datos, no un bloqueo real, y por eso van separadas.
        "dependencias_huerfanas": _recorte(huerfanas, limite),
    }


def _impacto_si_se_atrasa(tarea_id: str) -> dict:
    db.init_db()
    afectadas = dependencies.impacto_si_se_atrasa(tarea_id, db.tasks())
    return {
        "tarea": tarea_id,
        "tareas_afectadas": afectadas,
        "cantidad": len(afectadas),
    }


def _backlog_priorizado(limite: int = 10) -> dict:
    db.init_db()
    backlog = prioritizer.prioritized_backlog(db.projects(), db.tasks())
    return _recorte(backlog, limite)


def _politicas(solo_incumplidas: bool = True) -> dict:
    db.init_db()
    df = policies.evaluate(db.projects(), db.tasks(), db.team())
    if solo_incumplidas and "cumple" in df.columns:
        df = df[~df["cumple"].astype(bool)]
    return _recorte(df, LIMITE_MAXIMO)


def _kpis() -> dict:
    db.init_db()
    crudos = catalog.kpis(db.projects())
    return {k: exporters._valor_json(v) for k, v in crudos.items()}


def _glosario(termino: str | None = None) -> dict:
    df = glossary.glossary()
    if termino:
        mascara = False
        for col in df.columns:
            mascara = mascara | df[col].astype(str).str.lower().str.contains(
                termino.lower(), regex=False, na=False)
        df = df[mascara]
    return _recorte(df, LIMITE_MAXIMO)


HERRAMIENTAS = [
    {
        "name": "listar_tablas",
        "lee_portafolio": True,
        "description": (
            "Lista las tablas del portafolio disponibles, con su cantidad de "
            "filas y sus columnas. Usala primero para saber qué se puede "
            "consultar y con qué nombre exacto."),
        "inputSchema": {"type": "object", "properties": {}},
        "fn": lambda **kw: _listar_tablas(),
    },
    {
        "name": "consultar_tabla",
        "lee_portafolio": True,
        "description": (
            "Devuelve filas de una tabla del portafolio (proyectos, tareas, "
            "equipo, salud, backlog_priorizado, politicas), con orden y filtro "
            "opcionales. El resultado viene recortado: mirá 'truncado' y "
            "'filas_totales' antes de sacar conclusiones sobre el total."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "tabla": {"type": "string",
                          "description": "Nombre exacto, de listar_tablas."},
                "limite": {"type": "integer",
                           "description": f"Filas a devolver (máx. {LIMITE_MAXIMO}).",
                           "default": LIMITE_POR_DEFECTO},
                "orden": {"type": "string", "description": "Columna por la que ordenar."},
                "descendente": {"type": "boolean", "default": False},
                "filtro_columna": {"type": "string"},
                "filtro_valor": {"type": "string",
                                 "description": "Subcadena, sin distinguir mayúsculas."},
            },
            "required": ["tabla"],
        },
        "fn": _consultar_tabla,
    },
    {
        "name": "salud_portafolio",
        "lee_portafolio": True,
        "description": (
            "Salud del portafolio en las 6 dimensiones (cronograma, "
            "presupuesto, riesgo, dependencias, alcance y equipo): índice "
            "general, promedio por dimensión y detalle por proyecto. Es el "
            "cálculo del motor, no una estimación."),
        "inputSchema": {"type": "object", "properties": {}},
        "fn": lambda **kw: _salud_portafolio(),
    },
    {
        "name": "bloqueos_y_dependencias",
        "lee_portafolio": True,
        "description": (
            "Bloqueos activos (tareas frenadas por otra sin terminar) y "
            "dependencias huérfanas (que apuntan a una tarea inexistente, o "
            "sea un defecto de datos). Usala para responder qué está frenado "
            "y por culpa de qué."),
        "inputSchema": {
            "type": "object",
            "properties": {"limite": {"type": "integer", "default": LIMITE_POR_DEFECTO}},
        },
        "fn": _bloqueos_y_dependencias,
    },
    {
        "name": "impacto_si_se_atrasa",
        "lee_portafolio": True,
        "description": (
            "Dada una tarea, devuelve todas las que se caen en cascada si esa "
            "se atrasa. Para medir el costo real de un retraso antes de "
            "decidir."),
        "inputSchema": {
            "type": "object",
            "properties": {"tarea_id": {"type": "string"}},
            "required": ["tarea_id"],
        },
        "fn": _impacto_si_se_atrasa,
    },
    {
        "name": "backlog_priorizado",
        "lee_portafolio": True,
        "description": (
            "Backlog ordenado por valor esperado según el motor de "
            "priorización. Devolvé los primeros N para responder 'qué "
            "conviene hacer ahora'."),
        "inputSchema": {
            "type": "object",
            "properties": {"limite": {"type": "integer", "default": 10}},
        },
        "fn": _backlog_priorizado,
    },
    {
        "name": "politicas",
        "lee_portafolio": True,
        "description": (
            "Evaluación de las políticas de gobernanza. Por defecto devuelve "
            "sólo las incumplidas, que es lo accionable; pasá "
            "solo_incumplidas=false para ver todas."),
        "inputSchema": {
            "type": "object",
            "properties": {"solo_incumplidas": {"type": "boolean", "default": True}},
        },
        "fn": _politicas,
    },
    {
        "name": "kpis_portafolio",
        "lee_portafolio": True,
        "description": (
            "KPIs de cabecera del portafolio (cantidad de proyectos, "
            "presupuesto, ejecución). Es el resumen más barato: pedilo antes "
            "de traer tablas enteras."),
        "inputSchema": {"type": "object", "properties": {}},
        "fn": lambda **kw: _kpis(),
    },
    {
        "name": "glosario",
        "description": (
            "Definiciones de los términos del producto (qué mide cada "
            "dimensión de salud, qué es el valor esperado, etc.). Consultalo "
            "antes de explicarle una métrica al usuario, para no inventar la "
            "definición."),
        "inputSchema": {
            "type": "object",
            "properties": {"termino": {"type": "string",
                                       "description": "Filtra por subcadena."}},
        },
        "fn": _glosario,
    },
]

_POR_NOMBRE = {h["name"]: h for h in HERRAMIENTAS}


# --------------------------------------------------------------------------
# Protocolo
# --------------------------------------------------------------------------

def _catalogo_publico() -> list[dict]:
    """Las herramientas como las ve el cliente: sin la clave `fn`, que es
    interna y no es serializable."""
    return [{k: v for k, v in h.items() if k != "fn"} for h in HERRAMIENTAS]


def manejar(mensaje: dict) -> dict | None:
    """Un mensaje JSON-RPC -> la respuesta, o None si no lleva respuesta.

    Está separada del bucle de stdio para que los tests puedan ejercer el
    protocolo sin levantar un proceso.
    """
    metodo = mensaje.get("method")
    ident = mensaje.get("id")
    params = mensaje.get("params") or {}

    # Las notificaciones (sin id) nunca se responden: mandar una respuesta a
    # notifications/initialized rompe a clientes estrictos.
    if ident is None:
        return None

    def ok(resultado):
        return {"jsonrpc": "2.0", "id": ident, "result": resultado}

    def error(codigo, texto):
        return {"jsonrpc": "2.0", "id": ident, "error": {"code": codigo, "message": texto}}

    if metodo == "initialize":
        pedida = params.get("protocolVersion")
        return ok({
            "protocolVersion": pedida if pedida in VERSIONES else VERSION_POR_DEFECTO,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "mvpm", "version": _version()},
            "instructions": (
                "Portafolio de MV Project Management. Todas las herramientas "
                "son de sólo lectura. Empezá por kpis_portafolio o "
                "listar_tablas; los números vienen calculados por el motor, no "
                "los recalcules ni los estimes."),
        })

    if metodo == "ping":
        return ok({})

    if metodo == "tools/list":
        return ok({"tools": _catalogo_publico()})

    if metodo == "tools/call":
        nombre = params.get("name")
        herramienta = _POR_NOMBRE.get(nombre)
        if herramienta is None:
            return error(-32602, f"No existe la herramienta '{nombre}'.")
        argumentos = params.get("arguments") or {}
        try:
            resultado = herramienta["fn"](**argumentos)
        except _ErrorDeUso as e:
            # Error de la herramienta, no del protocolo: va como isError para
            # que el modelo lo lea y corrija la llamada.
            return ok({"content": [{"type": "text", "text": str(e)}], "isError": True})
        except TypeError as e:
            return ok({"content": [{"type": "text",
                                    "text": f"Argumentos inválidos para '{nombre}': {e}"}],
                       "isError": True})
        except Exception:  # noqa: BLE001
            return ok({"content": [{"type": "text",
                                    "text": f"Falló '{nombre}':\n{traceback.format_exc()}"}],
                       "isError": True})
        if herramienta.get("lee_portafolio") and isinstance(resultado, dict):
            aviso = _aviso_si_vacio()
            if aviso:
                resultado = {"aviso": aviso, **resultado}
        texto = json.dumps(resultado, ensure_ascii=False, indent=2, default=str)
        return ok({"content": [{"type": "text", "text": texto}]})

    return error(-32601, f"Método no soportado: {metodo}")


def _version() -> str:
    try:
        from mvpm import __version__
        return str(__version__)
    except Exception:  # noqa: BLE001
        return "0.1.0"


def main(entrada=None, salida=None) -> int:
    """Bucle de stdio. Nada más que JSON-RPC puede salir por stdout."""
    entrada = entrada or sys.stdin
    salida = salida or sys.stdout
    for linea in entrada:
        linea = linea.strip()
        if not linea:
            continue
        try:
            mensaje = json.loads(linea)
        except ValueError:
            # Sin id no hay a quién contestarle; se deja constancia por stderr.
            print(f"[mvpm-mcp] línea ilegible descartada: {linea[:120]}", file=sys.stderr)
            continue
        respuesta = manejar(mensaje)
        if respuesta is not None:
            salida.write(json.dumps(respuesta, ensure_ascii=False) + "\n")
            salida.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
