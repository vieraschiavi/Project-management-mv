# © 2026 Martín Viera. Todos los derechos reservados.
"""Tests del servidor MCP del portafolio (`mvpm/mcp_server.py`).

El protocolo se ejercita de verdad, no se simula: la mayoría de los tests le
pasan mensajes JSON-RPC a `manejar()` y miran la respuesta, y el último levanta
el proceso real con `python -m mvpm.mcp_server` y le habla por stdio, que es
exactamente lo que hace un cliente MCP.
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from mvpm import auth, db, mcp_server


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(db, "_DB_FILE", tmp_path / "datos.db")
    db.init_db()
    return db


@pytest.fixture
def con_datos(tmp_db):
    """Un portafolio sembrado con la demo, como el que ve un cliente que apretó
    'Cargar datos de ejemplo'."""
    auth.registrar("demo@ejemplo.com", "Demo", "clave-larga-de-prueba-123")
    tmp_db.cargar_datos_de_ejemplo()
    return tmp_db


def pedir(metodo, params=None, ident=1):
    return mcp_server.manejar(
        {"jsonrpc": "2.0", "id": ident, "method": metodo, "params": params or {}})


def llamar(nombre, argumentos=None):
    """Invoca una herramienta y devuelve (payload, hubo_error)."""
    r = pedir("tools/call", {"name": nombre, "arguments": argumentos or {}})
    contenido = r["result"]["content"][0]["text"]
    if r["result"].get("isError"):
        return contenido, True
    return json.loads(contenido), False


# ------------------------------------------------------------------ protocolo

def test_initialize_declara_herramientas_y_version():
    r = pedir("initialize", {"protocolVersion": "2025-06-18"})
    assert r["result"]["protocolVersion"] == "2025-06-18"
    assert "tools" in r["result"]["capabilities"]
    assert r["result"]["serverInfo"]["name"] == "mvpm"


def test_initialize_con_version_desconocida_responde_la_propia():
    """No se le devuelve al cliente una versión que este servidor no habla."""
    r = pedir("initialize", {"protocolVersion": "1999-01-01"})
    assert r["result"]["protocolVersion"] == mcp_server.VERSION_POR_DEFECTO


def test_las_notificaciones_no_se_responden():
    """Contestarle a una notificación rompe a los clientes estrictos."""
    assert mcp_server.manejar(
        {"jsonrpc": "2.0", "method": "notifications/initialized"}) is None


def test_metodo_desconocido_da_error_de_protocolo():
    assert pedir("metodo/inventado")["error"]["code"] == -32601


def test_ping_responde():
    assert pedir("ping")["result"] == {}


def test_tools_list_no_filtra_la_funcion_interna():
    """`fn` es un callable: si se colara en el catálogo, `json.dumps` de la
    respuesta explota y el cliente no puede listar nada."""
    herramientas = pedir("tools/list")["result"]["tools"]
    assert herramientas
    for h in herramientas:
        assert "fn" not in h
        assert {"name", "description", "inputSchema"} <= set(h)
    json.dumps(herramientas)


def test_toda_herramienta_declarada_es_invocable():
    for h in mcp_server.HERRAMIENTAS:
        assert callable(h["fn"]), h["name"]
        assert h["inputSchema"]["type"] == "object"


# ------------------------------------------------------------------ resultados

def test_kpis_y_salud_con_datos_reales(con_datos):
    kpis, error = llamar("kpis_portafolio")
    assert not error
    assert kpis["proyectos_activos"] == len(con_datos.projects())

    salud, error = llamar("salud_portafolio")
    assert not error
    assert 0 <= salud["indice_general"] <= 100
    # La peor dimensión tiene que ser realmente la de promedio más bajo.
    promedios = salud["promedio_por_dimension"]
    assert salud["peor_dimension"] == min(promedios, key=promedios.get)
    assert len(salud["por_proyecto"]) == len(con_datos.projects())


def test_consultar_tabla_recorta_y_lo_dice(con_datos):
    datos, error = llamar("consultar_tabla", {"tabla": "tareas", "limite": 5})
    assert not error
    assert datos["filas_devueltas"] == 5
    assert datos["truncado"] is True
    assert datos["filas_totales"] == len(con_datos.tasks())


def test_consultar_tabla_ordena(con_datos):
    datos, _ = llamar("consultar_tabla",
                      {"tabla": "salud", "orden": "indice", "limite": 5})
    indices = [f["indice"] for f in datos["datos"]]
    assert indices == sorted(indices)

    datos, _ = llamar("consultar_tabla",
                      {"tabla": "salud", "orden": "indice", "limite": 5,
                       "descendente": True})
    indices = [f["indice"] for f in datos["datos"]]
    assert indices == sorted(indices, reverse=True)


def test_filtro_no_distingue_mayusculas(con_datos):
    minus, _ = llamar("consultar_tabla",
                      {"tabla": "salud", "filtro_columna": "estado",
                       "filtro_valor": "riesgo"})
    mayus, _ = llamar("consultar_tabla",
                      {"tabla": "salud", "filtro_columna": "estado",
                       "filtro_valor": "RIESGO"})
    assert minus["filas_totales"] == mayus["filas_totales"]


def test_el_limite_tiene_techo(con_datos):
    """Un agente que pide 10.000 filas no puede vaciar la tabla entera en su
    contexto."""
    datos, _ = llamar("consultar_tabla", {"tabla": "tareas", "limite": 10_000})
    assert datos["filas_devueltas"] <= mcp_server.LIMITE_MAXIMO


def test_politicas_filtra_las_cumplidas(con_datos):
    incumplidas, _ = llamar("politicas")
    todas, _ = llamar("politicas", {"solo_incumplidas": False})
    assert incumplidas["filas_totales"] <= todas["filas_totales"]


def test_impacto_si_se_atrasa_usa_el_motor(con_datos):
    from mvpm import dependencies
    tarea = con_datos.tasks().iloc[0]["tarea_id"]
    resultado, _ = llamar("impacto_si_se_atrasa", {"tarea_id": tarea})
    esperado = dependencies.impacto_si_se_atrasa(tarea, con_datos.tasks())
    assert resultado["tareas_afectadas"] == esperado
    assert resultado["cantidad"] == len(esperado)


def test_toda_respuesta_es_json_valido(con_datos):
    """Cada herramienta tiene que serializar sin romperse: un NaN suelto tira
    abajo la respuesta entera y el agente no recibe nada."""
    argumentos = {"impacto_si_se_atrasa": {"tarea_id": con_datos.tasks().iloc[0]["tarea_id"]},
                  "consultar_tabla": {"tabla": "proyectos"}}
    for h in mcp_server.HERRAMIENTAS:
        r = pedir("tools/call", {"name": h["name"],
                                 "arguments": argumentos.get(h["name"], {})})
        texto = r["result"]["content"][0]["text"]
        assert not r["result"].get("isError"), f"{h['name']}: {texto[:200]}"
        json.loads(texto)


# ------------------------------------------------------------------ errores

def test_tabla_inexistente_dice_cuales_hay(con_datos):
    texto, error = llamar("consultar_tabla", {"tabla": "no_existe"})
    assert error
    assert "proyectos" in texto


def test_columna_inexistente_dice_cuales_hay(con_datos):
    texto, error = llamar("consultar_tabla",
                          {"tabla": "salud", "orden": "columna_falsa"})
    assert error
    assert "indice" in texto


def test_herramienta_inexistente_es_error_de_protocolo():
    assert pedir("tools/call", {"name": "no_existe"})["error"]["code"] == -32602


def test_argumento_de_mas_no_mata_al_servidor(con_datos):
    """El servidor tiene que sobrevivir a que el modelo invente un parámetro."""
    texto, error = llamar("kpis_portafolio", {"parametro_inventado": 1})
    assert not error or "inválidos" in texto


# ------------------------------------------------------ portafolio vacío

def test_portafolio_vacio_avisa_en_vez_de_mentir(tmp_db):
    """Con la base recién creada los números son 0. Sin aviso, un agente
    concluye que el portafolio está en cero en vez de que está vacío."""
    salud, error = llamar("salud_portafolio")
    assert not error
    assert salud["indice_general"] == 0
    assert "vacío" in salud["aviso"]


def test_el_glosario_no_lleva_aviso_de_vacio(tmp_db):
    """El glosario no depende del portafolio: avisar ahí sería ruido."""
    glosario, _ = llamar("glosario")
    assert "aviso" not in glosario
    assert glosario["filas_totales"] > 0


def test_con_datos_no_hay_aviso(con_datos):
    kpis, _ = llamar("kpis_portafolio")
    assert "aviso" not in kpis


# ------------------------------------------------------ el proceso de verdad

def test_el_proceso_real_completa_el_handshake(tmp_path):
    """Lo que hace un cliente MCP: levantar el proceso y hablarle por stdio.

    Es el único test que prueba que el módulo es ejecutable, que no imprime
    basura en stdout (cualquier `print` suelto corrompe el stream y el cliente
    ve el servidor como caído) y que el bucle de entrada responde de a una
    línea por mensaje.
    """
    import os
    entorno = dict(os.environ, MVPM_DATA_DIR=str(tmp_path))
    raiz = Path(__file__).resolve().parent.parent
    proceso = subprocess.Popen(
        [sys.executable, "-m", "mvpm.mcp_server"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, cwd=raiz, env=entorno)
    peticiones = "\n".join([
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18"}}),
        json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
        json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                    "params": {"name": "glosario", "arguments": {}}}),
    ]) + "\n"
    salida, errores = proceso.communicate(peticiones, timeout=120)

    lineas = [json.loads(l) for l in salida.splitlines() if l.strip()]
    # Tres pedidos con id -> exactamente tres respuestas. Si la notificación
    # se contestara, acá habría cuatro.
    assert len(lineas) == 3, f"stdout inesperado: {salida[:400]} | stderr: {errores[:400]}"
    assert [l["id"] for l in lineas] == [1, 2, 3]
    assert lineas[0]["result"]["serverInfo"]["name"] == "mvpm"
    assert len(lineas[1]["result"]["tools"]) == len(mcp_server.HERRAMIENTAS)
    assert not lineas[2]["result"].get("isError")


def test_una_linea_ilegible_no_tumba_el_servidor(tmp_path):
    """Basura en la entrada se descarta y se sigue atendiendo."""
    import os
    entorno = dict(os.environ, MVPM_DATA_DIR=str(tmp_path))
    raiz = Path(__file__).resolve().parent.parent
    proceso = subprocess.Popen(
        [sys.executable, "-m", "mvpm.mcp_server"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, cwd=raiz, env=entorno)
    entrada = ("esto no es json\n"
               + json.dumps({"jsonrpc": "2.0", "id": 7, "method": "ping"}) + "\n")
    salida, _ = proceso.communicate(entrada, timeout=120)
    lineas = [json.loads(l) for l in salida.splitlines() if l.strip()]
    assert [l["id"] for l in lineas] == [7]
