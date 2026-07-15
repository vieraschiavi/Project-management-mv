"""Gobernanza de definiciones: cada concepto de gestión de proyectos viene con
una definición YA PREESTABLECIDA de fábrica (correcta, lista para usar), y
sobre esa base:

  1. la IA puede RECOMENDAR una versión mejor/adaptada a la empresa
     (aparece pre-recomendada, no la escribe el usuario de cero);
  2. el DATA OWNER / DATA STEWARD la VALIDA o la MODIFICA y la GUARDA;
  3. cada cambio queda VERSIONADO por empresa (mvpm/db.py, tabla `versiones`),
     con quién lo recomendó y quién lo validó (nombre + cargo).

Mismo patrón de MV Data Governance: la definición vigente de un concepto en
una empresa es su última versión guardada; si nunca se tocó, se usa la
preestablecida de fábrica.
"""

from . import ai, db

ENTIDAD = "concepto"

# Definiciones preestablecidas de fábrica — correctas y listas para usar.
CONCEPTOS_BASE = [
    {"clave": "alcance", "termino": "Alcance (Scope)", "categoria": "Alcance",
     "definicion": "Todo el trabajo requerido — y sólo ese trabajo — para entregar el "
                   "producto o resultado del proyecto con las características acordadas. "
                   "Define qué está dentro y qué está fuera del proyecto."},
    {"clave": "linea_base", "termino": "Línea base (Baseline)", "categoria": "Integración",
     "definicion": "La versión aprobada de un plan (alcance, cronograma o costo) contra la "
                   "cual se mide el desempeño real. Sólo se cambia por control formal de cambios."},
    {"clave": "criticidad", "termino": "Criticidad", "categoria": "Riesgos",
     "definicion": "Qué tan importante es un proyecto para la organización. En este producto "
                   "pondera el índice de salud y el orden del backlog: Alta pesa más que Media, "
                   "que pesa más que Baja."},
    {"clave": "salud", "termino": "Índice de salud", "categoria": "Monitoreo",
     "definicion": "Puntaje 0-100 que resume el estado de un proyecto en 6 dimensiones "
                   "(alcance, cronograma, presupuesto, riesgo, dependencias, equipo). "
                   "≥75 saludable, 55-75 en observación, <55 en riesgo."},
    {"clave": "dependencia", "termino": "Dependencia", "categoria": "Cronograma",
     "definicion": "Relación en la que una tarea no puede empezar o terminar hasta que otra "
                   "avance. Una dependencia a una tarea inexistente es 'huérfana' y distorsiona "
                   "el cronograma."},
    {"clave": "bloqueo", "termino": "Bloqueo", "categoria": "Riesgos",
     "definicion": "Una tarea que no puede avanzar hasta resolver una dependencia u obstáculo "
                   "externo. Cuantas más tareas dependan de ella, mayor su impacto."},
    {"clave": "backlog", "termino": "Backlog priorizado", "categoria": "Alcance",
     "definicion": "Lista ordenada de tareas pendientes por valor esperado = criticidad × "
                   "prioridad × urgencia × impacto en dependencias. No es orden de llegada."},
    {"clave": "sponsor", "termino": "Sponsor (Patrocinador)", "categoria": "Interesados",
     "definicion": "La persona o área que provee los recursos y el respaldo político del "
                   "proyecto, y a quien rinde cuentas el líder de proyecto. Sin sponsor visible, "
                   "el proyecto pierde prioridad."},
    {"clave": "dueno", "termino": "Dueño de proyecto", "categoria": "Recursos",
     "definicion": "El responsable de que el proyecto avance y de reportar su estado real. "
                   "Un proyecto sin dueño asignado baja su dimensión de alcance."},
    {"clave": "data_owner", "termino": "Data Owner", "categoria": "Gobernanza",
     "definicion": "El responsable último de un dato o definición en la organización: aprueba "
                   "su significado y su uso. En este producto, quien valida una definición."},
    {"clave": "data_steward", "termino": "Data Steward", "categoria": "Gobernanza",
     "definicion": "Quien administra el dato en el día a día: mantiene la definición al día, "
                   "propone cambios y los lleva al Data Owner para su aprobación."},
    {"clave": "sobre_presupuesto", "termino": "Sobre presupuesto", "categoria": "Costos",
     "definicion": "Cuando lo ejecutado supera el presupuesto asignado al proyecto. Se detecta "
                   "automáticamente comparando ejecutado vs. presupuesto."},
    {"clave": "riesgo", "termino": "Riesgo", "categoria": "Riesgos",
     "definicion": "Evento incierto que, de ocurrir, afecta objetivos del proyecto. La "
                   "dimensión 'riesgo' del índice de salud lo aproxima por tareas bloqueadas."},
    {"clave": "interesado", "termino": "Interesado (Stakeholder)", "categoria": "Interesados",
     "definicion": "Cualquier persona o grupo que afecta o es afectado por el proyecto. Se "
                   "gestionan según su poder e interés."},
]

_POR_CLAVE = {c["clave"]: c for c in CONCEPTOS_BASE}


def catalogo() -> list[dict]:
    return CONCEPTOS_BASE


def concepto_base(clave: str) -> dict | None:
    return _POR_CLAVE.get(clave)


def definicion_vigente(empresa_id: int, clave: str) -> dict:
    """La definición que rige hoy para esta empresa: la última versión guardada,
    o la preestablecida de fábrica si nunca se tocó."""
    base = _POR_CLAVE.get(clave, {})
    version = db.obtener_version_actual(empresa_id, ENTIDAD, clave)
    if version:
        return {
            "texto": version["contenido"],
            "estado": version["estado"],
            "recomendado_por": version["recomendado_por"],
            "validado_por_nombre": version["validado_por_nombre"],
            "validado_por_cargo": version["validado_por_cargo"],
            "origen": "versionada",
        }
    return {
        "texto": base.get("definicion", ""),
        "estado": "preestablecida",
        "recomendado_por": "motor de reglas (definición de fábrica)",
        "validado_por_nombre": None,
        "validado_por_cargo": None,
        "origen": "preestablecida",
    }


def recomendar_definicion(clave: str, proveedor: str | None = None) -> dict:
    """Devuelve una definición RECOMENDADA como punto de partida (nunca en
    blanco): la de fábrica pulida por IA si hay proveedor, o la de fábrica tal
    cual. El usuario después la valida o la edita."""
    base = _POR_CLAVE.get(clave, {})
    texto_base = base.get("definicion", "")
    resultado = {"texto": texto_base, "recomendado_por": "motor de reglas (definición de fábrica)"}
    if proveedor:
        pulida = ai.completar(
            system="Sos un experto en gestión de proyectos (PMBOK). Redactás en español "
                   "rioplatense, claro y preciso. Mejorás definiciones sin cambiar su significado "
                   "técnico ni inventar conceptos nuevos.",
            user=f"Concepto: {base.get('termino', clave)}\nDefinición actual: {texto_base}\n"
                 "Devolvé UNA definición mejorada, más clara, en 1-3 frases. Sólo la definición.",
            proveedor=proveedor,
        )
        if pulida and pulida.strip():
            resultado = {"texto": pulida.strip(), "recomendado_por": f"IA ({ai.ETIQUETAS.get(proveedor, proveedor)})"}
    return resultado


def guardar(empresa_id: int, clave: str, texto: str, recomendado_por: str,
            validado_por_nombre: str, validado_por_cargo: str) -> int:
    """Guarda una definición validada por el data owner/steward. Queda como
    versión nueva (no pisa la anterior), en estado 'validado'."""
    return db.guardar_version(
        empresa_id, ENTIDAD, clave, texto, estado="validado",
        recomendado_por=recomendado_por,
        validado_por_nombre=validado_por_nombre, validado_por_cargo=validado_por_cargo,
    )
