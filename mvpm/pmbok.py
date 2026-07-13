"""Alineación con PMBOK (Project Management Body of Knowledge, guía del PMI) —
mapea las 10 áreas de conocimiento del estándar a lo que el producto cubre de
verdad. Mismo criterio de honestidad que el resto del motor (`reviews.py`,
`help_center.py`): donde el producto no cubre un área, o la cubre a medias,
lo dice — no es una certificación PMI, es una referencia de alineación.
"""

_COBERTURA_ORDEN = {"completa": 0, "parcial": 1, "no_cubierta": 2}

AREAS = [
    {
        "area": "Gestión de la integración", "area_en": "Integration management",
        "cobertura": "parcial",
        "como_lo_cubre": "El copiloto y el reporte ejecutivo (nav_copilot, nav_reports) consolidan "
                          "el estado de todo el portafolio en un solo lugar en tiempo real.",
        "lo_que_falta": "No reemplaza el acta de constitución del proyecto ni un control formal de "
                         "cambios — eso lo define y firma el PM fuera de la herramienta.",
    },
    {
        "area": "Gestión del alcance", "area_en": "Scope management",
        "cobertura": "completa",
        "como_lo_cubre": "Dimensión 'alcance' del índice de salud detecta tareas sin responsable "
                          "(alcance sin dueño claro); el catálogo de portafolio registra segmento y "
                          "criticidad de cada proyecto.",
        "lo_que_falta": None,
    },
    {
        "area": "Gestión del cronograma", "area_en": "Schedule management",
        "cobertura": "completa",
        "como_lo_cubre": "Dimensión 'cronograma' del índice de salud, vencimientos por tarea, grafo "
                          "de dependencias y bloqueos, y backlog priorizado por urgencia real.",
        "lo_que_falta": None,
    },
    {
        "area": "Gestión de los costos", "area_en": "Cost management",
        "cobertura": "completa",
        "como_lo_cubre": "Presupuesto vs. ejecutado por proyecto y por portafolio, dimensión "
                          "'presupuesto' del índice de salud, alerta de proyectos sobre presupuesto.",
        "lo_que_falta": None,
    },
    {
        "area": "Gestión de la calidad", "area_en": "Quality management",
        "cobertura": "parcial",
        "como_lo_cubre": "Las políticas de gestión (nav_policies) verifican reglas operativas contra "
                          "evidencia real del portafolio (dueños asignados, dependencias sanas, etc).",
        "lo_que_falta": "No hay checklist de aceptación de entregables ni control de calidad técnico "
                         "— sigue siendo responsabilidad del equipo y sus propias herramientas de QA.",
    },
    {
        "area": "Gestión de los recursos", "area_en": "Resource management",
        "cobertura": "completa",
        "como_lo_cubre": "Vista de equipo con carga actual vs. capacidad semanal, dimensión 'equipo' "
                          "del índice de salud, tareas activas por persona.",
        "lo_que_falta": None,
    },
    {
        "area": "Gestión de las comunicaciones", "area_en": "Communications management",
        "cobertura": "parcial",
        "como_lo_cubre": "Reporte ejecutivo listo para compartir y glosario compartido para que todo "
                          "el equipo hable el mismo idioma sobre los estados.",
        "lo_que_falta": "No hay mensajería, comentarios ni notificaciones dentro del producto todavía "
                         "— para eso, integralo con el chat que ya usa tu equipo.",
    },
    {
        "area": "Gestión de los riesgos", "area_en": "Risk management",
        "cobertura": "completa",
        "como_lo_cubre": "Dimensión 'riesgo' del índice de salud, detección de tareas bloqueadas y de "
                          "dependencias huérfanas que apuntan a nada.",
        "lo_que_falta": None,
    },
    {
        "area": "Gestión de las adquisiciones", "area_en": "Procurement management",
        "cobertura": "no_cubierta",
        "como_lo_cubre": None,
        "lo_que_falta": "No hay gestión de proveedores, contratos ni compras — usá tu herramienta de "
                         "compras habitual en paralelo; el sponsor y el presupuesto sí quedan acá.",
    },
    {
        "area": "Gestión de los interesados", "area_en": "Stakeholder management",
        "cobertura": "parcial",
        "como_lo_cubre": "Cada proyecto registra su sponsor, y el copiloto puede responder preguntas "
                          "sobre a quién le pertenece cada iniciativa.",
        "lo_que_falta": "No hay una matriz de interesados con poder/interés — si tu portafolio la "
                         "necesita, se arma una vez en una planilla aparte y se referencia desde acá.",
    },
]


def areas() -> list[dict]:
    return sorted(AREAS, key=lambda a: _COBERTURA_ORDEN[a["cobertura"]])


def resumen() -> dict:
    total = len(AREAS)
    por_estado = {"completa": 0, "parcial": 0, "no_cubierta": 0}
    for a in AREAS:
        por_estado[a["cobertura"]] += 1
    return {"total_areas": total, **por_estado}
