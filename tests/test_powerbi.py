"""El contrato que Power BI (y Tableau/Excel) consumen.

Los `.pbids` de `distribucion/powerbi/` son archivos con URLs escritas a mano:
si alguien renombra un endpoint en `api/main.py`, el `.pbids` sigue apuntando a
la ruta vieja y el consultor se entera recién cuando Power BI le tira 404 en la
demo delante del cliente. Estos tests atan el archivo a la API real.

También se fija acá lo que promete `CASO_DE_USO.md`: que `salud` trae el índice
YA calculado por el motor (el argumento de venta: no hay que rehacer la fórmula
en DAX) y que `?format=csv` devuelve CSV parseable.
"""

import csv
import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

CARPETA_PBIDS = Path(__file__).resolve().parent.parent / "distribucion" / "powerbi"
BASE = "http://127.0.0.1:8600"


@pytest.fixture(scope="module")
def client():
    import api.main as main
    return TestClient(main.app)


def _pbids() -> list[Path]:
    archivos = sorted(CARPETA_PBIDS.glob("*.pbids"))
    assert archivos, "no hay ningún .pbids en distribucion/powerbi/"
    return archivos


def _rutas(archivo: Path) -> list[str]:
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    return [c["details"]["address"]["url"].replace(BASE, "")
            for c in datos["connections"]]


def _todas_las_rutas() -> list[tuple[str, str]]:
    return [(a.name, r) for a in _pbids() for r in _rutas(a)]


# ------------------------------------------------------- los .pbids en sí

@pytest.mark.parametrize("archivo", _pbids(), ids=lambda a: a.name)
def test_el_pbids_es_json_valido_con_el_formato_que_espera_power_bi(archivo):
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    assert datos["version"] == "0.1"
    assert datos["connections"], "un .pbids sin conexiones no carga nada"
    for c in datos["connections"]:
        assert c["details"]["protocol"] == "http"
        assert c["details"]["address"]["url"].startswith(BASE)
        assert c["mode"] == "Import"


@pytest.mark.parametrize("archivo,ruta", _todas_las_rutas(),
                         ids=lambda v: v if isinstance(v, str) else str(v))
def test_toda_url_de_un_pbids_existe_en_la_api(client, archivo, ruta):
    """El que rompe esto es el que renombró un endpoint sin tocar el .pbids."""
    r = client.get(ruta)
    assert r.status_code != 404, (
        f"{archivo} apunta a {ruta}, que la API no sirve")
    assert r.status_code == 200


@pytest.mark.parametrize("archivo,ruta", _todas_las_rutas(),
                         ids=lambda v: v if isinstance(v, str) else str(v))
def test_toda_url_de_un_pbids_devuelve_una_tabla(client, archivo, ruta):
    """Power BI carga listas de objetos como filas. Un dict suelto entra como
    una sola fila de una columna por clave, que no es lo que espera nadie."""
    datos = client.get(ruta).json()
    assert isinstance(datos, list), f"{ruta} no devuelve una lista de filas"


@pytest.mark.parametrize("archivo,ruta", _todas_las_rutas(),
                         ids=lambda v: v if isinstance(v, str) else str(v))
def test_toda_url_de_un_pbids_sirve_csv_parseable(client, archivo, ruta):
    """`?format=csv` es lo que usan Tableau y Excel — CASO_DE_USO.md lo ofrece
    para todos los endpoints, así que tiene que andar en todos."""
    r = client.get(ruta, params={"format": "csv"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    filas = list(csv.reader(io.StringIO(r.text)))
    assert filas, f"{ruta}?format=csv vino vacío"
    assert len(filas[0]) > 1, (
        f"{ruta}?format=csv se parsea como una sola columna: {filas[0][:1]}")


# ----------------------------------------- lo que promete el caso de uso

def test_salud_trae_el_indice_ya_calculado_por_el_motor(client):
    """El argumento de venta del caso de uso: el consultor NO tiene que
    reconstruir el índice de salud en DAX, viene calculado."""
    from mvpm import db

    if db.projects().empty:
        pytest.skip("sin proyectos en la base: no hay salud que verificar")

    filas = client.get("/api/salud").json()
    assert filas, "la tabla salud vino vacía habiendo proyectos"
    columnas = set(filas[0])
    assert "indice" in columnas
    assert {c for c in columnas if c.startswith("dim_")}, (
        "faltan las dimensiones: el radar por dimensión del tablero no se puede armar")
    for f in filas:
        assert 0 <= f["indice"] <= 100


def test_el_promedio_de_la_api_coincide_con_el_motor(client):
    """CASO_DE_USO.md avisa que el dashboard muestra el índice redondeado a un
    decimal y la API el crudo. Se fija esa relación: si algún día divergen de
    verdad, el consultor estaría mostrando otro número que el cliente."""
    from mvpm import db, health

    if db.projects().empty:
        pytest.skip("sin proyectos en la base")

    filas = client.get("/api/salud").json()
    promedio_api = sum(f["indice"] for f in filas) / len(filas)
    del_motor = health.overall_index(db.projects(), db.tasks(), db.team())
    assert round(promedio_api, 1) == pytest.approx(del_motor, abs=0.05)


def test_el_caso_de_uso_no_referencia_pbids_que_no_existen():
    """El documento linkea los .pbids por nombre; si se renombra uno, el link
    queda roto y el consultor no encuentra el archivo del que le hablan."""
    doc = (CARPETA_PBIDS / "CASO_DE_USO.md").read_text(encoding="utf-8")
    for archivo in _pbids():
        assert archivo.name in doc, (
            f"{archivo.name} existe pero CASO_DE_USO.md no lo menciona")
