# © 2026 Martín Viera. Todos los derechos reservados.
"""Modo invitado: usar el producto sin crear cuenta (mvpm/invitado.py).

Lo que se fija acá es la promesa de la landing: alguien sube su Excel y ve la
salud de su portafolio sin registrarse. Si esto se rompe, se rompe la puerta de
entrada al producto.
"""

import pandas as pd
import pytest

from mvpm import (
    catalog,
    dependencies as dep_mod,
    health,
    importer,
    invitado,
    policies,
    prioritizer,
    reports,
)


@pytest.fixture
def almacen():
    return invitado.almacen_vacio()


# --------------------------------------------------------------- almacén vacío

def test_almacen_nuevo_esta_vacio(almacen):
    assert almacen.vacio
    assert almacen.total_proyectos() == 0
    assert almacen.total_tareas() == 0


def test_las_columnas_son_las_mismas_que_devuelve_la_base(almacen):
    """El dashboard no distingue entre invitado y usuario registrado: si las
    columnas no coinciden, se rompe en cuanto alguien entra sin cuenta."""
    assert list(almacen.proyectos().columns) == invitado.COLUMNAS_PROYECTOS
    assert list(almacen.tareas().columns) == invitado.COLUMNAS_TAREAS


def test_el_motor_no_revienta_con_el_almacen_vacio(almacen):
    """Mismo caso que rompía con una base recién instalada: un DataFrame sin
    filas infiere dtype object y la división de catalog explota."""
    p, t, e = almacen.proyectos(), almacen.tareas(), almacen.equipo()
    assert catalog.kpis(p)["proyectos_activos"] == 0
    assert health.overall_index(p, t, e) is not None
    assert dep_mod.bloqueos_activos(t).empty
    assert prioritizer.prioritized_backlog(p, t) is not None
    assert policies.evaluate(p, t, e) is not None


# ------------------------------------------------------------------- escritura

def test_crear_proyecto_le_pone_codigo_e_id(almacen):
    almacen.crear_proyecto(nombre="Migración ERP", portafolio="TI",
                           presupuesto=100000, ejecutado=25000)
    df = almacen.proyectos()
    assert len(df) == 1
    assert df.iloc[0]["nombre"] == "Migración ERP"
    assert df.iloc[0]["proyecto_id"] == "P-001"
    assert df.iloc[0]["_id"] == 1


def test_un_proyecto_sin_presupuesto_no_rompe_el_catalogo(almacen):
    """Se carga primero el nombre y el presupuesto después: es lo normal."""
    almacen.crear_proyecto(nombre="Sin cifras todavía")
    df = almacen.proyectos()
    assert df.iloc[0]["presupuesto"] == 0
    cat = catalog.catalog(df)
    assert pd.isna(cat.iloc[0]["ejecucion_pct"])  # 0/0 → sin dato, no "inf%"


def test_la_tarea_apunta_al_codigo_visible_del_proyecto(almacen):
    """El importador resuelve el proyecto a su _id interno; salud y
    dependencias trabajan con el código (P-001). Si no se traduce, la tarea
    queda huérfana y no aparece en ningún cálculo."""
    pid = almacen.crear_proyecto(nombre="Obra Norte")
    almacen.crear_tarea(proyecto_id=pid, titulo="Permisos", estado="blocked")
    t = almacen.tareas()
    assert t.iloc[0]["proyecto_id"] == "P-001"
    assert t.iloc[0]["tarea_id"] == "T-0001"


def test_sin_cuenta_los_proyectos_quedan_sin_dueno(almacen):
    """No hay equipo cargado, así que el motor de salud debe marcarlos sin
    dueño — que es la verdad, no un dato inventado."""
    almacen.crear_proyecto(nombre="X", dueno_id=99)
    assert almacen.proyectos().iloc[0]["dueno"] is None
    assert catalog.catalog(almacen.proyectos()).iloc[0]["sin_dueno"]


# ------------------------------------------------- el flujo real: subir Excel

def test_un_invitado_importa_su_excel_y_ve_la_salud(almacen):
    """El recorrido completo del criterio de aceptación, sin tocar la base."""
    excel_del_cliente = pd.DataFrame([
        {"Proyecto": "Migración de servidores", "Área": "Infraestructura",
         "Responsable del área": "Gerencia TI", "Importancia": "Alta",
         "Presupuesto $": "1.500.000", "Gastado $": "320.000"},
        {"Proyecto": "Portal de clientes", "Área": "Producto",
         "Responsable del área": "Comercial", "Importancia": "Media",
         "Presupuesto $": "800.000", "Gastado $": "910.000"},
    ])

    mapeo = importer.detectar_columnas(excel_del_cliente, "proyectos")
    mapa = {k: s.columna for k, s in mapeo.items() if s.columna}
    assert "nombre" in mapa, "no reconoció la columna del nombre del proyecto"

    reporte = importer.validar(excel_del_cliente, "proyectos", mapa,
                               existentes=almacen.proyectos())
    assert not reporte.faltan_requeridos
    assert reporte.filas_validas == 2

    creadas = importer.aplicar(reporte, almacen.crear_proyecto, almacen.crear_tarea)
    assert creadas == 2

    p, t, e = almacen.proyectos(), almacen.tareas(), almacen.equipo()
    kpis = catalog.kpis(p)
    assert kpis["proyectos_activos"] == 2
    assert kpis["presupuesto_total"] == 2_300_000     # 1.500.000 + 800.000
    assert kpis["sobre_presupuesto"] == 1             # el portal gastó de más

    indice = health.overall_index(p, t, e)
    assert 0 <= indice <= 100
    assert len(reports.as_text(p, t, e)) > 0


def test_nada_de_esto_toca_la_base(almacen, monkeypatch):
    """Garantía explícita: el invitado no escribe en la base compartida."""
    from mvpm import db
    def explotar(*a, **k):
        raise AssertionError("el modo invitado no debe escribir en la base")
    monkeypatch.setattr(db, "crear_proyecto", explotar)
    monkeypatch.setattr(db, "crear_tarea", explotar)

    almacen.crear_proyecto(nombre="Solo en memoria")
    almacen.crear_tarea(proyecto_id=1, titulo="Tampoco se guarda")
    assert almacen.total_proyectos() == 1
    assert almacen.total_tareas() == 1


# ---------------------------------------------------- portafolio real del UK

def test_el_boton_de_datos_reales_carga_los_132_proyectos():
    almacen = invitado.con_portafolio_real()
    assert almacen.total_proyectos() == 132
    p, t, e = almacen.proyectos(), almacen.tareas(), almacen.equipo()
    assert catalog.kpis(p)["proyectos_activos"] == 132
    assert 0 <= health.overall_index(p, t, e) <= 100


def test_dos_sesiones_de_invitado_no_comparten_datos():
    """Cada visitante tiene su propio almacén: si se compartieran, uno vería
    el portafolio del otro."""
    a, b = invitado.almacen_vacio(), invitado.almacen_vacio()
    a.crear_proyecto(nombre="De la sesión A")
    assert b.total_proyectos() == 0


# ------------------------------------------- el estado vacío del invitado

def test_el_estado_vacio_del_invitado_no_ofrece_sembrar_la_base():
    """Regresión: el bloque de "todavía no cargaste proyectos" de app.py era
    común a invitado y usuario registrado, así que el invitado terminaba
    llamando a db.cargar_datos_de_ejemplo(). Eso escribía 20 proyectos en la
    base COMPARTIDA del servidor —rompiendo el "nada se guarda" que promete la
    barra lateral y ensuciando el portafolio de los usuarios reales— mientras
    el invitado, que lee de su almacén de sesión, no veía aparecer nada.

    Se fija leyendo el código de app.py porque el bug vivía en la rama de UI,
    no en el motor: los módulos por separado estaban bien.
    """
    from pathlib import Path

    app = (Path(__file__).resolve().parent.parent / "app" / "app.py").read_text()
    bloque = app.split("if proj_df.empty and task_df.empty:")[1].split("# ---")[0]
    # Solo código ejecutable: los comentarios de este mismo bloque nombran el
    # bug que se está previniendo, y harían pasar/fallar el test por el texto.
    bloque = "\n".join(linea for linea in bloque.splitlines()
                       if not linea.strip().startswith("#"))

    assert "if INVITADO:" in bloque, (
        "el estado vacío tiene que distinguir invitado de usuario registrado")

    rama_invitado, rama_registrado = bloque.split("else:")
    assert "db.cargar_datos_de_ejemplo" not in rama_invitado, (
        "el invitado NO puede sembrar la base compartida del servidor")
    assert "invitado.con_portafolio_real" in rama_invitado, (
        "el invitado tiene que cargar el portafolio en SU almacén de sesión")
    assert "esta sesión" in rama_invitado, (
        "al invitado no se le habla de 'este servidor': sus datos no van ahí")
    assert "db.cargar_datos_de_ejemplo" in rama_registrado, (
        "el usuario registrado sí conserva el sembrado de ejemplo")
