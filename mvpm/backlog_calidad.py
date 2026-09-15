# © 2026 Martín Viera. Todos los derechos reservados.
"""Revisión de calidad de un backlog de Azure DevOps, y su corrección.

Azure DevOps no se queja de nada de esto. Una tarea titulada "DELETE" es un
título válido; un ítem en Doing hace tres meses es un estado válido; una
iteración llamada "Sprint Actual" es una ruta válida. La herramienta guarda lo
que le pongan. El costo aparece después, cuando hay que explicar por qué el
sprint no cerró o por qué el reporte de velocidad no significa nada.

Este módulo corre un conjunto de reglas sobre el backlog y devuelve dos cosas:

1. **Hallazgos** — qué está mal, en qué ítem, y con qué severidad.
2. **Correcciones** — el backlog arreglado, listo para volver a subir.

La regla de oro, que es la misma que rige toda la demo del producto: **no se
inventa dato que no está**. Si un ítem no tiene estimación, la corrección no le
pone un número: le pone la etiqueta `sin-estimar`, que en Azure DevOps se puede
filtrar, y lo deja a la vista del equipo. Lo que sí se corrige de verdad es todo
lo que se puede derivar del propio backlog: un título duplicado se desambigua
con el padre, un título que arrastra un estado se limpia y el estado se va a la
descripción, una etiqueta informal se reemplaza.

Cada regla dice tres cosas, y las tres viajan a la pantalla traducidas: qué
encontró, **por qué es un problema** y **cómo queda** después de corregir.

El módulo no sabe nada de HTTP: trabaja sobre un DataFrame. Por eso la demo
corre entera sin conexión ni credenciales.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date

import pandas as pd

ALTA, MEDIA, BAJA = "alta", "media", "baja"

DIAS_ESTANCADO = 30
REV_ALTA = 15
UMBRAL_UNIFORME = 0.8
UMBRAL_BUS_FACTOR = 0.7

ESTADOS_ACTIVOS = ("doing", "in progress", "active", "en curso", "committed")
ESTADOS_CERRADOS = ("done", "closed", "removed", "resolved", "cerrado", "hecho")

# Títulos que no son títulos: marcadores que alguien dejó y nadie sacó.
_MARCADORES_BORRAR = ("delete", "borrar", "eliminar", "remove", "excluir")
_MARCADORES_VAGOS = ("tbd", "xxx", "???", "sin titulo", "sin título", "prueba",
                     "test", "asdf", "nuevo elemento", "new item", "temp", "tmp")

# Un título no debería contar en qué estado está la tarea: para eso está el
# campo Estado. Cuando lo cuenta, el título cambia cada vez que cambia la
# realidad y deja de servir para buscar.
_ESTADO_EN_TITULO = re.compile(
    r"(?i)\(([^()]*(mientras|pendiente|en pausa|bloquead|no se resuelv|"
    r"provisorio|temporal|workaround|por ahora|a confirmar)[^()]*)\)"
)

# Rutas de iteración cuyo nombre se mueve con el tiempo. El problema no es el
# nombre: es que dentro de dos meses apunta a otro sprint y la historia miente.
_ITERACION_MOVIL = re.compile(
    r"(?i)^(sprint\s+)?(actual|current|corriente|en curso|proximo|próximo|next|"
    r"atual|esta semana|this week)$"
)
_SPRINT_NUMERADO = re.compile(r"(?i)^sprint\s+(\d+)$")

_TAGS_INFORMALES = ("verlo despues", "verlo después", "ver despues", "ver después",
                    "ojo", "urgente!!!", "revisar despues", "revisar después",
                    "no se", "no sé", "preguntar", "dudoso")

# Marcas de que la descripción se apoya en algo que el CSV no lleva.
_ADJUNTO = re.compile(
    r"(?i)(\[imagen adjunta\]|ver imagen|ver adjunto|imagen adjunta|"
    r"archivo adjunto|ver captura|como en la foto|ver el mail)"
)

_CRITERIO = ("criterio de aceptacion", "criterio de aceptación",
             "criterios de aceptacion", "criterios de aceptación",
             "acceptance criteria", "definition of done", "definicion de hecho",
             "definición de hecho", "dado que", "se considera terminado")

_TIPOS_HOJA = ("task", "tarea", "tarefa")
_TIPOS_PADRE = ("epic", "épica", "epica", "feature", "característica", "caracteristica")

PLANTILLA_DESCRIPCION = (
    "Objetivo: <completar>\n"
    "Entregable: <completar>\n"
    "Criterio de aceptación: <completar>"
)
NOTA_ESTADO = "Nota de estado (venía en el título): "
NOTA_ADJUNTO = ("Esta descripción referencia un adjunto que no viaja en la "
                "exportación: copiar acá lo que el adjunto decía.")

ETIQUETA_SIN_ESTIMAR = "sin-estimar"
ETIQUETA_SIN_PADRE = "sin-padre"
ETIQUETA_SIN_RESPONSABLE = "sin-responsable"
ETIQUETA_SIN_SPRINT = "sin-sprint"
ETIQUETA_ESTANCADO = "estancado"
ETIQUETA_REVISAR = "revisar-titulo"

# Cada regla: severidad y si es del ítem o del backlog entero. El nombre, el
# porqué y el cómo queda están en i18n con las claves adoq_r_/adoq_p_/adoq_f_.
REGLAS: dict[str, dict] = {
    "titulo_marcador": {"severidad": ALTA, "alcance": "item"},
    "titulo_duplicado": {"severidad": MEDIA, "alcance": "item"},
    "titulo_con_estado": {"severidad": MEDIA, "alcance": "item"},
    "sin_descripcion": {"severidad": MEDIA, "alcance": "item"},
    "sin_criterio_aceptacion": {"severidad": MEDIA, "alcance": "item"},
    "depende_de_adjunto": {"severidad": MEDIA, "alcance": "item"},
    "sin_esfuerzo": {"severidad": MEDIA, "alcance": "item"},
    "sin_padre": {"severidad": ALTA, "alcance": "item"},
    "iteracion_movil": {"severidad": ALTA, "alcance": "item"},
    "iteracion_inconsistente": {"severidad": MEDIA, "alcance": "item"},
    "estancado": {"severidad": ALTA, "alcance": "item"},
    "sin_asignar": {"severidad": MEDIA, "alcance": "item"},
    "tag_informal": {"severidad": BAJA, "alcance": "item"},
    "rev_alta": {"severidad": BAJA, "alcance": "item"},
    "prioridad_uniforme": {"severidad": MEDIA, "alcance": "backlog"},
    "bus_factor": {"severidad": MEDIA, "alcance": "backlog"},
}

ORDEN_SEVERIDAD = {ALTA: 0, MEDIA: 1, BAJA: 2}


@dataclass(frozen=True)
class Hallazgo:
    """Algo que está mal. `item` vacío = es del backlog entero, no de un ítem."""

    regla: str
    severidad: str
    item: str = ""
    titulo: str = ""
    dato: str = ""


@dataclass(frozen=True)
class Correccion:
    """Un cambio concreto: qué campo, qué decía antes y qué dice después."""

    regla: str
    item: str
    campo: str
    antes: str
    despues: str
    accion: str = "editar"          # editar | etiquetar | quitar


# ------------------------------------------------------------------ utilidades


def _sin_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _clave(texto: str) -> str:
    """Normaliza un título para comparar: sin acentos, sin puntuación, minúsculas."""
    s = _sin_acentos(str(texto)).lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _texto(fila, campo: str) -> str:
    valor = fila.get(campo, "")
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    return str(valor).strip()


def _hoja_iteracion(ruta: str) -> str:
    return ruta.replace("/", "\\").split("\\")[-1].strip()


def _es_activo(estado: str) -> bool:
    return _clave(estado) in {_clave(e) for e in ESTADOS_ACTIVOS}


def _es_cerrado(estado: str) -> bool:
    return _clave(estado) in {_clave(e) for e in ESTADOS_CERRADOS}


def _fecha(valor: str) -> date | None:
    s = str(valor).strip()[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _etiquetas(texto: str) -> list[str]:
    return [t.strip() for t in str(texto).split(";") if t.strip()]


def _con_etiqueta(texto: str, nueva: str) -> str:
    actuales = _etiquetas(texto)
    if any(_clave(t) == _clave(nueva) for t in actuales):
        return "; ".join(actuales)
    return "; ".join([*actuales, nueva])


def _tiene_criterio(descripcion: str) -> bool:
    plana = _clave(descripcion)
    return any(_clave(m) in plana for m in _CRITERIO)


def _sprint_siguiente(df: pd.DataFrame) -> int:
    """El número que sigue al sprint numerado más alto que hay en el backlog."""
    maximo = 0
    for ruta in df.get("Iteracion", pd.Series(dtype=str)).fillna(""):
        m = _SPRINT_NUMERADO.match(_hoja_iteracion(str(ruta)))
        if m:
            maximo = max(maximo, int(m.group(1)))
    return maximo + 1


# ---------------------------------------------------------------------- revisar


def revisar(df: pd.DataFrame, hoy: date | None = None) -> list[Hallazgo]:
    """Corre todas las reglas y devuelve los hallazgos ordenados por severidad."""
    hoy = hoy or date.today()
    if df.empty:
        return []
    hallazgos: list[Hallazgo] = []
    hallazgos.extend(_reglas_por_item(df, hoy))
    hallazgos.extend(_reglas_de_backlog(df))
    hallazgos.sort(key=lambda h: (ORDEN_SEVERIDAD.get(h.severidad, 9),
                                  h.regla, str(h.item)))
    return hallazgos


def _reglas_por_item(df: pd.DataFrame, hoy: date) -> list[Hallazgo]:
    salida: list[Hallazgo] = []
    duplicados = _titulos_duplicados(df)
    hay_padres = any(_clave(_texto(f, "Tipo")) in {_clave(t) for t in _TIPOS_PADRE}
                     for _, f in df.iterrows())
    hay_sprints = any(_SPRINT_NUMERADO.match(_hoja_iteracion(_texto(f, "Iteracion")))
                      for _, f in df.iterrows())

    for _, fila in df.iterrows():
        item = _texto(fila, "ID")
        titulo = _texto(fila, "Titulo")
        estado = _texto(fila, "Estado")
        tipo = _clave(_texto(fila, "Tipo"))
        descripcion = _texto(fila, "Descripcion_texto")

        def anotar(regla: str, dato: str = "") -> None:
            salida.append(Hallazgo(regla, REGLAS[regla]["severidad"], item, titulo, dato))

        if _es_marcador(titulo):
            anotar("titulo_marcador", titulo)
        elif _clave(titulo) in duplicados:
            anotar("titulo_duplicado", titulo)

        m = _ESTADO_EN_TITULO.search(titulo)
        if m:
            anotar("titulo_con_estado", m.group(1))

        if not descripcion:
            anotar("sin_descripcion")
        else:
            if not _tiene_criterio(descripcion):
                anotar("sin_criterio_aceptacion")
            if _ADJUNTO.search(descripcion):
                anotar("depende_de_adjunto", _ADJUNTO.search(descripcion).group(0))

        if not _texto(fila, "Esfuerzo") and not _es_cerrado(estado):
            anotar("sin_esfuerzo")

        if not _texto(fila, "AsignadoA"):
            anotar("sin_asignar")

        if hay_padres and tipo not in {_clave(t) for t in _TIPOS_PADRE} \
                and not _texto(fila, "Padre"):
            anotar("sin_padre")

        hoja = _hoja_iteracion(_texto(fila, "Iteracion"))
        if _ITERACION_MOVIL.match(hoja):
            anotar("iteracion_movil", hoja)
        elif hay_sprints and not _SPRINT_NUMERADO.match(hoja) and _texto(fila, "Iteracion"):
            anotar("iteracion_inconsistente", _texto(fila, "Iteracion"))

        dias = _dias_quieto(fila, hoy)
        if _es_activo(estado) and dias is not None and dias > DIAS_ESTANCADO:
            anotar("estancado", str(dias))

        for etiqueta in _etiquetas(_texto(fila, "Tags")):
            if _clave(etiqueta) in {_clave(t) for t in _TAGS_INFORMALES}:
                anotar("tag_informal", etiqueta)

        rev = _texto(fila, "Rev")
        if rev.isdigit() and int(rev) >= REV_ALTA:
            anotar("rev_alta", rev)

    return salida


def _dias_quieto(fila, hoy: date) -> int | None:
    modificado = _fecha(_texto(fila, "Modificado"))
    if modificado is None:
        return None
    return (hoy - modificado).days


def _es_marcador(titulo: str) -> bool:
    clave = _clave(titulo)
    if not clave:
        return True
    return clave in {_clave(m) for m in (*_MARCADORES_BORRAR, *_MARCADORES_VAGOS)}


def _titulos_duplicados(df: pd.DataFrame) -> set[str]:
    vistos: dict[str, int] = {}
    for _, fila in df.iterrows():
        clave = _clave(_texto(fila, "Titulo"))
        if clave and not _es_marcador(_texto(fila, "Titulo")):
            vistos[clave] = vistos.get(clave, 0) + 1
    return {k for k, n in vistos.items() if n > 1}


def _reglas_de_backlog(df: pd.DataFrame) -> list[Hallazgo]:
    salida: list[Hallazgo] = []
    total = len(df)
    if total < 5:
        # Con menos de cinco ítems, "el 80% tiene la misma prioridad" no dice
        # nada: es ruido estadístico, no un problema del backlog.
        return salida

    prioridades = [p for p in (_texto(f, "Prioridad") for _, f in df.iterrows()) if p]
    if prioridades:
        comun, veces = _mas_comun(prioridades)
        if veces / len(prioridades) >= UMBRAL_UNIFORME:
            salida.append(Hallazgo("prioridad_uniforme", MEDIA, "", "",
                                   f"{comun} ({veces}/{len(prioridades)})"))

    personas = [p for p in (_texto(f, "AsignadoA") for _, f in df.iterrows()) if p]
    if personas:
        comun, veces = _mas_comun(personas)
        if veces / total >= UMBRAL_BUS_FACTOR:
            salida.append(Hallazgo("bus_factor", MEDIA, "", "",
                                   f"{comun} ({veces}/{total})"))
    return salida


def _mas_comun(valores: list[str]) -> tuple[str, int]:
    conteo: dict[str, int] = {}
    for v in valores:
        conteo[v] = conteo.get(v, 0) + 1
    mejor = max(conteo.items(), key=lambda kv: kv[1])
    return mejor[0], mejor[1]


# --------------------------------------------------------------------- corregir


def corregir(df: pd.DataFrame, hoy: date | None = None
             ) -> tuple[pd.DataFrame, list[Correccion]]:
    """Devuelve el backlog corregido y la lista de cambios, uno por uno.

    Lo que se puede derivar del backlog se arregla de verdad. Lo que no —una
    estimación que nadie puso, un padre que no existe— se etiqueta para que se
    pueda filtrar en Azure DevOps, pero **no se inventa**.
    """
    hoy = hoy or date.today()
    if df.empty:
        return df.copy(), []

    salida = df.copy()
    cambios: list[Correccion] = []
    duplicados = _titulos_duplicados(df)
    por_id = {_texto(f, "ID"): _texto(f, "Titulo") for _, f in df.iterrows()}
    siguiente = _sprint_siguiente(df)
    a_quitar: list[int] = []

    for i, fila in salida.iterrows():
        item = _texto(fila, "ID")
        titulo = _texto(fila, "Titulo")

        if _clave(titulo) in {_clave(m) for m in _MARCADORES_BORRAR}:
            a_quitar.append(i)
            cambios.append(Correccion("titulo_marcador", item, "Titulo",
                                      titulo, "", "quitar"))
            continue
        if _es_marcador(titulo):
            salida.at[i, "Tags"] = _con_etiqueta(_texto(fila, "Tags"), ETIQUETA_REVISAR)
            cambios.append(Correccion("titulo_marcador", item, "Tags",
                                      _texto(fila, "Tags"),
                                      str(salida.at[i, "Tags"]), "etiquetar"))

        titulo = _corregir_titulo(salida, i, fila, item, titulo, duplicados,
                                  por_id, cambios)
        _corregir_descripcion(salida, i, fila, item, cambios)
        _corregir_iteracion(salida, i, fila, item, siguiente, cambios)
        _corregir_etiquetas(salida, i, fila, item, hoy, cambios)

    if a_quitar:
        salida = salida.drop(index=a_quitar)
    return salida.reset_index(drop=True), cambios


def _corregir_titulo(salida, i, fila, item, titulo, duplicados, por_id, cambios) -> str:
    m = _ESTADO_EN_TITULO.search(titulo)
    if m:
        limpio = re.sub(r"\s{2,}", " ", titulo.replace(m.group(0), "")).strip(" -–—")
        if limpio:
            salida.at[i, "Titulo"] = limpio
            descripcion = _texto(fila, "Descripcion_texto")
            nota = NOTA_ESTADO + m.group(1).strip()
            salida.at[i, "Descripcion_texto"] = (
                f"{descripcion}\n{nota}".strip() if descripcion else nota)
            cambios.append(Correccion("titulo_con_estado", item, "Titulo",
                                      titulo, limpio))
            titulo = limpio

    if _clave(titulo) in duplicados:
        padre = por_id.get(_texto(fila, "Padre"), "")
        distintivo = padre or _texto(fila, "Iteracion") or item
        nuevo = f"{titulo} ({distintivo})"
        salida.at[i, "Titulo"] = nuevo
        cambios.append(Correccion("titulo_duplicado", item, "Titulo", titulo, nuevo))
        titulo = nuevo
    return titulo


def _corregir_descripcion(salida, i, fila, item, cambios) -> None:
    descripcion = str(salida.at[i, "Descripcion_texto"] or "").strip()
    if not descripcion:
        salida.at[i, "Descripcion_texto"] = PLANTILLA_DESCRIPCION
        cambios.append(Correccion("sin_descripcion", item, "Descripcion_texto",
                                  "", PLANTILLA_DESCRIPCION))
        return
    # La nota se agrega una sola vez: sin este chequeo, cada pasada del
    # corrector pegaría otra copia y el archivo se degradaría solo.
    if _ADJUNTO.search(descripcion) and NOTA_ADJUNTO not in descripcion:
        nuevo = f"{descripcion}\n{NOTA_ADJUNTO}"
        salida.at[i, "Descripcion_texto"] = nuevo
        cambios.append(Correccion("depende_de_adjunto", item, "Descripcion_texto",
                                  descripcion, nuevo))
        descripcion = nuevo
    if not _tiene_criterio(descripcion):
        nuevo = f"{descripcion}\nCriterio de aceptación: <completar>"
        salida.at[i, "Descripcion_texto"] = nuevo
        cambios.append(Correccion("sin_criterio_aceptacion", item,
                                  "Descripcion_texto", descripcion, nuevo))


def _corregir_iteracion(salida, i, fila, item, siguiente, cambios) -> None:
    ruta = _texto(fila, "Iteracion")
    hoja = _hoja_iteracion(ruta)
    if not _ITERACION_MOVIL.match(hoja):
        return
    # Supuesto explícito: un sprint que se llama "Actual" mientras existen
    # Sprint 1..N es el que viene después del último numerado. Queda escrito en
    # el informe de correcciones para que se pueda pisar si no es así.
    nuevo = ruta[:len(ruta) - len(hoja)] + f"Sprint {siguiente}"
    salida.at[i, "Iteracion"] = nuevo
    cambios.append(Correccion("iteracion_movil", item, "Iteracion", ruta, nuevo))


def _corregir_etiquetas(salida, i, fila, item, hoy, cambios) -> None:
    antes = str(salida.at[i, "Tags"] or "")
    tags = antes
    estado = _texto(fila, "Estado")

    for etiqueta in _etiquetas(tags):
        if _clave(etiqueta) in {_clave(t) for t in _TAGS_INFORMALES}:
            tags = "; ".join(t for t in _etiquetas(tags) if t != etiqueta)
            tags = _con_etiqueta(tags, "revisar")
            cambios.append(Correccion("tag_informal", item, "Tags", etiqueta, "revisar"))

    if not _texto(fila, "Esfuerzo") and not _es_cerrado(estado):
        tags = _con_etiqueta(tags, ETIQUETA_SIN_ESTIMAR)
    if not _texto(fila, "AsignadoA"):
        tags = _con_etiqueta(tags, ETIQUETA_SIN_RESPONSABLE)
    if not _texto(fila, "Padre") and _clave(_texto(fila, "Tipo")) in \
            {_clave(t) for t in _TIPOS_HOJA}:
        tags = _con_etiqueta(tags, ETIQUETA_SIN_PADRE)
    if not _texto(fila, "Iteracion"):
        tags = _con_etiqueta(tags, ETIQUETA_SIN_SPRINT)

    dias = _dias_quieto(fila, hoy)
    if _es_activo(estado) and dias is not None and dias > DIAS_ESTANCADO:
        tags = _con_etiqueta(tags, f"{ETIQUETA_ESTANCADO}-{dias}d")

    if tags != antes:
        salida.at[i, "Tags"] = tags
        if not any(c.item == item and c.campo == "Tags" for c in cambios):
            cambios.append(Correccion("etiquetas", item, "Tags", antes, tags,
                                      "etiquetar"))


# ----------------------------------------------------------------------- resumen


def resumen(hallazgos: list[Hallazgo]) -> dict:
    """Conteos para el encabezado de la pantalla: por severidad y por regla."""
    por_severidad = {ALTA: 0, MEDIA: 0, BAJA: 0}
    por_regla: dict[str, int] = {}
    items: set[str] = set()
    for h in hallazgos:
        por_severidad[h.severidad] = por_severidad.get(h.severidad, 0) + 1
        por_regla[h.regla] = por_regla.get(h.regla, 0) + 1
        if h.item:
            items.add(h.item)
    return {
        "total": len(hallazgos),
        "por_severidad": por_severidad,
        "por_regla": dict(sorted(por_regla.items(), key=lambda kv: -kv[1])),
        "items_afectados": len(items),
    }


def a_dataframe(hallazgos: list[Hallazgo], traducir) -> pd.DataFrame:
    """Los hallazgos como tabla, con el nombre de cada regla ya traducido.

    `traducir` es la función T() de la pantalla; el motor no importa i18n para
    no atarse a la UI.
    """
    filas = [{
        "ID": h.item,
        "severidad": h.severidad,
        "regla": traducir(f"adoq_r_{h.regla}"),
        "titulo": h.titulo,
        "dato": h.dato,
        "por_que": traducir(f"adoq_p_{h.regla}"),
        "como_queda": traducir(f"adoq_f_{h.regla}"),
    } for h in hallazgos]
    return pd.DataFrame(filas, columns=["ID", "severidad", "regla", "titulo",
                                        "dato", "por_que", "como_queda"])


def correcciones_a_dataframe(cambios: list[Correccion]) -> pd.DataFrame:
    filas = [{"ID": c.item, "regla": c.regla, "campo": c.campo, "accion": c.accion,
              "antes": c.antes, "despues": c.despues} for c in cambios]
    return pd.DataFrame(filas, columns=["ID", "regla", "campo", "accion",
                                        "antes", "despues"])
