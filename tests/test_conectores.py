"""Tests de los conectores a ERP.

Lo que estos tests SÍ verifican: las conversiones de fecha y monto, el armado
del SQL, el candado de solo lectura, el sondeo y el encadenado con el importador.

Lo que NO pueden verificar: que los nombres de tabla y campo de cada perfil
coincidan con la instalación de un cliente concreto. Un SAP o un JDE con años
encima está personalizado. Para eso está `sondear()`, que compara el perfil
contra la base real antes de intentar la extracción.
"""

import pandas as pd
import pytest

from mvpm import conectores as cx
from mvpm import importer as imp


# ------------------------------------------------------- fechas de cada ERP

@pytest.mark.parametrize("crudo,esperado", [
    ("20260301", "2026-03-01"),
    ("19991231", "1999-12-31"),
    ("00000000", None),          # el vacío de SAP
    ("", None),
    ("2026-03-01", None),        # SAP no guarda así; si viene así, algo cambió
    ("20261301", None),          # mes 13
    (None, None),
])
def test_fecha_sap(crudo, esperado):
    assert cx.fecha_sap(crudo) == esperado


@pytest.mark.parametrize("crudo,esperado", [
    ("124001", "2024-01-01"),    # el caso canónico de JDE
    ("124366", "2024-12-31"),    # 2024 es bisiesto: tiene día 366
    ("123365", "2023-12-31"),
    ("095365", "1995-12-31"),    # siglo 0 = 1900s
    ("100001", "2000-01-01"),
    (124001, "2024-01-01"),      # a veces llega como número
    ("124001.0", "2024-01-01"),  # y a veces como float de pandas
    ("123366", None),            # 2023 no tiene día 366
    ("124000", None),            # día 0 no existe
    ("124367", None),
    ("0", None),
    ("", None),
    (None, None),
])
def test_fecha_jde_julian(crudo, esperado):
    assert cx.fecha_jde(crudo) == esperado


def test_fecha_jde_no_se_lee_como_numero_comun():
    """El error clásico: tomar 124001 por una fecha normal."""
    assert cx.fecha_jde("124001") == "2024-01-01"      # y no 2012-40-01 ni similar


@pytest.mark.parametrize("crudo,esperado", [
    ("2026-03-01", "2026-03-01"),
    (pd.Timestamp("2026-03-01"), "2026-03-01"),
    ("1900-01-01", None),        # el "sin fecha" de Dynamics
    ("1899-12-30", None),
    (None, None),
    ("cualquier cosa", None),
])
def test_fecha_dynamics(crudo, esperado):
    assert cx.fecha_dynamics(crudo) == esperado


def test_monto_con_decimales_implicitos():
    assert cx.monto_implicito(150000) == 1500.0
    assert cx.monto_implicito(150000, decimales=0) == 150000.0
    assert cx.monto_implicito(150000, decimales=4) == 15.0
    assert cx.monto_implicito(None) is None


# --------------------------------------------------------------- perfiles

def test_estan_los_erp_pedidos():
    claves = set(cx.PERFILES)
    assert {"sap_ps", "oracle_ebs", "jde_e1"} <= claves
    assert {"dynamics_fo", "dynamics_po", "dynamics_bc"} <= claves


def test_todo_perfil_esta_completo():
    for p in cx.perfiles():
        assert p.nombre and p.familia and p.dialecto
        assert p.como_conectar, f"{p.clave} no dice cómo conectarse"
        for tipo, consulta in p.consultas.items():
            assert consulta.tablas, f"{p.clave}/{tipo} sin tablas para sondear"
            assert consulta.campos, f"{p.clave}/{tipo} sin campos mapeados"
            assert "{esquema}" in consulta.sql, f"{p.clave}/{tipo} no parametriza el esquema"


def test_los_campos_apuntan_a_campos_reales_del_importador():
    """Un destino mal escrito haría que la columna se pierda sin avisar."""
    validos = set()
    for tipo in ("proyectos", "tareas"):
        validos |= {c.clave for c in imp.campos_de(tipo)}
    validos |= {"descripcion_larga", "codigo_externo"}   # extras informativos
    for p in cx.perfiles():
        for tipo, consulta in p.consultas.items():
            for campo in consulta.campos:
                assert campo.destino in validos, \
                    f"{p.clave}/{tipo}: destino desconocido {campo.destino!r}"


def test_toda_transformacion_declarada_existe():
    for p in cx.perfiles():
        for consulta in p.consultas.values():
            for campo in consulta.campos:
                assert campo.transformacion in cx.TRANSFORMACIONES


def test_las_fechas_de_sap_y_jde_usan_su_conversion():
    """Si alguien agrega una fecha sin conversión, entra corrupta y nadie lo ve."""
    for clave, esperada in [("sap_ps", "fecha_sap"), ("jde_e1", "fecha_jde")]:
        for consulta in cx.perfil(clave).consultas.values():
            for campo in consulta.campos:
                if campo.destino in ("fecha_inicio", "fecha_fin", "vencimiento"):
                    assert campo.transformacion == esperada, \
                        f"{clave}: {campo.columna} sin {esperada}"


# ------------------------------------------------------------ armado del SQL

def test_sql_con_esquema_propio():
    sql = cx.sql_de("sap_ps", "proyectos", esquema="SAPSR3")
    assert "SAPSR3.PROJ" in sql
    assert "{esquema}" not in sql


def test_esquema_vacio_para_bases_sin_prefijo():
    sql = cx.sql_de("dynamics_fo", "proyectos", esquema="")
    assert "FROM PROJTABLE" in sql


def test_limite_por_dialecto():
    assert "TOP 5" in cx.sql_de("dynamics_fo", "proyectos", limite=5)     # SQL Server
    assert "ROWNUM <= 5" in cx.sql_de("oracle_ebs", "proyectos", limite=5)  # Oracle
    assert "LIMIT 5" in cx.sql_de("sap_ps", "proyectos", limite=5)          # HANA


def test_nav_completa_el_nombre_de_empresa():
    sql = cx.sql_de("dynamics_bc", "proyectos", empresa="CRONUS")
    assert "[CRONUS$Job]" in sql


def test_pedir_una_consulta_que_el_perfil_no_tiene():
    with pytest.raises(ValueError, match="no trae una consulta"):
        cx.sql_de("jde_e1", "inexistente")


def test_perfil_desconocido():
    with pytest.raises(ValueError, match="desconocido"):
        cx.perfil("no_existe")


# --------------------------------------------------------- candado de escritura

@pytest.mark.parametrize("sql", [
    "DELETE FROM PROJ",
    "UPDATE PROJ SET POST1 = 'x'",
    "DROP TABLE PROJ",
    "TRUNCATE TABLE PROJ",
    "INSERT INTO PROJ VALUES (1)",
    "EXEC sp_algo",
    "SELECT 1; DELETE FROM PROJ",
    "SELECT * FROM PROJ; DROP TABLE PROJ",
    "",
    "   ",
])
def test_se_rechaza_todo_lo_que_no_sea_lectura(sql):
    with pytest.raises(cx.ConsultaInsegura):
        cx.validar_solo_lectura(sql)


@pytest.mark.parametrize("sql", [
    "SELECT * FROM PROJ",
    "  select a, b from t where x = 1  ",
    "WITH x AS (SELECT 1 FROM t) SELECT * FROM x",
    "SELECT * FROM PROJ;",
])
def test_se_aceptan_las_lecturas(sql):
    cx.validar_solo_lectura(sql)


def test_no_se_cuela_una_escritura_escondida_en_un_comentario():
    """Un DELETE comentado no debe bloquear; uno real detrás de un comentario sí."""
    cx.validar_solo_lectura("SELECT * FROM t -- DELETE FROM PROJ")
    cx.validar_solo_lectura("SELECT * FROM t /* DROP TABLE x */")
    with pytest.raises(cx.ConsultaInsegura):
        cx.validar_solo_lectura("SELECT 1 /* comentario */ ; DELETE FROM PROJ")


def test_el_ejecutor_tambien_valida():
    """Aunque alguien arme el SQL a mano, no puede escribir."""
    sql_visto = []

    def falso_ejecutar(sql):
        sql_visto.append(sql)
        return pd.DataFrame({"proyecto": ["A"]})

    cx.extraer(falso_ejecutar, "sap_ps", "proyectos")
    assert sql_visto and sql_visto[0].lstrip().upper().startswith("SELECT")


# ------------------------------------------------------------------ sondeo

def _ejecutor_falso(tablas: dict[str, pd.DataFrame]):
    """Simula una base: sólo conoce las tablas que se le declaran."""
    def ejecutar(sql: str) -> pd.DataFrame:
        for nombre, df in tablas.items():
            if nombre.lower() in sql.lower():
                return df.head(1)
        raise RuntimeError('table or view does not exist')
    return ejecutar


def test_sondeo_ok():
    cols = ["proyecto", "descripcion", "responsable_nro", "fecha_inicio",
            "fecha_fin", "sociedad", "centro_beneficio"]
    ej = _ejecutor_falso({"PROJ": pd.DataFrame(columns=cols),
                          "PRPS": pd.DataFrame(columns=cols)})
    s = cx.sondear(ej, "sap_ps", "proyectos")
    assert s.sirve
    assert "PROJ" in s.tablas_ok
    assert "Todo en orden" in s.resumen()


def test_sondeo_detecta_tabla_que_no_esta():
    ej = _ejecutor_falso({"PROJ": pd.DataFrame(columns=["proyecto"])})
    s = cx.sondear(ej, "sap_ps", "proyectos")
    assert not s.sirve
    assert "PRPS" in s.tablas_faltantes
    assert "Faltan tablas" in s.resumen()
    assert "PRPS" in s.detalle          # guarda el error del motor para diagnosticar


def test_sondeo_detecta_columna_personalizada_faltante():
    """El caso real: el ERP está, pero le cambiaron los campos."""
    ej = _ejecutor_falso({
        "PROJ": pd.DataFrame(columns=["proyecto", "descripcion"]),
        "PRPS": pd.DataFrame(columns=["proyecto", "descripcion"]),
    })
    s = cx.sondear(ej, "sap_ps", "proyectos")
    assert not s.sirve
    assert not s.tablas_faltantes
    assert "fecha_inicio" in s.columnas_faltantes
    assert "personalizado" in s.resumen()


def test_sondeo_reporta_error_de_conexion():
    def explota(sql):
        raise RuntimeError("ORA-01017: invalid username/password")
    s = cx.sondear(explota, "oracle_ebs", "proyectos")
    assert not s.sirve
    assert "PA_PROJECTS_ALL" in s.tablas_faltantes


# -------------------------------------------------------------- conversión

def test_convertir_sap_traduce_fechas_y_renombra():
    crudo = pd.DataFrame([
        {"proyecto": "P-001  ", "descripcion": "Planta nueva", "sociedad": "1000",
         "centro_beneficio": "CB1", "fecha_inicio": "20260301",
         "fecha_fin": "00000000", "responsable_nro": "42"},
    ])
    df = cx.convertir(crudo, "sap_ps", "proyectos")
    assert df.iloc[0]["nombre"] == "P-001"          # recorta el relleno
    assert df.iloc[0]["fecha_inicio"] == "2026-03-01"
    assert df.iloc[0]["fecha_fin"] is None          # 00000000 es vacío, no una fecha
    assert df.iloc[0]["portafolio"] == "1000"


def test_convertir_jde_traduce_julian():
    crudo = pd.DataFrame([
        {"orden": 1001, "descripcion": "Excavación   ", "unidad_negocio": "OBRA-1",
         "estado": "40", "fecha_inicio": "124001", "fecha_requerida": "124091"},
    ])
    df = cx.convertir(crudo, "jde_e1", "tareas")
    assert df.iloc[0]["titulo"] == "Excavación"
    assert df.iloc[0]["fecha_inicio"] == "2024-01-01"
    assert df.iloc[0]["vencimiento"] == "2024-03-31"
    assert df.iloc[0]["proyecto"] == "OBRA-1"


def test_convertir_ignora_columnas_que_no_vinieron():
    crudo = pd.DataFrame([{"proyecto": "P-001"}])       # sólo una de siete
    df = cx.convertir(crudo, "sap_ps", "proyectos")
    assert list(df.columns) == ["nombre"]
    assert df.iloc[0]["nombre"] == "P-001"


def test_convertir_no_se_cae_con_basura_en_las_fechas():
    crudo = pd.DataFrame([{"proyecto": "P", "fecha_inicio": "sin definir"}])
    df = cx.convertir(crudo, "sap_ps", "proyectos")
    assert df.iloc[0]["fecha_inicio"] is None


# ------------------------------- el punto del módulo: engancha con el importador

def test_lo_extraido_del_erp_entra_por_el_importador():
    """Un conector no saltea los controles: pasa por el mismo informe previo."""
    crudo = pd.DataFrame([
        {"proyecto": "Planta Norte", "descripcion": "Ampliación", "sociedad": "1000",
         "centro_beneficio": "IND", "fecha_inicio": "20260301",
         "fecha_fin": "20260930", "responsable_nro": "42"},
        {"proyecto": "Planta Sur", "descripcion": "Refacción", "sociedad": "1000",
         "centro_beneficio": "IND", "fecha_inicio": "20260415",
         "fecha_fin": "00000000", "responsable_nro": "17"},
        {"proyecto": "Planta Norte", "descripcion": "Ampliación", "sociedad": "1000",
         "centro_beneficio": "IND", "fecha_inicio": "20260301",
         "fecha_fin": "20260930", "responsable_nro": "42"},          # repetida
    ])
    df = cx.extraer(lambda sql: crudo, "sap_ps", "proyectos")

    sugerencias = imp.detectar_columnas(df, "proyectos")
    mapeo = {k: v.columna for k, v in sugerencias.items() if v.columna}
    assert mapeo["nombre"] == "nombre"

    rep = imp.validar(df, "proyectos", mapeo)
    assert rep.puede_importar
    assert rep.filas_validas == 2                 # la repetida se descarta sola
    assert rep.duplicados_archivo == 1
    assert rep.filas[0]["fecha_inicio"] == "2026-03-01"
    assert rep.filas[0]["portafolio"] == "1000"


def test_jde_end_to_end_hasta_la_base(tmp_path, monkeypatch):
    """De unidades de negocio de JDE a proyectos guardados de verdad."""
    from mvpm import db
    monkeypatch.setattr(db, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(db, "_DB_FILE", tmp_path / "jde.db")
    db.init_db()

    crudo = pd.DataFrame([
        {"unidad_negocio": "OBRA-1 ", "nombre": "Ruta 8 tramo 3", "compania": "00100",
         "tipo": "OB", "categoria": "VIAL"},
        {"unidad_negocio": "OBRA-2 ", "nombre": "Puente Arroyo", "compania": "00100",
         "tipo": "OB", "categoria": "VIAL"},
    ])
    df = cx.extraer(lambda sql: crudo, "jde_e1", "proyectos")

    sug = imp.detectar_columnas(df, "proyectos")
    rep = imp.validar(df, "proyectos",
                      {k: v.columna for k, v in sug.items() if v.columna},
                      existentes=db.projects())
    assert imp.aplicar(rep, db.crear_proyecto, db.crear_tarea) == 2

    guardados = db.projects()
    assert list(guardados["nombre"]) == ["Ruta 8 tramo 3", "Puente Arroyo"]
    assert list(guardados["portafolio"]) == ["00100", "00100"]


def test_toda_advertencia_tiene_texto():
    """Las advertencias son la parte honesta del perfil: no pueden estar vacías."""
    for p in cx.perfiles():
        for a in p.advertencias:
            assert len(a) > 30, f"{p.clave}: advertencia demasiado escueta"
