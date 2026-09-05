# © 2026 Martín Viera. Todos los derechos reservados.
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
        "id": "nav_data_eng",
        "titulo": "Ingeniería de datos",
        "resumen": "Perfilá cualquier tabla —no sólo proyectos y tareas— antes de "
                   "importarla o conectarla a un ERP: nulos, duplicados, outliers, la "
                   "clave primaria candidata y un CREATE TABLE de partida.",
        "pasos": [
            "Elegí el origen: un archivo CSV/Excel de cualquier esquema, o una base SQL "
            "con una consulta SELECT propia.",
            "Mirá el score de calidad y la lista de problemas: cada uno trae la acción "
            "concreta para resolverlo, no sólo el diagnóstico.",
            "Revisá la clave primaria candidata y, si hay una columna de fecha, la "
            "cobertura temporal —desde cuándo hay datos y qué días faltan.",
            "Descargá el CREATE TABLE sugerido o el informe completo en Excel para "
            "compartirlo con quien vaya a diseñar la base o revisar el archivo.",
        ],
        "tips": [
            "La conexión SQL es de solo lectura y la cadena de conexión no se guarda en "
            "ningún lado: vive únicamente en la sesión del navegador.",
            "Un ID con ceros a la izquierda («007») se deja como texto a propósito: "
            "convertirlo a número le borraría el cero.",
            "Está incluido en el mismo plan que los reportes automáticos, sin cargo "
            "aparte.",
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
        "id": "nav_bitacora",
        "titulo": "Bitácora técnica",
        "resumen": "El pipeline del producto explicado etapa por etapa, dos veces: en "
                   "términos técnicos y en criollo. Pensada para mandarla completa a "
                   "quien tiene que aprobar la compra sin traducirla antes.",
        "pasos": [
            "Las doce etapas están en el orden en que le pasan al dato: entra, se "
            "guarda versionado, se cataloga, se puntúa la salud, se arma el grafo de "
            "dependencias, se prioriza el backlog, se evalúan políticas, se detectan "
            "problemas, opina la IA, valida una persona, sale por las tres bocas y se "
            "licencia.",
            "Cada etapa dice además POR QUÉ se hizo así —qué se rompía antes— y CÓMO "
            "REPERCUTE aguas abajo, que son las dos preguntas que un informe técnico "
            "suele dejar sin responder.",
            "Los tres botones de arriba bajan el informe completo en HTML, Word o PDF, "
            "en el idioma que tengas elegido en el selector.",
        ],
        "tips": [
            "Cada etapa nombra el archivo del repositorio que la implementa, así que "
            "sirve también como mapa para alguien que se suma al equipo.",
            "El Word es un .docx de verdad, no un HTML renombrado: se abre y se edita "
            "para agregarle lo que haga falta antes de presentarlo.",
        ],
    },
    {
        "id": "nav_config_ia",
        "titulo": "Configuración de IA",
        "resumen": "Elegir qué modelo usa cada proveedor de IA que tengas configurado, para "
                   "regular cuánto gastás en tokens. La lista sale de tu propia API.",
        "pasos": [
            "Sólo aparecen los proveedores cuya clave tengas exportada: Claude "
            "(ANTHROPIC_API_KEY), ChatGPT (OPENAI_API_KEY), Gemini (GEMINI_API_KEY), Grok "
            "(XAI_API_KEY) y Copilot / GitHub Models (GITHUB_MODELS_TOKEN).",
            "Tocá «Actualizar modelos desde mi API»: el programa le pregunta a tu proveedor "
            "qué modelos tiene habilitados TU clave, y con esa respuesta arma la lista.",
            "Elegí el modelo y guardá. Desde ese momento lo usan el Asistente IA, el "
            "Copiloto, Gobernanza y Organigrama.",
            "Si tu proveedor no lista modelos, o querés uno que no aparece, escribí el "
            "identificador a mano: lo escrito a mano le gana a lo elegido en la lista.",
        ],
        "tips": [
            "El programa no trae ninguna lista de modelos precargada, y es a propósito: los "
            "catálogos cambian todos los meses y no todas las claves tienen habilitados los "
            "mismos modelos. Una lista inventada te ofrecería modelos que tu clave no puede "
            "usar y te escondería los que sí.",
            "El modelo es la palanca principal del gasto: dentro de un mismo proveedor, el "
            "más caro y el más barato se llevan más de un orden de magnitud por token.",
            "Cada cambio queda guardado como una versión nueva por empresa, con quién lo "
            "hizo y cuándo — igual que gobernanza y organigrama. No se pisa el historial.",
            "Nada de esto afecta al motor de reglas: salud, dependencias, backlog y políticas "
            "se calculan sin IA y no gastan un token.",
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


# --------------------------------------------------------------- traducciones
# Overlays de traducción por idioma, indexados por "id" de sección. SECTIONS
# (español) es la única fuente de verdad; sections(lang) copia cada sección y
# superpone estos campos cuando lang != "es". El "id" nunca se traduce: lo usa
# test_tutorial_cubre_todas_las_secciones_del_nav para cruzar contra las
# claves nav_* de mvpm/i18n.py.

_TRANSLATIONS: dict[str, dict[str, dict]] = {
    "en": {
        "primeros_pasos": {
            "titulo": "Getting started",
            "resumen": "How to start from scratch: the admin account, your first project, and "
                       "where the rest of the team comes from.",
            "pasos": [
                "The first person to open the dashboard on a new server creates the "
                "administrator account (username and password) — nobody needs to assign it "
                "to you.",
                "The rest of the team registers themselves from the same login screen with "
                "'Create account' — they're added as members, not as admin.",
                "If the portfolio is empty, a button lets you load sample data to explore the "
                "product before loading your own — it can be deleted at any time.",
                "For your first real project: Portfolio section → 'New project'.",
            ],
            "tips": [
                "The data lives in a real database on the server where the app runs "
                "(~/.mv_project_management/datos.db) — nothing is sent anywhere by default.",
            ],
        },
        "nav_case_study": {
            "titulo": "Complete use case",
            "resumen": "A simulated project walked end to end through every tool in the "
                       "program, with real numbers from the engine — so you can see the full "
                       "flow before loading your own data.",
            "pasos": [
                "The program picks the sample project with the worst health index and walks "
                "it through Portfolio, Health, Dependencies, Backlog, Copilot and Reports, one "
                "after another.",
                "Each step shows the real result of running the engine on that project — it's "
                "not a hand-written script, it's recalculated on every visit.",
            ],
            "tips": [
                "It's the best starting point for someone who's never used the product: it "
                "shows in 6 steps the same thing the Tutorial tab explains, but applied to a "
                "concrete case.",
            ],
        },
        "nav_real_demo": {
            "titulo": "Demo with real data",
            "resumen": "The engine running on 132 real projects from the UK government's "
                       "public portfolio (open data, not simulated) — with two case studies "
                       "narrated using the real text of their annual reports.",
            "pasos": [
                "The KPIs at the top (total budget, how many are over budget) are the real "
                "result of running the catalog on the public dataset — they aren't made up.",
                "The 'estimated savings' explicitly states its assumption (minutes per manual "
                "review) instead of hiding it — so it can be questioned or adjusted, it's not "
                "a marketing figure.",
                "Both cases include the real text from the British government's annual "
                "reports on why the budget went off track or why the project went well.",
            ],
            "tips": [
                "It's proof that the engine isn't tailor-made for the sample dataset — it "
                "works just as well on public data that nobody prepared with this tool in "
                "mind.",
            ],
        },
        "nav_portfolio": {
            "titulo": "Portfolio",
            "resumen": "A single catalog of projects, with the full portfolio's KPIs at the "
                       "top.",
            "pasos": [
                "'New project' opens a guided form: name, portfolio, sponsor, owner, segment, "
                "dates, budget and criticality.",
                "'Project record' lets you pick an existing project to edit any field, archive "
                "it (it leaves the active views but isn't deleted) or delete it permanently "
                "(this also deletes its tasks).",
                "The chart by portfolio compares budget vs. actual spend, grouped.",
            ],
            "tips": [
                "A project with no owner assigned pulls down the 'scope' dimension of its "
                "health index — assign one as soon as you know, even if it's provisional.",
            ],
        },
        "nav_tasks": {
            "titulo": "Tasks",
            "resumen": "The tasks from every project, with dependencies between them.",
            "pasos": [
                "'New task' asks for the project it belongs to, title, owner, status, "
                "priority, due date and — optionally — which other task it depends on.",
                "'Task record' lets you edit the title, owner, status and priority, or delete "
                "it.",
                "Marking a task as 'blocked' makes it show up in Dependencies as an active "
                "blocker.",
            ],
            "tips": [
                "An overdue task not marked 'done' penalizes the project's 'schedule' "
                "dimension — close it or move its date, don't leave it overdue without a "
                "reason.",
            ],
        },
        "nav_health": {
            "titulo": "Project health",
            "resumen": "A 0-100 index per project, calculated across 6 measurable dimensions "
                       "— never eyeballed.",
            "pasos": [
                "Every project has an index and a status (healthy / under watch / at risk) "
                "that recalculates itself with every change.",
                "The dimension matrix shows scope, schedule, budget, risk, dependencies and "
                "team — so you can see exactly what's weighing the index down.",
            ],
            "tips": [
                "A project 'at risk' (index below 55) needs its owner to present an action "
                "plan — that's how the team's shared glossary defines it.",
            ],
        },
        "nav_dependencies": {
            "titulo": "Dependencies",
            "resumen": "Which tasks are blocking how many others, and which dependencies "
                       "point to nothing.",
            "pasos": [
                "'Active blockers' lists tasks in 'blocked' status and how many tasks depend "
                "on them — prioritize unblocking the ones with the biggest impact.",
                "'Inconsistent dependencies' detects when a task depends on another that no "
                "longer exists (for example, it was deleted without updating the dependency) "
                "— fix these from the task's record.",
            ],
            "tips": [],
        },
        "nav_backlog": {
            "titulo": "Prioritized backlog",
            "resumen": "The order in which pending tasks are worth tackling — not based on "
                       "who shouts loudest.",
            "pasos": [
                "Expected value combines project criticality × task priority × urgency from "
                "the due date × how many other tasks it unblocks.",
                "Overdue tasks automatically rise to the top — you don't need to ask for it.",
            ],
            "tips": [
                "If a low-criticality project should weigh more, raise its criticality from "
                "its record instead of reordering the backlog by hand.",
            ],
        },
        "nav_copilot": {
            "titulo": "Copilot",
            "resumen": "Natural-language questions about the portfolio, with a rules engine "
                       "that's always on and an optional AI layer.",
            "pasos": [
                "Type your question and press 'Ask' — the rules engine always answers, no "
                "configuration needed.",
                "If ANTHROPIC_API_KEY is configured and your plan still has AI quota left, the "
                "answer gets polished by Claude without inventing new figures — it never "
                "replaces the engine.",
            ],
            "tips": [
                "The AI quota depends on your plan (see 'AI credit license and plan' below); "
                "the rules engine has no limit on any plan, including the demo.",
            ],
        },
        "nav_advisor": {
            "titulo": "AI Assistant",
            "resumen": "The rules engine detects portfolio problems (blockers, orphaned "
                       "dependencies, at-risk projects, budget overruns, overload, unmet "
                       "policies) and suggests an action — with persisted follow-up.",
            "pasos": [
                "Choose who drafts the suggestion: the rules engine alone, or an AI provider "
                "(Claude, ChatGPT or Gemini) — only the ones with a configured key show up.",
                "Each detected problem shows a concrete suggestion; 'Add to follow-up' saves "
                "it to the database with 'open' status.",
                "From the same problem you can move the follow-up to 'in progress' or "
                "'resolved' — it stays in the Follow-ups table even if the original problem is "
                "no longer detected.",
            ],
            "tips": [
                "The rules engine never depends on AI — if you don't configure any key, the "
                "assistant keeps detecting and suggesting all the same, just without the "
                "polished wording.",
                "ChatGPT and Gemini also need `OPENAI_MODEL` / `GEMINI_MODEL` in the "
                "environment — that way a model is never assumed on your behalf.",
            ],
        },
        "nav_reports": {
            "titulo": "Reports",
            "resumen": "An executive text report ready to copy, plus a full export of the "
                       "portfolio.",
            "pasos": [
                "The text report summarizes the real state of the portfolio — ready to paste "
                "into an email or a team channel.",
                "'Download JSON' and 'Download Excel' export exactly the real data you see in "
                "the dashboard at that moment (projects, tasks, team, health, backlog and "
                "policies).",
            ],
            "tips": [
                "The local REST API (api/main.py) serves the same data live so you can connect "
                "Power BI, Tableau or Looker — no need to export by hand every time.",
            ],
        },
        "nav_reviews": {
            "titulo": "Reviews",
            "resumen": "Real customer ratings — never invented testimonials.",
            "pasos": [
                "Until there are verified reviews, the section shows the real state ('program "
                "in beta'), not marketing copy.",
                "Anyone can leave a review from here — it stays pending verification before "
                "it's published.",
            ],
            "tips": [],
        },
        "nav_glossary": {
            "titulo": "Glossary",
            "resumen": "What each status means, the same for the whole team — no ambiguity.",
            "pasos": [
                "Check it before arguing over whether something 'is at risk' or 'is blocked' "
                "— the definition is already agreed here, no need to reinvent it in every "
                "meeting.",
            ],
            "tips": [],
        },
        "nav_policies": {
            "titulo": "Policies",
            "resumen": "Operational management rules, verified against real evidence from the "
                       "portfolio.",
            "pasos": [
                "Each policy shows whether it's met (✅) or not (⚠️) along with the concrete "
                "evidence behind it — it's not an opinion, it's a check against the real data.",
                "Below, the automation matrix clarifies what resolves itself, what needs a "
                "human nudge, and what's purely human (with suggested scripts by role).",
            ],
            "tips": [],
        },
        "nav_pmbok": {
            "titulo": "PMBOK Methodology",
            "resumen": "The PMBOK (the PMI guide) in two registers: technical (the way a PMP "
                       "would say it) and in plain language (everyday terms), covering the 10 "
                       "knowledge areas and the 5 process groups.",
            "pasos": [
                "In 'knowledge areas', each area has its technical definition and its "
                "plain-language version, plus how much the product covers it (full / partial "
                "/ not covered), without inflating anything.",
                "In 'process groups' you'll find the life cycle (Initiation → Planning → "
                "Execution → Monitoring → Closing), also technical + plain-language.",
                "Each area allows an internal note from your company (something that isn't "
                "automated) that's edited by hand and stays versioned, with who validated it.",
            ],
            "tips": [
                "It's not an official PMI certification, it's a reference for teams that "
                "already work with that guide and want to know what the tool is built on.",
            ],
        },
        "nav_governance": {
            "titulo": "Data governance",
            "resumen": "Every management concept comes with a preset definition; AI "
                       "recommends an improvement and the Data Owner / Data Steward validates "
                       "or edits it and saves it, versioned by company.",
            "pasos": [
                "The definition never shows up blank: it comes preset out of the box, or "
                "polished by AI if you have a provider configured.",
                "The person responsible (Data Owner) validates or edits it and saves it with "
                "their name and title — every change is a new version, the previous one is "
                "never overwritten.",
                "Everything is saved per company (you choose the active company in the "
                "sidebar), so each organization has its own history of definitions.",
            ],
            "tips": [
                "It's the same criterion as MV Data Governance: the current definition is the "
                "latest validated version; if it was never touched, the factory default "
                "applies.",
            ],
        },
        "nav_organigrama": {
            "titulo": "Org chart and owners",
            "resumen": "Upload the org chart (Excel/CSV or a SQLite database) and AI "
                       "auto-fills, by default, who's responsible for each stage of the "
                       "project — editable and versioned.",
            "pasos": [
                "Upload the org chart; it recognizes common columns (name, title, area, "
                "reports to) without requiring an exact format.",
                "For each stage (the PMBOK's 5 process groups) a pre-recommended owner "
                "appears based on their title — you validate or change it and it's saved.",
                "If the org chart is a photo, you'll need an AI provider with vision; without "
                "that, export it to Excel/CSV and upload it instead.",
            ],
            "tips": [
                "The validated owners per stage also show up in the PMBOK tab, in each "
                "process group.",
            ],
        },
        "nav_pharma": {
            "titulo": "Pharma lab demo",
            "resumen": "The engine running on 474 real clinical trials from three "
                       "multinational pharmaceutical companies (AstraZeneca, Pfizer, "
                       "Novartis), end to end through Power BI.",
            "pasos": [
                "Each trial is a project: sponsor (the lab), dates, phase and status. The "
                "engine derives criticality from the real status (completed/suspended = at "
                "risk).",
                "The charts by status and by lab, and the list of at-risk trials, come from "
                "running the engine on the real data — there are no invented figures (the "
                "source doesn't publish budget, and that's stated).",
                "From the same tab you can download the table ready for BI and follow the "
                "guide to connect Power BI to the local API with one click (.pbids).",
            ],
            "tips": [
                "Source: ClinicalTrials.gov (U.S. National Library of Medicine), public "
                "domain.",
            ],
        },
        "nav_plantillas": {
            "titulo": "Industry templates",
            "resumen": "Governance ready for the client's industry — stages with exit gates, "
                       "who approves, typical risks and regulations — so you don't start from "
                       "a blank page on every implementation.",
            "pasos": [
                "Pick the industry and walk through the stages: each one states what "
                "deliverables it requires, the criteria for moving to the next one, and who "
                "signs off.",
                "Check the roles and risks tab: the risk register starts populated with the "
                "ones typical of that industry instead of empty, each one tied to its PMBOK "
                "area.",
                "Adopt it from the 'Adopt' tab, with the name of who validates it. It's "
                "versioned: switching templates later doesn't erase the history.",
                "Edit it with your own people. It ships as a starting point to discuss, not "
                "to apply as-is.",
            ],
            "tips": [
                "The regulatory references are indicative and taken from Uruguay unless "
                "stated otherwise. Confirm them with quality, legal or compliance: they "
                "change, and every company interprets them its own way.",
                "An industry having PMBOK areas marked as critical points to where to put the "
                "effort, not which areas to ignore. All ten always apply.",
                "You can download the full governance document in Markdown to bring it "
                "printed to the kickoff meeting.",
            ],
        },
        "nav_conectores": {
            "titulo": "ERP connectors",
            "resumen": "Pull projects and tasks straight from SAP, Oracle, Dynamics or JD "
                       "Edwards, without exporting to Excel first. Always read-only.",
            "pasos": [
                "Choose the family and the system. Each profile comes with that ERP's default "
                "tables and fields and explains how to connect.",
                "Probe before extracting. The probe checks that the tables and columns exist "
                "and tells you exactly which ones are missing, instead of throwing you a raw "
                "engine error.",
                "If a column is missing, edit the query with that installation's real names. "
                "That's normal in an ERP with years of history behind it.",
                "Pull the data and review it: what gets extracted goes through the same "
                "preview report as a manually uploaded file, with duplicates and discarded "
                "rows.",
            ],
            "tips": [
                "The connectors are read-only and the system rejects any query that isn't a "
                "SELECT. Even so, connect with a read-only user: that's the real protection, "
                "the software's lock is the second line of defense.",
                "Odd conversions are the most common source of silent errors: JD Edwards "
                "stores dates in Julian format (124001 is 1/1/2024), SAP as YYYYMMDD text, "
                "and Dynamics uses 1900-01-01 as 'no date'.",
                "Cross-check a couple of dates and amounts against the ERP before signing off "
                "on a load. In JD Edwards, amounts come with implied decimals, and how many "
                "depends on each installation.",
                "If the ERP is in the cloud (Oracle Fusion, D365 SaaS) there's usually no "
                "direct database access: you export and import the file instead.",
            ],
        },
        "nav_data_eng": {
            "titulo": "Data engineering",
            "resumen": "Profile any table — not just projects and tasks — before importing it "
                       "or connecting it to an ERP: nulls, duplicates, outliers, the candidate "
                       "primary key and a starting CREATE TABLE.",
            "pasos": [
                "Choose the source: a CSV/Excel file with any schema, or a SQL database with "
                "your own SELECT query.",
                "Check the quality score and the list of issues: each one comes with the "
                "concrete action to fix it, not just the diagnosis.",
                "Review the candidate primary key and, if there's a date column, the time "
                "coverage — how far back the data goes and which days are missing.",
                "Download the suggested CREATE TABLE or the full report in Excel to share "
                "with whoever's going to design the database or review the file.",
            ],
            "tips": [
                "The SQL connection is read-only and the connection string is never saved "
                "anywhere: it lives only in the browser session.",
                "An ID with leading zeros ('007') is deliberately kept as text: converting it "
                "to a number would erase the zero.",
                "It's included in the same plan as the automated reports, at no extra charge.",
            ],
        },
        "nav_capacitacion": {
            "titulo": "Role-based training",
            "resumen": "Curriculum, recording script and verification questions for each "
                       "role, so you record once and stop repeating the same live session on "
                       "every implementation.",
            "pasos": [
                "Choose the role: sponsor, PM, member, PMO, administrator or data steward. "
                "Each one has its own path and duration.",
                "Each module comes with the recording script, the practice exercise the "
                "person does after watching, and the questions that confirm they can work on "
                "their own.",
                "Use the verification tab as a checklist when closing out the training.",
                "The recording plan lists every module without repeats: one that serves "
                "several roles gets recorded only once.",
            ],
            "tips": [
                "The sponsor's curriculum runs fifteen minutes on purpose. A sponsor won't "
                "watch an hour of video, and if you demand it, they won't watch anything.",
                "The verification questions are what makes it possible for the training to "
                "fail. A training that can't fail is useless for knowing whether anyone "
                "actually learned.",
                "The PMO starts with the PM's path, and the data steward with the "
                "administrator's: the app shows the prerequisites for each role.",
            ],
        },
        "nav_config_ia": {
            "titulo": "AI configuration",
            "resumen": "Choose which model each AI provider you've configured uses, to "
                       "control how much you spend on tokens. The list comes from your own "
                       "API.",
            "pasos": [
                "Only the providers whose key you've exported show up: Claude "
                "(ANTHROPIC_API_KEY), ChatGPT (OPENAI_API_KEY), Gemini (GEMINI_API_KEY), Grok "
                "(XAI_API_KEY) and Copilot / GitHub Models (GITHUB_MODELS_TOKEN).",
                "Tap 'Update models from my API': the program asks your provider which models "
                "YOUR key has enabled, and builds the list from that response.",
                "Pick the model and save. From then on, it's used by the AI Assistant, "
                "Copilot, Governance and Org Chart.",
                "If your provider doesn't list models, or you want one that isn't shown, type "
                "the identifier by hand: what's typed by hand wins over what's picked from "
                "the list.",
            ],
            "tips": [
                "The program doesn't ship with any preloaded model list, and that's on "
                "purpose: catalogs change every month and not every key has the same models "
                "enabled. A made-up list would offer you models your key can't use and hide "
                "the ones it can.",
                "The model is the main lever on spend: within the same provider, the most "
                "expensive and the cheapest can differ by more than an order of magnitude per "
                "token.",
                "Every change is saved as a new version per company, with who made it and "
                "when — just like governance and the org chart. History is never overwritten.",
                "None of this affects the rules engine: health, dependencies, backlog and "
                "policies are calculated without AI and don't spend a single token.",
            ],
        },
        "nav_import": {
            "titulo": "Import data",
            "resumen": "Upload projects or tasks from your CSV/Excel just as you have it — no "
                       "need to prep the file beforehand. They're actually loaded into the "
                       "database.",
            "pasos": [
                "Upload the file as-is. The system detects on its own which field each column "
                "corresponds to, even if it's called 'Project Name', 'Owning Area' or 'Total "
                "Amount'.",
                "Review the proposed mapping and fix whatever's needed using the dropdown "
                "lists. A green checkmark is an exact match; a yellow one is a guess.",
                "Check the preview report: how many rows will be created, how many will be "
                "discarded and why. Nothing is written until you confirm.",
                "Only then click Import.",
            ],
            "tips": [
                "It translates the values on its own: 'In progress' stays in progress, "
                "'URGENT' → High, '$ 1,234,567' → 1234567, '01/03/2026' → March 1st.",
                "Tasks are matched to their project by name, and the owner is looked up by "
                "name or email against the loaded team.",
                "It detects repeated rows and ones that already exist in the system, so you "
                "can re-import the same file without duplicating anything.",
                "If you don't have a file, download the template from the same screen.",
            ],
        },
        "nav_users": {
            "titulo": "Users",
            "resumen": "Who has an account on this server — visible only to administrators.",
            "pasos": [
                "To add someone to the team, have them register from the login screen with "
                "'Create account' — an admin doesn't need to create it by hand.",
            ],
            "tips": [],
        },
        "licencia_ia": {
            "titulo": "AI credit license and plan",
            "resumen": "How to activate the copilot's AI quota after purchasing a plan.",
            "pasos": [
                "When you pay for the Professional or Enterprise plan through MercadoPago, a "
                "license token is issued automatically.",
                "Paste it into the 'License token' field in the sidebar — without a token, "
                "the product keeps working in full on the demo plan, only the monthly AI "
                "quota changes.",
            ],
            "tips": [
                "The rules engine (catalog, health, dependencies, backlog, policies) never "
                "depends on the token — it works the same on any plan.",
            ],
        },
    },
    "pt": {
        "primeros_pasos": {
            "titulo": "Primeiros passos",
            "resumen": "Como começar do zero: conta de administrador, primeiro projeto e de "
                       "onde vem o restante da equipe.",
            "pasos": [
                "A primeira pessoa que abre o dashboard em um servidor novo cria a conta de "
                "administrador (usuário e senha) — não é preciso que ninguém a atribua a "
                "você.",
                "O restante da equipe se cadastra sozinho, na mesma tela de login, com "
                "'Criar conta' — eles ficam como membros, não como admin.",
                "Se o portfólio estiver vazio, um botão permite carregar dados de exemplo "
                "para explorar o produto antes de carregar os seus — podem ser apagados a "
                "qualquer momento.",
                "Para o seu primeiro projeto real: seção Portfólio → 'Novo projeto'.",
            ],
            "tips": [
                "Os dados ficam em um banco real no servidor onde o app roda "
                "(~/.mv_project_management/datos.db) — nada é enviado para lugar nenhum por "
                "padrão.",
            ],
        },
        "nav_case_study": {
            "titulo": "Caso de uso completo",
            "resumen": "Um projeto simulado percorrido de ponta a ponta por todas as "
                       "ferramentas do programa, com os números reais do motor — para ver o "
                       "fluxo completo antes de carregar seus próprios dados.",
            "pasos": [
                "O programa escolhe o projeto de exemplo com o pior índice de saúde e o "
                "percorre por Portfólio, Saúde, Dependências, Backlog, Copiloto e Relatórios, "
                "um atrás do outro.",
                "Cada passo mostra o resultado real de rodar o motor sobre esse projeto — não "
                "é um roteiro escrito à mão, é recalculado a cada visita.",
            ],
            "tips": [
                "É o melhor ponto de partida para quem nunca usou o produto: mostra em 6 "
                "passos o mesmo que a aba Tutorial explica, mas aplicado a um caso concreto.",
            ],
        },
        "nav_real_demo": {
            "titulo": "Demo com dados reais",
            "resumen": "O motor rodando sobre 132 projetos reais do portfólio público do "
                       "Reino Unido (dados abertos, não simulados) — com dois casos narrados "
                       "com o texto real de seus relatórios anuais.",
            "pasos": [
                "Os KPIs no topo (orçamento total, quantos estão acima do orçamento) são o "
                "resultado real de rodar o catálogo sobre o dataset público — não são "
                "inventados.",
                "A 'economia estimada' declara explicitamente sua premissa (minutos por "
                "revisão manual) em vez de escondê-la — assim pode ser questionada ou "
                "ajustada, não é um número de marketing.",
                "Os dois casos incluem o texto real dos relatórios anuais do governo "
                "britânico sobre por que o orçamento se desviou ou por que o projeto deu "
                "certo.",
            ],
            "tips": [
                "É a prova de que o motor não foi feito sob medida para o dataset de exemplo "
                "— funciona igual sobre dados públicos que ninguém preparou pensando nesta "
                "ferramenta.",
            ],
        },
        "nav_portfolio": {
            "titulo": "Portfólio",
            "resumen": "Catálogo único de projetos, com os KPIs do portfólio completo no "
                       "topo.",
            "pasos": [
                "'Novo projeto' abre um formulário guiado: nome, portfólio, patrocinador, "
                "dono, segmento, datas, orçamento e criticidade.",
                "'Ficha do projeto' permite escolher um projeto existente para editar "
                "qualquer campo, arquivá-lo (sai das visualizações ativas, mas não é apagado) "
                "ou excluí-lo definitivamente (também apaga suas tarefas).",
                "O gráfico por portfólio compara orçamento vs. executado agrupado.",
            ],
            "tips": [
                "Um projeto sem dono atribuído derruba a dimensão 'escopo' do seu índice de "
                "saúde — atribua um assim que souber, mesmo que seja provisório.",
            ],
        },
        "nav_tasks": {
            "titulo": "Tarefas",
            "resumen": "As tarefas de todos os projetos, com dependências entre elas.",
            "pasos": [
                "'Nova tarefa' pede o projeto a que pertence, título, responsável, status, "
                "prioridade, vencimento e — opcional — de qual outra tarefa depende.",
                "'Ficha da tarefa' permite editar título, responsável, status e prioridade, "
                "ou excluí-la.",
                "Marcar uma tarefa como 'blocked' faz com que ela apareça em Dependências "
                "como um bloqueio ativo.",
            ],
            "tips": [
                "Uma tarefa vencida e não marcada como 'done' penaliza a dimensão "
                "'cronograma' do projeto — feche-a ou mude a data, não a deixe vencida sem "
                "motivo.",
            ],
        },
        "nav_health": {
            "titulo": "Saúde do projeto",
            "resumen": "Índice de 0 a 100 por projeto, calculado em 6 dimensões mensuráveis "
                       "— nunca no olhômetro.",
            "pasos": [
                "Cada projeto tem um índice e um status (saudável / em observação / em "
                "risco) que se recalcula sozinho a cada mudança.",
                "A matriz por dimensão mostra escopo, cronograma, orçamento, risco, "
                "dependências e equipe — para ver exatamente o que está pesando no índice.",
            ],
            "tips": [
                "Um projeto 'em risco' (índice < 55) exige que o dono apresente um plano de "
                "ação — é assim que o glossário compartilhado da equipe define.",
            ],
        },
        "nav_dependencies": {
            "titulo": "Dependências",
            "resumen": "Quais tarefas estão bloqueando quantas outras, e quais dependências "
                       "apontam para nada.",
            "pasos": [
                "'Bloqueios ativos' lista tarefas em status 'blocked' e quantas tarefas "
                "dependem delas — priorize desbloquear as que mais impactam.",
                "'Dependências inconsistentes' detecta quando uma tarefa depende de outra "
                "que não existe mais (por exemplo, foi apagada sem atualizar a dependência) "
                "— corrija-as pela ficha da tarefa.",
            ],
            "tips": [],
        },
        "nav_backlog": {
            "titulo": "Backlog priorizado",
            "resumen": "A ordem em que vale a pena atacar as tarefas pendentes, não por quem "
                       "grita mais alto.",
            "pasos": [
                "O valor esperado combina criticidade do projeto × prioridade da tarefa × "
                "urgência pelo vencimento × quantas outras tarefas ela destrava.",
                "Tarefas vencidas sobem automaticamente para o topo — não é preciso pedir.",
            ],
            "tips": [
                "Se um projeto de baixa criticidade deveria pesar mais, aumente a "
                "criticidade pela ficha dele em vez de reordenar o backlog manualmente.",
            ],
        },
        "nav_copilot": {
            "titulo": "Copiloto",
            "resumen": "Perguntas em linguagem natural sobre o portfólio, com motor de "
                       "regras sempre ativo e uma camada opcional de IA.",
            "pasos": [
                "Digite a pergunta e clique em 'Perguntar' — o motor de regras sempre "
                "responde, sem precisar de configuração.",
                "Se houver ANTHROPIC_API_KEY configurada e ainda restar cota de IA no seu "
                "plano, a resposta é aprimorada com o Claude sem inventar números novos — "
                "nunca substitui o motor.",
            ],
            "tips": [
                "A cota de IA depende do plano (veja 'licença e plano de créditos de IA' "
                "mais abaixo); o motor de regras não tem limite em nenhum plano, incluindo o "
                "demo.",
            ],
        },
        "nav_advisor": {
            "titulo": "Assistente de IA",
            "resumen": "O motor de regras detecta problemas do portfólio (bloqueios, "
                       "dependências órfãs, projetos em risco, estouro de orçamento, "
                       "sobrecarga, políticas não cumpridas) e sugere uma ação — com "
                       "acompanhamento persistido.",
            "pasos": [
                "Escolha quem redige a sugestão: só o motor de regras, ou um provedor de IA "
                "(Claude, ChatGPT ou Gemini) — só aparecem os que tiverem a chave "
                "configurada.",
                "Cada problema detectado mostra uma sugestão concreta; 'Colocar em "
                "acompanhamento' a salva no banco com status 'aberto'.",
                "A partir do mesmo problema, você pode mover o acompanhamento para "
                "'em_andamento' ou 'resolvido' — ele permanece na tabela de Acompanhamentos "
                "mesmo que o problema original deixe de ser detectado.",
            ],
            "tips": [
                "O motor de regras nunca depende de IA — se você não configurar nenhuma "
                "chave, o assistente continua detectando e sugerindo do mesmo jeito, só sem "
                "o texto refinado.",
                "ChatGPT e Gemini também precisam de `OPENAI_MODEL` / `GEMINI_MODEL` no "
                "ambiente — assim nenhum modelo é presumido por você.",
            ],
        },
        "nav_reports": {
            "titulo": "Relatórios",
            "resumen": "Relatório executivo em texto pronto para copiar, e exportação "
                       "completa do portfólio.",
            "pasos": [
                "O relatório em texto resume o estado real do portfólio — para colar em um "
                "e-mail ou canal da equipe.",
                "'Baixar JSON' e 'Baixar Excel' exportam exatamente os dados reais que você "
                "vê no dashboard naquele momento (projetos, tarefas, equipe, saúde, backlog "
                "e políticas).",
            ],
            "tips": [
                "A API REST local (api/main.py) serve os mesmos dados ao vivo para conectar "
                "Power BI, Tableau ou Looker — não é preciso exportar manualmente todas as "
                "vezes.",
            ],
        },
        "nav_reviews": {
            "titulo": "Avaliações",
            "resumen": "Avaliação real de clientes — nunca depoimentos inventados.",
            "pasos": [
                "Enquanto não houver avaliações verificadas, a seção mostra o estado real "
                "('programa em fase beta'), não marketing.",
                "Qualquer pessoa pode deixar uma avaliação por aqui — ela fica pendente de "
                "verificação antes de ser publicada.",
            ],
            "tips": [],
        },
        "nav_glossary": {
            "titulo": "Glossário",
            "resumen": "O que significa cada status, igual para toda a equipe — sem "
                       "ambiguidade.",
            "pasos": [
                "Consulte antes de discutir se algo 'está em risco' ou 'está bloqueado' — a "
                "definição já está combinada aqui, não é preciso reinventá-la em cada "
                "reunião.",
            ],
            "tips": [],
        },
        "nav_policies": {
            "titulo": "Políticas",
            "resumen": "Regras operacionais de gestão, verificadas contra evidências reais "
                       "do portfólio.",
            "pasos": [
                "Cada política mostra se é cumprida (✅) ou não (⚠️) com a evidência concreta "
                "que a sustenta — não é uma opinião, é uma verificação sobre o dado real.",
                "Abaixo, a matriz de automação esclarece o que se resolve sozinho, o que "
                "precisa de um empurrão humano, e o que é puramente humano (com roteiros "
                "sugeridos por função).",
            ],
            "tips": [],
        },
        "nav_pmbok": {
            "titulo": "Metodologia PMBOK",
            "resumen": "O PMBOK (guia do PMI) em dois registros: técnico (como um PMP "
                       "diria) e em linguagem simples (português do dia a dia), com as 10 "
                       "áreas de conhecimento e os 5 grupos de processos.",
            "pasos": [
                "Em 'áreas de conhecimento', cada área tem sua definição técnica e sua "
                "versão em linguagem simples, além de quanto o produto cobre dela (completa "
                "/ parcial / não coberta), sem inflar nada.",
                "Em 'grupos de processos' está o ciclo de vida (Início → Planejamento → "
                "Execução → Monitoramento → Encerramento), também técnico + linguagem "
                "simples.",
                "Cada área admite uma nota interna da sua empresa (algo que não é "
                "automatizado) que é editada manualmente e fica versionada, com quem a "
                "validou.",
            ],
            "tips": [
                "Não é uma certificação oficial do PMI, é uma referência para equipes que já "
                "trabalham com esse guia e querem saber em que a ferramenta se apoia.",
            ],
        },
        "nav_governance": {
            "titulo": "Governança de dados",
            "resumen": "Cada conceito de gestão já vem com uma definição pré-estabelecida; "
                       "a IA recomenda uma melhoria e o Data Owner / Data Steward a valida "
                       "ou edita e salva, versionada por empresa.",
            "pasos": [
                "A definição nunca aparece em branco: sai pré-estabelecida de fábrica, ou "
                "aprimorada pela IA se você tiver um provedor configurado.",
                "O responsável (Data Owner) a valida ou edita e a salva com seu nome e "
                "cargo — cada mudança é uma versão nova, a anterior nunca é sobrescrita.",
                "Tudo é salvo por empresa (você escolhe a empresa ativa na barra lateral), "
                "assim cada organização tem seu próprio histórico de definições.",
            ],
            "tips": [
                "É o mesmo critério do MV Data Governance: a definição vigente é a última "
                "versão validada; se nunca foi alterada, vale a de fábrica.",
            ],
        },
        "nav_organigrama": {
            "titulo": "Organograma e responsáveis",
            "resumen": "Você carrega o organograma (Excel/CSV ou banco SQLite) e a IA "
                       "preenche automaticamente, por padrão, quem é responsável por cada "
                       "etapa do projeto, editável e versionado.",
            "pasos": [
                "Envie o organograma; ele reconhece colunas comuns (nome, cargo, área, "
                "reporta a) sem exigir um formato exato.",
                "Para cada etapa (os 5 grupos de processos do PMBOK) aparece um responsável "
                "pré-recomendado conforme o cargo — você valida ou muda e fica salvo.",
                "Se o organograma for uma foto, é preciso um provedor de IA com visão; sem "
                "isso, exporte para Excel/CSV e envie.",
            ],
            "tips": [
                "Os responsáveis validados por etapa também aparecem na aba PMBOK, em cada "
                "grupo de processos.",
            ],
        },
        "nav_pharma": {
            "titulo": "Demo laboratório (Pharma)",
            "resumen": "O motor rodando sobre 474 ensaios clínicos reais de três "
                       "laboratórios multinacionais (AstraZeneca, Pfizer, Novartis), de "
                       "ponta a ponta até o Power BI.",
            "pasos": [
                "Cada ensaio é um projeto: patrocinador (o laboratório), datas, fase e "
                "status. O motor deriva a criticidade do status real (concluído/suspenso = "
                "em risco).",
                "Os gráficos por status e por laboratório, e a lista de ensaios em risco, "
                "vêm de rodar o motor sobre o dado real — não há números inventados (a fonte "
                "não publica orçamento, e isso é informado).",
                "Na mesma aba você baixa a tabela pronta para BI e segue o guia para "
                "conectar o Power BI à API local com um clique (.pbids).",
            ],
            "tips": [
                "Fonte: ClinicalTrials.gov (U.S. National Library of Medicine), domínio "
                "público.",
            ],
        },
        "nav_plantillas": {
            "titulo": "Modelos por setor",
            "resumen": "Governança pronta para o setor do cliente — etapas com portão de "
                       "saída, quem aprova, riscos típicos e normas — para não começar do "
                       "zero em cada implementação.",
            "pasos": [
                "Escolha o setor e percorra as etapas: cada uma diz quais entregáveis "
                "exige, qual é o critério para passar para a próxima, e quem assina.",
                "Veja a aba de funções e riscos: o registro de riscos já começa com os "
                "típicos do setor em vez de vazio, cada um vinculado à sua área do PMBOK.",
                "Adote-o pela aba «Adotar», com o nome de quem o valida. Fica versionado: "
                "trocar de modelo mais tarde não apaga o histórico.",
                "Edite com o pessoal da casa. Sai de fábrica para ser discutido, não para "
                "ser aplicado tal como está.",
            ],
            "tips": [
                "As referências normativas são orientativas e tomadas do Uruguai, salvo "
                "indicação em contrário. É preciso confirmá-las com qualidade, jurídico ou "
                "compliance: elas mudam, e cada empresa as interpreta à sua maneira.",
                "Um setor ter áreas do PMBOK marcadas como críticas indica onde colocar o "
                "esforço, não quais áreas ignorar. As dez sempre se aplicam.",
                "É possível baixar a governança completa em Markdown para levá-la impressa "
                "à reunião de início.",
            ],
        },
        "nav_conectores": {
            "titulo": "Conectores ERP",
            "resumen": "Traga projetos e tarefas direto do SAP, Oracle, Dynamics ou JD "
                       "Edwards, sem exportar para Excel antes. Sempre somente leitura.",
            "pasos": [
                "Escolha a família e o sistema. Cada perfil traz as tabelas e campos de "
                "fábrica daquele ERP e explica como se conectar.",
                "Sonde antes de extrair. A sondagem verifica se as tabelas e colunas "
                "existem e diz exatamente quais estão faltando, em vez de jogar um erro do "
                "motor.",
                "Se faltar alguma coluna, edite a consulta com os nomes reais daquela "
                "instalação. É normal em um ERP com anos de uso.",
                "Traga os dados e revise-os: o que é extraído passa pelo mesmo relatório "
                "prévio de um arquivo enviado manualmente, com duplicados e linhas "
                "descartadas.",
            ],
            "tips": [
                "Os conectores são somente leitura e o sistema rejeita qualquer consulta que "
                "não seja um SELECT. Mesmo assim, conecte-se com um usuário somente leitura: "
                "essa é a proteção de verdade, o cadeado do software é a segunda linha.",
                "As conversões estranhas são a fonte mais comum de erros silenciosos: o JD "
                "Edwards guarda as datas em Julian (124001 é 1/1/2024), o SAP como texto "
                "YYYYMMDD, e o Dynamics usa 1900-01-01 como «sem data».",
                "Confira algumas datas e valores contra o ERP antes de aprovar uma carga. No "
                "JD Edwards os valores vêm com decimais implícitos, e a quantidade depende "
                "de cada instalação.",
                "Se o ERP está na nuvem (Oracle Fusion, D365 em SaaS) normalmente não há "
                "acesso direto ao banco: exporta-se e importa-se o arquivo.",
            ],
        },
        "nav_data_eng": {
            "titulo": "Engenharia de dados",
            "resumen": "Analise o perfil de qualquer tabela — não só projetos e tarefas — "
                       "antes de importá-la ou conectá-la a um ERP: nulos, duplicados, "
                       "outliers, a chave primária candidata e um CREATE TABLE inicial.",
            "pasos": [
                "Escolha a origem: um arquivo CSV/Excel de qualquer esquema, ou um banco "
                "SQL com sua própria consulta SELECT.",
                "Veja o score de qualidade e a lista de problemas: cada um traz a ação "
                "concreta para resolvê-lo, não só o diagnóstico.",
                "Revise a chave primária candidata e, se houver uma coluna de data, a "
                "cobertura temporal — desde quando há dados e quais dias faltam.",
                "Baixe o CREATE TABLE sugerido ou o relatório completo em Excel para "
                "compartilhar com quem for projetar o banco ou revisar o arquivo.",
            ],
            "tips": [
                "A conexão SQL é somente leitura e a string de conexão não é salva em "
                "nenhum lugar: vive apenas na sessão do navegador.",
                "Um ID com zeros à esquerda («007») é deixado como texto de propósito: "
                "convertê-lo em número apagaria o zero.",
                "Está incluído no mesmo plano dos relatórios automáticos, sem custo à "
                "parte.",
            ],
        },
        "nav_capacitacion": {
            "titulo": "Capacitação por função",
            "resumen": "Currículo, roteiro de gravação e perguntas de verificação para cada "
                       "função, para gravar uma vez e parar de repetir a mesma sessão ao "
                       "vivo em cada implementação.",
            "pasos": [
                "Escolha a função: patrocinador, PM, membro, PMO, administrador ou "
                "referente de dados. Cada uma tem seu próprio percurso e duração.",
                "Cada módulo traz o roteiro para gravar, a prática que a pessoa faz depois "
                "de assistir, e as perguntas que confirmam que ela consegue trabalhar "
                "sozinha.",
                "Use a aba de verificação como checklist ao encerrar a capacitação.",
                "O plano de gravação lista todos os módulos sem repetição: um que serve a "
                "várias funções é gravado uma única vez.",
            ],
            "tips": [
                "O currículo do patrocinador dura quinze minutos de propósito. Um "
                "patrocinador não assiste uma hora de vídeo, e se for exigido, não assiste "
                "nada.",
                "As perguntas de verificação são o que torna possível a capacitação falhar. "
                "Uma capacitação que não pode falhar não serve para saber se alguém "
                "aprendeu.",
                "O PMO começa pelo percurso do PM, e o referente de dados pelo do "
                "administrador: o app mostra os pré-requisitos de cada função.",
            ],
        },
        "nav_config_ia": {
            "titulo": "Configuração de IA",
            "resumen": "Escolha qual modelo cada provedor de IA configurado usa, para "
                       "controlar quanto você gasta em tokens. A lista vem da sua própria "
                       "API.",
            "pasos": [
                "Só aparecem os provedores cuja chave você exportou: Claude "
                "(ANTHROPIC_API_KEY), ChatGPT (OPENAI_API_KEY), Gemini (GEMINI_API_KEY), "
                "Grok (XAI_API_KEY) e Copilot / GitHub Models (GITHUB_MODELS_TOKEN).",
                "Toque em «Atualizar modelos da minha API»: o programa pergunta ao seu "
                "provedor quais modelos a SUA chave tem habilitados, e monta a lista com "
                "essa resposta.",
                "Escolha o modelo e salve. A partir daí ele é usado pelo Assistente de IA, "
                "Copiloto, Governança e Organograma.",
                "Se o seu provedor não listar modelos, ou você quiser um que não aparece, "
                "digite o identificador manualmente: o que é digitado manualmente prevalece "
                "sobre o escolhido na lista.",
            ],
            "tips": [
                "O programa não traz nenhuma lista de modelos pré-carregada, e isso é de "
                "propósito: os catálogos mudam todo mês e nem toda chave tem os mesmos "
                "modelos habilitados. Uma lista inventada ofereceria modelos que sua chave "
                "não pode usar e esconderia os que pode.",
                "O modelo é a principal alavanca de gasto: dentro do mesmo provedor, o mais "
                "caro e o mais barato podem ter mais de uma ordem de grandeza de diferença "
                "por token.",
                "Cada mudança fica salva como uma versão nova por empresa, com quem fez e "
                "quando — igual à governança e ao organograma. O histórico nunca é "
                "sobrescrito.",
                "Nada disso afeta o motor de regras: saúde, dependências, backlog e "
                "políticas são calculados sem IA e não gastam nenhum token.",
            ],
        },
        "nav_import": {
            "titulo": "Importar dados",
            "resumen": "Suba projetos ou tarefas do seu CSV/Excel do jeito que está — sem "
                       "precisar preparar o arquivo antes. Eles são realmente carregados no "
                       "banco.",
            "pasos": [
                "Envie o arquivo como está. O sistema detecta sozinho a qual campo cada "
                "coluna corresponde, mesmo que se chame «Nome do Projeto», «Área "
                "Responsável» ou «Valor Total».",
                "Revise o mapeamento proposto e corrija o que for preciso com as listas "
                "suspensas. O visto verde é uma correspondência exata; o amarelo é uma "
                "suposição.",
                "Veja o relatório prévio: quantas linhas são criadas, quantas são "
                "descartadas e por quê. Nada é gravado até você confirmar.",
                "Só então clique em Importar.",
            ],
            "tips": [
                "Traduz os valores sozinho: «Em andamento» → em andamento, «URGENTE» → "
                "Alta, «R$ 1.234.567» → 1234567, «01/03/2026» → 1º de março.",
                "As tarefas são associadas ao projeto pelo nome, e o responsável é buscado "
                "por nome ou e-mail na equipe já carregada.",
                "Detecta linhas repetidas e as que já existem no sistema, assim você pode "
                "reimportar o mesmo arquivo sem duplicar nada.",
                "Se você não tiver um arquivo, baixe o modelo na mesma tela.",
            ],
        },
        "nav_users": {
            "titulo": "Usuários",
            "resumen": "Quem tem conta neste servidor — visível apenas para "
                       "administradores.",
            "pasos": [
                "Para adicionar alguém da equipe, peça que se cadastre na tela de login com "
                "'Criar conta' — não é preciso que um admin a crie manualmente.",
            ],
            "tips": [],
        },
        "licencia_ia": {
            "titulo": "Licença e plano de créditos de IA",
            "resumen": "Como ativar a cota de IA do copiloto depois de comprar um plano.",
            "pasos": [
                "Ao pagar o plano Professional ou Enterprise pelo MercadoPago, um token de "
                "licença é emitido automaticamente.",
                "Cole-o no campo 'Token de licença' na barra lateral — sem token, o produto "
                "continua funcionando completo no plano demo, só muda a cota mensal de IA.",
            ],
            "tips": [
                "O motor de regras (catálogo, saúde, dependências, backlog, políticas) "
                "nunca depende do token — funciona igual em qualquer plano.",
            ],
        },
    },
}


def sections(lang: str = "es") -> list[dict]:
    """Devuelve las secciones del tutorial en el idioma pedido.

    lang="es" (default) devuelve exactamente SECTIONS, sin copiar ni tocar
    nada — es el contrato que ya asumen los tests existentes. Para "en"/"pt"
    arma una lista nueva copiando cada sección española y superponiendo el
    overlay de traducción correspondiente (si a una sección le falta alguna
    clave en el overlay, se usa el valor en español como respaldo, así nunca
    queda contenido vacío por una traducción incompleta).
    """
    if lang == "es":
        return SECTIONS

    overlay_lang = _TRANSLATIONS.get(lang, {})
    resultado = []
    for s in SECTIONS:
        overlay = overlay_lang.get(s["id"], {})
        resultado.append({
            "id": s["id"],
            "titulo": overlay.get("titulo", s["titulo"]),
            "resumen": overlay.get("resumen", s["resumen"]),
            "pasos": overlay.get("pasos", s["pasos"]),
            "tips": overlay.get("tips", s["tips"]),
        })
    return resultado
