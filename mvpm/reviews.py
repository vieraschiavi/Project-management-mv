"""Reseñas y calificación de usuarios reales.

Principio de honestidad (igual que Kobra/Data Governance MV): este módulo NUNCA
genera reseñas sintéticas y las presenta como reales. Mientras no haya reseñas
verificadas, `list_reviews()` devuelve una lista vacía y la web debe mostrar un
estado honesto ("programa en beta"), no testimonios inventados.

Persistencia simple en JSON local, igual patrón que `clients.py` de Data
Governance MV — pensado para migrar a una base de datos real cuando haya
usuarios de producción.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

_STORE_DIR = Path.home() / ".mv_project_management"
_STORE_FILE = _STORE_DIR / "resenas.json"


@dataclass
class Review:
    autor: str
    empresa: str
    rol: str
    calificacion: int  # 1-5
    comentario: str
    verificado: bool = False
    creado_en: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self):
        if not (1 <= self.calificacion <= 5):
            raise ValueError("La calificación debe estar entre 1 y 5.")
        if not self.autor.strip() or not self.comentario.strip():
            raise ValueError("Autor y comentario son obligatorios.")


def _load() -> list[dict]:
    if not _STORE_FILE.exists():
        return []
    try:
        return json.loads(_STORE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save(rows: list[dict]) -> None:
    _STORE_DIR.mkdir(parents=True, exist_ok=True)
    _STORE_FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def add_review(autor: str, empresa: str, rol: str, calificacion: int, comentario: str,
               verificado: bool = False) -> Review:
    """Registra una reseña nueva. `verificado=True` solo lo debe setear un proceso
    que confirme que el autor es un usuario real del producto (ej. login + uso
    activo), nunca a mano al cargar contenido de marketing."""
    review = Review(autor, empresa, rol, calificacion, comentario, verificado)
    rows = _load()
    rows.append(asdict(review))
    _save(rows)
    return review


def list_reviews(only_verified: bool = True) -> list[dict]:
    rows = _load()
    if only_verified:
        rows = [r for r in rows if r.get("verificado")]
    return sorted(rows, key=lambda r: r["creado_en"], reverse=True)


def average_rating(only_verified: bool = True) -> float | None:
    rows = list_reviews(only_verified)
    if not rows:
        return None
    return round(sum(r["calificacion"] for r in rows) / len(rows), 2)


def rating_distribution(only_verified: bool = True) -> dict:
    rows = list_reviews(only_verified)
    dist = {n: 0 for n in range(1, 6)}
    for r in rows:
        dist[r["calificacion"]] += 1
    return dist


def summary(only_verified: bool = True) -> dict:
    rows = list_reviews(only_verified)
    return {
        "total": len(rows),
        "promedio": average_rating(only_verified),
        "distribucion": rating_distribution(only_verified),
        "es_beta_sin_resenas": len(rows) == 0,
    }
