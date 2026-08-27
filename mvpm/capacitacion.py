# © 2026 Martín Viera. Todos los derechos reservados.
"""Capacitación por rol: currícula, guion de grabación y verificación.

En cada implementación se repetía la misma capacitación en vivo, y encima
completa para todo el mundo: al sponsor, que sólo necesita leer un tablero, se
le explicaba cómo cargar dependencias entre tareas. Resultado: sesiones largas
que aburren a la mitad de la sala y de las que nadie se lleva lo suyo.

Este módulo parte la capacitación por rol y deja cada pieza lista para grabar
una vez y reusar. Cada módulo trae:

* **Guion**, para grabar sin improvisar y que la segunda grabación salga igual
  que la primera.
* **Práctica**, porque nadie aprende a usar una herramienta mirando un video.
* **Verificación**, las preguntas que confirman que la persona puede trabajar
  sola. Sin esto la capacitación no tiene forma de fallar, y una capacitación
  que no puede fallar no sirve para saber si alguien aprendió.

La currícula del sponsor dura quince minutos a propósito. Un sponsor no va a
mirar una hora de video, y si se le exige, no mira nada.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

ENTIDAD = "capacitacion"


@dataclass(frozen=True)
class Modulo:
    clave: str
    titulo: str
    minutos: int
    objetivo: str
    seccion_app: str                      # dónde se hace, en el nav del producto
    guion: tuple[str, ...]                # qué decir al grabar
    practica: str                         # qué hace la persona después de mirar
    verificacion: tuple[str, ...]         # preguntas que confirman que puede sola


@dataclass(frozen=True)
class Curricula:
    clave: str
    rol: str
    para_quien: str
    promesa: str                          # qué va a poder hacer al terminar
    modulos: tuple[Modulo, ...]
    requiere: tuple[str, ...] = ()        # claves de otras currículas previas

    @property
    def minutos(self) -> int:
        return sum(m.minutos for m in self.modulos)


# ------------------------------------------------------------------- sponsor

SPONSOR = Curricula(
    clave="sponsor",
    rol="Sponsor / Dirección",
    para_quien="Quien pone la plata y decide prioridades, pero no carga datos.",
    promesa="Entrar una vez por semana, ver qué está en riesgo y por qué, y "
            "pedir lo que corresponde a quien corresponde.",
    modulos=(
        Modulo(
            "sponsor_salud", "Leer el tablero de salud", 5,
            "Entender el índice de salud y no confundirlo con opinión.",
            "Salud de proyecto",
            ("Mostrar el listado de proyectos ordenado por índice de salud.",
             "Explicar que el índice sale de seis dimensiones medibles, no del "
             "humor de nadie: alcance, cronograma, presupuesto, riesgo, "
             "dependencias y equipo.",
             "Abrir un proyecto en rojo y mostrar la matriz por dimensión: ahí "
             "se ve cuál de las seis lo está hundiendo.",
             "Recalcar que un proyecto en riesgo no es una acusación, es un "
             "pedido de decisión."),
            "Entrar, encontrar el proyecto con peor índice y decir en una frase "
            "qué dimensión lo está hundiendo.",
            ("¿De dónde sale el índice de salud?",
             "Si un proyecto está en rojo por 'cronograma', ¿qué preguntarías y a quién?"),
        ),
        Modulo(
            "sponsor_reporte", "El reporte ejecutivo", 5,
            "Sacar el resumen del portafolio sin pedírselo a nadie.",
            "Reportes",
            ("Generar el reporte ejecutivo en vivo.",
             "Mostrar que se exporta a Excel y a PDF.",
             "Señalar que los números se recalculan solos: no hay nadie armando "
             "esto a mano el día antes del directorio."),
            "Generar el reporte del mes y exportarlo.",
            ("¿Cada cuánto se actualizan los números del reporte?",),
        ),
        Modulo(
            "sponsor_decidir", "Qué decisiones te tocan", 5,
            "Saber qué pide el sistema del sponsor y qué no.",
            "Portafolio",
            ("Mostrar dónde se ve el sponsor de cada proyecto.",
             "Explicar que un proyecto sin dueño asignado baja su índice de "
             "salud, y que asignarlo es decisión del sponsor.",
             "Mostrar la criticidad y explicar que es la palanca del sponsor: "
             "subirla o bajarla reordena el backlog de todo el equipo.",
             "Aclarar qué NO le toca: cargar tareas, mover fechas, cerrar ítems."),
            "Cambiar la criticidad de un proyecto de prueba y ver cómo se "
            "reordena el backlog priorizado.",
            ("¿Qué le pasa al backlog si subís la criticidad de un proyecto?",
             "¿Quién asigna el dueño de un proyecto?"),
        ),
    ),
)

# ------------------------------------------------------------------------ PM

PM = Curricula(
    clave="pm",
    rol="Dueño de proyecto / Project Manager",
    para_quien="Quien lleva el proyecto adelante todos los días.",
    promesa="Llevar un proyecto completo en la herramienta: ficha, tareas, "
            "dependencias, riesgos y reporte, sin ayuda.",
    modulos=(
        Modulo(
            "pm_ficha", "Crear y mantener la ficha del proyecto", 8,
            "Dar de alta un proyecto con todo lo que el motor necesita.",
            "Portafolio",
            ("Crear un proyecto desde cero con el formulario guiado.",
             "Explicar campo por campo por qué está: portafolio agrupa, sponsor "
             "es a quién se le pide, criticidad pesa en el backlog, presupuesto "
             "y ejecutado alimentan la dimensión de costos.",
             "Mostrar la diferencia entre archivar y eliminar: archivar lo saca "
             "de las vistas activas y conserva la historia; eliminar borra "
             "también sus tareas y no vuelve.",
             "Insistir en asignar dueño: sin dueño, el índice de salud baja."),
            "Crear un proyecto propio con todos los campos completos.",
            ("¿Qué diferencia hay entre archivar y eliminar un proyecto?",
             "¿Por qué conviene cargar el presupuesto aunque sea aproximado?"),
        ),
        Modulo(
            "pm_tareas", "Tareas, estados y vencimientos", 10,
            "Cargar el trabajo real y mantener los estados al día.",
            "Tareas",
            ("Crear tareas asociadas al proyecto.",
             "Recorrer los cuatro estados y cuándo usar cada uno; detenerse en "
             "'blocked', que es el que dispara la vista de dependencias.",
             "Mostrar qué pasa con una tarea vencida y sin cerrar: castiga la "
             "dimensión cronograma del proyecto.",
             "Explicar que la prioridad de la tarea se combina con la criticidad "
             "del proyecto para armar el backlog."),
            "Cargar cinco tareas reales, poner una en 'blocked' y una con fecha "
            "vencida, y mirar cómo cambia el índice de salud.",
            ("¿Qué le pasa al índice si dejás una tarea vencida sin cerrar?",
             "¿Cuándo corresponde marcar 'blocked' y no simplemente 'todo'?"),
        ),
        Modulo(
            "pm_dependencias", "Dependencias y bloqueos", 8,
            "Ver qué está frenando a qué y priorizar el desbloqueo.",
            "Dependencias",
            ("Crear una dependencia entre dos tareas.",
             "Mostrar los bloqueos activos y cuántas tareas cuelgan de cada uno: "
             "ése es el orden en que conviene desbloquear.",
             "Mostrar las dependencias inconsistentes — cuando se borró la tarea "
             "de la que otra dependía — y cómo corregirlas."),
            "Armar una cadena de tres tareas dependientes, bloquear la primera "
            "y ver el impacto.",
            ("Si tenés dos bloqueos, ¿cuál atacás primero y por qué?",),
        ),
        Modulo(
            "pm_backlog", "Backlog priorizado", 7,
            "Entender por qué el orden es el que es, y no discutirlo a mano.",
            "Backlog priorizado",
            ("Mostrar el backlog y explicar el valor esperado: criticidad del "
             "proyecto × prioridad de la tarea × urgencia × cuántas destraba.",
             "Mostrar que las vencidas suben solas al tope.",
             "Recalcar: si algo debería pesar más, se cambia la criticidad del "
             "proyecto o la prioridad de la tarea. El backlog no se reordena a mano."),
            "Encontrar la tarea número uno del backlog y explicar por qué está ahí.",
            ("¿Cómo hacés para que una tarea suba en el backlog?",),
        ),
        Modulo(
            "pm_salud", "Salud de tu proyecto", 7,
            "Leer las seis dimensiones y saber cuál mover.",
            "Salud de proyecto",
            ("Abrir la matriz por dimensión del proyecto propio.",
             "Recorrer las seis y qué la sube o la baja en cada caso.",
             "Mostrar que el índice se recalcula solo con cada cambio: no hay "
             "que actualizarlo."),
            "Identificar la dimensión más floja del proyecto propio y hacer un "
            "cambio que la mejore.",
            ("¿Cuáles son las seis dimensiones del índice?",
             "¿Qué acción concreta subiría la dimensión de alcance?"),
        ),
        Modulo(
            "pm_copiloto", "Copiloto y reportes", 6,
            "Preguntar en castellano y sacar el reporte del proyecto.",
            "Copiloto",
            ("Hacer tres preguntas al copiloto sobre el portafolio.",
             "Aclarar que el motor de reglas responde siempre, sin configurar "
             "nada, y que la capa de IA es opcional y depende del plan.",
             "Generar el reporte del proyecto y exportarlo."),
            "Preguntarle al copiloto por el estado del proyecto propio y "
            "exportar el reporte.",
            ("¿El copiloto necesita conexión a internet para responder?",),
        ),
    ),
)

# --------------------------------------------------------------------- miembro

MIEMBRO = Curricula(
    clave="miembro",
    rol="Miembro del equipo",
    para_quien="Quien ejecuta tareas y no gestiona el proyecto.",
    promesa="Saber qué tiene que hacer hoy, en qué orden, y avisar cuando algo "
            "lo frena.",
    modulos=(
        Modulo(
            "miembro_mis_tareas", "Tus tareas", 7,
            "Encontrar lo asignado y mantenerlo al día.",
            "Tareas",
            ("Filtrar las tareas por responsable.",
             "Recorrer los estados y cuándo cambiar cada uno.",
             "Insistir en el hábito clave: cambiar el estado el mismo día, no el "
             "viernes. Todo lo demás del sistema depende de que el estado esté al día."),
            "Encontrar las tareas propias y actualizar el estado de una.",
            ("¿Cuándo tenés que cambiar el estado de una tarea?",),
        ),
        Modulo(
            "miembro_bloqueos", "Cuando algo te frena", 5,
            "Marcar un bloqueo en vez de esperar callado.",
            "Tareas",
            ("Marcar una tarea como 'blocked'.",
             "Mostrar que aparece de inmediato en la vista de dependencias del PM.",
             "Explicar por qué importa: un bloqueo marcado se ve y se gestiona; "
             "uno que se guarda en la cabeza de alguien, no."),
            "Marcar una tarea como bloqueada y avisar en la reunión siguiente.",
            ("¿Qué pasa cuando marcás una tarea como bloqueada?",),
        ),
        Modulo(
            "miembro_prioridad", "En qué orden trabajar", 5,
            "Usar el backlog en vez de decidir por intuición.",
            "Backlog priorizado",
            ("Mostrar el backlog filtrado por responsable.",
             "Explicar que el orden ya combina urgencia, criticidad y cuánto "
             "destraba: no hace falta discutirlo.",
             "Aclarar qué hacer si el orden parece equivocado: hablarlo con el "
             "PM, que ajusta prioridad o criticidad."),
            "Mirar el backlog propio y arrancar por la primera.",
            ("Si creés que el orden del backlog está mal, ¿qué hacés?",),
        ),
        Modulo(
            "miembro_glosario", "Hablar el mismo idioma", 3,
            "Saber dónde está la definición acordada de cada término.",
            "Glosario",
            ("Mostrar el glosario y un par de definiciones.",
             "Explicar que las definiciones las validó alguien de la empresa y "
             "que están versionadas: si dice eso, es lo acordado."),
            "Buscar en el glosario qué considera la empresa un proyecto 'en riesgo'.",
            ("¿Dónde mirás si no sabés qué quiere decir un término acá adentro?",),
        ),
    ),
)

# ------------------------------------------------------------------------ PMO

PMO = Curricula(
    clave="pmo",
    rol="PMO / Responsable de metodología",
    para_quien="Quien define cómo se gobiernan los proyectos en la empresa.",
    promesa="Dejar la gobernanza cargada, versionada y con responsables "
            "validados, y sostenerla en el tiempo.",
    requiere=("pm",),
    modulos=(
        Modulo(
            "pmo_plantilla", "Adoptar la plantilla del rubro", 10,
            "Arrancar de una gobernanza del rubro en vez de una hoja en blanco.",
            "Plantillas por rubro",
            ("Recorrer los rubros disponibles y abrir el del cliente.",
             "Mostrar etapas, puertas de salida, quién aprueba cada una.",
             "Insistir en que es un punto de partida discutible: se adopta y se "
             "edita con la gente de la casa.",
             "Mostrar que al adoptarla queda registrado quién la validó y cuándo.",
             "Advertir que las referencias normativas son orientativas y hay que "
             "confirmarlas con calidad o legales."),
            "Adoptar la plantilla del rubro y ajustar al menos dos etapas a cómo "
            "se trabaja realmente en la empresa.",
            ("¿Qué pasa si más adelante cambian de plantilla?",
             "¿Quién tiene que revisar las referencias normativas?"),
        ),
        Modulo(
            "pmo_gobernanza", "Definiciones y versionado", 10,
            "Fijar qué significa cada término y dejar rastro de quién lo aprobó.",
            "Gobernanza de datos",
            ("Abrir un concepto y mostrar la definición sugerida.",
             "Editarla y guardarla con nombre y cargo de quien la valida.",
             "Mostrar el historial: nada se pisa, todo queda.",
             "Explicar por qué importa: cuando alguien discute un número, la "
             "discusión se resuelve mirando la definición vigente y quién la firmó."),
            "Validar tres definiciones con el nombre real de quien las aprueba.",
            ("¿Se puede volver a una definición anterior?",
             "¿Qué diferencia hay entre una definición en borrador y una validada?"),
        ),
        Modulo(
            "pmo_organigrama", "Organigrama y responsables", 10,
            "Cargar la estructura y validar quién responde por cada etapa.",
            "Organigrama y responsables",
            ("Subir el organigrama desde Excel o CSV.",
             "Mostrar la sugerencia de responsable por etapa y cómo validarla.",
             "Recalcar que la sugerencia es una propuesta: la valida una persona "
             "y queda registrado quién fue."),
            "Cargar el organigrama real y validar los responsables de al menos "
            "tres etapas.",
            ("¿Quién queda registrado como responsable de validar?",),
        ),
        Modulo(
            "pmo_pmbok", "PMBOK aplicado a la empresa", 10,
            "Saber qué cubre la herramienta y qué sigue siendo trabajo del PM.",
            "Metodología PMBOK",
            ("Recorrer las diez áreas y su cobertura: completa, parcial o no cubierta.",
             "Detenerse en las 'no cubiertas' y ser explícito: eso lo hace el PM "
             "fuera de la herramienta.",
             "Mostrar las áreas críticas del rubro adoptado y por qué son ésas.",
             "Dejar notas propias por área."),
            "Escribir una nota en las tres áreas críticas del rubro explicando "
            "cómo se cubren en esta empresa.",
            ("¿Qué área NO cubre la herramienta, y quién la cubre entonces?",),
        ),
        Modulo(
            "pmo_politicas", "Políticas y umbrales", 8,
            "Fijar los umbrales que disparan alertas.",
            "Políticas",
            ("Mostrar las políticas vigentes y sus umbrales.",
             "Explicar cómo un umbral mal puesto genera alertas que nadie mira, "
             "y que eso es peor que no tener alertas.",
             "Ajustar un umbral y ver el efecto."),
            "Ajustar los umbrales a la realidad de la empresa y justificar cada cambio.",
            ("¿Qué pasa si ponés un umbral demasiado sensible?",),
        ),
    ),
)

# ------------------------------------------------------------------- admin

ADMIN = Curricula(
    clave="admin",
    rol="Administrador del sistema",
    para_quien="Quien instala, mantiene y responde cuando algo no anda.",
    promesa="Instalar, dar de alta al equipo, cargar los datos iniciales, hacer "
            "respaldo y resolver los problemas comunes sin llamar a nadie.",
    modulos=(
        Modulo(
            "admin_instalacion", "Instalación y primer arranque", 10,
            "Dejar el sistema corriendo y crear la cuenta de administrador.",
            "Primeros pasos",
            ("Instalar y arrancar.",
             "Crear la cuenta de administrador: la primera persona que entra "
             "queda como admin.",
             "Mostrar dónde vive la base de datos, que es lo que hay que respaldar.",
             "Explicar el token de licencia y la prueba de siete días."),
            "Instalar en una máquina limpia y crear la cuenta de administrador.",
            ("¿Dónde está el archivo que hay que respaldar?",
             "¿Qué pasa cuando vence la prueba? ¿Se pierden los datos?"),
        ),
        Modulo(
            "admin_usuarios", "Usuarios y roles", 7,
            "Sumar al equipo con el rol que corresponde.",
            "Usuarios",
            ("Mostrar cómo se registra el resto del equipo desde la pantalla de login.",
             "Explicar la diferencia entre admin y miembro.",
             "Aclarar que nadie puede auto-asignarse admin."),
            "Dar de alta a dos personas y verificar que entran.",
            ("¿Puede un miembro convertirse en admin por su cuenta?",),
        ),
        Modulo(
            "admin_importacion", "Cargar los datos del cliente", 12,
            "Importar proyectos y tareas desde el archivo que tenga el cliente.",
            "Importar datos",
            ("Subir un archivo desprolijo a propósito, sin prepararlo.",
             "Mostrar la detección automática de columnas y el semáforo de "
             "confianza: verde es coincidencia clara, amarillo es una suposición "
             "que conviene mirar.",
             "Recorrer el informe previo: cuántas entran, cuántas se descartan y "
             "por qué. Recalcar que hasta acá no se escribió nada.",
             "Detenerse en los avisos de columna — el punto de miles, las fechas "
             "ambiguas, los niveles numéricos — y explicar por qué el sistema "
             "avisa en vez de adivinar.",
             "Importar y mostrar que reimportar el mismo archivo no duplica."),
            "Importar el archivo real del cliente y explicar cada fila descartada.",
            ("¿En qué momento el importador escribe en la base?",
             "Si una columna sale en amarillo, ¿qué hacés?"),
        ),
        Modulo(
            "admin_conectores", "Conectar el ERP", 10,
            "Traer datos directo del ERP cuando el cliente lo permite.",
            "Conectores ERP",
            ("Elegir el perfil del ERP del cliente.",
             "Correr el sondeo ANTES de intentar la extracción y leer el "
             "resultado: qué tablas y columnas encontró y cuáles no.",
             "Explicar que los perfiles son de fábrica y que un ERP con años "
             "encima está personalizado: por eso el sondeo, y por eso la "
             "consulta se puede editar.",
             "Mostrar que todo es de solo lectura y que el sistema rechaza "
             "cualquier consulta que no sea un SELECT.",
             "Mostrar que lo extraído entra por el mismo informe previo del "
             "importador."),
            "Sondear un ERP de prueba y explicar qué haría si faltara una columna.",
            ("¿Por qué se sondea antes de extraer?",
             "¿Puede este conector modificar algo en el ERP del cliente?"),
        ),
        Modulo(
            "admin_respaldo", "Respaldo y problemas comunes", 6,
            "Respaldar, restaurar y resolver lo que suele romperse.",
            "Primeros pasos",
            ("Copiar el archivo de base de datos y restaurarlo en otra máquina.",
             "Recorrer los problemas frecuentes: contraseña olvidada, licencia "
             "vencida, puerto ocupado.",
             "Mostrar dónde se ven los mensajes de error."),
            "Hacer un respaldo, borrar la base y restaurarla.",
            ("¿Cada cuánto conviene respaldar y qué archivo exactamente?",),
        ),
    ),
)

# --------------------------------------------------------------- datos / BI

DATOS = Curricula(
    clave="datos",
    rol="Referente de datos / BI",
    para_quien="Quien conecta esto con el resto del mundo de datos de la empresa.",
    promesa="Sacar los datos a Power BI o Excel y mantener la carga desde el ERP.",
    requiere=("admin",),
    modulos=(
        Modulo(
            "datos_powerbi", "Conexión a Power BI", 10,
            "Dejar un tablero de Power BI leyendo del sistema.",
            "Reportes",
            ("Generar el archivo de conexión .pbids y abrirlo en Power BI.",
             "Mostrar las tablas disponibles y sus columnas.",
             "Explicar la frecuencia de actualización y sus límites."),
            "Armar un tablero simple en Power BI contra los datos reales.",
            ("¿Qué archivo abrís en Power BI para conectarte?",),
        ),
        Modulo(
            "datos_exportar", "Exportaciones", 6,
            "Sacar los datos en Excel cuando hace falta.",
            "Reportes",
            ("Exportar el portafolio y las tareas a Excel.",
             "Mostrar la estructura de hojas del archivo exportado."),
            "Exportar el portafolio completo y abrirlo en Excel.",
            ("¿Qué hojas trae el Excel exportado?",),
        ),
        Modulo(
            "datos_erp_mantenimiento", "Mantener la carga desde el ERP", 14,
            "Sostener la integración cuando el ERP cambia.",
            "Conectores ERP",
            ("Repasar el sondeo y qué hacer cuando aparece una columna faltante.",
             "Editar la consulta del perfil con los nombres reales de la "
             "instalación y guardarla.",
             "Detenerse en las conversiones raras: las fechas Julian de JD "
             "Edwards, el YYYYMMDD de SAP, el 1900 de Dynamics, los importes con "
             "decimales implícitos. Explicar que son la fuente más común de "
             "errores silenciosos.",
             "Mostrar cómo contrastar un par de importes y fechas contra el ERP "
             "antes de dar una carga por buena."),
            "Cambiar el nombre de una columna a propósito, ver que el sondeo lo "
            "detecta, y corregir la consulta.",
            ("¿Cómo verificás que los importes que trajiste son correctos?",
             "¿Qué es una fecha Julian y en qué ERP aparece?"),
        ),
    ),
)


CURRICULAS: dict[str, Curricula] = {
    c.clave: c for c in (SPONSOR, PM, MIEMBRO, PMO, ADMIN, DATOS)
}


# ------------------------------------------------------------------ traducción
#
# Las 6 currículas de arriba son la fuente de verdad y quedan intactas: nunca
# se mutan. Para "en"/"pt" se arma una copia con dataclasses.replace() por
# encima de una tabla de traducción; si a un texto le falta la traducción,
# se devuelve el original en español antes que romper. lang="es" no pasa por
# ninguna tabla y devuelve exactamente los objetos de siempre.

# 'seccion_app' hoy es texto libre en español. Acá se traduce con la MISMA
# redacción que usa el nav real del producto (mvpm/i18n.py, claves nav_*),
# para que la capacitación diga lo mismo que la persona ve en pantalla. No se
# importa i18n.py (el motor de capacitación queda desacoplado): es una copia
# a mano de esos textos.
_SECCION_APP_TRAD: dict[str, dict[str, str]] = {
    "Salud de proyecto": {"en": "Project health", "pt": "Saúde do projeto"},
    "Reportes": {"en": "Reports", "pt": "Relatórios"},
    "Portafolio": {"en": "Portfolio", "pt": "Portfólio"},
    "Tareas": {"en": "Tasks", "pt": "Tarefas"},
    "Dependencias": {"en": "Dependencies", "pt": "Dependências"},
    "Backlog priorizado": {"en": "Prioritized backlog", "pt": "Backlog priorizado"},
    "Copiloto": {"en": "Copilot", "pt": "Copiloto"},
    "Glosario": {"en": "Glossary", "pt": "Glossário"},
    "Plantillas por rubro": {"en": "Industry templates", "pt": "Modelos por setor"},
    "Gobernanza de datos": {"en": "Data governance", "pt": "Governança de dados"},
    "Organigrama y responsables": {
        "en": "Org chart & owners", "pt": "Organograma e responsáveis"},
    "Metodología PMBOK": {"en": "PMBOK methodology", "pt": "Metodologia PMBOK"},
    "Políticas": {"en": "Policies", "pt": "Políticas"},
    # No tiene clave nav_* propia en i18n.py (es la pantalla de instalación).
    "Primeros pasos": {"en": "Getting started", "pt": "Primeiros passos"},
    "Usuarios": {"en": "Users", "pt": "Usuários"},
    "Importar datos": {"en": "Import data", "pt": "Importar dados"},
    "Conectores ERP": {"en": "ERP connectors", "pt": "Conectores ERP"},
}

# Textos de nivel currícula (rol, para_quien, promesa).
_CURRICULA_TRAD: dict[str, dict[str, dict[str, str]]] = {
    "sponsor": {
        "en": {
            "rol": "Sponsor / Leadership",
            "para_quien": "Whoever funds the work and sets priorities, but "
                           "doesn't enter data.",
            "promesa": "Log in once a week, see what's at risk and why, and "
                       "ask the right person for the right thing.",
        },
        "pt": {
            "rol": "Sponsor / Diretoria",
            "para_quien": "Quem banca o projeto e decide prioridades, mas não "
                           "carrega dados.",
            "promesa": "Entrar uma vez por semana, ver o que está em risco e "
                       "por quê, e pedir o que cabe a cada um.",
        },
    },
    "pm": {
        "en": {
            "rol": "Project owner / Project Manager",
            "para_quien": "Whoever drives the project forward day to day.",
            "promesa": "Run a complete project in the tool — profile, tasks, "
                       "dependencies, risks and reporting — without help.",
        },
        "pt": {
            "rol": "Dono do projeto / Project Manager",
            "para_quien": "Quem toca o projeto no dia a dia.",
            "promesa": "Conduzir um projeto completo na ferramenta: ficha, "
                       "tarefas, dependências, riscos e relatório, sem ajuda.",
        },
    },
    "miembro": {
        "en": {
            "rol": "Team member",
            "para_quien": "Whoever executes tasks and doesn't manage the project.",
            "promesa": "Know what to do today, in what order, and flag it "
                       "when something's blocking you.",
        },
        "pt": {
            "rol": "Membro da equipe",
            "para_quien": "Quem executa tarefas e não gerencia o projeto.",
            "promesa": "Saber o que fazer hoje, em que ordem, e avisar quando "
                       "algo travar o trabalho.",
        },
    },
    "pmo": {
        "en": {
            "rol": "PMO / Methodology lead",
            "para_quien": "Whoever defines how projects are governed across "
                           "the company.",
            "promesa": "Get governance loaded, versioned, and with validated "
                       "owners — and keep it that way over time.",
        },
        "pt": {
            "rol": "PMO / Responsável pela metodologia",
            "para_quien": "Quem define como os projetos são governados na empresa.",
            "promesa": "Deixar a governança carregada, versionada e com "
                       "responsáveis validados, e sustentá-la ao longo do tempo.",
        },
    },
    "admin": {
        "en": {
            "rol": "System administrator",
            "para_quien": "Whoever installs, maintains, and responds when "
                           "something breaks.",
            "promesa": "Install the system, onboard the team, load the initial "
                       "data, back it up, and fix common problems without "
                       "calling anyone.",
        },
        "pt": {
            "rol": "Administrador do sistema",
            "para_quien": "Quem instala, mantém e responde quando algo para "
                           "de funcionar.",
            "promesa": "Instalar, cadastrar a equipe, carregar os dados "
                       "iniciais, fazer backup e resolver os problemas comuns "
                       "sem precisar chamar ninguém.",
        },
    },
    "datos": {
        "en": {
            "rol": "Data / BI lead",
            "para_quien": "Whoever connects this to the rest of the company's "
                           "data world.",
            "promesa": "Get the data out to Power BI or Excel and keep the "
                       "ERP feed running.",
        },
        "pt": {
            "rol": "Referência de dados / BI",
            "para_quien": "Quem conecta isto ao restante do mundo de dados da "
                           "empresa.",
            "promesa": "Levar os dados para o Power BI ou Excel e manter a "
                       "carga a partir do ERP.",
        },
    },
}

# Textos de nivel módulo (titulo, objetivo, guion, practica, verificacion),
# por clave de módulo — la clave nunca se traduce, es la que usan estas tablas.
_MODULO_TRAD: dict[str, dict[str, dict]] = {
    # --------------------------------------------------------------- sponsor
    "sponsor_salud": {
        "en": {
            "titulo": "Reading the health dashboard",
            "objetivo": "Understand the health index and not mistake it for opinion.",
            "guion": (
                "Show the project list sorted by health index.",
                "Explain that the index comes from six measurable dimensions, "
                "not anyone's gut feeling: scope, schedule, budget, risk, "
                "dependencies, and team.",
                "Open a project that's in the red and show the "
                "dimension-by-dimension matrix — that's where you see which "
                "of the six is dragging it down.",
                "Stress that a project at risk isn't an accusation — it's a "
                "call for a decision.",
            ),
            "practica": "Log in, find the project with the worst index, and "
                        "say in one sentence which dimension is dragging it down.",
            "verificacion": (
                "Where does the health index come from?",
                "If a project is red on 'schedule', what would you ask, and "
                "who would you ask?",
            ),
        },
        "pt": {
            "titulo": "Lendo o painel de saúde",
            "objetivo": "Entender o índice de saúde e não confundi-lo com opinião.",
            "guion": (
                "Mostrar a lista de projetos ordenada pelo índice de saúde.",
                "Explicar que o índice vem de seis dimensões mensuráveis, não "
                "do humor de ninguém: escopo, cronograma, orçamento, risco, "
                "dependências e equipe.",
                "Abrir um projeto no vermelho e mostrar a matriz por "
                "dimensão: ali se vê qual das seis está afundando o projeto.",
                "Reforçar que um projeto em risco não é uma acusação, é um "
                "pedido de decisão.",
            ),
            "practica": "Entrar, encontrar o projeto com pior índice e dizer "
                        "em uma frase qual dimensão está afundando o projeto.",
            "verificacion": (
                "De onde vem o índice de saúde?",
                "Se um projeto está no vermelho por 'cronograma', o que você "
                "perguntaria e para quem?",
            ),
        },
    },
    "sponsor_reporte": {
        "en": {
            "titulo": "The executive report",
            "objetivo": "Pull the portfolio summary without asking anyone for it.",
            "guion": (
                "Generate the executive report live.",
                "Show that it exports to Excel and PDF.",
                "Point out that the numbers recalculate on their own — "
                "nobody is putting this together by hand the night before "
                "the board meeting.",
            ),
            "practica": "Generate this month's report and export it.",
            "verificacion": ("How often do the report's numbers update?",),
        },
        "pt": {
            "titulo": "O relatório executivo",
            "objetivo": "Tirar o resumo do portfólio sem precisar pedir a ninguém.",
            "guion": (
                "Gerar o relatório executivo ao vivo.",
                "Mostrar que ele é exportado para Excel e PDF.",
                "Destacar que os números se recalculam sozinhos: não há "
                "ninguém montando isso na mão na véspera da reunião de "
                "diretoria.",
            ),
            "practica": "Gerar o relatório do mês e exportá-lo.",
            "verificacion": ("De quanto em quanto tempo os números do "
                              "relatório são atualizados?",),
        },
    },
    "sponsor_decidir": {
        "en": {
            "titulo": "Which decisions are yours",
            "objetivo": "Know what the system asks of the sponsor, and what "
                        "it doesn't.",
            "guion": (
                "Show where each project's sponsor is displayed.",
                "Explain that a project with no assigned owner drags its "
                "health index down, and that assigning one is the sponsor's call.",
                "Show criticality and explain it's the sponsor's lever — "
                "raising or lowering it reorders the whole team's backlog.",
                "Clarify what's NOT theirs to do: entering tasks, moving "
                "dates, closing items.",
            ),
            "practica": "Change the criticality of a test project and watch "
                        "the prioritized backlog reorder.",
            "verificacion": (
                "What happens to the backlog if you raise a project's criticality?",
                "Who assigns a project's owner?",
            ),
        },
        "pt": {
            "titulo": "Quais decisões são suas",
            "objetivo": "Saber o que o sistema pede do sponsor e o que não pede.",
            "guion": (
                "Mostrar onde se vê o sponsor de cada projeto.",
                "Explicar que um projeto sem dono atribuído derruba seu "
                "índice de saúde, e que atribuí-lo é decisão do sponsor.",
                "Mostrar a criticidade e explicar que é a alavanca do "
                "sponsor: subi-la ou baixá-la reordena o backlog de toda a equipe.",
                "Deixar claro o que NÃO cabe a ele: cadastrar tarefas, mudar "
                "datas, fechar itens.",
            ),
            "practica": "Mudar a criticidade de um projeto de teste e ver "
                        "como o backlog priorizado se reordena.",
            "verificacion": (
                "O que acontece com o backlog se você aumentar a criticidade "
                "de um projeto?",
                "Quem atribui o dono de um projeto?",
            ),
        },
    },
    # -------------------------------------------------------------------- pm
    "pm_ficha": {
        "en": {
            "titulo": "Creating and maintaining the project profile",
            "objetivo": "Set up a project with everything the engine needs.",
            "guion": (
                "Create a project from scratch with the guided form.",
                "Walk through each field and why it's there: portfolio "
                "groups projects, sponsor is who to ask, criticality weighs "
                "into the backlog, and budget plus actuals feed the cost "
                "dimension.",
                "Show the difference between archiving and deleting: "
                "archiving pulls it out of active views and keeps the "
                "history; deleting also erases its tasks and can't be undone.",
                "Push on assigning an owner: without one, the health index drops.",
            ),
            "practica": "Create your own project with every field filled in.",
            "verificacion": (
                "What's the difference between archiving and deleting a project?",
                "Why is it worth entering a budget even if it's just an estimate?",
            ),
        },
        "pt": {
            "titulo": "Criando e mantendo a ficha do projeto",
            "objetivo": "Cadastrar um projeto com tudo o que o motor precisa.",
            "guion": (
                "Criar um projeto do zero com o formulário guiado.",
                "Explicar campo por campo por que ele existe: portfólio "
                "agrupa, sponsor é para quem se pede, criticidade pesa no "
                "backlog, orçamento e executado alimentam a dimensão de custos.",
                "Mostrar a diferença entre arquivar e excluir: arquivar tira "
                "o projeto das visões ativas e preserva o histórico; excluir "
                "também apaga suas tarefas e não tem volta.",
                "Insistir em atribuir um dono: sem dono, o índice de saúde cai.",
            ),
            "practica": "Criar um projeto próprio com todos os campos preenchidos.",
            "verificacion": (
                "Qual é a diferença entre arquivar e excluir um projeto?",
                "Por que vale a pena carregar o orçamento mesmo que seja "
                "aproximado?",
            ),
        },
    },
    "pm_tareas": {
        "en": {
            "titulo": "Tasks, statuses, and due dates",
            "objetivo": "Load the real work and keep statuses up to date.",
            "guion": (
                "Create tasks tied to the project.",
                "Walk through the four statuses and when to use each; "
                "linger on 'blocked', the one that triggers the dependencies view.",
                "Show what happens with an overdue task left open: it hits "
                "the project's schedule dimension.",
                "Explain that a task's priority combines with the project's "
                "criticality to build the backlog.",
            ),
            "practica": "Load five real tasks, set one to 'blocked' and one "
                        "with a past due date, and watch how the health "
                        "index changes.",
            "verificacion": (
                "What happens to the index if you leave an overdue task open?",
                "When should you mark a task 'blocked' instead of just 'to do'?",
            ),
        },
        "pt": {
            "titulo": "Tarefas, status e vencimentos",
            "objetivo": "Carregar o trabalho real e manter os status em dia.",
            "guion": (
                "Criar tarefas associadas ao projeto.",
                "Percorrer os quatro status e quando usar cada um; parar em "
                "'blocked', que é o que aciona a visão de dependências.",
                "Mostrar o que acontece com uma tarefa vencida e não "
                "fechada: ela penaliza a dimensão cronograma do projeto.",
                "Explicar que a prioridade da tarefa se combina com a "
                "criticidade do projeto para montar o backlog.",
            ),
            "practica": "Carregar cinco tarefas reais, colocar uma em "
                        "'blocked' e outra com data vencida, e observar como "
                        "o índice de saúde muda.",
            "verificacion": (
                "O que acontece com o índice se você deixar uma tarefa "
                "vencida sem fechar?",
                "Quando é o caso de marcar 'blocked' e não simplesmente 'a fazer'?",
            ),
        },
    },
    "pm_dependencias": {
        "en": {
            "titulo": "Dependencies and blockers",
            "objetivo": "See what's blocking what, and prioritize unblocking it.",
            "guion": (
                "Create a dependency between two tasks.",
                "Show the active blockers and how many tasks hang off each "
                "one — that's the order in which to unblock them.",
                "Show inconsistent dependencies — when the task another one "
                "depended on was deleted — and how to fix them.",
            ),
            "practica": "Build a chain of three dependent tasks, block the "
                        "first one, and see the impact.",
            "verificacion": (
                "If you have two blockers, which one do you tackle first, and why?",
            ),
        },
        "pt": {
            "titulo": "Dependências e bloqueios",
            "objetivo": "Ver o que está travando o quê e priorizar o desbloqueio.",
            "guion": (
                "Criar uma dependência entre duas tarefas.",
                "Mostrar os bloqueios ativos e quantas tarefas dependem de "
                "cada um: essa é a ordem em que convém desbloquear.",
                "Mostrar as dependências inconsistentes — quando a tarefa da "
                "qual outra dependia foi apagada — e como corrigi-las.",
            ),
            "practica": "Montar uma cadeia de três tarefas dependentes, "
                        "bloquear a primeira e ver o impacto.",
            "verificacion": (
                "Se você tem dois bloqueios, qual ataca primeiro e por quê?",
            ),
        },
    },
    "pm_backlog": {
        "en": {
            "titulo": "Prioritized backlog",
            "objetivo": "Understand why the order is what it is, instead of "
                        "arguing over it by hand.",
            "guion": (
                "Show the backlog and explain expected value: project "
                "criticality × task priority × urgency × how many other "
                "tasks it unblocks.",
                "Show that overdue tasks climb to the top on their own.",
                "Stress this: if something should weigh more, change the "
                "project's criticality or the task's priority. The backlog "
                "is never reordered by hand.",
            ),
            "practica": "Find the number-one task in the backlog and explain "
                        "why it's there.",
            "verificacion": ("How do you get a task to move up in the backlog?",),
        },
        "pt": {
            "titulo": "Backlog priorizado",
            "objetivo": "Entender por que a ordem é a que é, em vez de "
                        "discuti-la manualmente.",
            "guion": (
                "Mostrar o backlog e explicar o valor esperado: criticidade "
                "do projeto × prioridade da tarefa × urgência × quantas "
                "tarefas ela destrava.",
                "Mostrar que as vencidas sobem sozinhas para o topo.",
                "Reforçar: se algo deveria pesar mais, muda-se a criticidade "
                "do projeto ou a prioridade da tarefa. O backlog não se "
                "reordena na mão.",
            ),
            "practica": "Encontrar a tarefa número um do backlog e explicar "
                        "por que ela está ali.",
            "verificacion": ("Como você faz para uma tarefa subir no backlog?",),
        },
    },
    "pm_salud": {
        "en": {
            "titulo": "Your project's health",
            "objetivo": "Read the six dimensions and know which one to move.",
            "guion": (
                "Open the dimension-by-dimension matrix for your own project.",
                "Go through all six and what raises or lowers each one.",
                "Show that the index recalculates on its own with every "
                "change — there's nothing to refresh.",
            ),
            "practica": "Identify the weakest dimension in your own project "
                        "and make a change that improves it.",
            "verificacion": (
                "What are the six dimensions of the index?",
                "What concrete action would raise the scope dimension?",
            ),
        },
        "pt": {
            "titulo": "A saúde do seu projeto",
            "objetivo": "Ler as seis dimensões e saber qual mexer.",
            "guion": (
                "Abrir a matriz por dimensão do próprio projeto.",
                "Percorrer as seis e o que sobe ou desce cada uma.",
                "Mostrar que o índice se recalcula sozinho a cada mudança: "
                "não é preciso atualizá-lo.",
            ),
            "practica": "Identificar a dimensão mais fraca do próprio "
                        "projeto e fazer uma mudança que a melhore.",
            "verificacion": (
                "Quais são as seis dimensões do índice?",
                "Que ação concreta elevaria a dimensão de escopo?",
            ),
        },
    },
    "pm_copiloto": {
        "en": {
            "titulo": "Copilot and reports",
            "objetivo": "Ask questions in plain English and pull the "
                        "project's report.",
            "guion": (
                "Ask the copilot three questions about the portfolio.",
                "Clarify that the rules engine always answers, with nothing "
                "to configure, and that the AI layer is optional and "
                "depends on the plan.",
                "Generate the project's report and export it.",
            ),
            "practica": "Ask the copilot about your own project's status "
                        "and export the report.",
            "verificacion": ("Does the copilot need an internet connection "
                              "to answer?",),
        },
        "pt": {
            "titulo": "Copiloto e relatórios",
            "objetivo": "Fazer perguntas em português e tirar o relatório "
                        "do projeto.",
            "guion": (
                "Fazer três perguntas ao copiloto sobre o portfólio.",
                "Deixar claro que o motor de regras sempre responde, sem "
                "precisar configurar nada, e que a camada de IA é opcional "
                "e depende do plano.",
                "Gerar o relatório do projeto e exportá-lo.",
            ),
            "practica": "Perguntar ao copiloto sobre o status do próprio "
                        "projeto e exportar o relatório.",
            "verificacion": ("O copiloto precisa de conexão à internet para "
                              "responder?",),
        },
    },
    # --------------------------------------------------------------- miembro
    "miembro_mis_tareas": {
        "en": {
            "titulo": "Your tasks",
            "objetivo": "Find what's assigned to you and keep it current.",
            "guion": (
                "Filter tasks by assignee.",
                "Go through the statuses and when to change each one.",
                "Push the one habit that matters: update the status the "
                "same day, not on Friday. Everything else in the system "
                "depends on the status being current.",
            ),
            "practica": "Find your own tasks and update the status of one.",
            "verificacion": ("When do you need to update a task's status?",),
        },
        "pt": {
            "titulo": "Suas tarefas",
            "objetivo": "Encontrar o que foi atribuído a você e mantê-lo em dia.",
            "guion": (
                "Filtrar as tarefas por responsável.",
                "Percorrer os status e quando mudar cada um.",
                "Insistir no hábito-chave: mudar o status no mesmo dia, não "
                "na sexta-feira. Todo o resto do sistema depende do status "
                "estar em dia.",
            ),
            "practica": "Encontrar as próprias tarefas e atualizar o status "
                        "de uma delas.",
            "verificacion": ("Quando você precisa mudar o status de uma tarefa?",),
        },
    },
    "miembro_bloqueos": {
        "en": {
            "titulo": "When something's blocking you",
            "objetivo": "Flag a blocker instead of waiting quietly.",
            "guion": (
                "Mark a task as 'blocked'.",
                "Show that it appears immediately in the PM's dependencies view.",
                "Explain why it matters: a flagged blocker gets seen and "
                "managed; one kept in someone's head doesn't.",
            ),
            "practica": "Mark a task as blocked and flag it in the next meeting.",
            "verificacion": ("What happens when you mark a task as blocked?",),
        },
        "pt": {
            "titulo": "Quando algo trava você",
            "objetivo": "Marcar um bloqueio em vez de esperar calado.",
            "guion": (
                "Marcar uma tarefa como 'blocked'.",
                "Mostrar que ela aparece imediatamente na visão de "
                "dependências do PM.",
                "Explicar por que isso importa: um bloqueio marcado é visto "
                "e gerenciado; um guardado na cabeça de alguém, não.",
            ),
            "practica": "Marcar uma tarefa como bloqueada e avisar na "
                        "próxima reunião.",
            "verificacion": ("O que acontece quando você marca uma tarefa "
                              "como bloqueada?",),
        },
    },
    "miembro_prioridad": {
        "en": {
            "titulo": "What order to work in",
            "objetivo": "Use the backlog instead of deciding by gut feeling.",
            "guion": (
                "Show the backlog filtered by assignee.",
                "Explain that the order already combines urgency, "
                "criticality, and how much it unblocks — there's no need to "
                "argue about it.",
                "Clarify what to do if the order looks wrong: talk to the "
                "PM, who adjusts priority or criticality.",
            ),
            "practica": "Look at your own backlog and start with the first item.",
            "verificacion": ("If you think the backlog order is wrong, what "
                              "do you do?",),
        },
        "pt": {
            "titulo": "Em que ordem trabalhar",
            "objetivo": "Usar o backlog em vez de decidir por intuição.",
            "guion": (
                "Mostrar o backlog filtrado por responsável.",
                "Explicar que a ordem já combina urgência, criticidade e "
                "quanto destrava: não é preciso discutir.",
                "Deixar claro o que fazer se a ordem parecer errada: falar "
                "com o PM, que ajusta prioridade ou criticidade.",
            ),
            "practica": "Olhar o próprio backlog e começar pela primeira tarefa.",
            "verificacion": ("Se você acha que a ordem do backlog está "
                              "errada, o que você faz?",),
        },
    },
    "miembro_glosario": {
        "en": {
            "titulo": "Speaking the same language",
            "objetivo": "Know where to find the agreed definition of each term.",
            "guion": (
                "Show the glossary and a couple of definitions.",
                "Explain that someone at the company validated the "
                "definitions and that they're versioned — if it says that, "
                "it's what was agreed.",
            ),
            "practica": "Look up in the glossary what the company considers "
                        "a project 'at risk'.",
            "verificacion": ("Where do you look if you don't know what a "
                              "term means here?",),
        },
        "pt": {
            "titulo": "Falando a mesma língua",
            "objetivo": "Saber onde está a definição combinada de cada termo.",
            "guion": (
                "Mostrar o glossário e um par de definições.",
                "Explicar que as definições foram validadas por alguém da "
                "empresa e que são versionadas: se diz isso, é o que foi "
                "combinado.",
            ),
            "practica": "Buscar no glossário o que a empresa considera um "
                        "projeto 'em risco'.",
            "verificacion": ("Onde você olha se não sabe o que um termo "
                              "significa aqui dentro?",),
        },
    },
    # ------------------------------------------------------------------- pmo
    "pmo_plantilla": {
        "en": {
            "titulo": "Adopting the industry template",
            "objetivo": "Start from an industry-specific governance model "
                        "instead of a blank page.",
            "guion": (
                "Browse the available industries and open the client's.",
                "Show stages, exit gates, and who approves each one.",
                "Push the point that it's a debatable starting point — you "
                "adopt it and edit it with the people who actually work there.",
                "Show that adopting it records who validated it and when.",
                "Warn that the regulatory references are indicative and "
                "need to be confirmed with quality or legal.",
            ),
            "practica": "Adopt the industry template and adjust at least "
                        "two stages to how the company actually works.",
            "verificacion": (
                "What happens if they switch templates later on?",
                "Who needs to review the regulatory references?",
            ),
        },
        "pt": {
            "titulo": "Adotando o modelo do setor",
            "objetivo": "Partir de uma governança do setor em vez de uma "
                        "folha em branco.",
            "guion": (
                "Percorrer os setores disponíveis e abrir o do cliente.",
                "Mostrar etapas, portões de saída, quem aprova cada uma.",
                "Insistir que é um ponto de partida discutível: se adota e "
                "se edita com o pessoal da casa.",
                "Mostrar que, ao adotá-la, fica registrado quem a validou e "
                "quando.",
                "Alertar que as referências normativas são orientativas e "
                "precisam ser confirmadas com qualidade ou jurídico.",
            ),
            "practica": "Adotar o modelo do setor e ajustar pelo menos duas "
                        "etapas para como a empresa realmente trabalha.",
            "verificacion": (
                "O que acontece se, mais adiante, trocarem de modelo?",
                "Quem precisa revisar as referências normativas?",
            ),
        },
    },
    "pmo_gobernanza": {
        "en": {
            "titulo": "Definitions and versioning",
            "objetivo": "Pin down what each term means and leave a trail of "
                        "who approved it.",
            "guion": (
                "Open a concept and show the suggested definition.",
                "Edit it and save it with the name and title of whoever validates it.",
                "Show the history: nothing gets overwritten, everything stays.",
                "Explain why it matters: when someone disputes a number, it "
                "gets resolved by checking the current definition and who "
                "signed off on it.",
            ),
            "practica": "Validate three definitions with the real name of "
                        "whoever approves them.",
            "verificacion": (
                "Can you revert to a previous definition?",
                "What's the difference between a draft definition and a "
                "validated one?",
            ),
        },
        "pt": {
            "titulo": "Definições e versionamento",
            "objetivo": "Fixar o que cada termo significa e deixar rastro de "
                        "quem o aprovou.",
            "guion": (
                "Abrir um conceito e mostrar a definição sugerida.",
                "Editá-la e salvá-la com nome e cargo de quem a valida.",
                "Mostrar o histórico: nada é sobrescrito, tudo fica registrado.",
                "Explicar por que isso importa: quando alguém questiona um "
                "número, a discussão se resolve olhando a definição vigente "
                "e quem a assinou.",
            ),
            "practica": "Validar três definições com o nome real de quem as aprova.",
            "verificacion": (
                "É possível voltar para uma definição anterior?",
                "Qual é a diferença entre uma definição em rascunho e uma validada?",
            ),
        },
    },
    "pmo_organigrama": {
        "en": {
            "titulo": "Org chart and owners",
            "objetivo": "Load the structure and validate who's accountable "
                        "for each stage.",
            "guion": (
                "Upload the org chart from Excel or CSV.",
                "Show the suggested owner per stage and how to validate it.",
                "Stress that the suggestion is only a proposal — a person "
                "validates it and it's recorded who that was.",
            ),
            "practica": "Load the real org chart and validate the owners "
                        "for at least three stages.",
            "verificacion": ("Who gets recorded as responsible for validating?",),
        },
        "pt": {
            "titulo": "Organograma e responsáveis",
            "objetivo": "Carregar a estrutura e validar quem responde por "
                        "cada etapa.",
            "guion": (
                "Subir o organograma a partir de Excel ou CSV.",
                "Mostrar a sugestão de responsável por etapa e como validá-la.",
                "Reforçar que a sugestão é uma proposta: uma pessoa a valida "
                "e fica registrado quem foi.",
            ),
            "practica": "Carregar o organograma real e validar os "
                        "responsáveis de pelo menos três etapas.",
            "verificacion": ("Quem fica registrado como responsável por validar?",),
        },
    },
    "pmo_pmbok": {
        "en": {
            "titulo": "PMBOK applied to the company",
            "objetivo": "Know what the tool covers and what's still the PM's job.",
            "guion": (
                "Go through the ten areas and their coverage: full, "
                "partial, or not covered.",
                "Linger on the 'not covered' ones and be explicit: the PM "
                "handles that outside the tool.",
                "Show the critical areas for the adopted industry and why "
                "those are the ones.",
                "Leave your own notes per area.",
            ),
            "practica": "Write a note in the three critical areas for the "
                        "industry, explaining how they're covered at this company.",
            "verificacion": ("Which area does the tool NOT cover, and who "
                              "covers it instead?",),
        },
        "pt": {
            "titulo": "PMBOK aplicado à empresa",
            "objetivo": "Saber o que a ferramenta cobre e o que continua "
                        "sendo trabalho do PM.",
            "guion": (
                "Percorrer as dez áreas e sua cobertura: completa, parcial "
                "ou não coberta.",
                "Parar nas 'não cobertas' e ser explícito: isso o PM faz "
                "fora da ferramenta.",
                "Mostrar as áreas críticas do setor adotado e por que são "
                "justamente essas.",
                "Deixar notas próprias por área.",
            ),
            "practica": "Escrever uma nota nas três áreas críticas do setor "
                        "explicando como são cobertas nesta empresa.",
            "verificacion": ("Qual área a ferramenta NÃO cobre, e quem a "
                              "cobre então?",),
        },
    },
    "pmo_politicas": {
        "en": {
            "titulo": "Policies and thresholds",
            "objetivo": "Set the thresholds that trigger alerts.",
            "guion": (
                "Show the current policies and their thresholds.",
                "Explain how a badly set threshold generates alerts nobody "
                "looks at, and that's worse than having no alerts at all.",
                "Adjust a threshold and see the effect.",
            ),
            "practica": "Adjust the thresholds to the company's reality and "
                        "justify each change.",
            "verificacion": ("What happens if you set a threshold too sensitive?",),
        },
        "pt": {
            "titulo": "Políticas e limites",
            "objetivo": "Definir os limites que disparam alertas.",
            "guion": (
                "Mostrar as políticas vigentes e seus limites.",
                "Explicar como um limite mal ajustado gera alertas que "
                "ninguém olha, e que isso é pior do que não ter alertas.",
                "Ajustar um limite e ver o efeito.",
            ),
            "practica": "Ajustar os limites à realidade da empresa e "
                        "justificar cada mudança.",
            "verificacion": ("O que acontece se você definir um limite "
                              "sensível demais?",),
        },
    },
    # ----------------------------------------------------------------- admin
    "admin_instalacion": {
        "en": {
            "titulo": "Installation and first launch",
            "objetivo": "Get the system running and create the "
                        "administrator account.",
            "guion": (
                "Install and start it up.",
                "Create the administrator account: the first person to log "
                "in becomes the admin.",
                "Show where the database lives — that's what needs to be backed up.",
                "Explain the license token and the seven-day trial.",
            ),
            "practica": "Install on a clean machine and create the "
                        "administrator account.",
            "verificacion": (
                "Where's the file that needs to be backed up?",
                "What happens when the trial expires? Is the data lost?",
            ),
        },
        "pt": {
            "titulo": "Instalação e primeira inicialização",
            "objetivo": "Deixar o sistema rodando e criar a conta de administrador.",
            "guion": (
                "Instalar e iniciar.",
                "Criar a conta de administrador: a primeira pessoa que "
                "entra fica como admin.",
                "Mostrar onde fica o banco de dados, que é o que precisa "
                "ser copiado no backup.",
                "Explicar o token de licença e o período de teste de sete dias.",
            ),
            "practica": "Instalar em uma máquina limpa e criar a conta de administrador.",
            "verificacion": (
                "Onde está o arquivo que precisa ser copiado no backup?",
                "O que acontece quando o teste vence? Os dados se perdem?",
            ),
        },
    },
    "admin_usuarios": {
        "en": {
            "titulo": "Users and roles",
            "objetivo": "Add the team with the right role for each person.",
            "guion": (
                "Show how the rest of the team signs up from the login screen.",
                "Explain the difference between admin and member.",
                "Clarify that nobody can self-assign the admin role.",
            ),
            "practica": "Onboard two people and verify that they can log in.",
            "verificacion": ("Can a member turn themselves into an admin?",),
        },
        "pt": {
            "titulo": "Usuários e funções",
            "objetivo": "Adicionar a equipe com a função que corresponde a cada um.",
            "guion": (
                "Mostrar como o resto da equipe se cadastra a partir da "
                "tela de login.",
                "Explicar a diferença entre admin e membro.",
                "Deixar claro que ninguém pode se auto-atribuir admin.",
            ),
            "practica": "Cadastrar duas pessoas e verificar que elas "
                        "conseguem entrar.",
            "verificacion": ("Um membro pode se transformar em admin por "
                              "conta própria?",),
        },
    },
    "admin_importacion": {
        "en": {
            "titulo": "Loading the client's data",
            "objetivo": "Import projects and tasks from whatever file the client has.",
            "guion": (
                "Upload a deliberately messy file, without cleaning it up first.",
                "Show the automatic column detection and the confidence "
                "traffic light: green is a clear match, yellow is a guess "
                "worth double-checking.",
                "Walk through the preview report: how many rows go in, how "
                "many get discarded and why. Stress that nothing has been "
                "written yet.",
                "Linger on the column warnings — the thousands separator, "
                "ambiguous dates, numeric levels — and explain why the "
                "system flags them instead of guessing.",
                "Import it, and show that re-importing the same file "
                "doesn't create duplicates.",
            ),
            "practica": "Import the client's real file and explain every "
                        "discarded row.",
            "verificacion": (
                "At what point does the importer actually write to the database?",
                "If a column comes up yellow, what do you do?",
            ),
        },
        "pt": {
            "titulo": "Carregando os dados do cliente",
            "objetivo": "Importar projetos e tarefas a partir do arquivo que "
                        "o cliente tiver.",
            "guion": (
                "Subir um arquivo desorganizado de propósito, sem prepará-lo antes.",
                "Mostrar a detecção automática de colunas e o semáforo de "
                "confiança: verde é correspondência clara, amarelo é uma "
                "suposição que vale a pena conferir.",
                "Percorrer o relatório prévio: quantas entram, quantas são "
                "descartadas e por quê. Reforçar que até aqui nada foi gravado.",
                "Parar nos avisos de coluna — o separador de milhares, as "
                "datas ambíguas, os níveis numéricos — e explicar por que o "
                "sistema avisa em vez de adivinhar.",
                "Importar e mostrar que reimportar o mesmo arquivo não duplica.",
            ),
            "practica": "Importar o arquivo real do cliente e explicar cada "
                        "linha descartada.",
            "verificacion": (
                "Em que momento o importador grava no banco de dados?",
                "Se uma coluna aparece em amarelo, o que você faz?",
            ),
        },
    },
    "admin_conectores": {
        "en": {
            "titulo": "Connecting the ERP",
            "objetivo": "Pull data straight from the ERP when the client allows it.",
            "guion": (
                "Choose the client's ERP profile.",
                "Run the probe BEFORE attempting extraction, and read the "
                "result: which tables and columns it found, and which it didn't.",
                "Explain that the profiles ship out of the box, and a "
                "years-old ERP has been customized — that's why there's a "
                "probe, and why the query can be edited.",
                "Show that everything is read-only, and the system rejects "
                "any query that isn't a SELECT.",
                "Show that whatever gets extracted goes through the same "
                "preview report as the importer.",
            ),
            "practica": "Probe a test ERP and explain what you'd do if a "
                        "column was missing.",
            "verificacion": (
                "Why do you probe before extracting?",
                "Can this connector modify anything in the client's ERP?",
            ),
        },
        "pt": {
            "titulo": "Conectando o ERP",
            "objetivo": "Trazer dados direto do ERP quando o cliente permite.",
            "guion": (
                "Escolher o perfil do ERP do cliente.",
                "Rodar o sondeio ANTES de tentar a extração e ler o "
                "resultado: quais tabelas e colunas encontrou e quais não.",
                "Explicar que os perfis vêm de fábrica e que um ERP com "
                "anos de uso está personalizado: por isso o sondeio, e por "
                "isso a consulta pode ser editada.",
                "Mostrar que tudo é somente leitura e que o sistema rejeita "
                "qualquer consulta que não seja um SELECT.",
                "Mostrar que o que é extraído entra pelo mesmo relatório "
                "prévio do importador.",
            ),
            "practica": "Sondar um ERP de teste e explicar o que faria se "
                        "faltasse uma coluna.",
            "verificacion": (
                "Por que se sonda antes de extrair?",
                "Esse conector pode modificar algo no ERP do cliente?",
            ),
        },
    },
    "admin_respaldo": {
        "en": {
            "titulo": "Backup and common problems",
            "objetivo": "Back up, restore, and fix what usually breaks.",
            "guion": (
                "Copy the database file and restore it on another machine.",
                "Go through the common problems: forgotten password, "
                "expired license, port already in use.",
                "Show where the error messages show up.",
            ),
            "practica": "Make a backup, delete the database, and restore it.",
            "verificacion": ("How often should you back up, and exactly "
                              "which file?",),
        },
        "pt": {
            "titulo": "Backup e problemas comuns",
            "objetivo": "Fazer backup, restaurar e resolver o que costuma quebrar.",
            "guion": (
                "Copiar o arquivo do banco de dados e restaurá-lo em outra máquina.",
                "Percorrer os problemas frequentes: senha esquecida, "
                "licença vencida, porta ocupada.",
                "Mostrar onde aparecem as mensagens de erro.",
            ),
            "practica": "Fazer um backup, apagar o banco e restaurá-lo.",
            "verificacion": ("De quanto em quanto tempo convém fazer "
                              "backup, e qual arquivo exatamente?",),
        },
    },
    # ----------------------------------------------------------- datos / BI
    "datos_powerbi": {
        "en": {
            "titulo": "Connecting to Power BI",
            "objetivo": "Get a Power BI dashboard reading live from the system.",
            "guion": (
                "Generate the .pbids connection file and open it in Power BI.",
                "Show the available tables and their columns.",
                "Explain the refresh frequency and its limits.",
            ),
            "practica": "Build a simple dashboard in Power BI against the real data.",
            "verificacion": ("Which file do you open in Power BI to connect?",),
        },
        "pt": {
            "titulo": "Conexão com o Power BI",
            "objetivo": "Deixar um painel do Power BI lendo do sistema.",
            "guion": (
                "Gerar o arquivo de conexão .pbids e abri-lo no Power BI.",
                "Mostrar as tabelas disponíveis e suas colunas.",
                "Explicar a frequência de atualização e seus limites.",
            ),
            "practica": "Montar um painel simples no Power BI contra os dados reais.",
            "verificacion": ("Qual arquivo você abre no Power BI para se conectar?",),
        },
    },
    "datos_exportar": {
        "en": {
            "titulo": "Exports",
            "objetivo": "Get the data out to Excel whenever it's needed.",
            "guion": (
                "Export the portfolio and the tasks to Excel.",
                "Show the sheet structure of the exported file.",
            ),
            "practica": "Export the full portfolio and open it in Excel.",
            "verificacion": ("What sheets does the exported Excel file have?",),
        },
        "pt": {
            "titulo": "Exportações",
            "objetivo": "Tirar os dados em Excel quando for preciso.",
            "guion": (
                "Exportar o portfólio e as tarefas para Excel.",
                "Mostrar a estrutura de planilhas do arquivo exportado.",
            ),
            "practica": "Exportar o portfólio completo e abri-lo no Excel.",
            "verificacion": ("Quais planilhas o Excel exportado traz?",),
        },
    },
    "datos_erp_mantenimiento": {
        "en": {
            "titulo": "Maintaining the ERP feed",
            "objetivo": "Keep the integration working when the ERP changes.",
            "guion": (
                "Review the probe and what to do when a missing column turns up.",
                "Edit the profile's query with the real names from the "
                "installation and save it.",
                "Linger on the odd conversions: JD Edwards' Julian dates, "
                "SAP's YYYYMMDD, Dynamics' 1900 quirk, amounts with implied "
                "decimals. Explain that these are the most common source of "
                "silent errors.",
                "Show how to cross-check a couple of amounts and dates "
                "against the ERP before signing off on a load.",
            ),
            "practica": "Rename a column on purpose, watch the probe catch "
                        "it, and fix the query.",
            "verificacion": (
                "How do you verify that the amounts you pulled in are correct?",
                "What is a Julian date, and which ERP uses it?",
            ),
        },
        "pt": {
            "titulo": "Mantendo a carga a partir do ERP",
            "objetivo": "Sustentar a integração quando o ERP muda.",
            "guion": (
                "Rever o sondeio e o que fazer quando aparece uma coluna faltante.",
                "Editar a consulta do perfil com os nomes reais da "
                "instalação e salvá-la.",
                "Parar nas conversões estranhas: as datas julianas do JD "
                "Edwards, o YYYYMMDD do SAP, o 1900 do Dynamics, os valores "
                "com decimais implícitos. Explicar que são a fonte mais "
                "comum de erros silenciosos.",
                "Mostrar como conferir um par de valores e datas contra o "
                "ERP antes de dar uma carga como boa.",
            ),
            "practica": "Mudar o nome de uma coluna de propósito, ver que o "
                        "sondeio detecta, e corrigir a consulta.",
            "verificacion": (
                "Como você verifica se os valores que trouxe estão corretos?",
                "O que é uma data juliana e em qual ERP ela aparece?",
            ),
        },
    },
}

# Etiquetas fijas del guion imprimible (encabezados, no contenido de currícula).
_TXT_GUION: dict[str, dict[str, str]] = {
    "es": {
        "encabezado": "Capacitación", "para_quien": "Para quién",
        "al_terminar": "Al terminar", "duracion": "Duración",
        "minutos_modulos": "{m} minutos en {n} módulos",
        "antes_de_esto": "Antes de esto", "se_hace_en": "se hace en",
        "guion": "Guion", "practica": "Práctica",
        "verificacion": "Verificación", "min": "min",
    },
    "en": {
        "encabezado": "Training", "para_quien": "Who it's for",
        "al_terminar": "By the end", "duracion": "Duration",
        "minutos_modulos": "{m} minutes across {n} modules",
        "antes_de_esto": "Before this", "se_hace_en": "done in",
        "guion": "Script", "practica": "Practice",
        "verificacion": "Verification", "min": "min",
    },
    "pt": {
        "encabezado": "Capacitação", "para_quien": "Para quem",
        "al_terminar": "Ao final", "duracion": "Duração",
        "minutos_modulos": "{m} minutos em {n} módulos",
        "antes_de_esto": "Antes disto", "se_hace_en": "feito em",
        "guion": "Roteiro", "practica": "Prática",
        "verificacion": "Verificação", "min": "min",
    },
}


def _seccion_app(es: str, lang: str) -> str:
    return _SECCION_APP_TRAD.get(es, {}).get(lang, es)


def _modulo_traducido(m: Modulo, lang: str) -> Modulo:
    if lang == "es":
        return m
    t = _MODULO_TRAD.get(m.clave, {}).get(lang)
    if not t:
        return m
    return replace(
        m,
        titulo=t.get("titulo", m.titulo),
        objetivo=t.get("objetivo", m.objetivo),
        seccion_app=_seccion_app(m.seccion_app, lang),
        guion=t.get("guion", m.guion),
        practica=t.get("practica", m.practica),
        verificacion=t.get("verificacion", m.verificacion),
    )


def _curricula_traducida(c: Curricula, lang: str) -> Curricula:
    if lang == "es":
        return c
    t = _CURRICULA_TRAD.get(c.clave, {}).get(lang, {})
    return replace(
        c,
        rol=t.get("rol", c.rol),
        para_quien=t.get("para_quien", c.para_quien),
        promesa=t.get("promesa", c.promesa),
        modulos=tuple(_modulo_traducido(m, lang) for m in c.modulos),
    )


def catalogo(lang: str = "es") -> list[Curricula]:
    return [_curricula_traducida(c, lang) for c in CURRICULAS.values()]


def obtener(clave: str, lang: str = "es") -> Curricula:
    if clave not in CURRICULAS:
        raise ValueError(f"Rol de capacitación desconocido: {clave!r}")
    return _curricula_traducida(CURRICULAS[clave], lang)


def roles(lang: str = "es") -> list[tuple[str, str, int]]:
    """(clave, rol, minutos) para armar el menú."""
    return [(c.clave, c.rol, c.minutos) for c in catalogo(lang)]


def ruta_completa(clave: str, lang: str = "es") -> list[Curricula]:
    """La currícula pedida, precedida por las que exige como requisito."""
    c = obtener(clave, lang)
    salida: list[Curricula] = []
    for req in c.requiere:
        for previa in ruta_completa(req, lang):
            if previa not in salida:
                salida.append(previa)
    salida.append(c)
    return salida


def plan_de_grabacion(lang: str = "es") -> list[dict]:
    """Todo lo que hay que grabar, sin repetir, con su duración.

    Un mismo módulo puede aparecer en varias rutas; acá se lista una sola vez
    para que grabar no sea más largo de lo necesario.
    """
    vistos: dict[str, dict] = {}
    for c in catalogo(lang):
        for m in c.modulos:
            if m.clave in vistos:
                vistos[m.clave]["roles"].append(c.rol)
                continue
            vistos[m.clave] = {
                "clave": m.clave, "titulo": m.titulo, "minutos": m.minutos,
                "seccion_app": m.seccion_app, "roles": [c.rol],
                "objetivo": m.objetivo,
            }
    return list(vistos.values())


def minutos_totales_a_grabar(lang: str = "es") -> int:
    return sum(m["minutos"] for m in plan_de_grabacion(lang))


def guion_de(clave_rol: str, lang: str = "es") -> str:
    """Guion imprimible de toda la currícula, para grabar sin improvisar."""
    c = obtener(clave_rol, lang)
    t = _TXT_GUION.get(lang, _TXT_GUION["es"])
    duracion_txt = t["minutos_modulos"].format(m=c.minutos, n=len(c.modulos))
    lineas = [f"# {t['encabezado']} — {c.rol}", "",
              f"**{t['para_quien']}:** {c.para_quien}",
              f"**{t['al_terminar']}:** {c.promesa}",
              f"**{t['duracion']}:** {duracion_txt}", ""]
    if c.requiere:
        previas = ", ".join(obtener(r, lang).rol for r in c.requiere)
        lineas += [f"**{t['antes_de_esto']}:** {previas}", ""]
    for i, m in enumerate(c.modulos, 1):
        lineas += [f"## {i}. {m.titulo} ({m.minutos} {t['min']})", "",
                   f"*{m.objetivo}* — {t['se_hace_en']} «{m.seccion_app}».", "",
                   f"{t['guion']}:"]
        lineas += [f"{j}. {p}" for j, p in enumerate(m.guion, 1)]
        lineas += ["", f"**{t['practica']}:** {m.practica}", "",
                   f"**{t['verificacion']}:**"]
        lineas += [f"- {v}" for v in m.verificacion]
        lineas.append("")
    return "\n".join(lineas)


def checklist_de_verificacion(clave_rol: str, lang: str = "es") -> list[dict]:
    """Las preguntas de toda la ruta, para confirmar que la persona puede sola."""
    salida = []
    for c in ruta_completa(clave_rol, lang):
        for m in c.modulos:
            for pregunta in m.verificacion:
                salida.append({"rol": c.rol, "modulo": m.titulo, "pregunta": pregunta})
    return salida
