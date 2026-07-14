"""Base de datos real (SQLite) para proyectos, tareas y usuarios.

Reemplaza a `demo_data.py` como fuente de datos operativa — pero devuelve
DataFrames con exactamente las mismas columnas que `demo_data.projects()`,
`demo_data.tasks()` y `demo_data.team()`, para que todo el motor
(`health.py`, `dependencies.py`, `prioritizer.py`, `policies.py`,
`reports.py`, `exporters.py`, `copilot.py`) siga funcionando sin cambios.

El archivo vive en el equipo/servidor del cliente (`~/.mv_project_management/`,
mismo directorio que licencias y reseñas) — no se manda a ningún lado por
defecto, consistente con "tus datos en tu servidor" de la landing.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_STORE_DIR = Path.home() / ".mv_project_management"
_DB_FILE = _STORE_DIR / "datos.db"

_HORAS_POR_TAREA_ACTIVA = 4  # estimación fija para el proxy de carga del equipo


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _connect():
    _STORE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Crea las tablas si no existen. Idempotente — se puede llamar en cada arranque."""
    with _connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'miembro',
            capacidad_semanal_hs INTEGER NOT NULL DEFAULT 40,
            creado_en TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            portafolio TEXT NOT NULL DEFAULT 'Sin portafolio',
            sponsor TEXT,
            dueno_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
            segmento TEXT NOT NULL DEFAULT 'Interno',
            fecha_inicio TEXT,
            fecha_fin TEXT,
            presupuesto REAL NOT NULL DEFAULT 0,
            ejecutado REAL NOT NULL DEFAULT 0,
            criticidad TEXT NOT NULL DEFAULT 'Media',
            archivado INTEGER NOT NULL DEFAULT 0,
            creado_en TEXT NOT NULL,
            actualizado_en TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
            titulo TEXT NOT NULL,
            responsable_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
            estado TEXT NOT NULL DEFAULT 'todo',
            vencimiento TEXT,
            prioridad TEXT NOT NULL DEFAULT 'Media',
            depende_de INTEGER REFERENCES tareas(id) ON DELETE SET NULL,
            creado_en TEXT NOT NULL,
            actualizado_en TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS seguimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problema_id TEXT UNIQUE NOT NULL,
            tipo TEXT NOT NULL,
            titulo TEXT NOT NULL,
            sugerencia TEXT NOT NULL,
            proveedor TEXT,
            estado TEXT NOT NULL DEFAULT 'abierto',
            creado_en TEXT NOT NULL,
            actualizado_en TEXT NOT NULL
        );
        """)


# ---------------------------------------------------------------- usuarios

def contar_usuarios() -> int:
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM usuarios").fetchone()["n"]


def crear_usuario(email: str, nombre: str, password_hash: str, password_salt: str,
                   rol: str = "miembro", capacidad_semanal_hs: int = 40) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO usuarios (email, nombre, password_hash, password_salt, rol, "
            "capacidad_semanal_hs, creado_en) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (email.strip().lower(), nombre, password_hash, password_salt, rol,
             capacidad_semanal_hs, _now()),
        )
        return cur.lastrowid


def obtener_usuario_por_email(email: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email.strip().lower(),)).fetchone()
        return dict(row) if row else None


def listar_usuarios() -> pd.DataFrame:
    with _connect() as conn:
        df = pd.read_sql_query("SELECT id, email, nombre, rol, capacidad_semanal_hs FROM usuarios ORDER BY nombre", conn)
    return df


# ---------------------------------------------------------------- proyectos

_PROJECT_FIELDS = ["nombre", "portafolio", "sponsor", "dueno_id", "segmento",
                    "fecha_inicio", "fecha_fin", "presupuesto", "ejecutado", "criticidad"]


def crear_proyecto(**kwargs) -> int:
    campos = {k: kwargs.get(k) for k in _PROJECT_FIELDS}
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO proyectos (nombre, portafolio, sponsor, dueno_id, segmento, "
            "fecha_inicio, fecha_fin, presupuesto, ejecutado, criticidad, creado_en, actualizado_en) "
            "VALUES (:nombre, :portafolio, :sponsor, :dueno_id, :segmento, :fecha_inicio, :fecha_fin, "
            ":presupuesto, :ejecutado, :criticidad, :creado_en, :actualizado_en)",
            {**campos, "creado_en": _now(), "actualizado_en": _now()},
        )
        return cur.lastrowid


def actualizar_proyecto(proyecto_id: int, **kwargs) -> None:
    campos = {k: v for k, v in kwargs.items() if k in _PROJECT_FIELDS}
    if not campos:
        return
    set_clause = ", ".join(f"{k} = :{k}" for k in campos)
    with _connect() as conn:
        conn.execute(
            f"UPDATE proyectos SET {set_clause}, actualizado_en = :actualizado_en WHERE id = :id",
            {**campos, "actualizado_en": _now(), "id": proyecto_id},
        )


def archivar_proyecto(proyecto_id: int, archivado: bool = True) -> None:
    with _connect() as conn:
        conn.execute("UPDATE proyectos SET archivado = ?, actualizado_en = ? WHERE id = ?",
                     (int(archivado), _now(), proyecto_id))


def eliminar_proyecto(proyecto_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))


def projects(incluir_archivados: bool = False) -> pd.DataFrame:
    """Mismo esquema de columnas que `demo_data.projects()`."""
    where = "" if incluir_archivados else "WHERE p.archivado = 0"
    with _connect() as conn:
        df = pd.read_sql_query(f"""
            SELECT p.id AS _id, 'PRJ-' || printf('%03d', p.id) AS proyecto_id,
                   p.nombre, p.portafolio, p.sponsor, u.nombre AS dueno, p.segmento,
                   p.fecha_inicio, p.fecha_fin, p.presupuesto, p.ejecutado, p.criticidad
            FROM proyectos p
            LEFT JOIN usuarios u ON u.id = p.dueno_id
            {where}
            ORDER BY p.id
        """, conn)
    return df


# ------------------------------------------------------------------- tareas

_TASK_FIELDS = ["proyecto_id", "titulo", "responsable_id", "estado", "vencimiento",
                 "prioridad", "depende_de"]


def crear_tarea(**kwargs) -> int:
    campos = {k: kwargs.get(k) for k in _TASK_FIELDS}
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO tareas (proyecto_id, titulo, responsable_id, estado, vencimiento, "
            "prioridad, depende_de, creado_en, actualizado_en) "
            "VALUES (:proyecto_id, :titulo, :responsable_id, :estado, :vencimiento, "
            ":prioridad, :depende_de, :creado_en, :actualizado_en)",
            {**campos, "creado_en": _now(), "actualizado_en": _now()},
        )
        return cur.lastrowid


def actualizar_tarea(tarea_id: int, **kwargs) -> None:
    campos = {k: v for k, v in kwargs.items() if k in _TASK_FIELDS}
    if not campos:
        return
    set_clause = ", ".join(f"{k} = :{k}" for k in campos)
    with _connect() as conn:
        conn.execute(
            f"UPDATE tareas SET {set_clause}, actualizado_en = :actualizado_en WHERE id = :id",
            {**campos, "actualizado_en": _now(), "id": tarea_id},
        )


def eliminar_tarea(tarea_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))


def tasks() -> pd.DataFrame:
    """Mismo esquema de columnas que `demo_data.tasks()`."""
    with _connect() as conn:
        df = pd.read_sql_query("""
            SELECT t.id AS _id, 'T-' || printf('%04d', t.id) AS tarea_id,
                   'PRJ-' || printf('%03d', t.proyecto_id) AS proyecto_id,
                   t.titulo, u.nombre AS responsable, t.estado, t.vencimiento, t.prioridad,
                   CASE WHEN t.depende_de IS NULL THEN NULL
                        ELSE 'T-' || printf('%04d', t.depende_de) END AS depende_de
            FROM tareas t
            LEFT JOIN usuarios u ON u.id = t.responsable_id
            ORDER BY t.id
        """, conn)
    return df


def team() -> pd.DataFrame:
    """Mismo esquema de columnas que `demo_data.team()`. `carga_actual_hs` es un
    proxy calculado (tareas activas asignadas × horas fijas por tarea), no un
    dato cargado a mano — evita pedirle a cada usuario que mantenga esa cifra."""
    with _connect() as conn:
        usuarios = pd.read_sql_query(
            "SELECT id, nombre, rol, capacidad_semanal_hs FROM usuarios", conn)
        carga = pd.read_sql_query("""
            SELECT responsable_id, COUNT(*) AS tareas_activas
            FROM tareas
            WHERE responsable_id IS NOT NULL AND estado != 'done'
            GROUP BY responsable_id
        """, conn)
    usuarios = usuarios.merge(carga, left_on="id", right_on="responsable_id", how="left")
    usuarios["tareas_activas"] = usuarios["tareas_activas"].fillna(0)
    usuarios["carga_actual_hs"] = (usuarios["tareas_activas"] * _HORAS_POR_TAREA_ACTIVA).astype(int)
    return usuarios[["nombre", "rol", "capacidad_semanal_hs", "carga_actual_hs"]]


# ---------------------------------------------------------------- seguimientos

def crear_o_actualizar_seguimiento(problema_id: str, tipo: str, titulo: str,
                                    sugerencia: str, proveedor: str | None = None) -> int:
    """Un seguimiento por problema (problema_id es estable: '{tipo}:{entidad}').
    Si ya existía, actualiza la sugerencia sin tocar su estado — así no se
    pierde el progreso si alguien vuelve a pedir una sugerencia."""
    with _connect() as conn:
        row = conn.execute("SELECT id FROM seguimientos WHERE problema_id = ?", (problema_id,)).fetchone()
        if row:
            conn.execute(
                "UPDATE seguimientos SET titulo = ?, sugerencia = ?, proveedor = ?, actualizado_en = ? WHERE id = ?",
                (titulo, sugerencia, proveedor, _now(), row["id"]),
            )
            return row["id"]
        cur = conn.execute(
            "INSERT INTO seguimientos (problema_id, tipo, titulo, sugerencia, proveedor, creado_en, actualizado_en) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (problema_id, tipo, titulo, sugerencia, proveedor, _now(), _now()),
        )
        return cur.lastrowid


def actualizar_estado_seguimiento(seguimiento_id: int, estado: str) -> None:
    with _connect() as conn:
        conn.execute("UPDATE seguimientos SET estado = ?, actualizado_en = ? WHERE id = ?",
                     (estado, _now(), seguimiento_id))


def listar_seguimientos() -> pd.DataFrame:
    with _connect() as conn:
        return pd.read_sql_query(
            "SELECT id, problema_id, tipo, titulo, sugerencia, proveedor, estado, creado_en, actualizado_en "
            "FROM seguimientos ORDER BY creado_en DESC", conn)


def obtener_seguimiento_por_problema(problema_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM seguimientos WHERE problema_id = ?", (problema_id,)).fetchone()
        return dict(row) if row else None


# --------------------------------------------------------------------- seed

def esta_vacia() -> bool:
    with _connect() as conn:
        n = conn.execute("SELECT COUNT(*) AS n FROM proyectos").fetchone()["n"]
    return n == 0


def cargar_datos_de_ejemplo() -> None:
    """Siembra la base con los mismos datos sintéticos de `demo_data.py`, para
    que una instalación nueva tenga algo para explorar. Idempotente respecto
    del motor: una vez sembrado, projects()/tasks()/team() vienen de acá, no
    de demo_data — el usuario puede editar o borrar libremente lo sembrado."""
    from . import demo_data

    with _connect() as conn:
        admin = conn.execute("SELECT id FROM usuarios ORDER BY id LIMIT 1").fetchone()
    if admin is None:
        raise RuntimeError("Creá el primer usuario antes de cargar datos de ejemplo.")
    admin_id = admin["id"]

    nombre_a_id: dict[str, int] = {}

    def _id_para(nombre: str | None) -> int | None:
        if not nombre or pd.isna(nombre):
            return None
        if nombre not in nombre_a_id:
            partes = nombre.split()
            email = f"{partes[0].lower()}.{nombre.replace(' ', '').lower()}@demo.local"
            nombre_a_id[nombre] = crear_usuario(
                email=email, nombre=nombre,
                password_hash="", password_salt="", rol="miembro",
            )
        return nombre_a_id[nombre]

    proy_id_map: dict[str, int] = {}
    for _, p in demo_data.projects().iterrows():
        new_id = crear_proyecto(
            nombre=p["nombre"], portafolio=p["portafolio"], sponsor=p["sponsor"],
            dueno_id=_id_para(p["dueno"]) or admin_id, segmento=p["segmento"],
            fecha_inicio=p["fecha_inicio"], fecha_fin=p["fecha_fin"],
            presupuesto=p["presupuesto"], ejecutado=p["ejecutado"], criticidad=p["criticidad"],
        )
        proy_id_map[p["proyecto_id"]] = new_id

    tarea_id_map: dict[str, int] = {}
    pendientes_dependencia = []
    for _, t in demo_data.tasks().iterrows():
        new_id = crear_tarea(
            proyecto_id=proy_id_map[t["proyecto_id"]], titulo=t["titulo"],
            responsable_id=_id_para(t["responsable"]), estado=t["estado"],
            vencimiento=t["vencimiento"], prioridad=t["prioridad"], depende_de=None,
        )
        tarea_id_map[t["tarea_id"]] = new_id
        if pd.notna(t["depende_de"]):
            pendientes_dependencia.append((new_id, t["depende_de"]))

    for tarea_id, dep_original in pendientes_dependencia:
        actualizar_tarea(tarea_id, depende_de=tarea_id_map.get(dep_original))
