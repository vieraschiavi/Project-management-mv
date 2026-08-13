# © 2026 Martín Viera. Todos los derechos reservados.
"""Tests del importador guiado.

El caso que importa es el último (`test_archivo_real_de_cliente`): un Excel con
nombres de columna inventados, estados en castellano, plata con símbolo y puntos,
fechas dd/mm y filas repetidas. Si ese pasa, el cliente puede importar solo.
"""

import pandas as pd
import pytest

from mvpm import importer as imp


# ------------------------------------------------------------------- números

@pytest.mark.parametrize("crudo,esperado", [
    ("1.234.567,89", 1234567.89),
    ("$ 1.234.567", 1234567.0),
    ("1,234,567.89", 1234567.89),
    ("USD 1.500", 1500.0),
    ("1234,56", 1234.56),
    ("1234.56", 1234.56),
    ("  42 ", 42.0),
    ("(1.500)", -1500.0),
    ("-2.000", -2000.0),
    (1500, 1500.0),
    ("", None),
    ("-", None),
    ("N/A", None),
    ("no es un número", None),
])
def test_parsear_numero(crudo, esperado):
    assert imp.parsear_numero(crudo).valor == esperado


def test_punto_de_miles_se_marca_ambiguo():
    """1.500 se lee como mil quinientos, pero el usuario tiene que enterarse."""
    assert imp.parsear_numero("1.500").ambiguo is True
    assert imp.parsear_numero("1.234.567").ambiguo is False
    assert imp.parsear_numero("1234,56").ambiguo is False


# -------------------------------------------------------------------- fechas

@pytest.mark.parametrize("crudo,esperado", [
    ("15/04/2026", "2026-04-15"),
    ("15-04-2026", "2026-04-15"),
    ("2026-04-15", "2026-04-15"),
    ("15.04.2026", "2026-04-15"),
    ("31/12/2025", "2025-12-31"),
    ("15/04/26", "2026-04-15"),
    ("2026-04-15 09:30:00", "2026-04-15"),
    (pd.Timestamp("2026-04-15"), "2026-04-15"),
    ("", None),
    ("cuando se pueda", None),
])
def test_parsear_fecha(crudo, esperado):
    assert imp.parsear_fecha(crudo).valor == esperado


def test_dia_primero_y_aviso_de_ambiguedad():
    r = imp.parsear_fecha("03/04/2026")
    assert r.valor == "2026-04-03"      # 3 de abril, no 4 de marzo
    assert r.ambiguo is True
    assert imp.parsear_fecha("25/04/2026").ambiguo is False


def test_fecha_serial_de_excel():
    assert imp.parsear_fecha("45000").valor == "2023-03-15"


# -------------------------------------------------------------------- valores

@pytest.mark.parametrize("crudo,esperado", [
    ("En curso", "in_progress"), ("EN PROCESO", "in_progress"), ("WIP", "in_progress"),
    ("Pendiente", "todo"), ("Sin empezar", "todo"), ("Backlog", "todo"),
    ("Finalizada", "done"), ("Completado", "done"), ("Cerrada", "done"),
    ("Bloqueada", "blocked"), ("En espera", "blocked"), ("On hold", "blocked"),
    ("Tarea finalizada", "done"),
    ("cualquier cosa", None), ("", None),
])
def test_normalizar_estado(crudo, esperado):
    assert imp.normalizar_estado(crudo) == esperado


@pytest.mark.parametrize("crudo,esperado", [
    ("Alta", "Alta"), ("ALTA", "Alta"), ("urgente", "Alta"), ("High", "Alta"),
    ("Crítica", "Alta"), ("Media", "Media"), ("normal", "Media"), ("Baja", "Baja"),
    ("low", "Baja"), ("", None), ("verde", None),
])
def test_normalizar_nivel(crudo, esperado):
    assert imp.normalizar_nivel(crudo) == esperado


def test_niveles_numericos_usan_convencion_jira():
    assert imp.normalizar_nivel("1") == "Alta"
    assert imp.normalizar_nivel("3") == "Baja"
    assert imp.columna_es_numerica(pd.Series(["1", "2", "3"])) is True
    assert imp.columna_es_numerica(pd.Series(["Alta", "Baja"])) is False


def test_acentos_y_mayusculas_dan_igual():
    assert imp.normalizar("Fecha Inicio") == imp.normalizar("FECHA_INICIO")
    assert imp.normalizar("Críticidad") == imp.normalizar("criticidad")
    assert imp.normalizar("Área") == imp.normalizar("area")


def test_area_responsable_es_portafolio_no_sponsor():
    """Caso real: 'Área Responsable' es el área dueña, no el sponsor."""
    df = pd.DataFrame(columns=["Proyecto", "Área Responsable"])
    s = imp.detectar_columnas(df, "proyectos")
    assert s["portafolio"].columna == "Área Responsable"
    assert s["sponsor"].columna is None


# --------------------------------------------------------- detección de columnas

def test_detecta_columnas_con_nombres_libres():
    df = pd.DataFrame(columns=["Nombre del Proyecto", "Área", "Monto Total",
                               "Fecha de Inicio", "Importancia"])
    s = imp.detectar_columnas(df, "proyectos")
    assert s["nombre"].columna == "Nombre del Proyecto"
    assert s["presupuesto"].columna == "Monto Total"
    assert s["fecha_inicio"].columna == "Fecha de Inicio"
    assert s["criticidad"].columna == "Importancia"


def test_una_columna_no_se_asigna_a_dos_campos():
    """'Prioridad' es sinónimo de criticidad y de prioridad: sólo puede ir a uno."""
    df = pd.DataFrame(columns=["Tarea", "Prioridad"])
    s = imp.detectar_columnas(df, "tareas")
    usadas = [x.columna for x in s.values() if x.columna]
    assert len(usadas) == len(set(usadas))


def test_las_palabras_vacias_no_bajan_la_confianza():
    """«Nombre del Proyecto» tiene que dar verde, no amarillo.

    Si todo sale amarillo el indicador no sirve para nada: el usuario deja de
    mirarlo justo cuando hace falta.
    """
    df = pd.DataFrame(columns=["Nombre del Proyecto", "Fecha de Inicio",
                               "Área Responsable"])
    s = imp.detectar_columnas(df, "proyectos")
    assert s["nombre"].confianza >= 0.9
    assert s["fecha_inicio"].confianza >= 0.9
    # Éste sí es una suposición razonable: tiene que quedar marcado como tal.
    assert 0.55 <= s["portafolio"].confianza < 0.9


def test_columna_desconocida_queda_sin_detectar():
    df = pd.DataFrame(columns=["Proyecto", "ZZZ_CAMPO_9"])
    s = imp.detectar_columnas(df, "proyectos")
    assert s["nombre"].columna == "Proyecto"
    assert s["presupuesto"].columna is None


# ------------------------------------------------------------------ validación

def test_falta_campo_requerido():
    rep = imp.validar(pd.DataFrame({"otra": [1]}), "proyectos", {})
    assert not rep.puede_importar
    assert "Nombre del proyecto" in rep.faltan_requeridos


def test_fila_sin_nombre_se_descarta():
    df = pd.DataFrame({"Proyecto": ["Uno", None, "Dos"]})
    rep = imp.validar(df, "proyectos", {"nombre": "Proyecto"})
    assert rep.filas_validas == 2
    assert rep.filas_rechazadas == 1


def test_duplicados_dentro_del_archivo():
    df = pd.DataFrame({"Proyecto": ["Obra A", "Obra A", "Obra B"]})
    rep = imp.validar(df, "proyectos", {"nombre": "Proyecto"})
    assert rep.filas_validas == 2
    assert rep.duplicados_archivo == 1


def test_duplicados_contra_la_base():
    df = pd.DataFrame({"Proyecto": ["Obra A", "Obra B"]})
    existentes = pd.DataFrame({"nombre": ["OBRA A"]})     # mismo nombre, otra grafía
    rep = imp.validar(df, "proyectos", {"nombre": "Proyecto"}, existentes=existentes)
    assert rep.duplicados_base == 1
    assert rep.filas_validas == 1


def test_se_puede_pedir_importar_los_duplicados_igual():
    df = pd.DataFrame({"Proyecto": ["Obra A", "Obra A"]})
    rep = imp.validar(df, "proyectos", {"nombre": "Proyecto"}, omitir_duplicados=False)
    assert rep.filas_validas == 2


def test_valor_ilegible_avisa_pero_no_descarta_la_fila():
    df = pd.DataFrame({"Proyecto": ["Obra A"], "Monto": ["ochocientos"]})
    rep = imp.validar(df, "proyectos", {"nombre": "Proyecto", "presupuesto": "Monto"})
    assert rep.filas_validas == 1
    assert len(rep.avisos) == 1
    assert "presupuesto" not in rep.filas[0]


def test_tarea_se_asocia_al_proyecto_por_nombre():
    proyectos = pd.DataFrame({"_id": [7, 9], "nombre": ["Obra A", "Obra B"]})
    df = pd.DataFrame({"Tarea": ["Excavar", "Pintar"], "Obra": ["Obra B", "obra a"]})
    rep = imp.validar(df, "tareas", {"titulo": "Tarea", "proyecto": "Obra"},
                      proyectos=proyectos)
    assert [f["proyecto_id"] for f in rep.filas] == [9, 7]


def test_tarea_sin_proyecto_valido_se_descarta_si_no_hay_default():
    proyectos = pd.DataFrame({"_id": [7], "nombre": ["Obra A"]})
    df = pd.DataFrame({"Tarea": ["Excavar"], "Obra": ["Obra Fantasma"]})
    rep = imp.validar(df, "tareas", {"titulo": "Tarea", "proyecto": "Obra"},
                      proyectos=proyectos)
    assert rep.filas_validas == 0
    assert rep.filas_rechazadas == 1


def test_tarea_sin_proyecto_valido_cae_al_default_si_se_indica():
    proyectos = pd.DataFrame({"_id": [7], "nombre": ["Obra A"]})
    df = pd.DataFrame({"Tarea": ["Excavar"], "Obra": ["Obra Fantasma"]})
    rep = imp.validar(df, "tareas", {"titulo": "Tarea", "proyecto": "Obra"},
                      proyectos=proyectos, proyecto_default_id=7)
    assert rep.filas_validas == 1
    assert rep.filas[0]["proyecto_id"] == 7
    assert len(rep.avisos) == 1


def test_responsable_se_matchea_por_nombre_o_email():
    usuarios = pd.DataFrame({"id": [3], "nombre": ["Ana Pérez"], "email": ["ana@x.com"]})
    proyectos = pd.DataFrame({"_id": [1], "nombre": ["P"]})
    df = pd.DataFrame({"Tarea": ["A", "B", "C"],
                       "Asignado a": ["ANA PEREZ", "ana@x.com", "Nadie"]})
    rep = imp.validar(df, "tareas", {"titulo": "Tarea", "responsable": "Asignado a"},
                      usuarios=usuarios, proyectos=proyectos, proyecto_default_id=1)
    assert [f.get("responsable_id") for f in rep.filas] == [3, 3, None]
    assert len(rep.avisos) == 1


def test_aviso_de_columna_por_punto_ambiguo():
    df = pd.DataFrame({"Proyecto": ["A"], "Monto": ["1.500"]})
    rep = imp.validar(df, "proyectos", {"nombre": "Proyecto", "presupuesto": "Monto"})
    assert rep.filas[0]["presupuesto"] == 1500.0
    assert any("miles" in a for a in rep.avisos_columna)


def test_aviso_de_columna_por_niveles_numericos():
    df = pd.DataFrame({"Proyecto": ["A", "B"], "Nivel": ["1", "3"]})
    rep = imp.validar(df, "proyectos", {"nombre": "Proyecto", "criticidad": "Nivel"})
    assert any("al revés" in a for a in rep.avisos_columna)


# ------------------------------------------------------------------ escritura

def test_defaults_al_escribir():
    df = pd.DataFrame({"Proyecto": ["Obra A"]})
    rep = imp.validar(df, "proyectos", {"nombre": "Proyecto"})
    fila = imp.filas_para_escribir(rep)[0]
    assert fila["portafolio"] == "Importado"
    assert fila["criticidad"] == "Media"
    assert fila["presupuesto"] == 0.0
    assert not any(k.startswith("_") for k in fila)


def test_aplicar_llama_a_la_funcion_de_escritura():
    escritas = []
    df = pd.DataFrame({"Proyecto": ["A", "B"]})
    rep = imp.validar(df, "proyectos", {"nombre": "Proyecto"})
    creadas = imp.aplicar(rep, lambda **kw: escritas.append(kw), lambda **kw: None)
    assert creadas == 2
    assert [e["nombre"] for e in escritas] == ["A", "B"]


def test_no_escribe_nada_si_falta_un_requerido():
    escritas = []
    rep = imp.validar(pd.DataFrame({"x": [1]}), "proyectos", {})
    assert imp.aplicar(rep, lambda **kw: escritas.append(kw), lambda **kw: None) == 0
    assert escritas == []


def test_la_plantilla_se_importa_a_si_misma():
    """La plantilla que descarga el cliente tiene que pasar el importador."""
    df = imp.plantilla("proyectos")
    s = imp.detectar_columnas(df, "proyectos")
    mapeo = {k: v.columna for k, v in s.items() if v.columna}
    rep = imp.validar(df, "proyectos", mapeo)
    assert rep.puede_importar
    assert rep.filas_validas == len(df)
    assert not rep.errores


# ------------------------------------------- el caso que justifica todo el módulo

def test_archivo_real_de_cliente():
    """Un Excel como los que llegan de verdad: nada coincide con el esquema."""
    df = pd.DataFrame([
        {"Nombre del Proyecto": "Migración de servidores", "Área Responsable": "TI",
         "Quien lo pide": "Gerencia", "Importancia": "ALTA",
         "Monto Total": "$ 1.234.567", "Gastado a la fecha": "320.000",
         "Fecha de Inicio": "01/03/2026", "Fecha de Cierre": "30/09/2026"},
        {"Nombre del Proyecto": "Rediseño del sitio", "Área Responsable": "Comercial",
         "Quien lo pide": "Marketing", "Importancia": "media",
         "Monto Total": "$ 400.000", "Gastado a la fecha": "-",
         "Fecha de Inicio": "15/04/2026", "Fecha de Cierre": ""},
        {"Nombre del Proyecto": "Migración de servidores", "Área Responsable": "TI",
         "Quien lo pide": "Gerencia", "Importancia": "ALTA",
         "Monto Total": "$ 1.234.567", "Gastado a la fecha": "320.000",
         "Fecha de Inicio": "01/03/2026", "Fecha de Cierre": "30/09/2026"},
        {"Nombre del Proyecto": None, "Área Responsable": "", "Quien lo pide": "",
         "Importancia": "", "Monto Total": "", "Gastado a la fecha": "",
         "Fecha de Inicio": "", "Fecha de Cierre": ""},
    ])

    sugerencias = imp.detectar_columnas(df, "proyectos")
    mapeo = {k: v.columna for k, v in sugerencias.items() if v.columna}

    # Detecta solo, sin que nadie toque el archivo.
    assert mapeo["nombre"] == "Nombre del Proyecto"
    assert mapeo["portafolio"] == "Área Responsable"
    assert mapeo["criticidad"] == "Importancia"
    assert mapeo["presupuesto"] == "Monto Total"
    assert mapeo["fecha_inicio"] == "Fecha de Inicio"

    rep = imp.validar(df, "proyectos", mapeo)

    assert rep.puede_importar
    assert rep.filas_validas == 2          # 4 filas − 1 repetida − 1 vacía
    assert rep.duplicados_archivo == 1
    assert rep.filas_rechazadas == 1

    primero = rep.filas[0]
    assert primero["nombre"] == "Migración de servidores"
    assert primero["criticidad"] == "Alta"           # venía "ALTA"
    assert primero["presupuesto"] == 1234567.0       # venía "$ 1.234.567"
    assert primero["fecha_inicio"] == "2026-03-01"   # venía "01/03/2026"

    # El segundo tiene el ejecutado en "-": no rompe, sólo queda sin dato.
    assert "ejecutado" not in rep.filas[1]


# ------------------------------------------------- end-to-end contra la base real

def test_end_to_end_contra_la_base(tmp_path, monkeypatch):
    """Importa proyectos y tareas de verdad y verifica lo que quedó guardado."""
    from mvpm import db

    monkeypatch.setattr(db, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(db, "_DB_FILE", tmp_path / "e2e.db")
    db.init_db()

    proyectos = pd.DataFrame([
        {"Nombre del Proyecto": "Obra Norte", "Área Responsable": "Ingeniería",
         "Importancia": "ALTA", "Monto Total": "$ 2.500.000",
         "Fecha de Inicio": "01/03/2026"},
        {"Nombre del Proyecto": "Obra Sur", "Área Responsable": "Ingeniería",
         "Importancia": "baja", "Monto Total": "$ 800.000",
         "Fecha de Inicio": "15/04/2026"},
    ])
    sug = imp.detectar_columnas(proyectos, "proyectos")
    rep = imp.validar(proyectos, "proyectos",
                      {k: v.columna for k, v in sug.items() if v.columna},
                      existentes=db.projects())
    assert imp.aplicar(rep, db.crear_proyecto, db.crear_tarea) == 2

    guardados = db.projects()
    assert list(guardados["nombre"]) == ["Obra Norte", "Obra Sur"]
    assert list(guardados["criticidad"]) == ["Alta", "Baja"]
    assert list(guardados["presupuesto"]) == [2500000.0, 800000.0]
    assert guardados.iloc[0]["fecha_inicio"] == "2026-03-01"
    assert list(guardados["portafolio"]) == ["Ingeniería", "Ingeniería"]

    tareas = pd.DataFrame([
        {"Actividad": "Excavación", "Obra": "Obra Sur", "Situación": "En curso",
         "Urgencia": "urgente", "Fecha límite": "30/05/2026"},
        {"Actividad": "Hormigonado", "Obra": "Obra Norte", "Situación": "Pendiente",
         "Urgencia": "normal", "Fecha límite": "30/06/2026"},
    ])
    sug_t = imp.detectar_columnas(tareas, "tareas")
    rep_t = imp.validar(tareas, "tareas",
                        {k: v.columna for k, v in sug_t.items() if v.columna},
                        proyectos=db.projects(), usuarios=db.listar_usuarios(),
                        existentes=db.tasks())
    assert imp.aplicar(rep_t, db.crear_proyecto, db.crear_tarea) == 2

    t = db.tasks()
    assert list(t["titulo"]) == ["Excavación", "Hormigonado"]
    assert list(t["estado"]) == ["in_progress", "todo"]
    assert list(t["prioridad"]) == ["Alta", "Media"]
    # Cada tarea quedó en SU proyecto, no todas en el primero.
    ids = {r["titulo"]: r["proyecto_id"] for _, r in t.iterrows()}
    assert ids["Excavación"] != ids["Hormigonado"]

    # Reimportar el mismo archivo no duplica nada.
    rep2 = imp.validar(proyectos, "proyectos",
                       {k: v.columna for k, v in sug.items() if v.columna},
                       existentes=db.projects())
    assert rep2.duplicados_base == 2
    assert imp.aplicar(rep2, db.crear_proyecto, db.crear_tarea) == 0
    assert len(db.projects()) == 2


# --------------------------------------------------- lectura del archivo real

def test_un_excel_con_miles_en_punto_no_se_lee_mil_veces_mas_chico(tmp_path):
    """Regresión: el presupuesto entraba dividido por mil, sin aviso.

    Un Excel de acá trae la plata escrita "320.000". Si se deja que pandas
    infiera el tipo al leerlo, convierte ese texto en el float 320.0 ANTES de
    que parsear_numero() lo vea — y el proyecto queda cargado con 320 pesos en
    vez de 320.000, con lo cual "sobre_presupuesto" da mal. La app lee con
    dtype=str justamente para que decida el parser del importador.
    """
    archivo = tmp_path / "portafolio.xlsx"
    pd.DataFrame([
        {"Proyecto": "Migración", "Presupuesto": "1.500.000", "Ejecutado": "320.000"},
        {"Proyecto": "Portal", "Presupuesto": "800.000", "Ejecutado": "910.000"},
    ]).to_excel(archivo, index=False)

    # Cómo lo lee la app (y por qué): todo como texto.
    df = pd.read_excel(archivo, dtype=str)
    assert imp.parsear_numero(df["Ejecutado"][0]).valor == 320_000.0
    assert imp.parsear_numero(df["Ejecutado"][1]).valor == 910_000.0

    # Y el camino contrario, que es el que fallaba: dejando adivinar a pandas.
    adivinado = pd.read_excel(archivo)
    assert imp.parsear_numero(adivinado["Ejecutado"][0]).valor == 320.0, (
        "si esto cambia, pandas dejó de convertir y el comentario de app.py "
        "sobre dtype=str hay que revisarlo")


def test_el_portafolio_importado_detecta_el_sobregasto(tmp_path):
    """El efecto de la regresión anterior sobre una decisión real: si el
    ejecutado entra mil veces más chico, nadie se entera de que se pasó."""
    from mvpm import catalog, invitado

    archivo = tmp_path / "p.xlsx"
    pd.DataFrame([
        {"Proyecto": "Portal", "Presupuesto": "800.000", "Ejecutado": "910.000"},
    ]).to_excel(archivo, index=False)
    df = pd.read_excel(archivo, dtype=str)

    almacen = invitado.almacen_vacio()
    sug = imp.detectar_columnas(df, "proyectos")
    rep = imp.validar(df, "proyectos", {k: v.columna for k, v in sug.items() if v.columna},
                      existentes=almacen.proyectos())
    imp.aplicar(rep, almacen.crear_proyecto, almacen.crear_tarea)

    fila = catalog.catalog(almacen.proyectos()).iloc[0]
    assert fila["ejecutado"] == 910_000
    assert bool(fila["sobre_presupuesto"]) is True


def test_un_legajo_con_ceros_adelante_no_pierde_los_ceros(tmp_path):
    """Regresión: "00123" se leía como el número 123.

    Los legajos, cédulas, códigos de centro de costo y teléfonos vienen con
    ceros a la izquierda que son parte del identificador. Si se leen como
    número, esos ceros se pierden y el dato deja de cruzar contra el ERP o el
    sistema de RRHH del cliente — que es justo para lo que se importa.
    """
    archivo = tmp_path / "organigrama.xlsx"
    pd.DataFrame([
        {"Legajo": "00123", "Nombre": "Ana Pérez", "Cargo": "Jefa de Obra"},
        {"Legajo": "00007", "Nombre": "Luis Gómez", "Cargo": "Gerente"},
    ]).to_excel(archivo, index=False)

    # Cómo lo lee la app: todo como texto.
    assert list(pd.read_excel(archivo, dtype=str)["Legajo"]) == ["00123", "00007"]

    # Y lo que pasaba antes, dejando que pandas infiriera el tipo.
    assert list(pd.read_excel(archivo)["Legajo"]) == [123, 7], (
        "si esto cambia, pandas dejó de convertir y hay que revisar los "
        "comentarios de app.py sobre dtype=str")


def test_el_organigrama_se_parsea_bien_leido_como_texto(tmp_path):
    """dtype=str deja las celdas vacías como NaN, no como el texto 'nan':
    quien no le reporta a nadie tiene que quedar en None, no en un jefe
    llamado "nan"."""
    from mvpm import organigrama

    archivo = tmp_path / "org.xlsx"
    pd.DataFrame([
        {"Nombre": "Ana Pérez", "Cargo": "Jefa", "Área": "Obra", "Reporta a": "Luis Gómez"},
        {"Nombre": "Luis Gómez", "Cargo": "Gerente", "Área": "Obra", "Reporta a": ""},
    ]).to_excel(archivo, index=False)

    personas = organigrama.parsear(pd.read_excel(archivo, dtype=str))
    assert personas[0]["reporta_a"] == "Luis Gómez"
    assert personas[1]["reporta_a"] is None
