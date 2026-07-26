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
        "id": "nav_real_demo",
        "titulo": "Demo con datos reales",
        "resumen": "El motor corriendo sobre 132 proyectos reales del portafolio público del "
                   "Reino Unido (datos abiertos, no simulados) — con dos casos narrados con el "
                   "texto real de sus informes anuales.",
        "pasos": [
            "Los KPIs de arriba (presupuesto total, cuántos están sobre presupuesto) son el "
            "resultado real de correr el catálogo sobre el dataset público — no son inventados.",
            "El 'ahorro estimado' declara explícitamente su supuesto (minutos por revisión manual) "
            "en vez de esconderlo — así se puede cuestionar o ajustar, no es una cifra de marketing.",
            "Los dos casos incluyen el texto real de los informes anuales del gobierno británico "
            "sobre por qué se desvió el presupuesto o por qué el proyecto salió bien.",
        ],
        "tips": [
            "Es la prueba de que el motor no está hecho a medida del dataset de ejemplo — funciona "
            "igual sobre datos públicos que nadie preparó pensando en esta herramienta.",
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
        "id": "nav_advisor",
        "titulo": "Asistente IA",
        "resumen": "El motor de reglas detecta problemas del portafolio (bloqueos, dependencias "
                   "huérfanas, proyectos en riesgo, sobrepresupuesto, sobrecarga, políticas "
                   "incumplidas) y sugiere una acción — con seguimiento persistido.",
        "pasos": [
            "Elegí quién redacta la sugerencia: el motor de reglas solo, o un proveedor de IA "
            "(Claude, ChatGPT o Gemini) — sólo aparecen los que tengan su clave configurada.",
            "Cada problema detectado muestra una sugerencia concreta; 'Poner en seguimiento' la "
            "guarda en la base con estado 'abierto'.",
            "Desde el mismo problema podés pasar el seguimiento a 'en_progreso' o 'resuelto' — "
            "queda en la tabla de Seguimientos aunque el problema original ya no se detecte.",
        ],
        "tips": [
            "El motor de reglas nunca depende de la IA — si no configurás ninguna clave, el "
            "asistente sigue detectando y sugiriendo igual, solo que sin pulir la redacción.",
            "ChatGPT y Gemini necesitan además `OPENAI_MODEL` / `GEMINI_MODEL` en el entorno — "
            "así nunca se asume un modelo por vos.",
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
        "resumen": "El PMBOK (guía del PMI) en dos registros: técnico (como lo diría un PMP) y en "
                   "criollo (castellano de todos los días), con las 10 áreas de conocimiento y "
                   "los 5 grupos de procesos.",
        "pasos": [
            "En 'áreas de conocimiento', cada área tiene su definición técnica y su versión en "
            "criollo, más cuánto la cubre el producto (completa / parcial / no cubierta), sin inflar.",
            "En 'grupos de procesos' está el ciclo de vida (Inicio → Planificación → Ejecución → "
            "Monitoreo → Cierre), también técnico + criollo.",
            "Cada área admite una nota interna de tu empresa (algo que no se automatiza) que se "
            "edita a mano y queda versionada, con quién la validó.",
        ],
        "tips": [
            "No es una certificación oficial del PMI, es una referencia para equipos que ya "
            "trabajan con esa guía y quieren saber en qué se apoya la herramienta.",
        ],
    },
    {
        "id": "nav_governance",
        "titulo": "Gobernanza de datos",
        "resumen": "Cada concepto de gestión ya viene con una definición preestablecida; la IA "
                   "recomienda una mejora y el Data Owner / Data Steward la valida o edita y "
                   "guarda, versionada por empresa.",
        "pasos": [
            "La definición nunca aparece en blanco: sale preestablecida de fábrica, o pulida por "
            "la IA si tenés un proveedor configurado.",
            "El responsable (Data Owner) la valida o la edita y la guarda con su nombre y cargo — "
            "cada cambio es una versión nueva, no se pisa la anterior.",
            "Todo se guarda por empresa (elegís la empresa activa en la barra lateral), así cada "
            "organización tiene su propia historia de definiciones.",
        ],
        "tips": [
            "Es el mismo criterio de MV Data Governance: la definición vigente es la última "
            "versión validada; si nunca se tocó, rige la de fábrica.",
        ],
    },
    {
        "id": "nav_organigrama",
        "titulo": "Organigrama y responsables",
        "resumen": "Cargás el organigrama (Excel/CSV o base SQLite) y la IA autocompleta por "
                   "defecto quién es responsable de cada etapa del proyecto, editable y versionado.",
        "pasos": [
            "Subí el organigrama; reconoce columnas comunes (nombre, cargo, área, reporta a) sin "
            "exigir un formato exacto.",
            "Para cada etapa (los 5 grupos de procesos del PMBOK) aparece un responsable "
            "pre-recomendado según el cargo — lo validás o lo cambiás y queda guardado.",
            "Si el organigrama es una foto, hace falta un proveedor de IA con visión; sin eso, "
            "exportalo a Excel/CSV y subilo.",
        ],
        "tips": [
            "Los responsables validados por etapa aparecen también en la pestaña PMBOK, en cada "
            "grupo de procesos.",
        ],
    },
    {
        "id": "nav_pharma",
        "titulo": "Demo laboratorio (Pharma)",
        "resumen": "El motor corriendo sobre 474 ensayos clínicos reales de tres laboratorios "
                   "multinacionales (AstraZeneca, Pfizer, Novartis), de punta a punta hasta Power BI.",
        "pasos": [
            "Cada ensayo es un proyecto: sponsor (el laboratorio), fechas, fase y estado. El motor "
            "deriva la criticidad del estado real (terminado/suspendido = en riesgo).",
            "Los gráficos por estado y por laboratorio, y la lista de ensayos en riesgo, salen de "
            "correr el motor sobre el dato real — no hay cifras inventadas (la fuente no publica "
            "presupuesto, y se dice).",
            "Desde la misma pestaña bajás la tabla lista para BI y seguís la guía para conectar "
            "Power BI a la API local con un clic (.pbids).",
        ],
        "tips": [
            "Fuente: ClinicalTrials.gov (U.S. National Library of Medicine), dominio público.",
        ],
    },
    {
        "id": "nav_plantillas",
        "titulo": "Plantillas por rubro",
        "resumen": "Gobernanza lista para el rubro del cliente — etapas con puerta de salida, "
                   "quién aprueba, riesgos típicos y normativa — para no arrancar de una hoja "
                   "en blanco en cada implementación.",
        "pasos": [
            "Elegí el rubro y recorré las etapas: cada una dice qué entregables pide, cuál es "
            "el criterio para pasar a la siguiente, y quién firma.",
            "Mirá la pestaña de roles y riesgos: el registro de riesgos arranca con los "
            "típicos del rubro en vez de vacío, cada uno atado a su área de PMBOK.",
            "Adoptala desde la pestaña «Adoptar», con el nombre de quien la valida. Queda "
            "versionada: cambiar de plantilla más adelante no borra la historia.",
            "Editala con la gente de la casa. Sale de fábrica para discutirla, no para "
            "aplicarla tal cual.",
        ],
        "tips": [
            "Las referencias normativas son orientativas y están tomadas de Uruguay salvo "
            "que digan otra cosa. Hay que confirmarlas con calidad, legales o compliance: "
            "cambian, y cada empresa las interpreta a su manera.",
            "Que un rubro tenga áreas de PMBOK marcadas como críticas indica dónde poner el "
            "esfuerzo, no qué áreas ignorar. Las diez aplican siempre.",
            "Se puede descargar la gobernanza completa en Markdown para llevarla impresa a "
            "la reunión de arranque.",
        ],
    },
    {
        "id": "nav_conectores",
        "titulo": "Conectores ERP",
        "resumen": "Traer proyectos y tareas directo de SAP, Oracle, Dynamics o JD Edwards, "
                   "sin exportar a Excel primero. Siempre de solo lectura.",
        "pasos": [
            "Elegí la familia y el sistema. Cada perfil trae las tablas y campos de fábrica "
            "de ese ERP y explica cómo se conecta.",
            "Sondeá antes de extraer. El sondeo verifica que las tablas y columnas existan y "
            "te dice exactamente cuáles faltan, en vez de tirarte un error del motor.",
            "Si falta alguna columna, editá la consulta con los nombres reales de esa "
            "instalación. Es lo normal en un ERP con años encima.",
            "Traé los datos y revisalos: lo extraído pasa por el mismo informe previo que un "
            "archivo subido a mano, con duplicados y filas descartadas.",
        ],
        "tips": [
            "Los conectores son de solo lectura y el sistema rechaza cualquier consulta que "
            "no sea un SELECT. Aun así, conectate con un usuario de solo lectura: ésa es la "
            "protección de verdad, el candado del software es la segunda línea.",
            "Las conversiones raras son la fuente más común de errores silenciosos: JD "
            "Edwards guarda las fechas en Julian (124001 es el 1/1/2024), SAP como texto "
            "YYYYMMDD, y Dynamics usa 1900-01-01 como «sin fecha».",
            "Contrastá un par de fechas e importes contra el ERP antes de dar una carga por "
            "buena. En JD Edwards los importes vienen con decimales implícitos y la cantidad "
            "depende de cada instalación.",
            "Si el ERP está en la nube (Oracle Fusion, D365 en SaaS) normalmente no hay "
            "acceso directo a la base: se exporta y se importa el archivo.",
        ],
    },
    {
        "id": "nav_capacitacion",
        "titulo": "Capacitación por rol",
        "resumen": "Currícula, guion de grabación y preguntas de verificación para cada rol, "
                   "para grabar una vez y dejar de repetir la misma sesión en vivo en cada "
                   "implementación.",
        "pasos": [
            "Elegí el rol: sponsor, PM, miembro, PMO, administrador o referente de datos. "
            "Cada uno tiene su propia ruta y duración.",
            "Cada módulo trae el guion para grabar, la práctica que hace la persona después "
            "de mirar, y las preguntas que confirman que puede trabajar sola.",
            "Usá la pestaña de verificación como checklist al cerrar la capacitación.",
            "El plan de grabación lista todos los módulos sin repetir: uno que sirve a varios "
            "roles se graba una sola vez.",
        ],
        "tips": [
            "La currícula del sponsor dura quince minutos a propósito. Un sponsor no mira una "
            "hora de video, y si se le exige, no mira nada.",
            "Las preguntas de verificación son lo que hace que la capacitación pueda fallar. "
            "Una capacitación que no puede fallar no sirve para saber si alguien aprendió.",
            "El PMO arranca por la ruta del PM, y el referente de datos por la del "
            "administrador: la app muestra los requisitos previos de cada rol.",
        ],
    },
    {
        "id": "nav_import",
        "titulo": "Importar datos",
        "resumen": "Subir proyectos o tareas desde tu CSV/Excel tal como lo tenés — sin "
                   "preparar el archivo antes. Se cargan de verdad a la base.",
        "pasos": [
            "Subí el archivo como está. El sistema detecta solo a qué campo corresponde cada "
            "columna, aunque se llame «Nombre del Proyecto», «Área Responsable» o «Monto Total».",
            "Revisá el mapeo propuesto y corregí con las listas desplegables lo que haga falta. "
            "El tilde verde es coincidencia exacta; el amarillo es una suposición.",
            "Mirá el informe previo: cuántas filas se crean, cuántas se descartan y por qué. "
            "Nada se escribe hasta que confirmás.",
            "Recién ahí apretá Importar.",
        ],
        "tips": [
            "Traduce los valores solo: «En curso» → en progreso, «URGENTE» → Alta, "
            "«$ 1.234.567» → 1234567, «01/03/2026» → 1 de marzo.",
            "Las tareas se asocian a su proyecto por nombre, y el responsable se busca "
            "por nombre o email contra el equipo cargado.",
            "Detecta filas repetidas y las que ya existen en el sistema, así podés reimportar "
            "el mismo archivo sin duplicar nada.",
            "Si no tenés archivo, descargá la plantilla desde la misma pantalla.",
        ],
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
