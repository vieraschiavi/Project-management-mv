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
# El modificador puede ir de los dos lados: en español se dice "Sprint Actual"
# y en inglés "Current Sprint". Tenerlo sólo de un lado dejaba pasar sin
# detectar justo el caso que el texto en inglés de la regla pone de ejemplo.
_ITERACION_MOVIL = re.compile(
    r"(?i)^(?:sprint\s+)?(actual|current|corriente|en curso|proximo|próximo|next|"
    r"atual|esta semana|this week)(?:\s+sprint)?$"
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

# Qué etiqueta deja cada regla. Está acá y no repartido dentro del corrector a
# propósito: cuando la condición que levanta el hallazgo y la que pone la
# etiqueta se escriben por separado, se separan. Pasó: `sin_padre` se informaba
# para cualquier tipo y se etiquetaba sólo en las Task, así que el usuario
# filtraba por `sin-padre` en Azure DevOps y no encontraba los ítems que el
# informe le había prometido. Ahora la etiqueta sale del hallazgo, no de una
# segunda condición escrita a mano.
ETIQUETA_DE_REGLA = {
    "sin_esfuerzo": ETIQUETA_SIN_ESTIMAR,
    "sin_asignar": ETIQUETA_SIN_RESPONSABLE,
    "sin_padre": ETIQUETA_SIN_PADRE,
    "iteracion_inconsistente": ETIQUETA_SIN_SPRINT,
}

# Campos que el corrector llega a escribir. Ningún otro se toca nunca.
CAMPOS_EDITABLES = ("Titulo", "Descripcion_texto", "Iteracion", "Tags")

# Clave donde el conector deja qué columnas venían DE VERDAD en la fuente.
# Sin esto, una columna que el export no trajo es indistinguible de una columna
# vacía, y el corrector la rellena con una plantilla que después se escribe
# encima del dato real del cliente. Ver `azure_devops.normalizar`.
CLAVE_ORIGEN = "mvpm_columnas_origen"


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
    hallazgos = [h for _, h in _reglas_por_item(df, hoy)]
    hallazgos.extend(_reglas_de_backlog(df))
    hallazgos.sort(key=lambda h: (ORDEN_SEVERIDAD.get(h.severidad, 9),
                                  h.regla, str(h.item)))
    return hallazgos


def campos_disponibles(df: pd.DataFrame) -> frozenset:
    """Columnas que venían de verdad en la fuente, no las que se rellenaron.

    Cuando el conector no anotó nada (la demo, o un DataFrame armado a mano),
    se asume que están todas: ahí no hay una fuente externa que respetar.
    """
    origen = df.attrs.get(CLAVE_ORIGEN)
    return frozenset(origen) if origen else frozenset(df.columns)


def _reglas_por_item(df: pd.DataFrame, hoy: date) -> list[tuple]:
    """(índice de fila, hallazgo). El índice es lo que usa el corrector.

    Va por índice y no por ID porque el ID puede venir vacío o repetido en un
    CSV armado a mano, y ahí agrupar por ID mezclaría ítems distintos.
    """
    salida: list[tuple] = []
    duplicados = _titulos_duplicados(df)
    hay_padres = any(_clave(_texto(f, "Tipo")) in {_clave(t) for t in _TIPOS_PADRE}
                     for _, f in df.iterrows())
    hay_sprints = any(_SPRINT_NUMERADO.match(_hoja_iteracion(_texto(f, "Iteracion")))
                      for _, f in df.iterrows())

    for indice, fila in df.iterrows():
        item = _texto(fila, "ID")
        titulo = _texto(fila, "Titulo")
        estado = _texto(fila, "Estado")
        tipo = _clave(_texto(fila, "Tipo"))
        descripcion = _texto(fila, "Descripcion_texto")

        def anotar(regla: str, dato: str = "", _i=indice, _id=item, _t=titulo) -> None:
            salida.append((_i, Hallazgo(regla, REGLAS[regla]["severidad"],
                                        _id, _t, dato)))

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

        ruta = _texto(fila, "Iteracion")
        hoja = _hoja_iteracion(ruta)
        if _ITERACION_MOVIL.match(hoja):
            anotar("iteracion_movil", hoja)
        elif hay_sprints and not _SPRINT_NUMERADO.match(hoja):
            # Sin iteración también es "no está en ningún sprint": antes este
            # caso no levantaba nada y el ítem quedaba invisible para la regla.
            anotar("iteracion_inconsistente", ruta or "(sin iteración)")

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

    **Sólo escribe campos que venían en la fuente.** Si el export no trajo la
    columna Descripción —la grilla de Azure Boards no puede exportarla— este
    corrector no la completa con la plantilla, porque ese archivo se vuelve a
    subir con el ID puesto y la plantilla pisaría la descripción real de todos
    los work items del proyecto. Un dato inventado en un informe es un error;
    escrito en el Azure DevOps del cliente es un incidente.
    """
    hoy = hoy or date.today()
    if df.empty:
        return df.copy(), []

    editables = campos_disponibles(df) & set(CAMPOS_EDITABLES)
    salida = df.copy()
    for c in CAMPOS_EDITABLES:
        if c not in salida.columns:
            salida[c] = ""

    # Las etiquetas se derivan de los hallazgos, no de condiciones reescritas:
    # así no pueden quedar desalineadas con lo que el informe promete.
    por_fila: dict = {}
    for indice, h in _reglas_por_item(df, hoy):
        por_fila.setdefault(indice, []).append(h)

    cambios: list[Correccion] = []
    duplicados = _titulos_duplicados(df)
    por_id = {_texto(f, "ID"): _texto(f, "Titulo") for _, f in df.iterrows()}
    siguiente = _sprint_siguiente(df)
    a_quitar: list = []
    # Títulos que ya son únicos. Sirve para que la desambiguación no genere una
    # colisión nueva contra un título que ya existía.
    usados = {_clave(_texto(f, "Titulo")) for _, f in df.iterrows()
              if _clave(_texto(f, "Titulo")) not in duplicados}

    for i, fila in salida.iterrows():
        item = _texto(fila, "ID")
        titulo = _texto(fila, "Titulo")
        reglas = {h.regla: h for h in por_fila.get(i, [])}

        if _clave(titulo) in {_clave(m) for m in _MARCADORES_BORRAR}:
            a_quitar.append(i)
            cambios.append(Correccion("titulo_marcador", item, "Titulo",
                                      titulo, "", "quitar"))
            continue

        if "Titulo" in editables:
            _corregir_titulo(salida, i, fila, item, titulo, duplicados,
                             por_id, usados, cambios)
        if "Descripcion_texto" in editables:
            _corregir_descripcion(salida, i, fila, item, cambios)
        if "Iteracion" in editables:
            _corregir_iteracion(salida, i, fila, item, siguiente, cambios)
        if "Tags" in editables:
            _corregir_etiquetas(salida, i, fila, item, reglas, cambios)

    if a_quitar:
        salida = salida.drop(index=a_quitar)
    salida = salida.reset_index(drop=True)
    salida.attrs[CLAVE_ORIGEN] = frozenset(campos_disponibles(df))
    return salida, cambios


def _leer(salida, i, campo: str) -> str:
    """Lee una celda del DataFrame de salida tolerando NaN y columna ausente.

    Sin esto, `str(valor or "")` sobre un NaN devuelve el texto literal "nan":
    una celda vacía de pandas terminaba como una etiqueta llamada `nan` en el
    Azure DevOps del cliente.
    """
    if campo not in salida.columns:
        return ""
    valor = salida.at[i, campo]
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    return str(valor).strip()


def _sin_estado_en_titulo(titulo: str) -> tuple[str, list[str]]:
    """Saca TODOS los paréntesis de estado, no sólo el primero.

    Con un solo paso, «Refresco (manual mientras no se resuelve) y carga
    (bloqueado por accesos)» quedaba con el segundo estado adentro del título y
    el informe decía que se había corregido.
    """
    notas: list[str] = []
    while True:
        m = _ESTADO_EN_TITULO.search(titulo)
        if not m:
            break
        notas.append(m.group(1).strip())
        titulo = titulo.replace(m.group(0), "", 1)
    return re.sub(r"\s{2,}", " ", titulo).strip(" -–—"), notas


def _corregir_titulo(salida, i, fila, item, titulo, duplicados, por_id,
                     usados, cambios) -> str:
    limpio, notas = _sin_estado_en_titulo(titulo)
    if notas and limpio:
        salida.at[i, "Titulo"] = limpio
        descripcion = _leer(salida, i, "Descripcion_texto")
        nota = NOTA_ESTADO + " / ".join(notas)
        if nota not in descripcion:
            salida.at[i, "Descripcion_texto"] = (
                f"{descripcion}\n{nota}".strip() if descripcion else nota)
        cambios.append(Correccion("titulo_con_estado", item, "Titulo",
                                  titulo, limpio))
        titulo = limpio

    if _clave(titulo) in duplicados:
        padre = por_id.get(_texto(fila, "Padre"), "")
        distintivo = padre or _texto(fila, "Iteracion") or item
        nuevo = f"{titulo} ({distintivo})"
        # Dos tareas con el mismo título colgadas del MISMO padre (o sin padre,
        # en la misma iteración) seguirían idénticas: el padre no las distingue.
        # Ahí sólo queda el ID, que es lo único que con seguridad es único.
        if _clave(nuevo) in usados:
            nuevo = f"{titulo} ({distintivo} · #{item})" if distintivo != item \
                else f"{titulo} (#{item})"
        usados.add(_clave(nuevo))
        salida.at[i, "Titulo"] = nuevo
        cambios.append(Correccion("titulo_duplicado", item, "Titulo", titulo, nuevo))
        titulo = nuevo
    return titulo


def _corregir_descripcion(salida, i, fila, item, cambios) -> None:
    descripcion = _leer(salida, i, "Descripcion_texto")
    if not descripcion:
        salida.at[i, "Descripcion_texto"] = PLANTILLA_DESCRIPCION
        cambios.append(Correccion("sin_descripcion", item, "Descripcion_texto",
                                  "", PLANTILLA_DESCRIPCION))
        return
    # Cada nota se agrega UNA vez: sin este chequeo, cada pasada del corrector
    # pegaría otra copia y el archivo se degradaría solo.
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


def _corregir_etiquetas(salida, i, fila, item, reglas, cambios) -> None:
    """Las etiquetas salen de los hallazgos de ESTE ítem, no de condiciones
    reescritas: si una regla se informa, su etiqueta se pone, y al revés."""
    antes = _leer(salida, i, "Tags")
    informales = [t for t in _etiquetas(antes)
                  if _clave(t) in {_clave(x) for x in _TAGS_INFORMALES}]
    # La etiqueta de estancado lleva los días adentro, así que `_con_etiqueta`
    # no la deduplica contra la de la corrida anterior. Sin sacar la vieja, un
    # equipo que corre esto cada mes acumula estancado-96d; estancado-126d; …
    # Ojo con `_clave()` acá: convierte el guion en espacio, así que
    # `_clave("estancado-96d")` es "estancado 96d" y nunca empezaría por
    # "estancado-". La comparación va sobre el texto crudo en minúsculas.
    viejo_estancado = (ETIQUETA_ESTANCADO + "-").lower()
    tags = "; ".join(t for t in _etiquetas(antes)
                     if t not in informales
                     and not t.strip().lower().startswith(viejo_estancado))
    if informales:
        tags = _con_etiqueta(tags, "revisar")

    if "titulo_marcador" in reglas:
        tags = _con_etiqueta(tags, ETIQUETA_REVISAR)
    for regla, etiqueta in ETIQUETA_DE_REGLA.items():
        if regla in reglas:
            tags = _con_etiqueta(tags, etiqueta)
    if "estancado" in reglas:
        tags = _con_etiqueta(tags, f"{ETIQUETA_ESTANCADO}-{reglas['estancado'].dato}d")

    if tags == antes:
        return
    salida.at[i, "Tags"] = tags
    # UN cambio por ítem y por campo, con el antes y el después reales. Antes se
    # filtraba con un `any()` sobre todos los cambios comparando por ID, así que
    # un ID vacío o repetido escondía del informe cambios que igual se escribían
    # en el archivo descargado.
    regla = "tag_informal" if informales else "etiquetas"
    cambios.append(Correccion(regla, item, "Tags", antes, tags, "etiquetar"))


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
