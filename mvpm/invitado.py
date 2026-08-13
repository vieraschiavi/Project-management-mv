# © 2026 Martín Viera. Todos los derechos reservados.
"""Modo invitado: usar el producto sin crear cuenta.

Por qué existe: antes, para ver el propio portafolio había que crear una cuenta
primero. Quien llega por la web y quiere saber si esto le sirve, no quiere dejar
un email antes de ver nada — y ese paso se comía la mayoría de las visitas.

Con este módulo, alguien puede subir su Excel (o abrir el portafolio real del
gobierno británico) y ver la salud de su cartera sin registrarse.

La diferencia con el modo normal es DÓNDE viven los datos: acá quedan en un
almacén en memoria, atado a la sesión del navegador, y se pierden al cerrarla.
Es a propósito y se avisa en pantalla — sin cuenta no hay a quién atribuirlos, y
escribir en la base compartida mezclaría los datos de un visitante con los del
equipo que sí usa el servidor.

El almacén imita la forma de lo que devuelve `db` (mismas columnas, incluida la
`_id` interna) para que el resto del motor y del dashboard funcionen igual sin
enterarse de si están mirando la base o una sesión de invitado.
"""

from __future__ import annotations

import pandas as pd

from . import demo_real

# Mismas columnas que devuelven db.projects() y db.tasks(), en el mismo orden.
COLUMNAS_PROYECTOS = ["_id", "proyecto_id", "nombre", "portafolio", "sponsor",
                      "dueno", "segmento", "fecha_inicio", "fecha_fin",
                      "presupuesto", "ejecutado", "criticidad"]
COLUMNAS_TAREAS = ["_id", "tarea_id", "proyecto_id", "titulo", "responsable",
                   "estado", "vencimiento", "prioridad", "depende_de"]

# Tipos de las columnas numéricas. Se fijan al crear el almacén vacío porque un
# DataFrame sin filas infiere dtype object, y ahí catalog.catalog() reventaba al
# dividir presupuesto/ejecutado (el mismo problema que se arregló en su momento
# para la base recién instalada).
_NUMERICAS_PROYECTOS = ["presupuesto", "ejecutado"]


class Almacen:
    """Portafolio en memoria de una sesión de invitado.

    Expone `crear_proyecto` / `crear_tarea` con la misma firma que las de `db`,
    justamente para poder pasárselas a `importer.aplicar()` sin ramificar el
    código del importador entre invitado y usuario registrado.
    """

    def __init__(self) -> None:
        self._proyectos: list[dict] = []
        self._tareas: list[dict] = []

    # ---------------------------------------------------------------- escritura

    def crear_proyecto(self, **campos) -> int:
        nuevo_id = len(self._proyectos) + 1
        self._proyectos.append({
            "_id": nuevo_id,
            "proyecto_id": campos.get("proyecto_id") or f"P-{nuevo_id:03d}",
            "nombre": campos.get("nombre"),
            "portafolio": campos.get("portafolio"),
            "sponsor": campos.get("sponsor"),
            # El importador trae dueno_id (un id de usuario de la base), que en
            # modo invitado no aplica: no hay equipo cargado. Queda sin dueño,
            # y el motor de salud lo va a marcar como tal — que es lo correcto.
            "dueno": None,
            "segmento": campos.get("segmento"),
            "fecha_inicio": campos.get("fecha_inicio"),
            "fecha_fin": campos.get("fecha_fin"),
            "presupuesto": campos.get("presupuesto") or 0,
            "ejecutado": campos.get("ejecutado") or 0,
            "criticidad": campos.get("criticidad") or "Media",
        })
        return nuevo_id

    def crear_tarea(self, **campos) -> int:
        nuevo_id = len(self._tareas) + 1
        proyecto_id = campos.get("proyecto_id")
        # El importador resuelve el proyecto a su _id interno; acá se traduce al
        # código visible (P-001), que es con el que trabajan salud y dependencias.
        codigo = next((p["proyecto_id"] for p in self._proyectos
                       if p["_id"] == proyecto_id), proyecto_id)
        self._tareas.append({
            "_id": nuevo_id,
            "tarea_id": campos.get("tarea_id") or f"T-{nuevo_id:04d}",
            "proyecto_id": codigo,
            "titulo": campos.get("titulo"),
            "responsable": None,
            "estado": campos.get("estado") or "todo",
            "vencimiento": campos.get("vencimiento"),
            "prioridad": campos.get("prioridad") or "Media",
            "depende_de": campos.get("depende_de"),
        })
        return nuevo_id

    # ---------------------------------------------------------------- lectura

    def proyectos(self) -> pd.DataFrame:
        df = pd.DataFrame(self._proyectos, columns=COLUMNAS_PROYECTOS)
        for col in _NUMERICAS_PROYECTOS:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df

    def tareas(self) -> pd.DataFrame:
        return pd.DataFrame(self._tareas, columns=COLUMNAS_TAREAS)

    def equipo(self) -> pd.DataFrame:
        """Sin cuenta no hay equipo cargado. Se devuelve la tabla vacía con sus
        columnas para que el motor de salud no tenga que tratar este caso
        distinto: ya sabe calcular con un equipo vacío."""
        return pd.DataFrame(columns=["nombre", "rol", "capacidad_semanal_hs",
                                     "carga_actual_hs"])

    # ---------------------------------------------------------------- estado

    @property
    def vacio(self) -> bool:
        return not self._proyectos and not self._tareas

    def total_proyectos(self) -> int:
        return len(self._proyectos)

    def total_tareas(self) -> int:
        return len(self._tareas)


def almacen_vacio() -> Almacen:
    return Almacen()


def con_portafolio_real() -> Almacen:
    """Almacén precargado con el portafolio real del gobierno británico.

    Son 132 proyectos públicos del Government Major Projects Portfolio (IPA /
    Cabinet Office). Sirve para que alguien que todavía no tiene su Excel a mano
    igual pueda ver el producto trabajando sobre datos reales, no inventados.
    """
    almacen = Almacen()
    df = demo_real.cargar_portafolio_real()
    for _, fila in df.iterrows():
        almacen.crear_proyecto(**{c: fila.get(c) for c in df.columns})
    return almacen
