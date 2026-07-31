"""La API de BI no puede caerse por una celda numérica vacía.

Bug real que esto fija: un proyecto recién creado, sin presupuesto cargado
todavía, produce ejecucion_pct = NaN (catalog.py lo deja así a propósito para
no mostrar "inf%"). NaN no es JSON válido, así que /api/proyectos respondía 500
y la conexión de Power BI del cliente se caía con su PRIMER proyecto.
"""

import json

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import api.main as main
from mvpm import demo_data, exporters


@pytest.fixture
def client_con_datos_incompletos(monkeypatch):
    """Portafolio realista donde un proyecto todavía no tiene presupuesto."""
    proj = demo_data.projects().copy()
    proj.loc[proj.index[0], "presupuesto"] = 0
    proj.loc[proj.index[0], "ejecutado"] = 0
    tasks, team = demo_data.tasks(), demo_data.team()

    monkeypatch.setattr(main, "_tables",
                        lambda: exporters.portfolio_tables(proj, tasks, team))
    return TestClient(main.app)


def test_hay_nan_en_los_datos_de_prueba(client_con_datos_incompletos):
    """Guarda de la guarda: si el motor dejara de producir NaN acá, este
    archivo dejaría de probar lo que dice probar."""
    df = main._tables()["proyectos"]
    assert df["ejecucion_pct"].isna().any(), "el escenario ya no genera NaN"


@pytest.mark.parametrize("tabla", ["proyectos", "tareas", "equipo", "salud",
                                   "backlog_priorizado", "politicas"])
def test_toda_tabla_devuelve_json_valido(client_con_datos_incompletos, tabla):
    r = client_con_datos_incompletos.get(f"/api/{tabla}")
    assert r.status_code == 200, f"{tabla} respondió {r.status_code}: {r.text[:200]}"
    # allow_nan=False es justamente lo que rechaza NaN/Infinity: si el endpoint
    # dejara pasar uno, esto levanta.
    json.dumps(r.json(), allow_nan=False)


def test_los_nan_viajan_como_null_no_como_texto(client_con_datos_incompletos):
    """Power BI interpreta null como celda vacía; la cadena "NaN" la tomaría
    como texto y rompería el tipo de la columna."""
    filas = client_con_datos_incompletos.get("/api/proyectos").json()
    vacios = [f for f in filas if f["ejecucion_pct"] is None]
    assert vacios, "se esperaba al menos un ejecucion_pct nulo"
    for f in filas:
        assert f["ejecucion_pct"] != "NaN"


def test_infinito_tambien_se_neutraliza(monkeypatch):
    """Aunque hoy catalog.py ya convierte inf a NaN, el borde de la API no
    debería confiar en eso: es su responsabilidad emitir JSON válido."""
    df = pd.DataFrame([{"a": 1.0, "b": float("inf")}, {"a": float("-inf"), "b": 2.0}])
    monkeypatch.setattr(main, "_tables", lambda: {"raro": df})
    r = TestClient(main.app).get("/api/raro")
    assert r.status_code == 200
    json.dumps(r.json(), allow_nan=False)
    assert r.json()[0]["b"] is None
    assert r.json()[1]["a"] is None
