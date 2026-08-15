# © 2026 Martín Viera. Todos los derechos reservados.
"""Tests de los conectores de BI (Power BI, Tableau, Fabric).

Lo que garantizan: que ningún conector apunte a una tabla o un endpoint que el
motor no sirve. Ese es el defecto que nadie ve hasta que el cliente hace doble
clic en el `.pbids` delante de su jefe — se renombra una tabla en
`exporters.portfolio_tables` y los archivos repartidos quedan apuntando al
vacío, sin que nada avise.

Los endpoints se LEEN de cada archivo de conector, no se escriben acá: si
alguien agrega una conexión y se olvida de probarla, igual queda cubierta.

Lo que NO pueden verificar: que Power BI Desktop, Tableau o Fabric acepten el
archivo. Eso necesita las tres herramientas instaladas. Para eso están
`distribucion/powerbi/verificar_conexion.py` y el exportador de Tableau, que
hacen los pedidos HTTP de verdad contra la API levantada.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from mvpm import demo_data, exporters

RAIZ = Path(__file__).resolve().parent.parent
DIST = RAIZ / "distribucion"

# Rutas que la API sirve y que NO son una tabla del portafolio.
ENDPOINTS_ESPECIALES = {"/api/demo/pharma"}


@pytest.fixture(scope="module")
def tablas_del_motor():
    return set(exporters.portfolio_tables(
        demo_data.projects(), demo_data.tasks(), demo_data.team()))


def urls_de_pbids(archivo: Path) -> list[str]:
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    return [c["details"]["address"]["url"] for c in datos["connections"]]


def tablas_del_pq(archivo: Path) -> list[str]:
    """La lista `Tablas = {...}` del Power Query, leída del archivo."""
    texto = archivo.read_text(encoding="utf-8")
    m = re.search(r"Tablas\s*=\s*\{(.+?)\}", texto, re.S)
    assert m, f"{archivo.name}: no se encontró la lista `Tablas`"
    return re.findall(r'"([^"]+)"', m.group(1))


# ------------------------------------------------------------------ Power BI

def test_hay_pbids():
    assert list((DIST / "powerbi").glob("*.pbids"))


@pytest.mark.parametrize("pbids", sorted((DIST / "powerbi").glob("*.pbids")),
                          ids=lambda p: p.name)
def test_todo_endpoint_de_un_pbids_existe(pbids, tablas_del_motor):
    for url in urls_de_pbids(pbids):
        ruta = url.split("8600", 1)[-1]
        if ruta in ENDPOINTS_ESPECIALES:
            continue
        tabla = ruta.removeprefix("/api/")
        assert tabla in tablas_del_motor, (
            f"{pbids.name} pide '{tabla}', que el motor no sirve. "
            f"Tablas reales: {sorted(tablas_del_motor)}")


# ------------------------------------------------------------------- Tableau

def test_las_tablas_del_exportador_existen(tablas_del_motor):
    from distribucion.tableau import exportar_para_tableau as tab
    for tabla in tab.TABLAS:
        assert tabla in tablas_del_motor, f"el exportador pide '{tabla}'"


def test_el_exportador_rechaza_un_csv_envuelto_como_json(monkeypatch):
    """El defecto que ya se arregló una vez en la API: CSV serializado como
    JSON entra en Tableau como una sola columna gigante. Si vuelve, el
    exportador tiene que cortar, no escribir el archivo roto."""
    from distribucion.tableau import exportar_para_tableau as tab

    class RespuestaFalsa:
        status = 200
        headers = {"content-type": "text/csv"}
        def read(self): return b'"a,b\\nc,d"'
        def __enter__(self): return self
        def __exit__(self, *a): return False

    monkeypatch.setattr(tab.urllib.request, "urlopen", lambda *a, **k: RespuestaFalsa())
    with pytest.raises(RuntimeError, match="envuelto como JSON"):
        tab.bajar_csv("proyectos")


def test_el_exportador_rechaza_un_content_type_que_no_es_csv(monkeypatch):
    from distribucion.tableau import exportar_para_tableau as tab

    class RespuestaFalsa:
        status = 200
        headers = {"content-type": "application/json"}
        def read(self): return b"[]"
        def __enter__(self): return self
        def __exit__(self, *a): return False

    monkeypatch.setattr(tab.urllib.request, "urlopen", lambda *a, **k: RespuestaFalsa())
    with pytest.raises(RuntimeError, match="no text/csv"):
        tab.bajar_csv("proyectos")


# -------------------------------------------------------------------- Fabric

def test_las_tablas_del_power_query_existen(tablas_del_motor):
    pq = DIST / "fabric" / "MV_ProjectManagement_Portafolio.pq"
    for tabla in tablas_del_pq(pq):
        assert tabla in tablas_del_motor, f"el Power Query pide '{tabla}'"


def test_el_power_query_usa_relativepath():
    """Con la URL completa pegada a mano, la actualización programada de Fabric
    falla porque Power Query no puede validar el origen."""
    pq = (DIST / "fabric" / "MV_ProjectManagement_Portafolio.pq").read_text(encoding="utf-8")
    assert "RelativePath" in pq
    assert "Web.Contents(BaseUrl" in pq


def test_el_power_query_no_trae_una_clave_hardcodeada():
    pq = (DIST / "fabric" / "MV_ProjectManagement_Portafolio.pq").read_text(encoding="utf-8")
    m = re.search(r'ClaveApi\s*=\s*"([^"]*)"', pq)
    assert m, "el Power Query tiene que declarar ClaveApi"
    assert m.group(1) == "", "no se commitea una clave de API en el conector"


# ------------------------------------------------- los tres, la misma verdad

def test_los_tres_conectores_cubren_las_mismas_tablas():
    """Si alguien agrega una tabla a un conector y no a los otros, el cliente
    de Tableau ve un portafolio distinto al de Power BI."""
    from distribucion.tableau import exportar_para_tableau as tab

    pbids = DIST / "powerbi" / "MV_ProjectManagement_Portafolio.pbids"
    de_powerbi = {u.split("/api/", 1)[1] for u in urls_de_pbids(pbids)}
    de_fabric = set(tablas_del_pq(DIST / "fabric" / "MV_ProjectManagement_Portafolio.pq"))
    de_tableau = set(tab.TABLAS)

    assert de_powerbi == de_tableau == de_fabric, (
        f"difieren -> Power BI: {sorted(de_powerbi)} | "
        f"Tableau: {sorted(de_tableau)} | Fabric: {sorted(de_fabric)}")
