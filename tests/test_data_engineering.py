# © 2026 Martín Viera. Todos los derechos reservados.
"""mvpm/data_engineering.py — el perfilador de tablas desconocidas.

Lo que se prueba acá, en orden de qué tan caro sale si falla:

 1. Que `perfilar_consulta_sql` nunca abra su propia conexión: tiene que
    delegar en `conectores.crear_ejecutor`, que es el único lugar que sabe
    imponer sólo-lectura. Una segunda vía de conexión sería el mismo riesgo
    con el doble de código para tener un bug.
 2. Que `tipar()` no rompa datos: un ID con cero a la izquierda no se vuelve
    número (pierde el cero), una fecha en texto sí se reconoce.
 3. Que `calidad()` marque lo que de verdad importa (duplicados, columna
    vacía, montos negativos) y no invente problemas sobre datos limpios.
 4. Que `detectar_claves()` encuentre la PK obvia y no la invente cuando no
    hay ninguna columna que alcance.
"""

import numpy as np
import pandas as pd
import pytest

from mvpm import conectores, data_engineering as de

# --------------------------------------------------------------------- tipar


def test_tipar_reconoce_fecha_en_texto():
    df = pd.DataFrame({"fecha_alta": ["2026-01-15", "2026-02-20", "2026-03-01"]})
    df2, cambios = de.tipar(df)
    assert pd.api.types.is_datetime64_any_dtype(df2["fecha_alta"])
    assert cambios == [("fecha_alta", "texto", "fecha")]


def test_tipar_reconoce_monto_es_uy():
    df = pd.DataFrame({"monto": ["1.234,56", "2.000,00", "10,50"]})
    df2, cambios = de.tipar(df)
    assert pd.api.types.is_numeric_dtype(df2["monto"])
    assert df2["monto"].iloc[0] == pytest.approx(1234.56)
    assert cambios == [("monto", "texto", "numérico")]


def test_tipar_reconoce_booleano_si_no():
    df = pd.DataFrame({"activo": ["Sí", "No", "Sí", "No"]})
    df2, cambios = de.tipar(df)
    assert set(df2["activo"].unique()) <= {0, 1}
    assert cambios == [("activo", "texto", "booleano (0/1)")]


def test_tipar_no_convierte_id_con_cero_a_la_izquierda():
    # Convertir "007" a número lo vuelve 7 — se pierde la identidad del código.
    df = pd.DataFrame({"codigo": ["007", "013", "099", "101"]})
    df2, cambios = de.tipar(df)
    assert df2["codigo"].dtype == object or pd.api.types.is_string_dtype(df2["codigo"])
    assert cambios == []


def test_tipar_no_toca_columnas_ya_bien_tipadas():
    df = pd.DataFrame({"n": [1, 2, 3], "f": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"])})
    df2, cambios = de.tipar(df)
    assert cambios == []
    pd.testing.assert_frame_equal(df, df2)


# --------------------------------------------------------------- rol_columna


def test_rol_columna_identifica_fecha():
    s = pd.to_datetime(["2026-01-01", "2026-01-02"])
    assert de.rol_columna("fecha_alta", pd.Series(s)) == "fecha"


def test_rol_columna_identifica_monto():
    s = pd.Series([100.0, 200.0, 300.0])
    assert de.rol_columna("monto_total", s) == "métrica_monetaria"


def test_rol_columna_identifica_flag():
    s = pd.Series([0, 1, 1, 0, 1])
    assert de.rol_columna("activo", s) == "flag"


def test_rol_columna_identifica_identificador_por_alta_cardinalidad():
    s = pd.Series([f"id_{i}" for i in range(100)])
    assert de.rol_columna("id_cliente", s) == "identificador"


# ------------------------------------------------------------------ perfilar


def test_perfilar_cuenta_nulos_y_unicos():
    df = pd.DataFrame({"a": [1, 2, None, 4], "b": ["x", "x", "y", "z"]})
    perfil = de.perfilar(df)
    assert perfil["filas"] == 4
    col_a = next(c for c in perfil["detalle"] if c["columna"] == "a")
    assert col_a["nulos"] == 1
    assert col_a["nulos_pct"] == pytest.approx(25.0)
    col_b = next(c for c in perfil["detalle"] if c["columna"] == "b")
    assert col_b["unicos"] == 3


def test_perfilar_detecta_outliers_por_iqr():
    valores = [10.0] * 20 + [1000.0]  # un outlier evidente
    df = pd.DataFrame({"monto": valores})
    perfil = de.perfilar(df)
    col = perfil["detalle"][0]
    assert col["outliers_iqr"] >= 1


def test_perfilar_columna_toda_nula_no_revienta():
    df = pd.DataFrame({"vacia": [None, None, None]})
    perfil = de.perfilar(df)
    assert perfil["detalle"][0]["nulos_pct"] == 100.0


# ------------------------------------------------------------------- calidad


def test_calidad_detecta_duplicados():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    perfil = de.perfilar(df)
    cal = de.calidad(df, perfil)
    tipos = [i["tipo"] for i in cal["issues"]]
    assert "Duplicados" in tipos


def test_calidad_no_marca_duplicados_sobre_datos_limpios():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    perfil = de.perfilar(df)
    cal = de.calidad(df, perfil)
    tipos = [i["tipo"] for i in cal["issues"]]
    assert "Duplicados" not in tipos


def test_calidad_marca_columna_practicamente_vacia_como_critico():
    # 96% de nulos: por encima del umbral de 95% que separa CRÍTICO de ALTO.
    df = pd.DataFrame({"a": range(100), "casi_vacia": [None] * 96 + [1, 2, 3, 4]})
    perfil = de.perfilar(df)
    cal = de.calidad(df, perfil)
    issue = next(i for i in cal["issues"] if i["columna"] == "casi_vacia")
    assert issue["severidad"] == "CRÍTICO"


def test_calidad_marca_columna_constante():
    df = pd.DataFrame({"a": [1, 2, 3], "siempre_igual": ["x", "x", "x"]})
    perfil = de.perfilar(df)
    cal = de.calidad(df, perfil)
    issue = next(i for i in cal["issues"] if i["columna"] == "siempre_igual")
    assert issue["tipo"] == "Constante"


def test_calidad_marca_montos_negativos_solo_en_columnas_monetarias():
    df = pd.DataFrame({"monto_total": [100.0, -50.0, 200.0]})
    perfil = de.perfilar(df)
    cal = de.calidad(df, perfil)
    issue = next(i for i in cal["issues"] if i["tipo"] == "Montos negativos")
    assert issue["columna"] == "monto_total"


def test_calidad_marca_nombres_no_aptos_para_sql():
    df = pd.DataFrame({"Nombre Cliente": [1, 2], "ok_col": [1, 2]})
    perfil = de.perfilar(df)
    cal = de.calidad(df, perfil)
    issue = next(i for i in cal["issues"] if i["tipo"] == "Nombres no aptos para SQL")
    assert "Nombre Cliente" in issue["columna"]
    assert "ok_col" not in issue["columna"]


def test_calidad_score_perfecto_en_datos_limpios():
    df = pd.DataFrame({"id": range(1, 101), "valor": np.random.default_rng(1).normal(100, 5, 100)})
    perfil = de.perfilar(df)
    cal = de.calidad(df, perfil)
    assert cal["score"] > 90


def test_calidad_issues_ordenados_por_severidad_descendente():
    df = pd.DataFrame({
        "a": [1, 1, 2, 3],                       # duplicado -> ALTO/CRÍTICO
        "medio_nulo": [1, None, 3, 4],           # nulos ~25% -> MEDIO
    })
    perfil = de.perfilar(df)
    cal = de.calidad(df, perfil)
    severidades = [de.SEVERIDAD[i["severidad"]] for i in cal["issues"]]
    assert severidades == sorted(severidades, reverse=True)


# --------------------------------------------------------------------- claves


def test_detectar_claves_pk_simple():
    df = pd.DataFrame({"id": [1, 2, 3, 4, 5], "valor": [10, 20, 30, 40, 50]})
    perfil = de.perfilar(df)
    claves = de.detectar_claves(df, perfil)
    assert claves["pk"]
    assert claves["pk"][0]["columna"] == "id"
    assert claves["pk"][0]["confianza"] == "alta"


def test_detectar_claves_no_inventa_pk_sin_columna_unica():
    df = pd.DataFrame({"categoria": ["a", "a", "b", "b", "b"] * 20})
    perfil = de.perfilar(df)
    claves = de.detectar_claves(df, perfil)
    assert claves["pk"] == []


def test_detectar_claves_pk_compuesta():
    # anio/mes como texto: así su rol es "dimensión" (candidata a PK compuesta
    # en detectar_claves) en vez de "métrica", que no entra en esa búsqueda.
    rng = np.random.default_rng(2)
    anios = rng.integers(2020, 2026, 200)
    meses = rng.integers(1, 13, 200)
    df = pd.DataFrame({"anio": anios, "mes": meses}).drop_duplicates().reset_index(drop=True)
    df["anio"] = df["anio"].astype(str)
    df["mes"] = df["mes"].astype(str)
    perfil = de.perfilar(df)
    claves = de.detectar_claves(df, perfil)
    assert claves["pk"], "debería encontrar al menos una combinación sin duplicados"
    assert claves["pk"][0]["tipo"] == "PK compuesta"


# --------------------------------------------------------------------- tiempo


def test_analizar_tiempo_devuelve_none_sin_columna_de_fecha():
    df = pd.DataFrame({"a": [1, 2, 3]})
    perfil = de.perfilar(df)
    assert de.analizar_tiempo(df, perfil) is None


def test_analizar_tiempo_calcula_cobertura_y_huecos():
    fechas = pd.date_range("2026-01-01", "2026-01-10", freq="D").tolist()
    fechas.pop(3)  # un hueco a propósito
    df = pd.DataFrame({"fecha_evento": fechas})
    df2, _ = de.tipar(df)
    perfil = de.perfilar(df2)
    t = de.analizar_tiempo(df2, perfil)
    assert t is not None
    assert t["columna"] == "fecha_evento"
    assert t["dias_faltantes"] == 1


# ------------------------------------------------------------------------ ddl


def test_generar_ddl_sanea_nombres_y_mapea_tipos():
    df = pd.DataFrame({"Id Cliente": [1, 2, 3], "Nombre Cliente": ["a", "b", "c"]})
    perfil = de.perfilar(df)
    claves = de.detectar_claves(df, perfil)
    ddl = de.generar_ddl("mi tabla rara!", perfil, claves)
    assert "CREATE TABLE mi_tabla_rara" in ddl
    assert "Id_Cliente" in ddl or "Id_Cliente".lower() in ddl.lower()
    assert "BIGINT" in ddl
    assert "NVARCHAR(255)" in ddl


def test_generar_ddl_solo_agrega_pk_con_confianza_alta():
    df = pd.DataFrame({"id": [1, 2, 3], "v": [1, 2, 3]})
    perfil = de.perfilar(df)
    claves_altas = de.detectar_claves(df, perfil)
    ddl_con_pk = de.generar_ddl("t", perfil, claves_altas)
    assert "PRIMARY KEY" in ddl_con_pk

    ddl_sin_pk = de.generar_ddl("t", perfil, {"pk": [{"columna": "id", "tipo": "PK candidata", "confianza": "media"}]})
    assert "PRIMARY KEY" not in ddl_sin_pk


# ------------------------------------------------------------------- reporte


def test_perfilar_tabla_orquesta_el_pipeline_completo():
    df = pd.DataFrame({
        "id": [1, 2, 3, 4],
        "fecha_alta": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
        "monto": ["100,00", "200,00", "300,00", "400,00"],
    })
    reporte = de.perfilar_tabla("clientes", df)
    assert reporte.nombre == "clientes"
    assert reporte.perfil["filas"] == 4
    assert reporte.claves["pk"][0]["columna"] == "id"
    assert reporte.tiempo is not None
    assert "CREATE TABLE clientes" in reporte.ddl
    assert len(reporte.cambios_tipado) == 2  # fecha_alta y monto


# --------------------------------------------------------------------- excel


def test_exportar_excel_bytes_produce_un_archivo_abrible():
    df = pd.DataFrame({"id": [1, 1, 2], "monto": [100.0, 100.0, -5.0]})
    reporte = de.perfilar_tabla("t", df)
    contenido = de.exportar_excel_bytes(reporte)
    assert contenido[:2] == b"PK"  # cabecera de zip/xlsx
    hojas = pd.read_excel(pd_io(contenido), sheet_name=None, engine="openpyxl")
    assert "Perfil" in hojas
    assert "Calidad" in hojas  # hay issues: duplicado y monto negativo


def pd_io(contenido: bytes):
    import io
    return io.BytesIO(contenido)


# ----------------------------------------------------------------------- SQL


def test_perfilar_consulta_sql_delega_en_conectores(monkeypatch):
    """No tiene que existir SQLAlchemy ni una base real: sólo probar que
    `perfilar_consulta_sql` llama a `conectores.crear_ejecutor` con la cadena
    recibida y perfila lo que esa función devuelva — nunca abre su propia
    conexión."""
    llamadas = []

    def ejecutor_falso(sql):
        llamadas.append(sql)
        return pd.DataFrame({"id": [1, 2, 3], "valor": [10, 20, 30]})

    def crear_ejecutor_falso(cadena_conexion):
        llamadas.append(("cadena", cadena_conexion))
        return ejecutor_falso

    monkeypatch.setattr(conectores, "crear_ejecutor", crear_ejecutor_falso)
    reporte = de.perfilar_consulta_sql("postgresql://u:p@host/db", "SELECT * FROM clientes",
                                       nombre="clientes_sql")
    assert reporte.nombre == "clientes_sql"
    assert reporte.perfil["filas"] == 3
    assert ("cadena", "postgresql://u:p@host/db") in llamadas
    assert "SELECT * FROM clientes" in llamadas


def test_perfilar_consulta_sql_propaga_el_error_de_lectura(monkeypatch):
    """Un DELETE/UPDATE tiene que rechazarse — el mismo guardia que usan todos
    los conectores existentes, no uno nuevo escrito a mano para este módulo."""
    def crear_ejecutor_real(cadena_conexion):
        def ejecutar(sql):
            conectores.validar_solo_lectura(sql)
            return pd.DataFrame()
        return ejecutar

    monkeypatch.setattr(conectores, "crear_ejecutor", crear_ejecutor_real)
    with pytest.raises(conectores.ConsultaInsegura):
        de.perfilar_consulta_sql("sqlite:///:memory:", "DELETE FROM clientes")


def test_perfilar_consulta_sql_sin_sqlalchemy_da_error_claro(monkeypatch):
    """Si SQLAlchemy no está instalado, `conectores.crear_ejecutor` ya lo
    explica en castellano — acá sólo se prueba que ese error llegue tal cual
    hasta quien llamó `perfilar_consulta_sql`, sin que se lo trague."""
    def crear_ejecutor_sin_driver(cadena_conexion):
        raise RuntimeError("Para conectarse a un ERP hace falta SQLAlchemy y el driver del motor.")

    monkeypatch.setattr(conectores, "crear_ejecutor", crear_ejecutor_sin_driver)
    with pytest.raises(RuntimeError, match="SQLAlchemy"):
        de.perfilar_consulta_sql("mssql://x", "SELECT 1")
