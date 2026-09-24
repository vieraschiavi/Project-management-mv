# © 2026 Martín Viera. Todos los derechos reservados.
"""Fuente activa: con datos del usuario cargados, la demo desaparece de TODAS
las pestañas (y de la API y el MCP); al volver a la demo, vuelve; nunca se
mezclan."""

import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import pytest

from mvpm import (
    case_study, catalog, copilot, db, demo_data, dependencies as dep_mod, exporters,
    fuente, health, importer, invitado, policies, prioritizer, reports,
)

RAIZ = Path(__file__).resolve().parent.parent
NOMBRES_DEMO = set(demo_data.projects()["nombre"])
NOMBRES_USUARIO = {"Obra Norte", "Obra Sur"}


@pytest.fixture
def base(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(db, "_DB_FILE", tmp_path / "datos.db")
    db.init_db()
    db.crear_usuario(email="admin@empresa.com", nombre="Admin", password_hash="x",
                     password_salt="y", rol="admin")
    return db


def _importar_archivo(nombre_archivo="cartera.xlsx"):
    df = pd.DataFrame([
        {"Nombre del Proyecto": "Obra Norte", "Área Responsable": "Ingeniería",
         "Monto Total": "2500000", "Fecha de Inicio": "01/03/2026"},
        {"Nombre del Proyecto": "Obra Sur", "Área Responsable": "Ingeniería",
         "Monto Total": "800000", "Fecha de Inicio": "15/04/2026"},
    ])
    sug = importer.detectar_columnas(df, "proyectos")
    rep = importer.validar(df, "proyectos", {k: v.columna for k, v in sug.items() if v.columna},
                           existentes=fuente.desde_db().proyectos)
    origen = fuente.origen_archivo(nombre_archivo)
    n = importer.aplicar(rep, lambda **c: db.crear_proyecto(origen=origen, **c), db.crear_tarea)
    assert n == 2
    ids = db.projects()
    ids = ids[ids["nombre"] == "Obra Norte"]["_id"].tolist()
    db.crear_tarea(proyecto_id=ids[0], titulo="Relevar terreno", estado="blocked",
                   prioridad="Alta")


# ------------------------------------------------------------ resolver puro

def _p(nombre, origen, pid):
    return {"_id": pid, "proyecto_id": f"PRJ-{pid:03d}", "nombre": nombre, "origen": origen}


def test_resolver_solo_demo_es_demo():
    proy = pd.DataFrame([_p("A", "demo", 1)])
    tar = pd.DataFrame([{"proyecto_id": "PRJ-001", "titulo": "t"}])
    f = fuente.resolver(proy, tar, pd.DataFrame(columns=["nombre"]))
    assert f.es_demo and len(f.proyectos) == 1 and len(f.tareas) == 1
    assert "origen" not in f.proyectos.columns


def test_resolver_con_usuario_oculta_demo_tareas_y_equipo():
    proy = pd.DataFrame([_p("Demo", "demo", 1), _p("Mio", "archivo:x.csv", 2)])
    tar = pd.DataFrame([{"proyecto_id": "PRJ-001", "titulo": "demo"},
                        {"proyecto_id": "PRJ-002", "titulo": "mia"}])
    eq = pd.DataFrame([{"nombre": "Ficticio", "origen": "demo"},
                       {"nombre": "Real", "origen": "manual"}])
    f = fuente.resolver(proy, tar, eq)
    assert f.es_usuario and f.origenes == ("archivo:x.csv",) and f.nombre == "x.csv"
    assert f.proyectos["nombre"].tolist() == ["Mio"]
    assert f.tareas["titulo"].tolist() == ["mia"]
    assert f.equipo["nombre"].tolist() == ["Real"]
    assert "origen" not in f.equipo.columns


def test_resolver_vacio_y_sin_columna_origen():
    vacio = pd.DataFrame(columns=["_id", "proyecto_id", "nombre", "origen"])
    assert fuente.resolver(vacio, pd.DataFrame(columns=["proyecto_id"]),
                           pd.DataFrame()).tipo == fuente.TIPO_VACIA
    sin_col = pd.DataFrame([{"_id": 1, "proyecto_id": "PRJ-001", "nombre": "X"}])
    assert fuente.resolver(sin_col, pd.DataFrame(columns=["proyecto_id"]),
                           pd.DataFrame()).es_usuario


def test_base_vacia_conserva_las_columnas(base):
    """Con cero filas la fuente tiene que devolver las mismas columnas que la
    base: el motor (políticas, catálogo) indexa por nombre de columna."""
    f = fuente.desde_db()
    assert f.tipo == fuente.TIPO_VACIA
    assert list(f.proyectos.columns) == list(db.projects().columns)
    assert list(f.tareas.columns) == list(db.tasks().columns)
    assert list(f.equipo.columns) == list(db.team().columns)
    policies.evaluate(f.proyectos, f.tareas, f.equipo)
    catalog.kpis(f.proyectos)


def test_clave_cambia_con_la_fuente():
    demo = fuente.resolver(pd.DataFrame([_p("A", "demo", 1)]),
                           pd.DataFrame(columns=["proyecto_id"]), pd.DataFrame())
    mix = fuente.resolver(pd.DataFrame([_p("A", "demo", 1), _p("B", "sql:SAP", 2)]),
                          pd.DataFrame(columns=["proyecto_id"]), pd.DataFrame())
    assert demo.clave != mix.clave


# ------------------------------------------------------------ base real

def test_demo_sembrada_es_la_fuente_hasta_importar(base):
    db.cargar_datos_de_ejemplo()
    f = fuente.desde_db()
    assert f.es_demo
    assert set(f.proyectos["nombre"]) == NOMBRES_DEMO
    assert len(f.tareas) == len(demo_data.tasks())


def test_con_archivo_importado_ningun_consumidor_ve_la_demo(base):
    db.cargar_datos_de_ejemplo()
    _importar_archivo()
    f = fuente.desde_db()
    assert f.es_usuario and f.nombre == "cartera.xlsx"
    p, t, e = f.proyectos, f.tareas, f.equipo

    # Nada de la demo: ni proyectos, ni sus tareas, ni su equipo ficticio.
    assert set(p["nombre"]) == NOMBRES_USUARIO
    assert t["titulo"].tolist() == ["Relevar terreno"]
    assert not any(n in set(e["nombre"]) for n in demo_data.team()["nombre"])

    # Cada consumidor del motor (una pestaña cada uno) recibe sólo lo del usuario.
    assert set(catalog.catalog(p)["nombre"]) == NOMBRES_USUARIO                 # Portafolio
    assert catalog.kpis(p)["proyectos_activos"] == 2
    assert set(health.project_health(p, t, e)["nombre"]) == NOMBRES_USUARIO     # Salud
    assert set(health.matriz_por_dimension(p, t, e)["nombre"]) == NOMBRES_USUARIO
    assert len(dep_mod.bloqueos_activos(t)) == 1                               # Dependencias
    backlog = prioritizer.prioritized_backlog(p, t)                            # Backlog
    assert set(backlog["proyecto_id"]) <= set(p["proyecto_id"])
    pol = policies.evaluate(p, t, e)                                           # Políticas
    assert not (set(pol.astype(str).stack()) & NOMBRES_DEMO)
    texto = reports.as_text(p, t, e)                                           # Reportes
    assert not any(n in texto for n in NOMBRES_DEMO)
    tablas = exporters.portfolio_tables(p, t, e)                               # Exportes / BI
    assert set(tablas["proyectos"]["nombre"]) == NOMBRES_USUARIO
    caso = case_study.narrar_caso(p, t, e)                                     # Caso de uso
    assert caso["nombre"] in NOMBRES_USUARIO
    resp = copilot.answer("¿qué proyectos están en riesgo?", p, t, e, use_ai=False)  # Copiloto
    assert not any(n in str(resp) for n in NOMBRES_DEMO)


def test_volver_a_la_demo_archiva_sin_borrar(base):
    db.cargar_datos_de_ejemplo()
    _importar_archivo()
    assert fuente.volver_a_demo_db() == 2
    f = fuente.desde_db()
    assert f.es_demo and set(f.proyectos["nombre"]) == NOMBRES_DEMO
    assert "Relevar terreno" not in set(f.tareas["titulo"])
    # Los datos del usuario siguen en la base, archivados.
    todos = db.projects(incluir_archivados=True)
    assert NOMBRES_USUARIO <= set(todos["nombre"])


def test_reimportar_despues_de_volver_a_la_demo(base):
    """Con la demo activa, los proyectos del usuario archivados y los de la
    demo no cuentan como duplicados: re-importar el mismo archivo funciona."""
    db.cargar_datos_de_ejemplo()
    _importar_archivo()
    fuente.volver_a_demo_db()
    activa = fuente.desde_db()
    todos = db.projects(incluir_archivados=True, con_origen=True)
    assert fuente.existentes_para_importar(activa, "proyectos", todos).empty
    _importar_archivo()
    assert set(fuente.desde_db().proyectos["nombre"]) == NOMBRES_USUARIO


def test_con_usuario_activo_detecta_duplicados_propios_no_demo(base):
    db.cargar_datos_de_ejemplo()
    _importar_archivo()
    ex = fuente.existentes_para_importar(
        fuente.desde_db(), "proyectos", db.projects(incluir_archivados=True, con_origen=True))
    assert set(ex["nombre"]) == NOMBRES_USUARIO


def test_sin_demo_sembrada_volver_deja_la_base_vacia(base):
    _importar_archivo()
    fuente.volver_a_demo_db()
    assert fuente.desde_db().tipo == fuente.TIPO_VACIA


def test_origen_sql_tambien_reemplaza_la_demo(base):
    db.cargar_datos_de_ejemplo()
    db.crear_proyecto(nombre="Desde SAP", portafolio="ERP", segmento="Interno",
                      criticidad="Media", presupuesto=0, ejecutado=0,
                      origen=fuente.origen_sql("SAP ERP"))
    f = fuente.desde_db()
    assert f.es_usuario and f.proyectos["nombre"].tolist() == ["Desde SAP"]
    assert f.nombre == "SAP ERP"


def test_migracion_marca_demo_en_base_vieja(tmp_path, monkeypatch):
    """Una base creada antes de la columna `origen`: la demo sembrada se
    reconoce y no se mezcla con lo que el usuario ya había cargado."""
    archivo = tmp_path / "vieja.db"
    monkeypatch.setattr(db, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(db, "_DB_FILE", archivo)
    db.init_db()
    con = sqlite3.connect(archivo)
    con.execute("ALTER TABLE proyectos DROP COLUMN origen")
    demo = demo_data.projects().iloc[0]
    for nombre, porta in [(demo["nombre"], demo["portafolio"]), ("Mío", "Propio")]:
        con.execute("INSERT INTO proyectos (nombre, portafolio, creado_en, actualizado_en) "
                    "VALUES (?, ?, 'x', 'x')", (nombre, porta))
    con.commit()
    con.close()

    f = fuente.desde_db()  # corre init_db -> migración
    assert f.es_usuario and f.proyectos["nombre"].tolist() == ["Mío"]


# ------------------------------------------------------------ API y MCP

def test_api_y_mcp_sirven_la_fuente_activa(base):
    from mvpm import mcp_server

    db.cargar_datos_de_ejemplo()
    _importar_archivo()
    p, _, _ = mcp_server._datos()
    assert set(p["nombre"]) == NOMBRES_USUARIO
    assert set(mcp_server._tablas()["proyectos"]["nombre"]) == NOMBRES_USUARIO
    assert mcp_server._kpis()["proyectos_activos"] == 2

    api = (RAIZ / "api" / "main.py").read_text(encoding="utf-8")
    assert "fuente.desde_db()" in api
    assert not re.search(r"db\.(projects|tasks|team)\(\)", api)


# ------------------------------------------------------------ invitado

def test_invitado_importa_y_la_demo_real_desaparece():
    a = invitado.con_portafolio_real()
    assert a.fuente_activa().es_demo
    total_demo = len(a.proyectos())
    a.crear_proyecto(nombre="Mi obra", portafolio="Propio",
                     origen=fuente.origen_archivo("mio.csv"))
    f = a.fuente_activa()
    assert f.es_usuario and f.proyectos["nombre"].tolist() == ["Mi obra"]
    assert a.archivar_proyectos_de_usuario() == 1
    f = a.fuente_activa()
    assert f.es_demo and len(f.proyectos) == total_demo


# ------------------------------------------------------------ dashboard

def test_dashboard_lee_solo_la_fuente_activa():
    """Guarda de regresión: ninguna pestaña vuelve a leer la base entera ni la
    demo por su cuenta."""
    app = (RAIZ / "app" / "app.py").read_text(encoding="utf-8")
    # db.projects() sólo aparece con con_origen=True (para el resolver de
    # duplicados); nunca una lectura cruda de la base que mezcle la demo.
    assert not re.search(r"db\.(tasks|team)\(", app)
    for m in re.finditer(r"db\.projects\(([^)]*)\)", app):
        assert "con_origen=True" in m.group(1), m.group(0)
    assert "demo_data." not in app
    assert "proj_df, task_df, team_df = FUENTE.proyectos, FUENTE.tareas, FUENTE.equipo" in app
    # El caso de uso antes narraba siempre la demo (narrar_caso sin datos).
    assert "case_study.narrar_caso(proj_df, task_df, team_df" in app
    # Toda llamada al motor de portafolio recibe los DataFrames de la fuente.
    for llamada in re.findall(
            r"(?:catalog|health|policies|prioritizer|reports|exporters)\.\w+\(([^)]*)\)", app):
        if llamada.strip():
            assert "proj_df" in llamada or "task_df" in llamada or "_df" in llamada, llamada
    # Las importaciones etiquetan su origen (archivo y SQL).
    assert "fuente.origen_archivo(uploaded.name)" in app
    assert "fuente.origen_sql(_perfil.nombre)" in app
