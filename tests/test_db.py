import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import pytest

from mvpm import auth, catalog, db, dependencies as dep_mod, exporters, health, prioritizer


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(db, "_DB_FILE", tmp_path / "datos.db")
    db.init_db()
    return db


# ---------------------------------------------------------------- schema

def test_init_db_is_idempotent(tmp_db):
    tmp_db.init_db()
    tmp_db.init_db()
    assert tmp_db.esta_vacia()


def test_projects_tasks_team_match_demo_data_schema(tmp_db):
    from mvpm import demo_data
    assert list(tmp_db.projects().columns.drop("_id")) == list(demo_data.projects().columns)
    assert list(tmp_db.tasks().columns.drop("_id")) == list(demo_data.tasks().columns)
    assert list(tmp_db.team().columns) == list(demo_data.team().columns)


# ------------------------------------------------------------- CRUD proyectos

def test_crear_y_leer_proyecto(tmp_db):
    admin = auth.registrar("admin@test.com", "Admin", "password123")
    pid = tmp_db.crear_proyecto(nombre="Migración X", portafolio="Core", sponsor="G. Suárez",
                                 dueno_id=admin["id"], segmento="Interno",
                                 fecha_inicio="2026-01-01", fecha_fin="2026-06-01",
                                 presupuesto=10000, ejecutado=2000, criticidad="Alta")
    df = tmp_db.projects()
    assert len(df) == 1
    assert df.iloc[0]["nombre"] == "Migración X"
    assert df.iloc[0]["dueno"] == "Admin"
    assert df.iloc[0]["proyecto_id"] == "PRJ-001"
    assert pid > 0


def test_archivar_proyecto_lo_saca_de_projects(tmp_db):
    pid = tmp_db.crear_proyecto(nombre="Viejo", portafolio="Core", sponsor=None, dueno_id=None,
                                 segmento="Interno", fecha_inicio=None, fecha_fin=None,
                                 presupuesto=0, ejecutado=0, criticidad="Baja")
    tmp_db.archivar_proyecto(pid)
    assert tmp_db.projects().empty
    assert len(tmp_db.projects(incluir_archivados=True)) == 1


def test_eliminar_proyecto_elimina_sus_tareas(tmp_db):
    pid = tmp_db.crear_proyecto(nombre="P", portafolio="Core", sponsor=None, dueno_id=None,
                                 segmento="Interno", fecha_inicio=None, fecha_fin=None,
                                 presupuesto=0, ejecutado=0, criticidad="Media")
    tmp_db.crear_tarea(proyecto_id=pid, titulo="T1", responsable_id=None, estado="todo",
                        vencimiento=None, prioridad="Media", depende_de=None)
    tmp_db.eliminar_proyecto(pid)
    assert tmp_db.tasks().empty


# ---------------------------------------------------------------- CRUD tareas

def test_crear_tarea_y_dependencia(tmp_db):
    pid = tmp_db.crear_proyecto(nombre="P", portafolio="Core", sponsor=None, dueno_id=None,
                                 segmento="Interno", fecha_inicio=None, fecha_fin=None,
                                 presupuesto=0, ejecutado=0, criticidad="Media")
    t1 = tmp_db.crear_tarea(proyecto_id=pid, titulo="Primero", responsable_id=None, estado="done",
                             vencimiento="2026-01-01", prioridad="Alta", depende_de=None)
    t2 = tmp_db.crear_tarea(proyecto_id=pid, titulo="Segundo", responsable_id=None, estado="todo",
                             vencimiento="2026-02-01", prioridad="Media", depende_de=t1)
    df = tmp_db.tasks()
    fila2 = df[df["titulo"] == "Segundo"].iloc[0]
    fila1 = df[df["titulo"] == "Primero"].iloc[0]
    assert fila2["depende_de"] == fila1["tarea_id"]


def test_actualizar_tarea_cambia_estado(tmp_db):
    pid = tmp_db.crear_proyecto(nombre="P", portafolio="Core", sponsor=None, dueno_id=None,
                                 segmento="Interno", fecha_inicio=None, fecha_fin=None,
                                 presupuesto=0, ejecutado=0, criticidad="Media")
    tid = tmp_db.crear_tarea(proyecto_id=pid, titulo="T", responsable_id=None, estado="todo",
                              vencimiento=None, prioridad="Media", depende_de=None)
    tmp_db.actualizar_tarea(tid, estado="blocked")
    df = tmp_db.tasks()
    assert df.iloc[0]["estado"] == "blocked"


# --------------------------------------------------------------------- team

def test_team_carga_actual_es_proxy_de_tareas_activas(tmp_db):
    admin = auth.registrar("admin@test.com", "Admin", "password123")
    pid = tmp_db.crear_proyecto(nombre="P", portafolio="Core", sponsor=None, dueno_id=None,
                                 segmento="Interno", fecha_inicio=None, fecha_fin=None,
                                 presupuesto=0, ejecutado=0, criticidad="Media")
    tmp_db.crear_tarea(proyecto_id=pid, titulo="Activa", responsable_id=admin["id"], estado="todo",
                        vencimiento=None, prioridad="Media", depende_de=None)
    tmp_db.crear_tarea(proyecto_id=pid, titulo="Hecha", responsable_id=admin["id"], estado="done",
                        vencimiento=None, prioridad="Media", depende_de=None)
    fila = tmp_db.team().iloc[0]
    assert fila["carga_actual_hs"] == db._HORAS_POR_TAREA_ACTIVA  # solo cuenta la activa


# ---------------------------------------------------------------- motor real

def test_engine_funciona_sobre_datos_reales_de_db(tmp_db):
    admin = auth.registrar("admin@test.com", "Admin", "password123")
    pid = tmp_db.crear_proyecto(nombre="Proyecto real", portafolio="Core", sponsor="Sponsor",
                                 dueno_id=admin["id"], segmento="Interno",
                                 fecha_inicio="2026-01-01", fecha_fin="2026-12-31",
                                 presupuesto=5000, ejecutado=1000, criticidad="Alta")
    tmp_db.crear_tarea(proyecto_id=pid, titulo="Tarea 1", responsable_id=admin["id"], estado="todo",
                        vencimiento="2026-08-01", prioridad="Alta", depende_de=None)

    proj, tasks, team = tmp_db.projects(), tmp_db.tasks(), tmp_db.team()
    kpis = catalog.kpis(proj)
    assert kpis["proyectos_activos"] == 1
    h = health.project_health(proj, tasks, team)
    assert len(h) == 1
    assert 0 <= h.iloc[0]["indice"] <= 100
    backlog = prioritizer.prioritized_backlog(proj, tasks)
    assert len(backlog) == 1
    assert dep_mod.orphan_dependencies(tasks).empty


def test_engine_funciona_con_proyecto_recien_creado_sin_tareas(tmp_db):
    """Primer flujo real de un usuario nuevo: crea un proyecto y todavía no
    cargó ninguna tarea — todas las secciones del dashboard deben poder
    renderizar sobre eso sin excepciones."""
    admin = auth.registrar("admin@test.com", "Admin", "password123")
    tmp_db.crear_proyecto(nombre="Proyecto nuevo", portafolio="Core", sponsor=None,
                           dueno_id=admin["id"], segmento="Interno",
                           fecha_inicio=None, fecha_fin=None,
                           presupuesto=0, ejecutado=0, criticidad="Media")
    proj, tasks, team = tmp_db.projects(), tmp_db.tasks(), tmp_db.team()
    assert tasks.empty
    assert prioritizer.prioritized_backlog(proj, tasks).empty
    assert len(health.project_health(proj, tasks, team)) == 1
    assert dep_mod.orphan_dependencies(tasks).empty
    assert dep_mod.bloqueos_activos(tasks).empty


# --------------------------------------------------------------------- seed

def test_cargar_datos_de_ejemplo_requiere_usuario_previo(tmp_db):
    with pytest.raises(RuntimeError):
        tmp_db.cargar_datos_de_ejemplo()


def test_cargar_datos_de_ejemplo_puebla_proyectos_y_tareas(tmp_db):
    from mvpm import demo_data
    auth.registrar("admin@test.com", "Admin", "password123")
    tmp_db.cargar_datos_de_ejemplo()
    assert len(tmp_db.projects()) == len(demo_data.projects())
    assert len(tmp_db.tasks()) == len(demo_data.tasks())


# ----------------------------------------------------------------------- auth

def test_registrar_primer_usuario_es_admin(tmp_db):
    u = auth.registrar("primero@test.com", "Primero", "password123")
    assert u["rol"] == "admin"


def test_registrar_segundo_usuario_es_miembro(tmp_db):
    auth.registrar("primero@test.com", "Primero", "password123")
    u2 = auth.registrar("segundo@test.com", "Segundo", "password123")
    assert u2["rol"] == "miembro"


def test_registrar_rechaza_email_invalido(tmp_db):
    with pytest.raises(ValueError):
        auth.registrar("no-es-un-email", "Nombre", "password123")


def test_registrar_rechaza_password_corta(tmp_db):
    with pytest.raises(ValueError):
        auth.registrar("a@test.com", "A", "corta")


def test_registrar_rechaza_email_duplicado(tmp_db):
    auth.registrar("dup@test.com", "Uno", "password123")
    with pytest.raises(ValueError):
        auth.registrar("dup@test.com", "Dos", "password456")


def test_iniciar_sesion_correcto(tmp_db):
    auth.registrar("login@test.com", "Login", "password123")
    user = auth.iniciar_sesion("login@test.com", "password123")
    assert user is not None
    assert user["email"] == "login@test.com"


def test_iniciar_sesion_password_incorrecta(tmp_db):
    auth.registrar("login2@test.com", "Login2", "password123")
    assert auth.iniciar_sesion("login2@test.com", "password-mala") is None


def test_iniciar_sesion_usuario_inexistente(tmp_db):
    assert auth.iniciar_sesion("nadie@test.com", "cualquiera") is None


def test_cuentas_de_ejemplo_no_pueden_loguearse(tmp_db):
    auth.registrar("admin@test.com", "Admin", "password123")
    tmp_db.cargar_datos_de_ejemplo()
    equipo = tmp_db.listar_usuarios()
    demo_user = equipo[equipo["email"].str.endswith("@demo.local")].iloc[0]
    assert auth.iniciar_sesion(demo_user["email"], "") is None
    assert auth.iniciar_sesion(demo_user["email"], "cualquiera") is None


# ------------------------------------------------------------------ exporters

def test_exporters_usan_datos_reales_de_db_no_la_demo(tmp_db):
    """Los botones de descarga del dashboard le pasan sus DataFrames reales a
    exporters — si portfolio_tables() ignorara esos argumentos y volviera a
    demo_data por dentro, este test detectaría el nombre del proyecto demo en
    vez del real."""
    admin = auth.registrar("admin@test.com", "Admin", "password123")
    tmp_db.crear_proyecto(nombre="Proyecto Real Único", portafolio="Core", sponsor=None,
                           dueno_id=admin["id"], segmento="Interno",
                           fecha_inicio=None, fecha_fin=None,
                           presupuesto=1000, ejecutado=100, criticidad="Alta")
    proj, tasks, team = tmp_db.projects(), tmp_db.tasks(), tmp_db.team()

    bundle = json.loads(exporters.to_json_bundle(proj, tasks, team))
    nombres = [p["nombre"] for p in bundle["proyectos"]]
    assert nombres == ["Proyecto Real Único"]

    libro = exporters.to_excel_bytes(proj, tasks, team)
    hojas = pd.read_excel(io.BytesIO(libro), sheet_name="proyectos")
    assert hojas["nombre"].tolist() == ["Proyecto Real Único"]
