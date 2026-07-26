"""Conectores a los ERP más usados: SAP, Oracle, Dynamics y JD Edwards.

Sin esto, cada implementación arranca con alguien escribiendo a mano la consulta
contra el ERP del cliente, adivinando nombres de tabla y peleando con los
formatos raros que cada sistema usa para fechas y montos. Eso es la mitad de las
horas de una integración.

Cómo está pensado, y por qué así:

* **Los perfiles son un punto de partida, no una verdad.** Traen las tablas y
  campos de fábrica de cada ERP, que es lo que sirve para arrancar. Pero un SAP
  o un JDE con diez años de vida está personalizado: campos agregados, vistas
  propias, tablas Z. Por eso todo perfil se puede pisar y la consulta se puede
  reemplazar entera.

* **Primero se sondea, después se extrae.** `sondear()` verifica que las tablas
  y columnas existan ANTES de correr la extracción. Es la diferencia entre
  "faltan las columnas PLFAZ y PLSEZ en PROJ" y un error de base de datos de
  cuarenta líneas que no le dice nada a nadie.

* **Sólo lectura, siempre.** Las consultas son SELECT y el módulo no expone
  ninguna forma de escribir. Nadie va a autorizar conectar una herramienta nueva
  a su ERP productivo si existe la posibilidad de que le toque un dato.

* **La salida entra por el importador.** `convertir()` deja un DataFrame que
  `importer.detectar_columnas()` y `importer.validar()` procesan igual que un
  Excel: mismo mapeo revisable, mismo informe previo, misma detección de
  duplicados. Un conector no es una vía rápida que saltea los controles.

Las conversiones de fecha y monto (Julian de JDE, YYYYMMDD de SAP, el 1900 de
Dynamics) son la parte que más errores silenciosos causa y están testeadas.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta

import pandas as pd

# --------------------------------------------------------------- conversiones


def fecha_sap(valor) -> str | None:
    """SAP guarda las fechas como texto YYYYMMDD, y el vacío como '00000000'."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    if isinstance(valor, (pd.Timestamp, date)):
        d = valor.date() if isinstance(valor, pd.Timestamp) else valor
        return None if d.year <= 1900 else d.isoformat()
    s = str(valor).strip()
    if not re.fullmatch(r"\d{8}", s) or s == "00000000":
        return None
    try:
        return date(int(s[:4]), int(s[4:6]), int(s[6:])).isoformat()
    except ValueError:
        return None


def fecha_jde(valor) -> str | None:
    """JD Edwards guarda las fechas en Julian CYYDDD.

    C es el siglo (0 = 1900, 1 = 2000), YY el año y DDD el día del año. O sea
    124001 es el 1 de enero de 2024. Leído como número común daría cualquier
    cosa, y es el error clásico de una integración con JDE.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    s = str(valor).strip()
    if s in {"", "0", "0.0"}:
        return None
    if s.endswith(".0"):
        s = s[:-2]
    if not s.isdigit() or len(s) > 6:
        return None
    s = s.zfill(6)
    siglo, anio, dia = int(s[0]), int(s[1:3]), int(s[3:])
    if not 1 <= dia <= 366:
        return None
    try:
        base = date(1900 + siglo * 100 + anio, 1, 1)
    except ValueError:
        return None
    resultado = base + timedelta(days=dia - 1)
    return None if resultado.year != 1900 + siglo * 100 + anio else resultado.isoformat()


def fecha_dynamics(valor) -> str | None:
    """Dynamics AX/F&O usa 1900-01-01 como 'sin fecha' en vez de NULL."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    try:
        d = pd.Timestamp(valor).date()
    except (ValueError, TypeError):
        return None
    return None if d.year <= 1900 else d.isoformat()


def monto_implicito(valor, decimales: int = 2) -> float | None:
    """JDE guarda importes como enteros con decimales implícitos: 150000 = 1500,00.

    Los decimales dependen del diccionario de datos de cada instalación, así que
    es configurable — y por eso conviene contrastar un par de importes contra el
    ERP antes de dar la carga por buena.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    try:
        return float(valor) / (10 ** decimales)
    except (ValueError, TypeError):
        return None


def _passthrough(valor):
    return None if valor is None or (isinstance(valor, float) and pd.isna(valor)) else valor


TRANSFORMACIONES = {
    "fecha_sap": fecha_sap,
    "fecha_jde": fecha_jde,
    "fecha_dynamics": fecha_dynamics,
    "monto_jde": monto_implicito,
    "directo": _passthrough,
}


# ------------------------------------------------------------------- perfiles


@dataclass(frozen=True)
class Campo:
    """Una columna del SELECT y a qué campo del sistema corresponde."""
    columna: str
    destino: str
    transformacion: str = "directo"
    nota: str = ""


@dataclass(frozen=True)
class Consulta:
    tablas: tuple[str, ...]
    sql: str
    campos: tuple[Campo, ...]
    nota: str = ""

    def columnas(self) -> list[str]:
        return [c.columna for c in self.campos]


@dataclass(frozen=True)
class Perfil:
    clave: str
    nombre: str
    familia: str
    dialecto: str                      # sqlserver | oracle | hana | db2 | generico
    esquema_default: str
    consultas: dict[str, Consulta]
    como_conectar: str = ""
    advertencias: tuple[str, ...] = ()


# --- SAP ---------------------------------------------------------------------
# Módulo PS (Project System). PROJ es la definición de proyecto y PRPS los
# elementos PEP colgados de ella. Los costos viven en COSP por período
# (WKG001..WKG016) y se enganchan por OBJNR, que es la clave de objeto que SAP
# usa para todo lo que acumula costos.

_SAP_PROYECTOS = Consulta(
    tablas=("PROJ", "PRPS"),
    sql="""
SELECT p.PSPID  AS proyecto,
       p.POST1  AS descripcion,
       p.VERNR  AS responsable_nro,
       p.PLFAZ  AS fecha_inicio,
       p.PLSEZ  AS fecha_fin,
       p.VBUKR  AS sociedad,
       p.PRCTR  AS centro_beneficio
FROM {esquema}PROJ p
WHERE p.LOEVM <> 'X'
""".strip(),
    campos=(
        Campo("proyecto", "nombre", nota="ID de definición de proyecto (PSPID)"),
        Campo("descripcion", "descripcion_larga"),
        Campo("sociedad", "portafolio", nota="Sociedad (código de empresa)"),
        Campo("centro_beneficio", "segmento"),
        Campo("fecha_inicio", "fecha_inicio", "fecha_sap"),
        Campo("fecha_fin", "fecha_fin", "fecha_sap"),
        Campo("responsable_nro", "sponsor",
              nota="Número de responsable; para el nombre hay que cruzar con la tabla de personal"),
    ),
    nota="LOEVM <> 'X' saca los proyectos marcados para borrado.",
)

_SAP_TAREAS = Consulta(
    tablas=("PRPS", "PROJ"),
    sql="""
SELECT w.POSID  AS tarea,
       w.POST1  AS descripcion,
       p.PSPID  AS proyecto,
       w.VERNA  AS responsable,
       w.PSTRT  AS fecha_inicio,
       w.PENDE  AS fecha_fin,
       w.STUFE  AS nivel
FROM {esquema}PRPS w
JOIN {esquema}PROJ p ON p.PSPNR = w.PSPHI
WHERE w.LOEVM <> 'X'
""".strip(),
    campos=(
        Campo("tarea", "titulo", nota="Elemento PEP (POSID)"),
        Campo("proyecto", "proyecto"),
        Campo("responsable", "responsable"),
        Campo("fecha_inicio", "fecha_inicio", "fecha_sap"),
        Campo("fecha_fin", "vencimiento", "fecha_sap"),
    ),
    nota="PRPS.PSPHI apunta al PSPNR interno de PROJ — no al PSPID visible.",
)

SAP = Perfil(
    clave="sap_ps",
    nombre="SAP ERP / S4HANA — Project System (PS)",
    familia="SAP",
    dialecto="hana",
    esquema_default="SAPABAP1.",
    consultas={"proyectos": _SAP_PROYECTOS, "tareas": _SAP_TAREAS},
    como_conectar="Vía ODBC contra HANA, o pidiendo al equipo de SAP una vista "
                  "de solo lectura. En muchas empresas el acceso directo a las "
                  "tablas está cerrado y hay que ir por CDS views o una extracción.",
    advertencias=(
        "El esquema cambia según la instalación: SAPABAP1 en HANA, SAPSR3 en "
        "instalaciones viejas sobre Oracle o DB2. Ajustalo antes de sondear.",
        "Los costos no están en PROJ: hay que ir a COSP por OBJNR y sumar los "
        "períodos WKG001..WKG016, filtrando WRTTP='04' para real y '01' para plan.",
        "Si la empresa usa redes y actividades (AFKO/AFVC) además de elementos "
        "PEP, las tareas finas están ahí y no en PRPS.",
    ),
)

# --- Oracle EBS --------------------------------------------------------------

_ORACLE_PROYECTOS = Consulta(
    tablas=("PA_PROJECTS_ALL", "PA_PROJECT_STATUSES", "HR_ALL_ORGANIZATION_UNITS"),
    sql="""
SELECT p.SEGMENT1                AS numero,
       p.NAME                    AS nombre,
       p.DESCRIPTION             AS descripcion,
       o.NAME                    AS organizacion,
       s.PROJECT_STATUS_NAME     AS estado,
       p.START_DATE              AS fecha_inicio,
       p.COMPLETION_DATE         AS fecha_fin,
       p.PROJECT_TYPE            AS tipo
FROM {esquema}PA_PROJECTS_ALL p
LEFT JOIN {esquema}PA_PROJECT_STATUSES s
       ON s.PROJECT_STATUS_CODE = p.PROJECT_STATUS_CODE
LEFT JOIN {esquema}HR_ALL_ORGANIZATION_UNITS o
       ON o.ORGANIZATION_ID = p.CARRYING_OUT_ORGANIZATION_ID
""".strip(),
    campos=(
        Campo("nombre", "nombre"),
        Campo("organizacion", "portafolio"),
        Campo("tipo", "segmento"),
        Campo("fecha_inicio", "fecha_inicio"),
        Campo("fecha_fin", "fecha_fin"),
        Campo("descripcion", "descripcion_larga"),
    ),
)

_ORACLE_TAREAS = Consulta(
    tablas=("PA_TASKS", "PA_PROJECTS_ALL"),
    sql="""
SELECT t.TASK_NAME       AS tarea,
       t.TASK_NUMBER     AS numero,
       p.NAME            AS proyecto,
       t.START_DATE      AS fecha_inicio,
       t.COMPLETION_DATE AS fecha_fin
FROM {esquema}PA_TASKS t
JOIN {esquema}PA_PROJECTS_ALL p ON p.PROJECT_ID = t.PROJECT_ID
""".strip(),
    campos=(
        Campo("tarea", "titulo"),
        Campo("proyecto", "proyecto"),
        Campo("fecha_inicio", "fecha_inicio"),
        Campo("fecha_fin", "vencimiento"),
    ),
)

ORACLE_EBS = Perfil(
    clave="oracle_ebs",
    nombre="Oracle E-Business Suite — Projects (PA)",
    familia="Oracle",
    dialecto="oracle",
    esquema_default="APPS.",
    consultas={"proyectos": _ORACLE_PROYECTOS, "tareas": _ORACLE_TAREAS},
    como_conectar="Vía ODBC/JDBC contra la base con un usuario de solo lectura "
                  "sobre el esquema APPS.",
    advertencias=(
        "Las tablas _ALL traen todas las unidades operativas juntas. Si la "
        "empresa tiene varias, filtrá por ORG_ID o vas a mezclar carteras.",
        "El presupuesto no está en PA_PROJECTS_ALL: sale de PA_BUDGET_VERSIONS "
        "y PA_BUDGET_LINES, y hay que elegir la versión vigente.",
    ),
)

ORACLE_FUSION = Perfil(
    clave="oracle_fusion",
    nombre="Oracle Fusion Cloud — Project Portfolio Management",
    familia="Oracle",
    dialecto="oracle",
    esquema_default="FUSION.",
    consultas={
        "proyectos": Consulta(
            tablas=("PJF_PROJECTS_ALL_VL",),
            sql="""
SELECT p.PROJECT_NUMBER    AS numero,
       p.NAME              AS nombre,
       p.DESCRIPTION       AS descripcion,
       p.START_DATE        AS fecha_inicio,
       p.COMPLETION_DATE   AS fecha_fin,
       p.PROJECT_STATUS_CODE AS estado
FROM {esquema}PJF_PROJECTS_ALL_VL p
""".strip(),
            campos=(
                Campo("nombre", "nombre"),
                Campo("fecha_inicio", "fecha_inicio"),
                Campo("fecha_fin", "fecha_fin"),
                Campo("descripcion", "descripcion_larga"),
            ),
        ),
    },
    como_conectar="En Fusion Cloud normalmente NO hay acceso directo a la base. "
                  "Lo habitual es exportar por BI Publisher o consumir la API "
                  "REST y traer el resultado como archivo.",
    advertencias=(
        "Éste es el perfil menos probable de funcionar por SQL directo: Oracle "
        "no da acceso a la base en Cloud. Sirve si la empresa replica a un "
        "datawarehouse propio. Si no, conviene exportar e importar el archivo.",
    ),
)

# --- Microsoft Dynamics ------------------------------------------------------

_DYN_FO_PROYECTOS = Consulta(
    tablas=("PROJTABLE", "PROJGROUP"),
    sql="""
SELECT t.PROJID           AS proyecto,
       t.NAME             AS nombre,
       t.PROJGROUPID      AS grupo,
       t.STATUS           AS estado,
       t.DATAAREAID       AS empresa,
       t.PSAPROJSTARTDATE AS fecha_inicio,
       t.PSASCHEDENDDATE  AS fecha_fin
FROM {esquema}PROJTABLE t
""".strip(),
    campos=(
        Campo("nombre", "nombre"),
        Campo("grupo", "portafolio"),
        Campo("empresa", "segmento", nota="DATAAREAID es la entidad legal"),
        Campo("fecha_inicio", "fecha_inicio", "fecha_dynamics"),
        Campo("fecha_fin", "fecha_fin", "fecha_dynamics"),
    ),
    nota="Si hay varias entidades legales, filtrá por DATAAREAID.",
)

DYNAMICS_FO = Perfil(
    clave="dynamics_fo",
    nombre="Microsoft Dynamics 365 Finance & Operations (AX)",
    familia="Microsoft",
    dialecto="sqlserver",
    esquema_default="dbo.",
    consultas={"proyectos": _DYN_FO_PROYECTOS},
    como_conectar="ODBC a SQL Server. En la nube se usa la base de entidad de "
                  "datos exportada (BYOD) o Azure Synapse Link, no la productiva.",
    advertencias=(
        "Los nombres de campo de fechas cambiaron entre AX 2012 y D365 F&O: "
        "PSAPROJSTARTDATE puede llamarse distinto en tu versión. Sondeá primero.",
        "STATUS es un enumerado numérico, no texto — el mapeo de estados hay que "
        "confirmarlo contra la instalación.",
        "En la nube no hay acceso a la base de producción: se trabaja sobre BYOD "
        "o Synapse Link.",
    ),
)

DYNAMICS_PO = Perfil(
    clave="dynamics_po",
    nombre="Microsoft Dynamics 365 Project Operations (Dataverse)",
    familia="Microsoft",
    dialecto="sqlserver",
    esquema_default="dbo.",
    consultas={
        "proyectos": Consulta(
            tablas=("msdyn_project",),
            sql="""
SELECT p.msdyn_subject        AS nombre,
       p.msdyn_scheduledstart AS fecha_inicio,
       p.msdyn_scheduledend   AS fecha_fin,
       p.statecode            AS estado
FROM {esquema}msdyn_project p
""".strip(),
            campos=(
                Campo("nombre", "nombre"),
                Campo("fecha_inicio", "fecha_inicio", "fecha_dynamics"),
                Campo("fecha_fin", "fecha_fin", "fecha_dynamics"),
            ),
        ),
        "tareas": Consulta(
            tablas=("msdyn_projecttask", "msdyn_project"),
            sql="""
SELECT t.msdyn_subject        AS tarea,
       p.msdyn_subject        AS proyecto,
       t.msdyn_scheduledstart AS fecha_inicio,
       t.msdyn_scheduledend   AS fecha_fin
FROM {esquema}msdyn_projecttask t
LEFT JOIN {esquema}msdyn_project p ON p.msdyn_projectid = t.msdyn_project
""".strip(),
            campos=(
                Campo("tarea", "titulo"),
                Campo("proyecto", "proyecto"),
                Campo("fecha_fin", "vencimiento", "fecha_dynamics"),
            ),
        ),
    },
    como_conectar="Endpoint TDS de Dataverse (permite SQL de solo lectura) o la "
                  "Web API. El endpoint TDS hay que habilitarlo en el entorno.",
    advertencias=(
        "El endpoint TDS es de solo lectura por diseño, que es justo lo que "
        "necesitamos, pero suele venir apagado y lo tiene que habilitar un admin.",
    ),
)

DYNAMICS_BC = Perfil(
    clave="dynamics_bc",
    nombre="Microsoft Dynamics 365 Business Central / NAV — Jobs",
    familia="Microsoft",
    dialecto="sqlserver",
    esquema_default="dbo.",
    consultas={
        "proyectos": Consulta(
            tablas=("Job",),
            sql="""
SELECT j.[No_]             AS numero,
       j.[Description]     AS nombre,
       j.[Starting Date]   AS fecha_inicio,
       j.[Ending Date]     AS fecha_fin,
       j.[Status]          AS estado
FROM {esquema}[{empresa}$Job] j
""".strip(),
            campos=(
                Campo("nombre", "nombre"),
                Campo("fecha_inicio", "fecha_inicio", "fecha_dynamics"),
                Campo("fecha_fin", "fecha_fin", "fecha_dynamics"),
            ),
            nota="En NAV/BC las tablas llevan el nombre de la empresa adelante: "
                 "«CRONUS$Job». Por eso el SQL tiene un {empresa} para completar.",
        ),
    },
    como_conectar="ODBC a SQL Server contra la base de NAV/BC on-premise.",
    advertencias=(
        "El nombre de tabla incluye la empresa y, en versiones nuevas, un GUID "
        "de extensión: «CRONUS$Job$437dbf0e-...». Sondeá para ver el nombre real.",
    ),
)

# --- JD Edwards --------------------------------------------------------------
# En JDE los proyectos son unidades de negocio (F0006), extendidas por F51006
# cuando está el módulo de Job Cost. Las órdenes de trabajo (F4801) hacen de
# tareas. Todo campo lleva el prefijo de dos letras de su tabla.

_JDE_PROYECTOS = Consulta(
    tablas=("F0006",),
    sql="""
SELECT b.MCMCU  AS unidad_negocio,
       b.MCDL01 AS nombre,
       b.MCCO   AS compania,
       b.MCSTYL AS tipo,
       b.MCRP01 AS categoria
FROM {esquema}F0006 b
""".strip(),
    campos=(
        Campo("nombre", "nombre"),
        Campo("compania", "portafolio"),
        Campo("tipo", "segmento"),
        Campo("unidad_negocio", "codigo_externo"),
    ),
    nota="F0006 es el maestro de unidades de negocio. Si está Job Cost, "
         "F51006 agrega fechas y datos de obra.",
)

_JDE_TAREAS = Consulta(
    tablas=("F4801",),
    sql="""
SELECT w.WADOCO AS orden,
       w.WADL01 AS descripcion,
       w.WAMCU  AS unidad_negocio,
       w.WASRST AS estado,
       w.WASTRT AS fecha_inicio,
       w.WADRQJ AS fecha_requerida
FROM {esquema}F4801 w
""".strip(),
    campos=(
        Campo("descripcion", "titulo"),
        Campo("unidad_negocio", "proyecto"),
        Campo("fecha_inicio", "fecha_inicio", "fecha_jde"),
        Campo("fecha_requerida", "vencimiento", "fecha_jde"),
    ),
    nota="Las fechas de JDE son Julian CYYDDD y se convierten con fecha_jde.",
)

JD_EDWARDS = Perfil(
    clave="jde_e1",
    nombre="Oracle JD Edwards EnterpriseOne — Job Cost / Work Orders",
    familia="Oracle",
    dialecto="oracle",
    esquema_default="PRODDTA.",
    consultas={"proyectos": _JDE_PROYECTOS, "tareas": _JDE_TAREAS},
    como_conectar="ODBC/JDBC contra el esquema de datos de negocio (PRODDTA en "
                  "producción, CRPDTA en el ambiente de pruebas).",
    advertencias=(
        "Las fechas son Julian CYYDDD: 124001 es el 1/1/2024. Leerlas como "
        "número común es el error clásico de una integración con JDE.",
        "Los importes vienen como enteros con decimales implícitos: 150000 puede "
        "ser 1.500,00. La cantidad de decimales está en el diccionario de datos "
        "de cada instalación — verificá un par de importes contra el ERP.",
        "Los textos vienen con espacios de relleno a la derecha; el importador "
        "los recorta solo.",
        "Los presupuestos de obra están en F0902 por cuenta y período (GBAN01.."
        "GBAN12), filtrando por tipo de libro: AA es real, BA es presupuesto.",
    ),
)

# --- genéricos ---------------------------------------------------------------

GENERICO_SQL = Perfil(
    clave="generico_sql",
    nombre="Base SQL propia (SQL Server / PostgreSQL / MySQL / Oracle)",
    familia="Genérico",
    dialecto="generico",
    esquema_default="",
    consultas={},
    como_conectar="Cualquier base a la que se pueda llegar por ODBC o "
                  "SQLAlchemy. Escribís la consulta y el resultado entra por el "
                  "mismo mapeo revisable que un Excel.",
    advertencias=("Escribí siempre un SELECT. El módulo rechaza cualquier otra cosa.",),
)


PERFILES: dict[str, Perfil] = {
    p.clave: p for p in (SAP, ORACLE_EBS, ORACLE_FUSION, DYNAMICS_FO, DYNAMICS_PO,
                         DYNAMICS_BC, JD_EDWARDS, GENERICO_SQL)
}


def perfiles() -> list[Perfil]:
    return list(PERFILES.values())


def perfil(clave: str) -> Perfil:
    if clave not in PERFILES:
        raise ValueError(f"Perfil de ERP desconocido: {clave!r}")
    return PERFILES[clave]


def familias() -> dict[str, list[Perfil]]:
    salida: dict[str, list[Perfil]] = {}
    for p in PERFILES.values():
        salida.setdefault(p.familia, []).append(p)
    return salida


# ------------------------------------------------------------ armado del SQL

_PROHIBIDO = re.compile(
    r"\b(insert|update|delete|drop|truncate|alter|create|grant|revoke|merge|exec|"
    r"execute|call)\b", re.IGNORECASE)


class ConsultaInsegura(ValueError):
    """La consulta hace algo más que leer."""


def validar_solo_lectura(sql: str) -> None:
    """Rechaza cualquier cosa que no sea un SELECT.

    No pretende ser una defensa contra alguien decidido — para eso está el
    usuario de solo lectura en la base, que es la protección de verdad. Sirve
    para que un error de tipeo no termine escribiendo en el ERP del cliente.
    """
    limpio = re.sub(r"--[^\n]*", " ", sql)
    limpio = re.sub(r"/\*.*?\*/", " ", limpio, flags=re.DOTALL)
    if not limpio.strip():
        raise ConsultaInsegura("La consulta está vacía.")
    if not re.match(r"^\s*(select|with)\b", limpio, re.IGNORECASE):
        raise ConsultaInsegura("La consulta tiene que empezar con SELECT.")
    if _PROHIBIDO.search(limpio):
        prohibida = _PROHIBIDO.search(limpio).group(0)
        raise ConsultaInsegura(
            f"La consulta contiene «{prohibida.upper()}». Los conectores son de "
            f"solo lectura: no se puede escribir en el ERP.")
    if ";" in limpio.strip().rstrip(";"):
        raise ConsultaInsegura("No se permite más de una sentencia.")


def sql_de(clave_perfil: str, tipo: str, *, esquema: str | None = None,
           empresa: str = "", limite: int | None = None) -> str:
    """Devuelve la consulta lista para correr, con esquema y límite aplicados."""
    p = perfil(clave_perfil)
    if tipo not in p.consultas:
        raise ValueError(
            f"El perfil «{p.nombre}» no trae una consulta de {tipo}. "
            f"Trae: {', '.join(p.consultas) or 'ninguna'}.")
    esq = p.esquema_default if esquema is None else esquema
    if esq and not esq.endswith("."):
        esq += "."
    sql = p.consultas[tipo].sql.format(esquema=esq, empresa=empresa)
    if limite:
        sql = _aplicar_limite(sql, p.dialecto, limite)
    validar_solo_lectura(sql)
    return sql


def _aplicar_limite(sql: str, dialecto: str, limite: int) -> str:
    """Cada motor limita filas a su manera; para una prueba hay que acotar."""
    if dialecto == "oracle":
        return f"SELECT * FROM (\n{sql}\n) WHERE ROWNUM <= {limite}"
    if dialecto == "sqlserver":
        return re.sub(r"^\s*SELECT\b", f"SELECT TOP {limite}", sql, count=1,
                      flags=re.IGNORECASE)
    return f"{sql}\nLIMIT {limite}"          # hana, postgres, mysql, sqlite


# ------------------------------------------------------------------- sondeo


@dataclass
class Sondeo:
    """Qué encontró y qué no antes de intentar la extracción de verdad."""
    perfil: str
    tipo: str
    tablas_ok: list[str] = field(default_factory=list)
    tablas_faltantes: list[str] = field(default_factory=list)
    columnas_ok: list[str] = field(default_factory=list)
    columnas_faltantes: list[str] = field(default_factory=list)
    detalle: dict[str, str] = field(default_factory=dict)   # tabla → error del motor
    error: str | None = None

    @property
    def sirve(self) -> bool:
        return not self.error and not self.tablas_faltantes and not self.columnas_faltantes

    def resumen(self) -> str:
        if self.error:
            return f"No se pudo conectar o consultar: {self.error}"
        if self.tablas_faltantes:
            return (f"Faltan tablas: {', '.join(self.tablas_faltantes)}. "
                    f"Puede ser el esquema equivocado o que el módulo no esté instalado.")
        if self.columnas_faltantes:
            return (f"Las tablas están, pero faltan columnas: "
                    f"{', '.join(self.columnas_faltantes)}. Es lo esperable en un "
                    f"ERP personalizado — ajustá la consulta con los nombres reales.")
        return (f"Todo en orden: {len(self.tablas_ok)} tabla(s) y "
                f"{len(self.columnas_ok)} columna(s) encontradas.")


def sondear(ejecutar, clave_perfil: str, tipo: str, *,
            esquema: str | None = None, empresa: str = "") -> Sondeo:
    """Corre la consulta pidiendo cero filas para ver si el esquema coincide.

    `ejecutar` es una función que recibe SQL y devuelve un DataFrame. Se pasa
    desde afuera para poder probar esto sin un ERP al lado — y para que el
    módulo no dependa de ningún driver en particular.
    """
    p = perfil(clave_perfil)
    s = Sondeo(perfil=p.nombre, tipo=tipo)
    if tipo not in p.consultas:
        s.error = f"El perfil no trae consulta de {tipo}."
        return s
    consulta = p.consultas[tipo]

    esq = p.esquema_default if esquema is None else esquema
    if esq and not esq.endswith("."):
        esq += "."

    for tabla in consulta.tablas:
        try:
            ejecutar(_aplicar_limite(f"SELECT * FROM {esq}{tabla}", p.dialecto, 1))
            s.tablas_ok.append(tabla)
        except Exception as exc:                       # no existe, sin permiso, driver
            s.tablas_faltantes.append(tabla)
            s.detalle.setdefault(tabla, str(exc)[:200])
    if s.tablas_faltantes:
        return s

    try:
        muestra = ejecutar(sql_de(clave_perfil, tipo, esquema=esquema,
                                  empresa=empresa, limite=1))
    except Exception as exc:
        s.error = str(exc)[:300]
        return s

    presentes = {str(c).lower() for c in muestra.columns}
    for c in consulta.columnas():
        (s.columnas_ok if c.lower() in presentes else s.columnas_faltantes).append(c)
    return s


# --------------------------------------------------------------- extracción


def convertir(df: pd.DataFrame, clave_perfil: str, tipo: str) -> pd.DataFrame:
    """Aplica las conversiones del perfil y renombra a los campos del sistema.

    La salida entra tal cual por `importer.detectar_columnas()` /
    `importer.validar()`: mismo mapeo revisable y mismo informe previo que un
    archivo subido a mano.
    """
    p = perfil(clave_perfil)
    if tipo not in p.consultas:
        raise ValueError(f"El perfil «{p.nombre}» no trae consulta de {tipo}.")

    columnas = {str(c).lower(): c for c in df.columns}
    salida = pd.DataFrame(index=df.index)
    for campo in p.consultas[tipo].campos:
        origen = columnas.get(campo.columna.lower())
        if origen is None:
            continue
        fn = TRANSFORMACIONES.get(campo.transformacion, _passthrough)
        serie = df[origen]
        if campo.transformacion == "directo":
            # Los ERP de mainframe rellenan con espacios a la derecha.
            serie = serie.map(lambda v: v.strip() if isinstance(v, str) else v)
        else:
            serie = serie.map(fn)
        salida[campo.destino] = serie
    return salida


def extraer(ejecutar, clave_perfil: str, tipo: str, *,
            esquema: str | None = None, empresa: str = "",
            limite: int | None = None) -> pd.DataFrame:
    """Sondeo → consulta → conversión. Devuelve algo listo para el importador."""
    sql = sql_de(clave_perfil, tipo, esquema=esquema, empresa=empresa, limite=limite)
    return convertir(ejecutar(sql), clave_perfil, tipo)


# --------------------------------------------------------------- conexión


def crear_ejecutor(cadena_conexion: str):
    """Devuelve una función `ejecutar(sql) -> DataFrame` sobre esa conexión.

    Se apoya en SQLAlchemy, que es lo que pandas usa para hablar con cualquier
    motor. Si no está instalado se avisa en castellano en vez de reventar con un
    ImportError que no le dice nada al usuario.
    """
    try:
        from sqlalchemy import create_engine, text
    except ImportError as exc:                          # pragma: no cover
        raise RuntimeError(
            "Para conectarse a un ERP hace falta SQLAlchemy y el driver del "
            "motor. Instalalos con: pip install sqlalchemy pyodbc "
            "(o cx_Oracle / psycopg2 según el ERP)."
        ) from exc

    motor = create_engine(cadena_conexion)

    def ejecutar(sql: str) -> pd.DataFrame:
        validar_solo_lectura(sql)
        with motor.connect() as conn:
            return pd.read_sql_query(text(sql), conn)

    return ejecutar
