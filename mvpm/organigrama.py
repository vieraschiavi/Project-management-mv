"""Organigrama: se carga desde Excel/CSV/SQL (o se pega una tabla), la IA lo
investiga y AUTOCOMPLETA por defecto quién es responsable de cada etapa del
proyecto — y todo eso queda editable y guardado por empresa, con versión.

- `parsear(df)`  : mapea columnas comunes (nombre, cargo, área, reporta a) sin
                   exigir un formato exacto.
- `sugerir_responsables(...)` : para cada una de las 5 etapas (grupos de
                   procesos del PMBOK), recomienda una persona del organigrama
                   por su cargo — con el motor de reglas siempre, y pulido por
                   IA si hay proveedor. Aparece pre-recomendado; el usuario lo
                   valida o lo cambia.
- La asignación validada se guarda versionada (mvpm/db.py, entidad
                   `responsable_etapa`) con quién la validó (nombre + cargo).

Foto del organigrama: se puede subir, pero extraer texto de una imagen requiere
un proveedor de IA con visión configurado — sin eso, el módulo lo dice
honestamente y pide el organigrama como Excel/CSV/SQL en su lugar.
"""

import json

import pandas as pd

from . import ai, db

ENTIDAD = "responsable_etapa"

# Las 5 etapas = grupos de procesos del PMBOK.
ETAPAS = [
    {"clave": "inicio", "nombre": "Inicio",
     "desc": "Autorizar el proyecto, definir objetivos e identificar sponsor e interesados.",
     "cargos_clave": ["sponsor", "director", "gerente general", "gerente general", "vp",
                      "vicepresidente", "ceo", "dueño", "socio", "gerente de área"]},
    {"clave": "planificacion", "nombre": "Planificación",
     "desc": "Definir alcance, cronograma, costos, riesgos y el plan de trabajo.",
     "cargos_clave": ["pmo", "gerente de proyecto", "project manager", "planificador",
                      "líder de proyecto", "lider de proyecto", "jefe de proyecto"]},
    {"clave": "ejecucion", "nombre": "Ejecución",
     "desc": "Realizar el trabajo del plan, coordinar al equipo y los recursos.",
     "cargos_clave": ["líder técnico", "lider tecnico", "team lead", "coordinador",
                      "desarrollador", "analista", "ingeniero", "especialista"]},
    {"clave": "monitoreo", "nombre": "Monitoreo y Control",
     "desc": "Medir avance vs. línea base, controlar cambios, riesgos y calidad.",
     "cargos_clave": ["qa", "calidad", "control", "auditor", "pmo",
                      "analista de riesgos", "controller"]},
    {"clave": "cierre", "nombre": "Cierre",
     "desc": "Formalizar la aceptación, cerrar contratos y documentar lecciones aprendidas.",
     "cargos_clave": ["pmo", "gerente de proyecto", "sponsor", "director", "jefe de proyecto"]},
]

_ETAPAS_POR_CLAVE = {e["clave"]: e for e in ETAPAS}


def _col(df: pd.DataFrame, *nombres: str) -> str | None:
    cols = {c.lower().strip(): c for c in df.columns}
    for n in nombres:
        if n in cols:
            return cols[n]
    return None


def parsear(df: pd.DataFrame) -> list[dict]:
    """Mapea un DataFrame (de Excel/CSV/SQL) a personas del organigrama,
    reconociendo nombres de columna comunes en español e inglés."""
    c_nombre = _col(df, "nombre", "name", "persona", "empleado", "full name")
    c_cargo = _col(df, "cargo", "puesto", "role", "title", "position", "rol")
    c_area = _col(df, "area", "área", "department", "departamento", "sector", "gerencia")
    c_reporta = _col(df, "reporta_a", "reporta a", "reports to", "manager", "jefe", "supervisor")
    c_email = _col(df, "email", "correo", "mail", "e-mail")

    personas = []
    for _, row in df.iterrows():
        nombre = row.get(c_nombre) if c_nombre else None
        if nombre is None or (isinstance(nombre, float) and pd.isna(nombre)) or not str(nombre).strip():
            continue
        personas.append({
            "nombre": str(nombre).strip(),
            "cargo": str(row[c_cargo]).strip() if c_cargo and pd.notna(row.get(c_cargo)) else None,
            "area": str(row[c_area]).strip() if c_area and pd.notna(row.get(c_area)) else None,
            "reporta_a": str(row[c_reporta]).strip() if c_reporta and pd.notna(row.get(c_reporta)) else None,
            "email": str(row[c_email]).strip() if c_email and pd.notna(row.get(c_email)) else None,
        })
    return personas


def _puntuar(persona: dict, etapa: dict) -> int:
    texto = f"{persona.get('cargo') or ''} {persona.get('area') or ''}".lower()
    return sum(1 for kw in etapa["cargos_clave"] if kw in texto)


def sugerir_responsables(personas: list[dict], proveedor: str | None = None) -> list[dict]:
    """Para cada etapa, recomienda la persona cuyo cargo mejor encaja (motor de
    reglas). Si hay proveedor de IA, agrega una breve justificación. Devuelve
    una entrada por etapa; 'persona' es None si el organigrama no tiene un
    cargo que encaje (ahí el usuario asigna a mano)."""
    sugerencias = []
    for etapa in ETAPAS:
        mejor, mejor_score = None, 0
        for p in personas:
            s = _puntuar(p, etapa)
            if s > mejor_score:
                mejor, mejor_score = p, s
        justificacion = None
        recomendado_por = "motor de reglas (por cargo)"
        if mejor and proveedor:
            texto = ai.completar(
                system="Sos un experto en gestión de proyectos. Respondés en una sola frase, "
                       "en español rioplatense, sin inventar datos.",
                user=f"Etapa del proyecto: {etapa['nombre']} — {etapa['desc']}\n"
                     f"Persona candidata: {mejor['nombre']}, cargo {mejor.get('cargo') or 's/d'}, "
                     f"área {mejor.get('area') or 's/d'}.\n"
                     "En una frase, justificá por qué encaja como responsable de esta etapa.",
                proveedor=proveedor,
            )
            if texto and texto.strip():
                justificacion = texto.strip()
                recomendado_por = f"IA ({ai.ETIQUETAS.get(proveedor, proveedor)})"
        sugerencias.append({
            "etapa_clave": etapa["clave"], "etapa_nombre": etapa["nombre"], "etapa_desc": etapa["desc"],
            "persona": mejor, "justificacion": justificacion, "recomendado_por": recomendado_por,
        })
    return sugerencias


def responsable_vigente(empresa_id: int, etapa_clave: str) -> dict | None:
    """Responsable guardado (validado) para una etapa, o None si todavía no se
    asignó."""
    version = db.obtener_version_actual(empresa_id, ENTIDAD, etapa_clave)
    if not version:
        return None
    try:
        persona = json.loads(version["contenido"])
    except (ValueError, TypeError):
        persona = {"nombre": version["contenido"], "cargo": None}
    return {
        "persona": persona, "estado": version["estado"],
        "recomendado_por": version["recomendado_por"],
        "validado_por_nombre": version["validado_por_nombre"],
        "validado_por_cargo": version["validado_por_cargo"],
    }


def guardar_responsable(empresa_id: int, etapa_clave: str, nombre: str, cargo: str,
                        recomendado_por: str, validado_por_nombre: str,
                        validado_por_cargo: str) -> int:
    contenido = json.dumps({"nombre": nombre, "cargo": cargo}, ensure_ascii=False)
    return db.guardar_version(
        empresa_id, ENTIDAD, etapa_clave, contenido, estado="validado",
        recomendado_por=recomendado_por,
        validado_por_nombre=validado_por_nombre, validado_por_cargo=validado_por_cargo,
    )


def etapa(clave: str) -> dict | None:
    return _ETAPAS_POR_CLAVE.get(clave)
