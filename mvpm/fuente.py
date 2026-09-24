# © 2026 Martín Viera. Todos los derechos reservados.
"""Fuente activa del portafolio: la demo o los datos del usuario, nunca las dos.

Por qué existe: la base (y el almacén del invitado) puede tener a la vez el
portafolio de ejemplo sembrado con "Cargar datos de ejemplo" y lo que el
usuario trajo después desde un archivo o desde su base SQL. Antes cada pestaña
leía TODO lo que había, así que al importar el Excel propio los 20 proyectos
sintéticos seguían apareciendo mezclados con los reales en salud, backlog,
reportes y en la API de BI.

La regla es una sola y vive acá, sin Streamlit, para que la usen igual el
dashboard, la API REST y el servidor MCP:

- Cada proyecto lleva un `origen`: ``demo`` (sembrado o datos públicos de
  ejemplo), ``manual`` (creado a mano) o ``archivo:<nombre>`` / ``sql:<perfil>``.
- Si existe al menos un proyecto activo que NO es demo, la fuente activa es la
  del usuario y la demo desaparece de todas partes (proyectos, sus tareas y
  el equipo ficticio que la acompaña).
- Si no, la fuente activa es la demo.

Volver a la demo no borra nada: archiva los proyectos del usuario (se pueden
desarchivar), en línea con la regla del producto de no destruir historia.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

DEMO = "demo"
MANUAL = "manual"
PREFIJO_ARCHIVO = "archivo:"
PREFIJO_SQL = "sql:"

TIPO_DEMO = "demo"
TIPO_USUARIO = "usuario"
TIPO_VACIA = "vacia"


def origen_archivo(nombre: str | None) -> str:
    return f"{PREFIJO_ARCHIVO}{(nombre or '').strip() or 'archivo'}"


def origen_sql(nombre: str | None) -> str:
    return f"{PREFIJO_SQL}{(nombre or '').strip() or 'sql'}"


def es_demo(origen) -> bool:
    return str(origen) == DEMO


def nombre_visible(origen: str) -> str:
    """'archivo:cartera.xlsx' -> 'cartera.xlsx'; 'manual' queda igual."""
    for prefijo in (PREFIJO_ARCHIVO, PREFIJO_SQL):
        if origen.startswith(prefijo):
            return origen[len(prefijo):]
    return origen


@dataclass(frozen=True)
class FuenteActiva:
    tipo: str
    origenes: tuple[str, ...]
    proyectos: pd.DataFrame
    tareas: pd.DataFrame
    equipo: pd.DataFrame

    @property
    def es_demo(self) -> bool:
        return self.tipo == TIPO_DEMO

    @property
    def es_usuario(self) -> bool:
        return self.tipo == TIPO_USUARIO

    @property
    def nombre(self) -> str:
        return ", ".join(nombre_visible(o) for o in self.origenes)

    @property
    def clave(self) -> str:
        """Identifica la fuente para invalidar cualquier cache que dependa de
        ella: cambia al pasar de demo a usuario, al sumar otro origen o al
        cambiar la cantidad de filas."""
        return (f"{self.tipo}|{'|'.join(self.origenes)}|"
                f"{len(self.proyectos)}|{len(self.tareas)}|{len(self.equipo)}")


def _sin_origen(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=["origen"]) if "origen" in df.columns else df


def resolver(proyectos: pd.DataFrame, tareas: pd.DataFrame,
             equipo: pd.DataFrame) -> FuenteActiva:
    """Decide la fuente activa y devuelve sólo sus filas.

    `proyectos` trae una columna `origen` (si falta, todo cuenta como
    ``manual``: dato del usuario). `equipo` puede traerla también; si no, no se
    filtra. Las tareas se quedan sólo con las de los proyectos que sobreviven,
    así una tarea de la demo no se cuela colgada de un proyecto oculto.
    Las columnas devueltas son las mismas de siempre, sin `origen`.
    """
    origen = (proyectos["origen"].fillna(MANUAL).astype(str)
              if "origen" in proyectos.columns
              else pd.Series(MANUAL, index=proyectos.index, dtype=object))
    # astype(bool): con cero filas map() devuelve dtype object, y pandas toma
    # una máscara object vacía como lista de columnas -> DataFrame sin columnas.
    demo_mask = origen.map(es_demo).astype(bool)

    if (~demo_mask).any():
        tipo = TIPO_USUARIO
        keep = ~demo_mask
    elif demo_mask.any():
        tipo = TIPO_DEMO
        keep = demo_mask
    else:
        tipo = TIPO_VACIA
        keep = demo_mask  # todo False

    proy = proyectos.loc[keep.to_numpy()].reset_index(drop=True)
    origenes = tuple(dict.fromkeys(origen[keep].tolist()))

    ids = set(proy["proyecto_id"]) if "proyecto_id" in proy.columns else set()
    if "proyecto_id" in tareas.columns:
        tar = tareas[tareas["proyecto_id"].isin(ids)].reset_index(drop=True)
    else:
        tar = tareas

    eq = equipo
    if "origen" in equipo.columns:
        eq_demo = equipo["origen"].fillna(MANUAL).astype(str).map(es_demo).astype(bool)
        # El equipo "de la demo" (usuarios ficticios @demo.local) sólo se ve
        # con la demo. Los usuarios reales se ven siempre.
        eq = equipo.loc[(~eq_demo).to_numpy()] if tipo == TIPO_USUARIO else equipo
        eq = eq.reset_index(drop=True)

    return FuenteActiva(tipo=tipo, origenes=origenes, proyectos=_sin_origen(proy),
                        tareas=tar, equipo=_sin_origen(eq))


def existentes_para_importar(activa: FuenteActiva, tipo: str,
                             todos_proyectos: pd.DataFrame | None = None) -> pd.DataFrame:
    """Contra qué filas detecta duplicados el importador.

    - Tareas: las de la fuente activa.
    - Proyectos con la demo activa: ninguna. Importar REEMPLAZA a la demo, así
      que un proyecto propio que se llame igual que uno de ejemplo no es un
      duplicado (y re-importar el archivo después de "volver a la demo" tiene
      que funcionar).
    - Proyectos con datos del usuario activos: todos los del usuario, incluidos
      los archivados si se pasan en `todos_proyectos` (con columna `origen`),
      para no duplicar un proyecto que alguien archivó a mano.
    """
    if tipo != "proyectos":
        return activa.tareas
    if not activa.es_usuario:
        return activa.proyectos.iloc[0:0]
    if todos_proyectos is None or "origen" not in todos_proyectos.columns:
        return activa.proyectos
    propios = todos_proyectos.loc[
        ~todos_proyectos["origen"].fillna(MANUAL).map(es_demo).astype(bool).to_numpy()]
    return _sin_origen(propios).reset_index(drop=True)


# ---------------------------------------------------------------- base real

def desde_db() -> FuenteActiva:
    """Fuente activa de la base SQLite (usuario registrado, API, MCP)."""
    from . import db

    # Idempotente y barato; cubre una base restaurada desde un respaldo viejo
    # que todavía no tiene la columna `origen`.
    db.init_db()
    return resolver(db.projects(con_origen=True), db.tasks(), db.team(con_origen=True))


def volver_a_demo_db() -> int:
    """Archiva (no borra) los proyectos del usuario para que vuelva la demo.
    Devuelve cuántos proyectos se archivaron."""
    from . import db

    return db.archivar_proyectos_de_usuario()
