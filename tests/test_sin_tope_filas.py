"""Carga de datos sin tope de filas por defecto.

Pedido del dueño: «¿Hay límite de filas? ... debe ser sin límite de tamaño
cada módulo». El default es traer todo; un tope explícito se puede seguir
poniendo, y si recorta se avisa con el total real — nunca un recorte mudo.
"""
import json
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from mvpm import azure_devops as ado
from mvpm import conectores as cx
from mvpm import i18n

FILAS = 30_000


def _erp_sap(tmp_path) -> str:
    """ERP SAP sintético en SQLite: tabla PROJ con FILAS proyectos."""
    ruta = tmp_path / "sap.db"
    con = sqlite3.connect(ruta)
    con.execute("CREATE TABLE PROJ (PSPID TEXT, POST1 TEXT, VERNR TEXT, PLFAZ TEXT,"
                " PLSEZ TEXT, VBUKR TEXT, PRCTR TEXT, LOEVM TEXT)")
    con.executemany(
        "INSERT INTO PROJ VALUES (?,?,?,?,?,?,?,?)",
        ((f"P-{i:06d}", f"Proyecto {i}", str(i % 90), "20260301", "20260930",
          "1000", "IND", "") for i in range(FILAS)))
    con.commit()
    con.close()
    return f"sqlite:///{ruta}"


def test_extraer_sin_limite_trae_todas_las_filas(tmp_path):
    pytest.importorskip("sqlalchemy")  # CI no la instala; el ejecutor la necesita
    ej = cx.crear_ejecutor(_erp_sap(tmp_path))
    df = cx.extraer(ej, "sap_ps", "proyectos", esquema="")
    assert len(df) == FILAS
    assert cx.aviso_recorte(df) is None
    # 0 también es «sin tope».
    assert len(cx.extraer(ej, "sap_ps", "proyectos", esquema="", limite=0)) == FILAS


def test_sql_de_sin_limite_no_agrega_LIMIT():
    assert "LIMIT" not in cx.sql_de("sap_ps", "proyectos").upper()
    assert "LIMIT" not in cx.sql_de("sap_ps", "proyectos", limite=0).upper()


def test_extraer_con_tope_explicito_recorta_y_avisa_con_el_total(tmp_path):
    pytest.importorskip("sqlalchemy")  # CI no la instala; el ejecutor la necesita
    ej = cx.crear_ejecutor(_erp_sap(tmp_path))
    df = cx.extraer(ej, "sap_ps", "proyectos", esquema="", limite=1000)
    assert len(df) == 1000
    assert df.attrs[cx.CLAVE_RECORTADA] is True
    assert df.attrs[cx.CLAVE_TOTAL_FILAS] == FILAS
    for lang in ("es", "en", "pt"):
        aviso = cx.aviso_recorte(df, lang)
        assert aviso and "1000" in aviso and str(FILAS) in aviso


def test_los_avisos_nuevos_estan_en_los_tres_idiomas():
    for clave in ("erp_recorte_filas", "erp_recorte_filas_sin_total"):
        for lang in ("es", "en", "pt"):
            texto = i18n.t(clave, lang).format(n=10, total=20)
            assert "{" not in texto and "10" in texto


# ---------------------------------------------------------------- Azure DevOps

class _Resp:
    def __init__(self, cuerpo: dict):
        self._c = json.dumps(cuerpo).encode()
        self.headers = {"Content-Type": "application/json"}

    def read(self):
        return self._c

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _azure_falso(monkeypatch, n_items: int):
    """Simula Azure DevOps con n_items: WIQL paginado (≤20.000) + lotes."""
    vistos = []

    def abrir(pedido, timeout=None):
        vistos.append(pedido)
        if pedido.data:                                   # consulta WIQL
            q = json.loads(pedido.data)["query"]
            desde = 0
            if "[System.Id] >" in q:
                desde = int(q.split("[System.Id] >")[1].split()[0])
            top = int(pedido.full_url.split("$top=")[1].split("&")[0]) \
                if "$top=" in pedido.full_url else n_items
            ids = list(range(desde + 1, n_items + 1))[:top]
            return _Resp({"workItems": [{"id": i} for i in ids]})
        ids = pedido.full_url.split("ids=")[1].split("&")[0].replace("%2C", ",")
        return _Resp({"value": [{"id": int(i), "rev": 1, "fields": {"System.Title": f"T{i}"}}
                                for i in ids.split(",")]})
    monkeypatch.setattr(ado._ABRIDOR, "open", abrir)
    return vistos


def test_azure_trae_todo_el_backlog_por_defecto_pasando_el_techo_de_wiql(monkeypatch):
    assert ado.LIMITE_POR_DEFECTO is None
    n = ado.PAGINA_WIQL + 250                     # más que una página de WIQL
    vistos = _azure_falso(monkeypatch, n)
    df = ado.traer_backlog(ado.Credenciales("acme", "D", "a@b.com", "t"))
    assert len(df) == n
    assert ado.sobraron(df) == 0 and ado.total_real(df) == n
    assert sum(1 for p in vistos if p.data) == 2  # dos páginas de WIQL


def test_azure_con_tope_explicito_avisa_el_total_real(monkeypatch):
    _azure_falso(monkeypatch, 2000)
    df = ado.traer_backlog(ado.Credenciales("acme", "D", "a@b.com", "t"), limite=500)
    assert len(df) == 500
    assert ado.sobraron(df) == 1500               # no «1»: el total es el real
    assert ado.total_real(df) == 2000


def test_el_tope_de_subida_de_streamlit_es_200000_mb():
    cfg = (Path(__file__).resolve().parent.parent / ".streamlit" / "config.toml").read_text()
    assert "maxUploadSize = 200000" in cfg


def test_extraer_no_pierde_filas_con_un_dataframe_grande():
    crudo = pd.DataFrame({"proyecto": [f"P{i}" for i in range(FILAS)]})
    df = cx.extraer(lambda sql: crudo, "sap_ps", "proyectos")
    assert len(df) == FILAS
