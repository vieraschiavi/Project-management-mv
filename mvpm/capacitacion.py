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

from dataclasses import dataclass

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


def catalogo() -> list[Curricula]:
    return list(CURRICULAS.values())


def obtener(clave: str) -> Curricula:
    if clave not in CURRICULAS:
        raise ValueError(f"Rol de capacitación desconocido: {clave!r}")
    return CURRICULAS[clave]


def roles() -> list[tuple[str, str, int]]:
    """(clave, rol, minutos) para armar el menú."""
    return [(c.clave, c.rol, c.minutos) for c in CURRICULAS.values()]


def ruta_completa(clave: str) -> list[Curricula]:
    """La currícula pedida, precedida por las que exige como requisito."""
    c = obtener(clave)
    salida: list[Curricula] = []
    for req in c.requiere:
        for previa in ruta_completa(req):
            if previa not in salida:
                salida.append(previa)
    salida.append(c)
    return salida


def plan_de_grabacion() -> list[dict]:
    """Todo lo que hay que grabar, sin repetir, con su duración.

    Un mismo módulo puede aparecer en varias rutas; acá se lista una sola vez
    para que grabar no sea más largo de lo necesario.
    """
    vistos: dict[str, dict] = {}
    for c in CURRICULAS.values():
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


def minutos_totales_a_grabar() -> int:
    return sum(m["minutos"] for m in plan_de_grabacion())


def guion_de(clave_rol: str) -> str:
    """Guion imprimible de toda la currícula, para grabar sin improvisar."""
    c = obtener(clave_rol)
    lineas = [f"# Capacitación — {c.rol}", "",
              f"**Para quién:** {c.para_quien}",
              f"**Al terminar:** {c.promesa}",
              f"**Duración:** {c.minutos} minutos en {len(c.modulos)} módulos", ""]
    if c.requiere:
        previas = ", ".join(obtener(r).rol for r in c.requiere)
        lineas += [f"**Antes de esto:** {previas}", ""]
    for i, m in enumerate(c.modulos, 1):
        lineas += [f"## {i}. {m.titulo} ({m.minutos} min)", "",
                   f"*{m.objetivo}* — se hace en «{m.seccion_app}».", "", "Guion:"]
        lineas += [f"{j}. {p}" for j, p in enumerate(m.guion, 1)]
        lineas += ["", f"**Práctica:** {m.practica}", "", "**Verificación:**"]
        lineas += [f"- {v}" for v in m.verificacion]
        lineas.append("")
    return "\n".join(lineas)


def checklist_de_verificacion(clave_rol: str) -> list[dict]:
    """Las preguntas de toda la ruta, para confirmar que la persona puede sola."""
    salida = []
    for c in ruta_completa(clave_rol):
        for m in c.modulos:
            for pregunta in m.verificacion:
                salida.append({"rol": c.rol, "modulo": m.titulo, "pregunta": pregunta})
    return salida
