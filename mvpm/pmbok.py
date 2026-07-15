"""PMBOK (Project Management Body of Knowledge, guía del PMI), en dos registros:

  - **técnico**: la definición formal de cada área de conocimiento y de cada
    grupo de procesos, como la usaría un PMP.
  - **criollo**: la misma idea explicada en castellano de todos los días, para
    que se entienda sin jerga.

Además, con el mismo criterio de honestidad del resto del motor (`reviews.py`,
`help_center.py`), cada área declara qué tanto la cubre ESTE producto y qué le
falta — no es una certificación PMI, es una referencia de alineación.

Cualquier área o grupo de procesos admite una NOTA de la empresa (algo que no
se automatiza: un matiz, una decisión interna) que se edita a mano y queda
versionada por empresa (mvpm/db.py, entidad `pmbok`) con quién la validó.
"""

from . import db

ENTIDAD = "pmbok"

_COBERTURA_ORDEN = {"completa": 0, "parcial": 1, "no_cubierta": 2}

AREAS = [
    {
        "clave": "integracion", "area": "Gestión de la integración", "area_en": "Integration management",
        "definicion_tecnica": "Procesos para unificar, consolidar y coordinar los distintos "
                              "procesos y actividades del proyecto: acta de constitución, plan "
                              "para la dirección del proyecto y control integrado de cambios.",
        "criollo": "Que todas las partes del proyecto tiren para el mismo lado y nada quede "
                   "suelto — el pegamento que mantiene todo junto.",
        "cobertura": "parcial",
        "como_lo_cubre": "El copiloto y el reporte ejecutivo consolidan el estado de todo el "
                          "portafolio en un solo lugar en tiempo real.",
        "lo_que_falta": "No reemplaza el acta de constitución del proyecto ni un control formal de "
                         "cambios — eso lo define y firma el PM fuera de la herramienta.",
    },
    {
        "clave": "alcance", "area": "Gestión del alcance", "area_en": "Scope management",
        "definicion_tecnica": "Asegurar que el proyecto incluya todo el trabajo requerido — y "
                              "sólo ese — para completarlo con éxito. Incluye recolectar "
                              "requisitos, definir y validar el alcance y controlarlo.",
        "criollo": "Tener clarísimo qué entra y qué no entra en el proyecto, para que no se "
                   "infle con pedidos de último momento.",
        "cobertura": "completa",
        "como_lo_cubre": "Dimensión 'alcance' del índice de salud detecta tareas sin responsable; "
                          "el catálogo registra segmento y criticidad de cada proyecto.",
        "lo_que_falta": None,
    },
    {
        "clave": "cronograma", "area": "Gestión del cronograma", "area_en": "Schedule management",
        "definicion_tecnica": "Procesos para gestionar la finalización del proyecto a tiempo: "
                              "definir y secuenciar actividades, estimar duraciones, desarrollar "
                              "y controlar el cronograma.",
        "criollo": "Poner fechas realistas, saber qué va antes que qué, y darse cuenta a tiempo "
                   "cuando algo se está atrasando.",
        "cobertura": "completa",
        "como_lo_cubre": "Dimensión 'cronograma' del índice de salud, vencimientos por tarea, "
                          "grafo de dependencias y bloqueos, y backlog priorizado por urgencia.",
        "lo_que_falta": None,
    },
    {
        "clave": "costos", "area": "Gestión de los costos", "area_en": "Cost management",
        "definicion_tecnica": "Planificar, estimar, presupuestar, financiar, gestionar y "
                              "controlar los costos para completar el proyecto dentro del "
                              "presupuesto aprobado.",
        "criollo": "Cuánto va a salir, cuánto llevás gastado, y avisar antes de que se te vaya "
                   "la plata de las manos.",
        "cobertura": "completa",
        "como_lo_cubre": "Presupuesto vs. ejecutado por proyecto y por portafolio, dimensión "
                          "'presupuesto' del índice de salud, alerta de proyectos sobre presupuesto.",
        "lo_que_falta": None,
    },
    {
        "clave": "calidad", "area": "Gestión de la calidad", "area_en": "Quality management",
        "definicion_tecnica": "Incorporar la política de calidad de la organización en cuanto a "
                              "planificar, gestionar y controlar los requisitos de calidad del "
                              "proyecto y del producto.",
        "criollo": "Que lo que entregás sirva de verdad y cumpla lo prometido, no que 'ande más "
                   "o menos'.",
        "cobertura": "parcial",
        "como_lo_cubre": "Las políticas de gestión verifican reglas operativas contra evidencia "
                          "real del portafolio (dueños asignados, dependencias sanas, etc).",
        "lo_que_falta": "No hay checklist de aceptación de entregables ni control de calidad "
                         "técnico — sigue siendo del equipo y sus propias herramientas de QA.",
    },
    {
        "clave": "recursos", "area": "Gestión de los recursos", "area_en": "Resource management",
        "definicion_tecnica": "Identificar, adquirir y gestionar los recursos (personas, "
                              "equipos, materiales) necesarios para completar el proyecto.",
        "criollo": "Tener a la gente y las cosas que hacen falta, sin sobrecargar a nadie ni "
                   "dejar a nadie de brazos cruzados.",
        "cobertura": "completa",
        "como_lo_cubre": "Vista de equipo con carga actual vs. capacidad semanal, dimensión "
                          "'equipo' del índice de salud, tareas activas por persona.",
        "lo_que_falta": None,
    },
    {
        "clave": "comunicaciones", "area": "Gestión de las comunicaciones", "area_en": "Communications management",
        "definicion_tecnica": "Asegurar que la información del proyecto se planifique, genere, "
                              "recopile, distribuya, almacene y disponga de forma oportuna y "
                              "adecuada.",
        "criollo": "Que todos se enteren de lo que tienen que saber, cuando lo tienen que saber "
                   "— ni de más ni de menos.",
        "cobertura": "parcial",
        "como_lo_cubre": "Reporte ejecutivo listo para compartir y glosario compartido para que "
                          "todo el equipo hable el mismo idioma sobre los estados.",
        "lo_que_falta": "No hay mensajería, comentarios ni notificaciones dentro del producto "
                         "todavía — para eso, integralo con el chat que ya usa tu equipo.",
    },
    {
        "clave": "riesgos", "area": "Gestión de los riesgos", "area_en": "Risk management",
        "definicion_tecnica": "Planificar, identificar, analizar, responder y monitorear los "
                              "riesgos del proyecto para aumentar la probabilidad de los eventos "
                              "positivos y disminuir la de los negativos.",
        "criollo": "Pensar antes qué puede salir mal, tener un plan por las dudas, y estar atento "
                   "a las señales de humo.",
        "cobertura": "completa",
        "como_lo_cubre": "Dimensión 'riesgo' del índice de salud, detección de tareas bloqueadas "
                          "y de dependencias huérfanas que apuntan a nada.",
        "lo_que_falta": None,
    },
    {
        "clave": "adquisiciones", "area": "Gestión de las adquisiciones", "area_en": "Procurement management",
        "definicion_tecnica": "Comprar o adquirir los productos, servicios o resultados "
                              "necesarios de fuera del equipo del proyecto: planificar, efectuar "
                              "y controlar las adquisiciones.",
        "criollo": "Cuando algo hay que comprarlo o contratarlo afuera, manejar bien a los "
                   "proveedores y los contratos.",
        "cobertura": "no_cubierta",
        "como_lo_cubre": None,
        "lo_que_falta": "No hay gestión de proveedores, contratos ni compras — usá tu "
                         "herramienta de compras en paralelo; el sponsor y el presupuesto sí quedan acá.",
    },
    {
        "clave": "interesados", "area": "Gestión de los interesados", "area_en": "Stakeholder management",
        "definicion_tecnica": "Identificar a las personas, grupos u organizaciones que pueden "
                              "afectar o ser afectados por el proyecto, y desarrollar estrategias "
                              "para involucrarlos eficazmente.",
        "criollo": "Saber quiénes tienen algo que ver con el proyecto (para bien o para mal) y "
                   "cómo llevarse bien con cada uno.",
        "cobertura": "parcial",
        "como_lo_cubre": "Cada proyecto registra su sponsor, y el copiloto puede responder "
                          "preguntas sobre a quién le pertenece cada iniciativa.",
        "lo_que_falta": "No hay una matriz de interesados con poder/interés — si tu portafolio la "
                         "necesita, se arma una vez en una planilla aparte y se referencia acá.",
    },
]

# Los 5 grupos de procesos del PMBOK (el ciclo de vida de la dirección).
GRUPOS_PROCESO = [
    {"clave": "inicio", "nombre": "Inicio", "nombre_en": "Initiating",
     "definicion_tecnica": "Procesos para definir un nuevo proyecto o fase y obtener la "
                           "autorización para iniciarlo (acta de constitución, identificación "
                           "de interesados).",
     "criollo": "El arranque: decidir que el proyecto va, nombrar al responsable y ver quiénes "
                "están involucrados."},
    {"clave": "planificacion", "nombre": "Planificación", "nombre_en": "Planning",
     "definicion_tecnica": "Procesos para establecer el alcance, refinar los objetivos y definir "
                           "el curso de acción para alcanzarlos.",
     "criollo": "Armar el plan: qué se hace, en qué orden, con qué plata, quién, y qué puede "
                "salir mal."},
    {"clave": "ejecucion", "nombre": "Ejecución", "nombre_en": "Executing",
     "definicion_tecnica": "Procesos para completar el trabajo definido en el plan y satisfacer "
                           "los requisitos del proyecto.",
     "criollo": "Poner manos a la obra: hacer el trabajo y coordinar al equipo."},
    {"clave": "monitoreo", "nombre": "Monitoreo y Control", "nombre_en": "Monitoring & Controlling",
     "definicion_tecnica": "Procesos para dar seguimiento, revisar y regular el progreso y el "
                           "desempeño; identificar cambios y ejecutarlos.",
     "criollo": "Ir midiendo cómo va contra el plan y corregir el rumbo cuando hace falta."},
    {"clave": "cierre", "nombre": "Cierre", "nombre_en": "Closing",
     "definicion_tecnica": "Procesos para completar o cerrar formalmente el proyecto, fase o "
                           "contrato.",
     "criollo": "Cerrar prolijo: entregar, cobrar/pagar lo pendiente y anotar las lecciones "
                "aprendidas para la próxima."},
]

_AREAS_POR_CLAVE = {a["clave"]: a for a in AREAS}
_GRUPOS_POR_CLAVE = {g["clave"]: g for g in GRUPOS_PROCESO}


def areas() -> list[dict]:
    return sorted(AREAS, key=lambda a: _COBERTURA_ORDEN[a["cobertura"]])


def grupos_proceso() -> list[dict]:
    return GRUPOS_PROCESO


def resumen() -> dict:
    total = len(AREAS)
    por_estado = {"completa": 0, "parcial": 0, "no_cubierta": 0}
    for a in AREAS:
        por_estado[a["cobertura"]] += 1
    return {"total_areas": total, "grupos_proceso": len(GRUPOS_PROCESO), **por_estado}


def nota_empresa(empresa_id: int, clave: str) -> dict | None:
    """Nota interna de la empresa sobre un área o grupo (algo no automatizable),
    si se guardó alguna; None si no."""
    version = db.obtener_version_actual(empresa_id, ENTIDAD, clave)
    if not version:
        return None
    return {
        "texto": version["contenido"], "estado": version["estado"],
        "validado_por_nombre": version["validado_por_nombre"],
        "validado_por_cargo": version["validado_por_cargo"],
    }


def guardar_nota(empresa_id: int, clave: str, texto: str,
                 validado_por_nombre: str, validado_por_cargo: str) -> int:
    return db.guardar_version(
        empresa_id, ENTIDAD, clave, texto, estado="validado",
        recomendado_por="edición manual",
        validado_por_nombre=validado_por_nombre, validado_por_cargo=validado_por_cargo,
    )
