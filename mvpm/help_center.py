"""Centro de adopción: qué se automatiza solo, qué necesita un empujón, y qué
es puramente humano — más los guiones (speeches) que cierran esa parte humana
que ningún software resuelve solo. Mismo patrón que `help_center.py` de
Data Governance MV, adaptado a gestión de proyectos.
"""

AUTOMATION = [
    {"area": "Rollup de estado tarea → proyecto → portafolio", "nivel": "auto",
     "detalle": "Se recalcula solo en cada cambio de estado de una tarea."},
    {"area": "Reporte ejecutivo semanal", "nivel": "auto",
     "detalle": "Se genera solo a partir del dato real del portafolio."},
    {"area": "Detección de riesgo y tareas bloqueadas", "nivel": "parcial",
     "detalle": "El sistema las detecta; alguien confirma la causa raíz.", "speech_id": "dueno"},
    {"area": "Creación de tareas desde reunión o email", "nivel": "parcial",
     "detalle": "El copiloto sugiere; un clic humano las crea de verdad.", "speech_id": "equipo"},
    {"area": "Asignación de dueño de proyecto", "nivel": "humano",
     "detalle": "Decisión organizacional, no técnica.", "speech_id": "direccion"},
    {"area": "Definir qué significa 'en riesgo' para el equipo", "nivel": "humano",
     "detalle": "Acuerdo breve de criterios, una vez, en el glosario.", "speech_id": "comite"},
    {"area": "Adopción y patrocinio del cambio", "nivel": "humano",
     "detalle": "Ningún software reemplaza al sponsor.", "speech_id": "direccion"},
]

SPEECHES = {
    "direccion": {
        "titulo": "Guion para dirección / sponsor",
        "audiencia": "Gerencia general, directorio",
        "texto": (
            "Necesito 30 minutos al mes de comité de portafolio y un sponsor visible. "
            "A cambio, en 90 días vas a tener una sola versión de la verdad del estado "
            "de todos los proyectos, sin pedirle un informe manual a nadie."
        ),
    },
    "dueno": {
        "titulo": "Guion para dueños de proyecto",
        "audiencia": "Líderes de proyecto, PMs",
        "texto": (
            "Ser dueño del proyecto en la herramienta no es carga extra, es control: "
            "10 minutos por semana confirmando el estado real evitan que alguien más "
            "decida por vos con datos viejos."
        ),
    },
    "equipo": {
        "titulo": "Guion para el equipo",
        "audiencia": "Equipo operativo",
        "texto": (
            "El standup de 5 minutos alimenta el sistema solo. No estás 'cargando datos "
            "para un jefe', estás evitando que alguien te pregunte lo mismo tres veces."
        ),
    },
    "comite": {
        "titulo": "Guion para el comité de definiciones",
        "audiencia": "Comité de portafolio",
        "texto": (
            "Diez minutos de discusión por término del glosario alcanzan: el dueño del "
            "área decide, se publica, y listo — nadie vuelve a discutir qué es 'en riesgo'."
        ),
    },
}


def automation_rows():
    return AUTOMATION


def speeches():
    return SPEECHES
