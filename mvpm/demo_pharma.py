"""Demo con datos reales de un laboratorio multinacional: ensayos clínicos.

Un ensayo clínico ES un proyecto — tiene sponsor (un laboratorio como
AstraZeneca, Pfizer o Novartis), un título, fechas de inicio/fin, una fase, y
un estado (RECRUITING / COMPLETED / TERMINATED / SUSPENDED) que se comporta
igual que el estado de un proyecto. Este módulo corre el mismo motor de
salud/criticidad sobre 474 ensayos reales de tres laboratorios multinacionales.

Fuente: ClinicalTrials.gov (U.S. National Library of Medicine, NIH). Datos de
dominio público. No requiere credenciales. Se muestra la atribución en la
pestaña, como pide NLM.

Honestidad: ClinicalTrials.gov **no publica presupuesto** de los ensayos, así
que las columnas de presupuesto/ejecutado quedan en 0 y se aclara — no se
inventan cifras de plata. La criticidad se deriva del estado real del ensayo,
que es un dato que sí existe:
  TERMINATED / SUSPENDED     -> Alta   (rojo, en riesgo / frenado)
  RECRUITING / ACTIVE...     -> Media  (ámbar, en curso)
  COMPLETED                  -> Baja   (verde, cerrado ok)
"""

from pathlib import Path

import pandas as pd

from . import catalog

_CSV_PATH = Path(__file__).parent / "data" / "clinicaltrials_pharma.csv"

FUENTE = "ClinicalTrials.gov — U.S. National Library of Medicine (NIH). Dominio público."
FUENTE_URL = "https://clinicaltrials.gov"

_ESTADO_A_CRITICIDAD = {
    "TERMINATED": "Alta",
    "SUSPENDED": "Alta",
    "RECRUITING": "Media",
    "ACTIVE_NOT_RECRUITING": "Media",
    "ENROLLING_BY_INVITATION": "Media",
    "NOT_YET_RECRUITING": "Media",
    "COMPLETED": "Baja",
}

_ESTADO_ES = {
    "TERMINATED": "Terminado anticipadamente",
    "SUSPENDED": "Suspendido",
    "RECRUITING": "Reclutando",
    "ACTIVE_NOT_RECRUITING": "Activo, sin reclutar",
    "ENROLLING_BY_INVITATION": "Inscripción por invitación",
    "NOT_YET_RECRUITING": "Aún sin reclutar",
    "COMPLETED": "Completado",
}


def _sponsor_normalizado(nombre: str) -> str:
    """Agrupa subsidiarias bajo el laboratorio matriz para el portafolio
    (los datos traen 'Novartis Pharmaceuticals', 'Alcon, a Novartis Company',
    etc. — son todos Novartis a efectos de portafolio)."""
    n = (nombre or "").lower()
    if "astrazeneca" in n:
        return "AstraZeneca"
    if "pfizer" in n or "wyeth" in n or "seagen" in n:
        return "Pfizer"
    if "novartis" in n or "alcon" in n or "corthera" in n or "tourmaline" in n:
        return "Novartis"
    return nombre


def cargar_portafolio_pharma() -> pd.DataFrame:
    """DataFrame con el mismo esquema que `demo_data.projects()`, construido a
    partir de los ensayos reales. presupuesto/ejecutado en 0 (el dataset no
    tiene esa info) — la criticidad viene del estado real del ensayo."""
    df = pd.read_csv(_CSV_PATH).fillna("")
    return pd.DataFrame({
        "proyecto_id": [f"NCT-{i + 1:03d}" for i in range(len(df))],
        "nombre": df["titulo"].str.slice(0, 90),
        "portafolio": df["sponsor"].map(_sponsor_normalizado),
        "sponsor": df["sponsor"].map(_sponsor_normalizado),
        "dueno": None,
        "segmento": "Ensayo clínico (fase " + df["fase"].astype(str) + ")",
        "fecha_inicio": df["fecha_inicio"].astype(str),
        "fecha_fin": df["fecha_fin"].astype(str),
        "presupuesto": 0.0,
        "ejecutado": 0.0,
        "criticidad": df["estado_ct"].map(_ESTADO_A_CRITICIDAD).fillna("Media"),
    })


def _crudo() -> pd.DataFrame:
    return pd.read_csv(_CSV_PATH).fillna("")


def resumen_portafolio() -> dict:
    """KPIs reales del motor sobre los ensayos. La señal de PM acá es el
    estado del ensayo (no el presupuesto, que no existe en la fuente)."""
    crudo = _crudo()
    proj = cargar_portafolio_pharma()
    total = len(proj)
    por_estado = crudo["estado_ct"].map(lambda e: _ESTADO_ES.get(e, e)).value_counts().to_dict()
    por_sponsor = proj["portafolio"].value_counts().to_dict()
    en_riesgo = int((proj["criticidad"] == "Alta").sum())
    minutos_por_revision_manual = 10  # supuesto explícito, no medido — declarado
    horas_ahorradas = round(total * minutos_por_revision_manual / 60, 1)
    return {
        "total_ensayos": total,
        "en_riesgo": en_riesgo,
        "por_estado": por_estado,
        "por_sponsor": por_sponsor,
        "minutos_por_revision_manual_supuesto": minutos_por_revision_manual,
        "horas_ahorradas_estimadas": horas_ahorradas,
    }


def en_riesgo_detalle(limite: int = 15) -> pd.DataFrame:
    """Los ensayos que el motor marca en riesgo (terminados/suspendidos),
    con su sponsor y fechas — lo que un PMO de portafolio miraría primero."""
    crudo = _crudo()
    riesgo = crudo[crudo["estado_ct"].isin(["TERMINATED", "SUSPENDED"])].copy()
    riesgo["estado"] = riesgo["estado_ct"].map(lambda e: _ESTADO_ES.get(e, e))
    riesgo["sponsor"] = riesgo["sponsor"].map(_sponsor_normalizado)
    return riesgo[["titulo", "sponsor", "estado", "fase", "fecha_inicio", "fecha_fin"]].head(limite)


def tabla_para_bi() -> pd.DataFrame:
    """Tabla lista para exportar a Power BI / Tableau: un ensayo por fila, con
    su estado en español, criticidad derivada y sponsor normalizado. Es la
    misma que sirve la API REST local (api/main.py) para la conexión de BI."""
    crudo = _crudo()
    proj = cargar_portafolio_pharma()
    return pd.DataFrame({
        "nct": crudo["nct"],
        "titulo": crudo["titulo"],
        "laboratorio": proj["portafolio"],
        "estado": crudo["estado_ct"].map(lambda e: _ESTADO_ES.get(e, e)),
        "estado_ct": crudo["estado_ct"],
        "fase": crudo["fase"],
        "tipo_estudio": crudo["tipo_estudio"],
        "criticidad": proj["criticidad"],
        "fecha_inicio": crudo["fecha_inicio"],
        "fecha_fin": crudo["fecha_fin"],
    })
