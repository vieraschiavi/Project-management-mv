"""Importador guiado: convierte un archivo del cliente en filas cargables.

El importador viejo exigía que el archivo ya viniera con los nombres de columna
y los valores exactos que espera la base. En la práctica ningún cliente tiene
eso, así que alguien (nosotros) terminaba limpiando el Excel a mano antes de
cada implementación. Eso es la mayor parte de las horas de una puesta en marcha.

Este módulo mueve ese trabajo al producto:

* detecta a qué campo corresponde cada columna, sin importar cómo se llame;
* traduce los valores ("En curso" → in_progress, "$ 1.234.567" → 1234567.0);
* revisa TODO antes de escribir y devuelve un informe de qué va a pasar;
* detecta duplicados contra el archivo y contra la base.

El módulo no importa Streamlit a propósito: es lógica pura y testeable, y la
interfaz sólo la muestra.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime

import pandas as pd

# --------------------------------------------------------------- normalizado


def normalizar(texto) -> str:
    """Baja a minúsculas, saca acentos y deja sólo letras y números.

    Es la base de todo el matcheo: así "Fecha de Inicio", "FECHA_INICIO" y
    "fechainicio" son la misma cosa.
    """
    if texto is None or (isinstance(texto, float) and pd.isna(texto)):
        return ""
    s = unicodedata.normalize("NFKD", str(texto))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", s.lower())


# Palabras que no aportan al significado del encabezado: "Nombre del Proyecto"
# y "Nombre Proyecto" tienen que valer lo mismo.
_VACIAS = {"de", "del", "la", "el", "los", "las", "un", "una", "y", "o", "a",
           "por", "para", "en", "the", "of"}


def _tokens(texto, sin_vacias: bool = True) -> set[str]:
    s = unicodedata.normalize("NFKD", str(texto or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    t = {x for x in re.split(r"[^a-z0-9]+", s.lower()) if x}
    return (t - _VACIAS) or t if sin_vacias else t


# ------------------------------------------------------------------- valores

_ESTADOS = {
    "todo": ["todo", "to do", "pendiente", "pendientes", "sin empezar", "sin iniciar",
             "no iniciada", "no iniciado", "nueva", "nuevo", "backlog", "abierta",
             "abierto", "por hacer", "planificada", "planificado", "a fazer"],
    "in_progress": ["in progress", "in_progress", "en curso", "en progreso", "en proceso",
                    "en ejecucion", "haciendo", "doing", "wip", "activa", "activo",
                    "iniciada", "iniciado", "trabajando", "em andamento"],
    "blocked": ["blocked", "bloqueada", "bloqueado", "trabada", "trabado", "detenida",
                "detenido", "en espera", "on hold", "pausada", "pausado", "impedimento",
                "frenada", "frenado", "bloqueada por dependencia", "bloqueado"],
    "done": ["done", "hecha", "hecho", "terminada", "terminado", "finalizada",
             "finalizado", "completada", "completado", "cerrada", "cerrado", "lista",
             "listo", "ok", "entregada", "entregado", "concluida", "100", "concluido"],
}

_NIVELES = {
    "Alta": ["alta", "alto", "high", "urgente", "critica", "critico", "muy alta",
             "muy alto", "maxima", "p1", "a", "1", "3"],
    "Media": ["media", "medio", "medium", "normal", "moderada", "moderado", "estandar",
              "p2", "b", "2"],
    "Baja": ["baja", "bajo", "low", "menor", "minima", "p3", "c"],
}

# "1" y "3" aparecen en las dos escalas que se usan en la práctica: 1=Alta con
# prioridad tipo Jira, y 3=Alta con escala de 1 a 3 donde más es más grave. No
# se puede resolver mirando un valor suelto, así que se resuelve por columna
# (ver `_escala_numerica`) y se avisa.
_NUM_AMBIGUOS = {"1", "2", "3"}


def _invertir(mapa: dict[str, list[str]]) -> dict[str, str]:
    salida = {}
    for canonico, sinonimos in mapa.items():
        salida[normalizar(canonico)] = canonico
        for s in sinonimos:
            salida[normalizar(s)] = canonico
    return salida


_ESTADO_LOOKUP = _invertir(_ESTADOS)
_NIVEL_LOOKUP = _invertir(_NIVELES)


def normalizar_estado(valor) -> str | None:
    """'En curso' → 'in_progress'. Devuelve None si no lo reconoce."""
    n = normalizar(valor)
    if not n:
        return None
    if n in _ESTADO_LOOKUP:
        return _ESTADO_LOOKUP[n]
    # "Tarea finalizada", "50% en curso": buscar el sinónimo adentro del texto.
    for sinonimo, canonico in sorted(_ESTADO_LOOKUP.items(), key=lambda kv: -len(kv[0])):
        if len(sinonimo) >= 4 and sinonimo in n:
            return canonico
    return None


def normalizar_nivel(valor, escala_invertida: bool = False) -> str | None:
    """'URGENTE' → 'Alta'. Sirve para criticidad y para prioridad.

    `escala_invertida` es para las escalas 1-3 donde 3 es lo más grave; por
    defecto se asume la convención de Jira (1 = lo más grave).
    """
    n = normalizar(valor)
    if not n:
        return None
    if n in _NUM_AMBIGUOS:
        if n == "2":
            return "Media"
        alto, bajo = ("3", "1") if escala_invertida else ("1", "3")
        return "Alta" if n == alto else "Baja" if n == bajo else "Media"
    return _NIVEL_LOOKUP.get(n)


def columna_es_numerica(valores: pd.Series) -> bool:
    """¿La columna de nivel viene como números en vez de texto?

    Importa porque una columna de puros 1/2/3 es genuinamente ambigua: puede ser
    la convención de Jira (1 = lo más grave) o una escala donde 3 es lo peor.
    No se puede resolver mirando los datos, así que se asume Jira y se avisa —
    adivinar en silencio sería corromper la criticidad de toda la cartera.
    """
    vistos = [normalizar(v) for v in valores.dropna()]
    vistos = [v for v in vistos if v]
    return bool(vistos) and all(v in _NUM_AMBIGUOS for v in vistos)


# ------------------------------------------------------------------- números

_MONEDA = re.compile(r"[^\d,.\-]")


@dataclass
class ResultadoNumero:
    valor: float | None
    ambiguo: bool = False


def parsear_numero(valor) -> ResultadoNumero:
    """Entiende '$ 1.234.567,89', '1,234,567.89', 'USD 1.500' y '-'.

    Cuando el separador es ambiguo ('1.500' puede ser mil quinientos o uno coma
    cinco) se resuelve con la convención local — punto de miles — y se marca
    `ambiguo` para poder avisarle al usuario.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ResultadoNumero(None)
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return ResultadoNumero(float(valor))

    crudo = str(valor).strip()
    if not crudo or crudo in {"-", "--", "N/A", "n/a", "NA", "s/d", "S/D", "."}:
        return ResultadoNumero(None)

    negativo = crudo.startswith("(") and crudo.endswith(")")
    limpio = _MONEDA.sub("", crudo)
    if not limpio or limpio in {"-", ".", ","}:
        return ResultadoNumero(None)

    negativo = negativo or limpio.startswith("-")
    limpio = limpio.lstrip("-")
    ambiguo = False

    tiene_punto, tiene_coma = "." in limpio, "," in limpio
    if tiene_punto and tiene_coma:
        # El último separador que aparece es el decimal.
        decimal = "," if limpio.rfind(",") > limpio.rfind(".") else "."
        miles = "." if decimal == "," else ","
        limpio = limpio.replace(miles, "").replace(decimal, ".")
    elif tiene_coma:
        entero, _, resto = limpio.rpartition(",")
        if limpio.count(",") == 1 and len(resto) != 3:
            limpio = f"{entero}.{resto}"           # 1234,56 → decimal
        else:
            limpio = limpio.replace(",", "")       # 1,234,567 → miles
    elif tiene_punto:
        entero, _, resto = limpio.rpartition(".")
        if limpio.count(".") == 1 and len(resto) == 3 and entero:
            limpio = limpio.replace(".", "")       # 1.500 → convención local: miles
            ambiguo = True
        elif limpio.count(".") > 1:
            limpio = limpio.replace(".", "")

    try:
        n = float(limpio)
    except ValueError:
        return ResultadoNumero(None)
    return ResultadoNumero(-n if negativo else n, ambiguo)


# ------------------------------------------------------------------- fechas

_FORMATOS = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%y", "%d-%m-%y",
             "%d.%m.%Y", "%Y%m%d", "%d de %B de %Y", "%m/%d/%Y"]


@dataclass
class ResultadoFecha:
    valor: str | None          # ISO yyyy-mm-dd
    ambiguo: bool = False      # dd/mm vs mm/dd no se puede distinguir


def parsear_fecha(valor) -> ResultadoFecha:
    """Devuelve la fecha en ISO. Asume día primero (convención local).

    Marca `ambiguo` cuando día y mes son ambos <= 12, que es el caso donde
    03/04/2026 puede ser 3 de abril o 4 de marzo según quién exportó el archivo.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ResultadoFecha(None)
    if isinstance(valor, (pd.Timestamp, datetime)):
        return ResultadoFecha(valor.date().isoformat())
    if isinstance(valor, date):
        return ResultadoFecha(valor.isoformat())

    crudo = str(valor).strip()
    if not crudo or crudo in {"-", "N/A", "n/a", "s/d", "S/D"}:
        return ResultadoFecha(None)

    # Fecha serial de Excel (días desde 1899-12-30).
    if re.fullmatch(r"\d{5}(\.\d+)?", crudo):
        try:
            return ResultadoFecha(
                (pd.Timestamp("1899-12-30") + pd.Timedelta(days=float(crudo))).date().isoformat())
        except (ValueError, OverflowError):
            pass

    base = crudo.split(" ")[0] if re.match(r"^\S+\s+\d{1,2}:\d{2}", crudo) else crudo
    for fmt in _FORMATOS:
        try:
            f = datetime.strptime(base, fmt).date()
        except ValueError:
            continue
        partes = re.split(r"[/\-.]", base)
        ambiguo = (fmt.startswith("%d") and len(partes) == 3
                   and partes[0].isdigit() and partes[1].isdigit()
                   and int(partes[0]) <= 12 and int(partes[1]) <= 12
                   and partes[0] != partes[1])
        return ResultadoFecha(f.isoformat(), ambiguo)
    return ResultadoFecha(None)


# -------------------------------------------------------------- campos destino


@dataclass(frozen=True)
class Campo:
    clave: str
    etiqueta: str
    tipo: str                      # texto | numero | fecha | estado | nivel | proyecto | persona
    requerido: bool = False
    sinonimos: tuple[str, ...] = ()
    ayuda: str = ""


CAMPOS: dict[str, list[Campo]] = {
    "proyectos": [
        Campo("nombre", "Nombre del proyecto", "texto", True,
              ("nombre", "proyecto", "titulo", "descripcion", "obra", "iniciativa",
               "project", "project name", "nombre proyecto", "denominacion")),
        Campo("portafolio", "Portafolio / programa", "texto", False,
              ("portafolio", "programa", "cartera", "area", "linea", "unidad",
               "portfolio", "program", "categoria", "gerencia")),
        # "responsable" queda afuera a propósito: es ambiguo (¿responsable de
        # qué?) y como subcadena se roba columnas tipo "Área Responsable", que
        # en realidad son el portafolio.
        Campo("sponsor", "Sponsor", "texto", False,
              ("sponsor", "patrocinador", "solicitante", "referente",
               "dueno", "duenio", "owner", "quien lo pide")),
        Campo("criticidad", "Criticidad", "nivel", False,
              ("criticidad", "prioridad", "importancia", "severidad", "priority",
               "criticality", "nivel", "riesgo")),
        Campo("presupuesto", "Presupuesto", "numero", False,
              ("presupuesto", "budget", "monto", "costo", "importe", "valor",
               "presupuestado", "monto total", "inversion")),
        Campo("ejecutado", "Ejecutado", "numero", False,
              ("ejecutado", "spent", "gastado", "consumido", "real", "devengado",
               "monto ejecutado", "gasto", "erogado")),
        Campo("fecha_inicio", "Fecha de inicio", "fecha", False,
              ("fecha inicio", "inicio", "fecha de inicio", "desde", "start",
               "start date", "comienzo", "alta", "fecha alta")),
        Campo("fecha_fin", "Fecha de fin", "fecha", False,
              ("fecha fin", "fin", "fecha de fin", "hasta", "end", "end date",
               "vencimiento", "cierre", "entrega", "fecha entrega", "deadline")),
        Campo("segmento", "Segmento", "texto", False,
              ("segmento", "tipo", "clasificacion", "segment", "modalidad")),
    ],
    "tareas": [
        Campo("titulo", "Título de la tarea", "texto", True,
              ("titulo", "tarea", "nombre", "descripcion", "actividad", "task",
               "task name", "detalle", "asunto", "resumen", "summary")),
        Campo("proyecto", "Proyecto al que pertenece", "proyecto", False,
              ("proyecto", "project", "obra", "iniciativa", "portafolio",
               "nombre proyecto", "proyecto asociado", "epic"),
              "Se busca por nombre contra los proyectos ya cargados."),
        Campo("responsable", "Responsable", "persona", False,
              ("responsable", "asignado", "asignado a", "encargado", "owner",
               "assignee", "ejecutor", "quien", "persona", "recurso"),
              "Se busca por nombre o email contra los usuarios del equipo."),
        Campo("estado", "Estado", "estado", False,
              ("estado", "status", "situacion", "avance", "etapa", "fase")),
        Campo("prioridad", "Prioridad", "nivel", False,
              ("prioridad", "priority", "importancia", "criticidad", "urgencia")),
        Campo("vencimiento", "Vencimiento", "fecha", False,
              ("vencimiento", "fecha fin", "fin", "deadline", "due", "due date",
               "fecha limite", "limite", "entrega", "fecha entrega", "hasta")),
    ],
}


def campos_de(tipo: str) -> list[Campo]:
    if tipo not in CAMPOS:
        raise ValueError(f"Tipo de importación desconocido: {tipo!r}")
    return CAMPOS[tipo]


# ------------------------------------------------------------ detección de columnas


@dataclass
class Sugerencia:
    columna: str | None
    confianza: float               # 0..1
    motivo: str = ""


def _puntaje(columna: str, campo: Campo) -> tuple[float, str]:
    col_n = normalizar(columna)
    if not col_n:
        return 0.0, ""
    sinonimos = (campo.clave,) + campo.sinonimos
    normalizados = {normalizar(s) for s in sinonimos}

    if col_n in normalizados:
        return 1.0, "coincidencia exacta"

    # Contención: "nombredelproyecto" contiene "nombreproyecto"? No, pero sí
    # contiene "proyecto". Se pondera por cuánto del nombre cubre el sinónimo.
    mejor, motivo = 0.0, ""
    for s in normalizados:
        if len(s) < 3:
            continue
        if s in col_n or col_n in s:
            cobertura = len(s) / max(len(col_n), len(s))
            puntaje = 0.55 + 0.35 * cobertura
            if puntaje > mejor:
                mejor, motivo = puntaje, f"parecido a «{s}»"

    # Palabras en común, ignorando las vacías: "Fecha de Inicio" == "fecha inicio".
    col_tokens = _tokens(columna)
    for s in sinonimos:
        s_tokens = _tokens(s)
        if not s_tokens:
            continue
        if s_tokens == col_tokens:
            return 1.0, "mismas palabras"
        comunes = col_tokens & s_tokens
        if comunes and s_tokens <= col_tokens:
            puntaje = 0.6 + 0.3 * (len(comunes) / max(len(col_tokens), 1))
            if puntaje > mejor:
                mejor, motivo = puntaje, f"contiene «{' '.join(sorted(comunes))}»"
    return mejor, motivo


def detectar_columnas(df: pd.DataFrame, tipo: str) -> dict[str, Sugerencia]:
    """Propone qué columna del archivo corresponde a cada campo del sistema.

    Cada columna se asigna a un solo campo: se resuelven primero las parejas de
    mayor puntaje, así "prioridad" no se lleva a la vez `criticidad` y `prioridad`.
    """
    campos = campos_de(tipo)
    pares = []
    for campo in campos:
        for columna in df.columns:
            puntaje, motivo = _puntaje(str(columna), campo)
            if puntaje >= 0.55:
                pares.append((puntaje, campo.clave, str(columna), motivo))
    pares.sort(key=lambda p: (-p[0], p[1], p[2]))

    asignadas: set[str] = set()
    resuelto: dict[str, Sugerencia] = {}
    for puntaje, clave, columna, motivo in pares:
        if clave in resuelto or columna in asignadas:
            continue
        resuelto[clave] = Sugerencia(columna, round(puntaje, 2), motivo)
        asignadas.add(columna)

    for campo in campos:
        resuelto.setdefault(campo.clave, Sugerencia(None, 0.0, "sin detectar"))
    return resuelto


# ------------------------------------------------------------------- informe


@dataclass
class Problema:
    fila: int                      # número de fila como lo ve el usuario (1 = primera de datos)
    campo: str
    valor: str
    motivo: str
    severidad: str                 # "error" descarta la fila; "aviso" la deja pasar


@dataclass
class Reporte:
    tipo: str
    total_filas: int = 0
    filas: list[dict] = field(default_factory=list)          # listas para escribir
    problemas: list[Problema] = field(default_factory=list)
    avisos_columna: list[str] = field(default_factory=list)
    faltan_requeridos: list[str] = field(default_factory=list)
    duplicados_archivo: int = 0
    duplicados_base: int = 0
    mapeo: dict[str, str] = field(default_factory=dict)

    @property
    def filas_validas(self) -> int:
        return len(self.filas)

    @property
    def filas_rechazadas(self) -> int:
        return len({p.fila for p in self.problemas if p.severidad == "error"})

    @property
    def errores(self) -> list[Problema]:
        return [p for p in self.problemas if p.severidad == "error"]

    @property
    def avisos(self) -> list[Problema]:
        return [p for p in self.problemas if p.severidad == "aviso"]

    @property
    def puede_importar(self) -> bool:
        return not self.faltan_requeridos and bool(self.filas)

    def resumen(self) -> str:
        if self.faltan_requeridos:
            return f"Falta mapear: {', '.join(self.faltan_requeridos)}."
        partes = [f"{self.filas_validas} de {self.total_filas} filas listas"]
        if self.filas_rechazadas:
            partes.append(f"{self.filas_rechazadas} se descartan")
        if self.duplicados_archivo:
            partes.append(f"{self.duplicados_archivo} repetidas en el archivo")
        if self.duplicados_base:
            partes.append(f"{self.duplicados_base} ya existen en el sistema")
        return " · ".join(partes) + "."

    def problemas_df(self) -> pd.DataFrame:
        if not self.problemas:
            return pd.DataFrame(columns=["fila", "campo", "valor", "motivo", "severidad"])
        return pd.DataFrame([p.__dict__ for p in self.problemas])

    def vista_previa(self, n: int = 20) -> pd.DataFrame:
        return pd.DataFrame(self.filas[:n]) if self.filas else pd.DataFrame()


# ------------------------------------------------------------------ validación


def _indice_por_nombre(df: pd.DataFrame, col_nombre: str, col_id: str) -> dict[str, int]:
    if df is None or df.empty or col_nombre not in df.columns:
        return {}
    return {normalizar(r[col_nombre]): int(r[col_id]) for _, r in df.iterrows()
            if normalizar(r[col_nombre])}


def validar(df: pd.DataFrame, tipo: str, mapeo: dict[str, str], *,
            proyectos: pd.DataFrame | None = None,
            usuarios: pd.DataFrame | None = None,
            existentes: pd.DataFrame | None = None,
            proyecto_default_id: int | None = None,
            omitir_duplicados: bool = True) -> Reporte:
    """Simula la importación completa sin escribir nada.

    Es el corazón del importador guiado: el cliente ve exactamente qué va a
    entrar, qué se va a descartar y por qué, antes de tocar la base.
    """
    campos = {c.clave: c for c in campos_de(tipo)}
    mapeo = {k: v for k, v in mapeo.items() if v and k in campos}
    rep = Reporte(tipo=tipo, total_filas=len(df), mapeo=dict(mapeo))

    rep.faltan_requeridos = [c.etiqueta for c in campos.values()
                             if c.requerido and c.clave not in mapeo]
    if rep.faltan_requeridos:
        return rep

    idx_proyectos = _indice_por_nombre(proyectos, "nombre", "_id")
    idx_usuarios = _indice_por_nombre(usuarios, "nombre", "id")
    if usuarios is not None and not usuarios.empty and "email" in usuarios.columns:
        idx_usuarios.update(_indice_por_nombre(usuarios, "email", "id"))

    clave_existente: set[str] = set()
    if existentes is not None and not existentes.empty:
        col = "nombre" if tipo == "proyectos" else "titulo"
        if col in existentes.columns:
            clave_existente = {normalizar(v) for v in existentes[col] if normalizar(v)}

    # Escala de los niveles: se decide una vez por columna, no fila por fila.
    niveles_numericos = [campos[c].etiqueta for c in ("criticidad", "prioridad")
                         if c in mapeo and columna_es_numerica(df[mapeo[c]])]

    vistas: set[str] = set()
    numeros_ambiguos: set[str] = set()
    fechas_ambiguas: set[str] = set()

    for pos, (_, row) in enumerate(df.iterrows(), start=1):
        fila: dict = {}
        errores_fila = False

        for clave, columna in mapeo.items():
            campo = campos[clave]
            crudo = row.get(columna)
            vacio = crudo is None or (not isinstance(crudo, (list, dict)) and pd.isna(crudo)) \
                or str(crudo).strip() == ""

            if vacio:
                if campo.requerido:
                    rep.problemas.append(Problema(pos, campo.etiqueta, "", "está vacío", "error"))
                    errores_fila = True
                continue

            if campo.tipo == "texto":
                fila[clave] = str(crudo).strip()

            elif campo.tipo == "numero":
                r = parsear_numero(crudo)
                if r.valor is None:
                    rep.problemas.append(Problema(
                        pos, campo.etiqueta, str(crudo), "no se entiende como número", "aviso"))
                else:
                    fila[clave] = r.valor
                    if r.ambiguo:
                        numeros_ambiguos.add(campo.etiqueta)

            elif campo.tipo == "fecha":
                r = parsear_fecha(crudo)
                if r.valor is None:
                    rep.problemas.append(Problema(
                        pos, campo.etiqueta, str(crudo), "no se entiende como fecha", "aviso"))
                else:
                    fila[clave] = r.valor
                    if r.ambiguo:
                        fechas_ambiguas.add(campo.etiqueta)

            elif campo.tipo == "estado":
                v = normalizar_estado(crudo)
                if v is None:
                    rep.problemas.append(Problema(
                        pos, campo.etiqueta, str(crudo),
                        "estado no reconocido, queda como pendiente", "aviso"))
                else:
                    fila[clave] = v

            elif campo.tipo == "nivel":
                v = normalizar_nivel(crudo)
                if v is None:
                    rep.problemas.append(Problema(
                        pos, campo.etiqueta, str(crudo),
                        "nivel no reconocido, queda como Media", "aviso"))
                else:
                    fila[clave] = v

            elif campo.tipo == "proyecto":
                pid = idx_proyectos.get(normalizar(crudo))
                if pid is None:
                    if proyecto_default_id is None:
                        rep.problemas.append(Problema(
                            pos, campo.etiqueta, str(crudo),
                            "no existe un proyecto con ese nombre", "error"))
                        errores_fila = True
                    else:
                        rep.problemas.append(Problema(
                            pos, campo.etiqueta, str(crudo),
                            "no existe ese proyecto, va al proyecto por defecto", "aviso"))
                        fila["proyecto_id"] = proyecto_default_id
                else:
                    fila["proyecto_id"] = pid

            elif campo.tipo == "persona":
                uid = idx_usuarios.get(normalizar(crudo))
                if uid is None:
                    rep.problemas.append(Problema(
                        pos, campo.etiqueta, str(crudo),
                        "no hay un usuario con ese nombre o email, queda sin asignar", "aviso"))
                else:
                    fila["responsable_id"] = uid

        if errores_fila:
            continue

        clave_dedup = normalizar(fila.get("nombre") or fila.get("titulo") or "")
        if clave_dedup:
            if clave_dedup in vistas:
                rep.duplicados_archivo += 1
                if omitir_duplicados:
                    continue
            elif clave_dedup in clave_existente:
                rep.duplicados_base += 1
                if omitir_duplicados:
                    continue
            vistas.add(clave_dedup)

        if tipo == "tareas" and "proyecto_id" not in fila:
            if proyecto_default_id is None:
                rep.problemas.append(Problema(
                    pos, "Proyecto", "", "no hay proyecto al que asociar la tarea", "error"))
                continue
            fila["proyecto_id"] = proyecto_default_id

        fila["_fila_origen"] = pos
        rep.filas.append(fila)

    for etiqueta in sorted(numeros_ambiguos):
        rep.avisos_columna.append(
            f"«{etiqueta}»: se interpretó el punto como separador de miles "
            f"(1.500 = mil quinientos). Si en tu archivo es decimal, corregilo antes de importar.")
    for etiqueta in sorted(fechas_ambiguas):
        rep.avisos_columna.append(
            f"«{etiqueta}»: hay fechas donde día y mes son ambos ≤ 12 (ej. 03/04). "
            f"Se leyeron como día/mes.")
    for etiqueta in niveles_numericos:
        rep.avisos_columna.append(
            f"«{etiqueta}»: la columna viene con números. Se leyó 1 = Alta, 2 = Media, "
            f"3 = Baja. Si en tu escala 3 es lo más grave, está al revés — conviene "
            f"reemplazar los números por Alta/Media/Baja antes de importar.")
    return rep


# ------------------------------------------------------------------ escritura

_DEFAULTS_PROYECTO = {"portafolio": "Importado", "segmento": "Interno",
                      "criticidad": "Media", "presupuesto": 0.0, "ejecutado": 0.0}
_DEFAULTS_TAREA = {"estado": "todo", "prioridad": "Media"}


def filas_para_escribir(rep: Reporte) -> list[dict]:
    """Completa los valores por defecto y saca los campos internos."""
    defaults = _DEFAULTS_PROYECTO if rep.tipo == "proyectos" else _DEFAULTS_TAREA
    salida = []
    for fila in rep.filas:
        limpia = {k: v for k, v in fila.items() if not k.startswith("_")}
        limpia.pop("proyecto", None)
        limpia.pop("responsable", None)
        salida.append({**defaults, **limpia})
    return salida


def aplicar(rep: Reporte, crear_proyecto, crear_tarea) -> int:
    """Escribe de verdad. Recibe las funciones de escritura para poder testear
    sin tocar la base real."""
    if not rep.puede_importar:
        return 0
    creadas = 0
    for fila in filas_para_escribir(rep):
        crear_proyecto(**fila) if rep.tipo == "proyectos" else crear_tarea(**fila)
        creadas += 1
    return creadas


# ------------------------------------------------------------------ plantilla


def plantilla(tipo: str) -> pd.DataFrame:
    """Archivo de ejemplo para que el cliente arranque sin inventar el formato."""
    if tipo == "proyectos":
        return pd.DataFrame([
            {"nombre": "Migración de servidores", "portafolio": "Infraestructura",
             "sponsor": "Gerencia de TI", "criticidad": "Alta",
             "presupuesto": 1500000, "ejecutado": 320000,
             "fecha_inicio": "01/03/2026", "fecha_fin": "30/09/2026"},
            {"nombre": "Rediseño del sitio web", "portafolio": "Comercial",
             "sponsor": "Marketing", "criticidad": "Media",
             "presupuesto": 400000, "ejecutado": 0,
             "fecha_inicio": "15/04/2026", "fecha_fin": "15/07/2026"},
        ])
    return pd.DataFrame([
        {"titulo": "Relevar servidores actuales", "proyecto": "Migración de servidores",
         "responsable": "", "estado": "En curso", "prioridad": "Alta",
         "vencimiento": "30/04/2026"},
        {"titulo": "Definir proveedor de nube", "proyecto": "Migración de servidores",
         "responsable": "", "estado": "Pendiente", "prioridad": "Media",
         "vencimiento": "15/05/2026"},
    ])
