"""Pestaña de tutorial: contenido explicado paso a paso de cada herramienta
real del producto — no un texto de marketing, una guía operativa. Un
elemento por sección del dashboard (y por herramienta que vive fuera del nav
principal, como el token de licencia), para que no falte nada al recorrerlo.
"""

SECTIONS = [
    {
        "id": "primeros_pasos",
        "titulo": "Primeros pasos",
        "resumen": "Cómo arrancar de cero: cuenta de administrador, primer proyecto, y de dónde "
                   "sale el resto del equipo.",
        "pasos": [
            "La primera persona que abre el dashboard en un servidor nuevo crea la cuenta de "
            "administrador (usuario y contraseña) — no hace falta que nadie te la asigne.",
            "El resto del equipo se registra solo, desde la misma pantalla de login, con "
            "'Crear cuenta' — quedan como miembros, no como admin.",
            "Si el portafolio está vacío, un botón deja cargar datos de ejemplo para explorar "
            "el producto antes de cargar los tuyos — se pueden borrar en cualquier momento.",
            "Para tu primer proyecto real: sección Portafolio → 'Nuevo proyecto'.",
        ],
        "tips": [
            "Los datos quedan en una base real en el servidor donde corre la app "
            "(~/.mv_project_management/datos.db), no se mandan a ningún lado por defecto.",
        ],
    },
    {
        "id": "nav_case_study",
        "titulo": "Caso de uso completo",
        "resumen": "Un proyecto simulado recorrido de punta a punta por todas las herramientas del "
                   "programa, con los números reales del motor — para ver el flujo completo antes "
                   "de cargar tus propios datos.",
        "pasos": [
            "El programa elige el proyecto de ejemplo con peor índice de salud y lo recorre por "
            "Portafolio, Salud, Dependencias, Backlog, Copiloto y Reportes, uno detrás del otro.",
            "Cada paso muestra el resultado real de correr el motor sobre ese proyecto — no es un "
            "guion escrito a mano, se recalcula en cada visita.",
        ],
        "tips": [
            "Es el mejor punto de partida para alguien que nunca usó el producto: muestra en 6 "
            "pasos lo mismo que explica la pestaña Tutorial, pero aplicado a un caso concreto.",
        ],
    },
    {
        "id": "nav_portfolio",
        "titulo": "Portafolio",
        "resumen": "Catálogo único de proyectos, con KPIs del portafolio completo arriba.",
        "pasos": [
            "'Nuevo proyecto' abre un formulario guiado: nombre, portafolio, sponsor, dueño, "
            "segmento, fechas, presupuesto y criticidad.",
            "'Ficha de proyecto' deja elegir un proyecto existente para editar cualquier campo, "
            "archivarlo (sale de las vistas activas pero no se borra) o eliminarlo definitivamente "
            "(borra también sus tareas).",
            "El gráfico por portafolio compara presupuesto vs. ejecutado agrupado.",
        ],
        "tips": [
            "Un proyecto sin dueño asignado baja la dimensión 'alcance' de su índice de salud — "
            "asignalo apenas lo sepas, aunque sea provisorio.",
        ],
    },
    {
        "id": "nav_tasks",
        "titulo": "Tareas",
        "resumen": "Las tareas de todos los proyectos, con dependencias entre ellas.",
        "pasos": [
            "'Nueva tarea' pide el proyecto al que pertenece, título, responsable, estado, "
            "prioridad, vencimiento y — opcional — de qué otra tarea depende.",
            "'Ficha de tarea' permite editar título, responsable, estado y prioridad, o eliminarla.",
            "Marcar una tarea como 'blocked' la hace aparecer en Dependencias como bloqueo activo.",
        ],
        "tips": [
            "Una tarea vencida y no marcada 'done' castiga la dimensión 'cronograma' del proyecto "
            "— cerrala o movele la fecha, no la dejes vencida sin motivo.",
        ],
    },
    {
        "id": "nav_health",
        "titulo": "Salud de proyecto",
        "resumen": "Índice 0-100 por proyecto, calculado en 6 dimensiones medibles — nunca a ojo.",
        "pasos": [
            "Cada proyecto tiene un índice y un estado (saludable / en observación / en riesgo) "
            "que se recalcula solo con cada cambio.",
            "La matriz por dimensión muestra alcance, cronograma, presupuesto, riesgo, "
            "dependencias y equipo — para ver exactamente qué está pesando el índice.",
        ],
        "tips": [
            "Un proyecto 'en riesgo' (índice < 55) necesita que su dueño presente un plan de "
            "acción — así lo define el glosario compartido del equipo.",
        ],
    },
    {
        "id": "nav_dependencies",
        "titulo": "Dependencias",
        "resumen": "Qué tareas están bloqueando a cuántas otras, y qué dependencias apuntan a nada.",
        "pasos": [
            "'Bloqueos activos' lista tareas en estado 'blocked' y cuántas tareas dependen de "
            "ellas — priorizá desbloquear las que más impactan.",
            "'Dependencias inconsistentes' detecta cuando una tarea depende de otra que ya no "
            "existe (por ejemplo, se borró sin actualizar la dependencia) — corregilas desde la "
            "ficha de la tarea.",
        ],
        "tips": [],
    },
    {
        "id": "nav_backlog",
        "titulo": "Backlog priorizado",
        "resumen": "El orden en el que conviene atacar las tareas pendientes, no por quién grita más.",
        "pasos": [
            "El valor esperado combina criticidad del proyecto × prioridad de la tarea × "
            "urgencia por vencimiento × cuántas otras tareas destraba.",
            "Las tareas vencidas suben automáticamente al tope — no hace falta pedirlo.",
        ],
        "tips": [
            "Si un proyecto de baja criticidad debería pesar más, subile la criticidad desde su "
            "ficha en vez de reordenar el backlog a mano.",
        ],
    },
    {
        "id": "nav_copilot",
        "titulo": "Copiloto",
        "resumen": "Preguntas en lenguaje natural sobre el portafolio, con motor de reglas siempre "
                   "activo y una capa de IA opcional.",
        "pasos": [
            "Escribí la pregunta y presioná 'Preguntar' — el motor de reglas responde siempre, "
            "sin necesitar configuración.",
            "Si hay ANTHROPIC_API_KEY configurada y todavía queda cupo de IA en tu plan, la "
            "respuesta se pule con Claude sin inventar cifras nuevas — nunca reemplaza al motor.",
        ],
        "tips": [
            "El cupo de IA depende del plan (ver 'licencia y plan de créditos de IA' más abajo); "
            "el motor de reglas no tiene límite en ningún plan, incluido el demo.",
        ],
    },
    {
        "id": "nav_reports",
        "titulo": "Reportes",
        "resumen": "Reporte ejecutivo de texto listo para copiar, y exportación completa del "
                   "portafolio.",
        "pasos": [
            "El reporte de texto resume el estado real del portafolio — para pegar en un email "
            "o un canal de equipo.",
            "'Descargar JSON' y 'Descargar Excel' exportan exactamente los datos reales que ves "
            "en el dashboard en ese momento (proyectos, tareas, equipo, salud, backlog y políticas).",
        ],
        "tips": [
            "La API REST local (api/main.py) sirve la misma data en vivo para conectar Power BI, "
            "Tableau o Looker — no hace falta exportar a mano cada vez.",
        ],
    },
    {
        "id": "nav_reviews",
        "titulo": "Reseñas",
        "resumen": "Calificación real de clientes — nunca testimonios inventados.",
        "pasos": [
            "Mientras no haya reseñas verificadas, la sección muestra el estado real ('programa "
            "en fase beta'), no marketing.",
            "Cualquiera puede dejar una reseña desde acá — queda pendiente de verificación antes "
            "de publicarse.",
        ],
        "tips": [],
    },
    {
        "id": "nav_glossary",
        "titulo": "Glosario",
        "resumen": "Qué significa cada estado, igual para todo el equipo — sin ambigüedad.",
        "pasos": [
            "Consultalo antes de discutir si algo 'está en riesgo' o 'está bloqueado' — la "
            "definición ya está acordada acá, no hace falta reinventarla en cada reunión.",
        ],
        "tips": [],
    },
    {
        "id": "nav_policies",
        "titulo": "Políticas",
        "resumen": "Reglas operativas de gestión, verificadas contra evidencia real del portafolio.",
        "pasos": [
            "Cada política muestra si se cumple (✅) o no (⚠️) con la evidencia concreta que la "
            "sustenta — no es una opinión, es un chequeo sobre el dato real.",
            "Debajo, la matriz de automatización aclara qué se resuelve solo, qué necesita un "
            "empujón humano, y qué es puramente humano (con guiones sugeridos por rol).",
        ],
        "tips": [],
    },
    {
        "id": "nav_pmbok",
        "titulo": "Metodología PMBOK",
        "resumen": "Cómo se alinea el producto con las 10 áreas de conocimiento del PMBOK (guía "
                   "del PMI) — honesto sobre lo que cubre y lo que no.",
        "pasos": [
            "Cada área muestra su nivel de cobertura real (completa / parcial / no cubierta) y "
            "qué parte del producto la resuelve.",
            "Donde falta cobertura, se dice explícitamente qué sigue siendo trabajo humano o de "
            "otra herramienta — no se infla la cobertura para vender más.",
        ],
        "tips": [
            "No es una certificación oficial del PMI, es una referencia para equipos que ya "
            "trabajan con esa guía y quieren saber en qué se apoya la herramienta.",
        ],
    },
    {
        "id": "nav_import",
        "titulo": "Importar datos",
        "resumen": "Subir proyectos o tareas existentes desde un CSV/Excel — se cargan de verdad "
                   "a la base, no es solo una vista previa.",
        "pasos": [
            "Elegí si estás importando proyectos o tareas, subí el archivo, y revisá la vista "
            "previa y las columnas con datos faltantes antes de confirmar.",
            "El importador reconoce nombres de columna comunes (nombre/proyecto/titulo, "
            "presupuesto/budget, estado/status, etc.) sin exigir un formato exacto.",
            "Las tareas importadas quedan asociadas al primer proyecto del portafolio — "
            "reasignalas desde la ficha de tarea si corresponde a otro.",
        ],
        "tips": [],
    },
    {
        "id": "nav_users",
        "titulo": "Usuarios",
        "resumen": "Quién tiene cuenta en este servidor — visible solo para administradores.",
        "pasos": [
            "Para sumar a alguien del equipo, pedile que se registre desde la pantalla de login "
            "con 'Crear cuenta' — no hace falta que un admin la cree a mano.",
        ],
        "tips": [],
    },
    {
        "id": "licencia_ia",
        "titulo": "Licencia y plan de créditos de IA",
        "resumen": "Cómo activar el cupo de IA del copiloto después de comprar un plan.",
        "pasos": [
            "Al pagar el plan Professional o Enterprise por MercadoPago, se emite un token de "
            "licencia automáticamente.",
            "Pegalo en el campo 'Token de licencia' de la barra lateral — sin token, el producto "
            "sigue funcionando completo en plan demo, solo cambia el cupo mensual de IA.",
        ],
        "tips": [
            "El motor de reglas (catálogo, salud, dependencias, backlog, políticas) nunca "
            "depende del token — funciona igual en cualquier plan.",
        ],
    },
]


def sections() -> list[dict]:
    return SECTIONS
