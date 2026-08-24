# © 2026 Martín Viera. Todos los derechos reservados.
"""Ingeniería de datos: perfila CUALQUIER tabla — no sólo proyectos y tareas.

Antes de importar un archivo grande y desconocido (o de conectar una base por
primera vez), la pregunta no es "¿a qué campo de MVPM corresponde esta
columna?" —eso lo resuelve `mvpm/importer.py`— sino una más básica: "¿qué tan
sucio está esto, y con qué me voy a encontrar?" Esa pregunta es la mitad de las
horas de cualquier puesta en marcha con datos reales, y hasta ahora no tenía
respuesta dentro del producto.

Este módulo la contesta sin asumir ningún esquema:

* `tipar()` corrige columnas mal tipadas (fechas y montos que llegaron como
  texto, booleanos disfrazados de "Sí"/"No") ANTES de perfilar, porque perfilar
  una fecha-como-texto da estadísticas de texto y no dice nada útil.
* `perfilar()` calcula nulos, únicos, percentiles y outliers por columna.
* `calidad()` traduce el perfil en un score 0-100 por seis dimensiones y una
  lista de problemas priorizada, con la acción concreta para cada uno.
* `detectar_claves()` sugiere la clave primaria (simple o compuesta) sin que
  nadie tenga que decirle cuál es.
* `analizar_tiempo()` mide cobertura, huecos y frescura sobre la primera
  columna de fecha que encuentra.
* `generar_ddl()` deja un `CREATE TABLE` de partida, con nombres saneados para
  SQL y la PK detectada.

## Por qué no reutiliza `mvpm/importer.py`

`importer.parsear_numero()` / `parsear_fecha()` trabajan sobre un valor a la
vez, con un esquema de campos fijo (los de proyecto/tarea) y un informe de
error pensado para esa importación guiada. Acá el esquema es desconocido y lo
que hace falta es inferencia vectorizada sobre una columna entera de cualquier
forma — dos problemas distintos, dos módulos distintos.

## De dónde vienen los datos

Un archivo (CSV/Excel, ya lo lee `app/app.py` con pandas) o una base SQL. Para
SQL, este módulo NO abre su propia conexión: reutiliza
`mvpm.conectores.crear_ejecutor()` y su `validar_solo_lectura()`, que ya
resuelven "sólo SELECT, nunca conectado a las claves del cliente en el
código" — inventar una segunda forma de conectarse a una base sería el mismo
riesgo con el doble de superficie para tener un bug.
"""

from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# --------------------------------------------------------------- utilidades


def _slug(texto: str, maxlen: int = 60) -> str:
    """Nombre de columna/tabla apto para SQL: sin espacios, acentos ni símbolos."""
    s = unicodedata.normalize("NFKD", str(texto))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^0-9A-Za-z_]+", "_", s).strip("_")
    return (s[:maxlen] or "columna")


PAT_FECHA = re.compile(r"(fec|fch|date|dt_|_dt|fecha|periodo|mes|alta|baja|vto|venc)", re.I)
PAT_ID = re.compile(r"(^id|_id$|codigo|cod_|nro|numero|documento|cedula|ruc|cuit|clave|key)", re.I)
PAT_MONTO = re.compile(r"(monto|importe|saldo|valor|precio|total|deuda|cobrad|pagad|amount|revenue)", re.I)


def _a_numero(serie: pd.Series) -> pd.Series:
    """'1.234,56' (es-UY) o '$ 1,234.56' (en-US) → numérico. Ambigüedad rota por
    cuál separador aparece más seguido en la columna, no por configuración."""
    s = serie.astype("string").str.strip()
    s = s.str.replace(r"[^\d,.\-]", "", regex=True)
    con_coma = s.str.contains(",", na=False).mean()
    con_punto = s.str.contains(r"\.", na=False).mean()
    if con_coma > 0.3 and con_punto > 0.3:
        s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    elif con_coma > 0.3:
        s = s.str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def _a_fecha(serie: pd.Series) -> pd.Series:
    for kwargs in ({"format": "mixed", "dayfirst": True}, {"dayfirst": True}, {}):
        try:
            return pd.to_datetime(serie, errors="coerce", **kwargs)
        except (ValueError, TypeError):
            continue
    return pd.Series([pd.NaT] * len(serie), index=serie.index)


# ------------------------------------------------------------------- tipado


def tipar(df: pd.DataFrame) -> tuple[pd.DataFrame, list[tuple[str, str, str]]]:
    """Corrige columnas mal tipadas. Devuelve (df_corregido, cambios).

    `cambios` es (columna, tipo_antes, tipo_después) — se muestra en la
    interfaz para que quede claro qué tocó el sistema antes de perfilar, en
    vez de que el usuario descubra un tipo distinto sin que nadie se lo avisara.
    """
    df = df.copy()
    cambios: list[tuple[str, str, str]] = []
    for c in df.columns:
        s = df[c]
        if pd.api.types.is_numeric_dtype(s) or pd.api.types.is_datetime64_any_dtype(s):
            continue
        no_nulos = s.dropna()
        if no_nulos.empty:
            continue
        muestra = no_nulos.astype(str).head(2000)

        vals = set(muestra.str.strip().str.lower().unique())
        if vals and vals <= {"si", "sí", "no", "true", "false", "s", "n", "1", "0", "y", "yes"}:
            mapa = {"si": 1, "sí": 1, "s": 1, "true": 1, "y": 1, "yes": 1, "1": 1,
                    "no": 0, "n": 0, "false": 0, "0": 0}
            df[c] = s.astype(str).str.strip().str.lower().map(mapa)
            cambios.append((str(c), "texto", "booleano (0/1)"))
            continue

        parece_fecha = bool(PAT_FECHA.search(str(c))) or bool(
            muestra.str.match(r"^\s*\d{2,4}[-/.]\d{1,2}[-/.]\d{1,4}").mean() > 0.7)
        if parece_fecha:
            conv = _a_fecha(s)
            if conv.notna().mean() > 0.8:
                df[c] = conv
                cambios.append((str(c), "texto", "fecha"))
                continue

        # Los IDs con ceros a la izquierda ("007") no son números: convertirlos
        # los rompe (pierden el cero). Se los deja como texto a propósito.
        ceros_izq = muestra.str.match(r"^0\d+$").mean() > 0.1
        parece_numero = muestra.str.match(
            r"^\s*[-+]?\s*[$€\s]{0,4}\s*\d[\d.,]*\s*%?\s*$").mean() > 0.85
        if not ceros_izq and parece_numero:
            conv = _a_numero(s)
            if conv.notna().mean() > 0.85 and conv.notna().sum() > 0:
                df[c] = conv
                cambios.append((str(c), "texto", "numérico"))
    return df, cambios


def rol_columna(nombre, serie: pd.Series) -> str:
    """Clasifica el rol de negocio de la columna, para priorizar qué mostrar."""
    n = str(nombre)
    if pd.api.types.is_datetime64_any_dtype(serie):
        return "fecha"
    if PAT_ID.search(n) and serie.nunique(dropna=True) > max(20, len(serie) * 0.5):
        return "identificador"
    if PAT_ID.search(n):
        return "clave_foránea"
    if pd.api.types.is_numeric_dtype(serie):
        if PAT_MONTO.search(n):
            return "métrica_monetaria"
        if serie.dropna().isin([0, 1]).all() and serie.nunique(dropna=True) <= 2:
            return "flag"
        return "métrica"
    if serie.nunique(dropna=True) <= 50:
        return "dimensión"
    return "texto_libre"


# ----------------------------------------------------------------- perfilado


def perfilar(df: pd.DataFrame) -> dict:
    """Nulos, únicos, percentiles y outliers por columna. No decide nada por sí
    solo — `calidad()` es quien traduce esto en problemas y acciones."""
    filas = len(df)
    columnas = []
    for c in df.columns:
        s = df[c]
        nn = int(s.notna().sum())
        nulos = filas - nn
        uniq = int(s.nunique(dropna=True))
        info = {
            "columna": str(c), "dtype": str(s.dtype), "rol": rol_columna(c, s),
            "nulos": nulos, "nulos_pct": (nulos / filas * 100) if filas else 0.0,
            "unicos": uniq, "unicos_pct": (uniq / nn * 100) if nn else 0.0,
        }
        try:
            if pd.api.types.is_numeric_dtype(s) and nn:
                d = s.dropna().astype(float)
                q1, q3 = float(d.quantile(0.25)), float(d.quantile(0.75))
                iqr = q3 - q1
                lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                info.update({
                    "min": float(d.min()), "mediana": float(d.median()), "max": float(d.max()),
                    "media": float(d.mean()), "ceros": int((d == 0).sum()),
                    "negativos": int((d < 0).sum()),
                    "outliers_iqr": int(((d < lo) | (d > hi)).sum()),
                })
            elif pd.api.types.is_datetime64_any_dtype(s) and nn:
                d = s.dropna()
                info.update({"min": str(d.min()), "max": str(d.max()),
                            "rango_dias": int((d.max() - d.min()).days)})
            else:
                top = s.astype("string").value_counts(dropna=True).head(5)
                info["top_valores"] = [(str(k), int(v)) for k, v in top.items()]
        except (ValueError, TypeError, OverflowError):
            pass  # una columna rara no puede tumbar el perfil de las otras
        columnas.append(info)
    return {"filas": filas, "columnas": len(df.columns), "detalle": columnas}


# ------------------------------------------------------------------- calidad

SEVERIDAD = {"CRÍTICO": 3, "ALTO": 2, "MEDIO": 1, "BAJO": 0}


def calidad(df: pd.DataFrame, perfil: dict) -> dict:
    """Score 0-100 por seis dimensiones + lista de problemas priorizada, cada
    uno con la acción concreta para resolverlo — no sólo "hay nulos", sino
    qué hacer con ellos."""
    filas = max(perfil["filas"], 1)
    issues = []

    def agregar(severidad, tipo, columna, detalle, accion):
        issues.append({"severidad": severidad, "tipo": tipo, "columna": columna,
                       "detalle": detalle, "accion": accion})

    dup = int(df.duplicated().sum())
    if dup:
        agregar("CRÍTICO" if dup / filas > 0.05 else "ALTO", "Duplicados", "(fila completa)",
                f"{dup} filas duplicadas ({dup / filas * 100:.1f}%)",
                "Definir la clave de negocio y deduplicar antes de cargar.")

    for c in perfil["detalle"]:
        nombre, nulos_pct = c["columna"], c["nulos_pct"]
        if nulos_pct >= 95:
            agregar("CRÍTICO", "Columna vacía", nombre, f"{nulos_pct:.1f}% de nulos",
                    "Descartarla o confirmar con el origen si dejó de poblarse.")
        elif nulos_pct >= 40:
            agregar("ALTO", "Nulos masivos", nombre, f"{nulos_pct:.1f}% de nulos",
                    "Imputar con criterio de negocio o tratar el vacío como categoría propia.")
        elif nulos_pct >= 5:
            agregar("MEDIO", "Nulos", nombre, f"{nulos_pct:.1f}% de nulos",
                    "Documentar el valor por defecto que se le va a dar.")

        if c["unicos"] == 1 and c["nulos"] < filas:
            agregar("MEDIO", "Constante", nombre, "Un solo valor distinto",
                    "No aporta información: se puede sacar del modelo.")

        if c.get("negativos", 0) and c["rol"] == "métrica_monetaria":
            agregar("ALTO", "Montos negativos", nombre, f"{c['negativos']} valores < 0",
                    "Confirmar si son notas de crédito/reversas o error de origen.")

        if c.get("outliers_iqr", 0) and c["outliers_iqr"] / filas > 0.05:
            agregar("MEDIO", "Outliers", nombre,
                    f"{c['outliers_iqr']} fuera de 1,5×RIC ({c['outliers_iqr'] / filas * 100:.1f}%)",
                    "Revisar antes de usar en un promedio o un total.")

    malos = [str(c) for c in df.columns
             if re.search(r"[^0-9A-Za-z_]", str(c)) or str(c)[:1].isdigit()]
    if malos:
        agregar("MEDIO", "Nombres no aptos para SQL", ", ".join(malos[:8]),
                f"{len(malos)} columnas con espacios, acentos o símbolos",
                "Normalizar a snake_case antes de escribir en una base (ver DDL sugerido).")

    completitud = 100 - float(np.mean([c["nulos_pct"] for c in perfil["detalle"]] or [0]))
    unicidad = 100 - (dup / filas * 100)
    consistencia = 100 - min(100, len(malos) / max(len(df.columns), 1) * 100)
    n_out = sum(c.get("outliers_iqr", 0) for c in perfil["detalle"])
    validez = 100 - min(100, n_out / max(filas * max(len(df.columns), 1), 1) * 1000)
    n_const = sum(1 for c in perfil["detalle"] if c["unicos"] <= 1)
    utilidad = 100 - min(100, n_const / max(len(df.columns), 1) * 100)
    criticos = sum(1 for i in issues if i["severidad"] == "CRÍTICO")
    integridad = max(0.0, 100 - criticos * 15)

    dimensiones = {"Completitud": completitud, "Unicidad": unicidad,
                  "Consistencia": consistencia, "Validez": validez,
                  "Utilidad": utilidad, "Integridad": integridad}
    orden = sorted(issues, key=lambda i: -SEVERIDAD[i["severidad"]])
    return {"score": float(np.mean(list(dimensiones.values()))),
            "dimensiones": dimensiones, "issues": orden}


# -------------------------------------------------------------------- claves


def detectar_claves(df: pd.DataFrame, perfil: dict) -> dict:
    """Sugiere la clave primaria — simple, candidata o compuesta — sin que
    nadie tenga que decirle a mano cuál es."""
    filas = max(len(df), 1)
    pk = []
    for c in perfil["detalle"]:
        col = c["columna"]
        if c["nulos"] == 0 and c["unicos"] == filas and filas > 1:
            pk.append({"columna": col, "tipo": "PK simple", "confianza": "alta"})
        elif c["unicos"] >= filas * 0.98 and c["nulos_pct"] < 1 and filas > 50:
            pk.append({"columna": col, "tipo": "PK candidata", "confianza": "media"})

    if not pk and filas > 1:
        candidatas = [c["columna"] for c in perfil["detalle"]
                     if c["rol"] in ("clave_foránea", "identificador", "dimensión", "fecha")][:6]
        for i in range(len(candidatas)):
            for j in range(i + 1, len(candidatas)):
                try:
                    if not df.duplicated(subset=[candidatas[i], candidatas[j]]).any():
                        pk.append({"columna": f"{candidatas[i]} + {candidatas[j]}",
                                  "tipo": "PK compuesta", "confianza": "media"})
                        break
                except (KeyError, TypeError):
                    continue
            if pk:
                break
    return {"pk": pk}


# --------------------------------------------------------------------- tiempo


def analizar_tiempo(df: pd.DataFrame, perfil: dict, columna: str | None = None) -> dict | None:
    """Cobertura, huecos y frescura sobre una columna de fecha. None si no hay
    ninguna — no es un error, muchas tablas no son series de tiempo."""
    fechas = [c["columna"] for c in perfil["detalle"] if c["rol"] == "fecha"]
    col = columna if (columna and columna in df.columns) else (fechas[0] if fechas else None)
    if not col:
        return None
    s = pd.to_datetime(df[col], errors="coerce").dropna()
    if s.empty:
        return None
    diario = s.dt.floor("D").value_counts().sort_index()
    idx = pd.date_range(diario.index.min(), diario.index.max(), freq="D")
    faltantes = idx.difference(diario.index)
    mensual = s.dt.to_period("M").value_counts().sort_index()
    return {
        "columna": col, "desde": str(s.min()), "hasta": str(s.max()),
        "dias_cubiertos": int(diario.shape[0]), "dias_rango": int(len(idx)),
        "dias_faltantes": int(len(faltantes)),
        "frescura_dias": int((pd.Timestamp.now().normalize() - s.max().normalize()).days),
        "serie_mensual": {str(k): int(v) for k, v in mensual.items()},
        "futuras": int((s > pd.Timestamp.now()).sum()),
    }


# ----------------------------------------------------------------------- DDL

_TIPO_SQL = {"int64": "BIGINT", "Int64": "BIGINT", "int32": "INT",
            "float64": "DECIMAL(18,4)", "float32": "DECIMAL(18,4)", "bool": "BIT"}


def generar_ddl(nombre_tabla: str, perfil: dict, claves: dict) -> str:
    """`CREATE TABLE` de partida: nombres saneados, tipos inferidos, la PK
    detectada. Es un punto de partida para el DBA, no la verdad final —
    ninguna herramienta puede saber las reglas de negocio de una base ajena."""
    lineas = ["-- Generado por el perfilador de datos de MV Project Management",
              f"-- a partir de '{nombre_tabla}'. Revisar antes de correr.",
              f"CREATE TABLE {_slug(nombre_tabla)} ("]
    campos = []
    for c in perfil["detalle"]:
        col, dt = _slug(c["columna"], 60), c["dtype"]
        if "datetime" in dt:
            tipo = "DATETIME2"
        elif dt in _TIPO_SQL:
            tipo = _TIPO_SQL[dt]
        elif "int" in dt.lower():
            tipo = "BIGINT"
        elif "float" in dt.lower():
            tipo = "DECIMAL(18,4)"
        else:
            tipo = "NVARCHAR(255)"
        nn = "NOT NULL" if c["nulos"] == 0 else "NULL"
        campos.append(f"    {col:<40} {tipo:<16} {nn}")
    lineas.append(",\n".join(campos))
    pk_alta = [k for k in claves["pk"] if k["confianza"] == "alta"]
    if pk_alta:
        col_pk = _slug(pk_alta[0]["columna"], 60)
        lineas.append(f"    ,CONSTRAINT PK_{_slug(nombre_tabla, 25)} PRIMARY KEY ({col_pk})")
    lineas.append(");")
    return "\n".join(lineas)


# --------------------------------------------------------------- orquestación


@dataclass
class ReportePerfilado:
    nombre: str
    perfil: dict
    calidad: dict
    claves: dict
    tiempo: dict | None
    cambios_tipado: list[tuple[str, str, str]] = field(default_factory=list)
    ddl: str = ""


def perfilar_tabla(nombre: str, df: pd.DataFrame) -> ReportePerfilado:
    """El pipeline completo sobre una tabla: tipar → perfilar → calidad →
    claves → tiempo → DDL. Es lo único que necesita llamar la interfaz."""
    df_tipado, cambios = tipar(df)
    perfil = perfilar(df_tipado)
    cal = calidad(df_tipado, perfil)
    claves = detectar_claves(df_tipado, perfil)
    tiempo = analizar_tiempo(df_tipado, perfil)
    ddl = generar_ddl(nombre, perfil, claves)
    return ReportePerfilado(nombre=nombre, perfil=perfil, calidad=cal, claves=claves,
                            tiempo=tiempo, cambios_tipado=cambios, ddl=ddl)


# ------------------------------------------------------------------------ SQL


def perfilar_consulta_sql(cadena_conexion: str, consulta: str,
                          nombre: str = "consulta_sql") -> ReportePerfilado:
    """Perfila el resultado de una consulta SQL de sólo lectura.

    No abre la conexión acá: `mvpm.conectores.crear_ejecutor()` ya sabe hacerlo
    y ya exige que la consulta sea un SELECT (`validar_solo_lectura()`). Una
    segunda implementación de "conectate a una base" sería el mismo riesgo con
    el doble de código para tener un bug — se importa adentro de la función,
    igual que en conectores.py, para no exigir SQLAlchemy a quien sólo importa
    archivos.
    """
    from mvpm import conectores
    ejecutar = conectores.crear_ejecutor(cadena_conexion)
    df = ejecutar(consulta)
    return perfilar_tabla(nombre, df)


# ---------------------------------------------------------------------- Excel


def exportar_excel_bytes(reporte: ReportePerfilado) -> bytes:
    """El informe completo en un .xlsx: perfil, calidad y claves en hojas
    separadas — mismo patrón que `mvpm/exporters.py::to_excel_bytes`, pero acá
    vive aparte porque el perfil de una tabla arbitraria no tiene nada que ver
    con el esquema de portafolio que exporta ese módulo."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        pd.DataFrame(reporte.perfil["detalle"]).to_excel(xw, sheet_name="Perfil", index=False)
        if reporte.calidad["issues"]:
            pd.DataFrame(reporte.calidad["issues"]).to_excel(
                xw, sheet_name="Calidad", index=False)
        if reporte.claves["pk"]:
            pd.DataFrame(reporte.claves["pk"]).to_excel(
                xw, sheet_name="Claves candidatas", index=False)
        if reporte.cambios_tipado:
            pd.DataFrame(reporte.cambios_tipado,
                        columns=["columna", "tipo_antes", "tipo_después"]).to_excel(
                xw, sheet_name="Tipado corregido", index=False)
    return buf.getvalue()
