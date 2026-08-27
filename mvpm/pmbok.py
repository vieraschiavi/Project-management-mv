# © 2026 Martín Viera. Todos los derechos reservados.
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

# Traducciones EN/PT de los campos de cara al usuario de AREAS y GRUPOS_PROCESO.
# AREAS/GRUPOS_PROCESO (arriba) son la fuente de verdad en español y NO se tocan:
# `areas()`/`grupos_proceso()` copian esos dicts y superponen estos campos según
# `lang`. `clave` y `cobertura` nunca se traducen (son claves estables / un enum
# comparado contra `_COBERTURA_ORDEN`).
_AREAS_TRADUCCION = {
    "integracion": {
        "en": {
            "area": "Integration management",
            "definicion_tecnica": "Processes to unify, consolidate, and coordinate the "
                                  "project's various processes and activities: project "
                                  "charter, project management plan, and integrated change "
                                  "control.",
            "criollo": "Getting every part of the project pulling in the same direction so "
                       "nothing falls through the cracks — the glue that holds it all together.",
            "como_lo_cubre": "The copilot and the executive report consolidate the status of "
                              "the whole portfolio in one place, in real time.",
            "lo_que_falta": "It doesn't replace the project charter or formal change control "
                             "— the PM still defines and signs those outside the tool.",
        },
        "pt": {
            "area": "Gerenciamento da integração",
            "definicion_tecnica": "Processos para unificar, consolidar e coordenar os "
                                  "diversos processos e atividades do projeto: termo de "
                                  "abertura, plano de gerenciamento do projeto e controle "
                                  "integrado de mudanças.",
            "criollo": "Fazer com que todas as partes do projeto puxem para o mesmo lado e "
                       "nada fique solto — a cola que mantém tudo junto.",
            "como_lo_cubre": "O copiloto e o relatório executivo consolidam o status de todo "
                              "o portfólio em um só lugar, em tempo real.",
            "lo_que_falta": "Não substitui o termo de abertura do projeto nem um controle "
                             "formal de mudanças — isso o PM ainda define e assina fora da "
                             "ferramenta.",
        },
    },
    "alcance": {
        "en": {
            "area": "Scope management",
            "definicion_tecnica": "Ensuring the project includes all the work required — and "
                                  "only that — to complete it successfully. Includes collecting "
                                  "requirements, defining and validating scope, and controlling "
                                  "it.",
            "criollo": "Being crystal clear about what's in and what's out of the project, so "
                       "it doesn't balloon with last-minute requests.",
            "como_lo_cubre": "The 'scope' dimension of the health index flags tasks with no "
                              "owner; the catalog records each project's segment and "
                              "criticality.",
            "lo_que_falta": None,
        },
        "pt": {
            "area": "Gerenciamento do escopo",
            "definicion_tecnica": "Garantir que o projeto inclua todo o trabalho necessário — "
                                  "e somente esse — para concluí-lo com sucesso. Inclui coletar "
                                  "requisitos, definir e validar o escopo e controlá-lo.",
            "criollo": "Ter bem claro o que entra e o que não entra no projeto, para que não "
                       "infle com pedidos de última hora.",
            "como_lo_cubre": "A dimensão 'escopo' do índice de saúde detecta tarefas sem "
                              "responsável; o catálogo registra segmento e criticidade de cada "
                              "projeto.",
            "lo_que_falta": None,
        },
    },
    "cronograma": {
        "en": {
            "area": "Schedule management",
            "definicion_tecnica": "Processes to manage the timely completion of the project: "
                                  "defining and sequencing activities, estimating durations, "
                                  "and developing and controlling the schedule.",
            "criollo": "Setting realistic dates, knowing what has to happen before what, and "
                       "catching a slip early instead of finding out too late.",
            "como_lo_cubre": "The 'schedule' dimension of the health index, per-task due dates, "
                              "the dependency and blocker graph, and a backlog prioritized by "
                              "urgency.",
            "lo_que_falta": None,
        },
        "pt": {
            "area": "Gerenciamento do cronograma",
            "definicion_tecnica": "Processos para gerenciar a conclusão do projeto no prazo: "
                                  "definir e sequenciar atividades, estimar durações, e "
                                  "desenvolver e controlar o cronograma.",
            "criollo": "Definir prazos realistas, saber o que vem antes do quê, e perceber a "
                       "tempo quando algo está atrasando.",
            "como_lo_cubre": "Dimensão 'cronograma' do índice de saúde, vencimentos por tarefa, "
                              "grafo de dependências e bloqueios, e backlog priorizado por "
                              "urgência.",
            "lo_que_falta": None,
        },
    },
    "costos": {
        "en": {
            "area": "Cost management",
            "definicion_tecnica": "Planning, estimating, budgeting, financing, managing, and "
                                  "controlling costs so the project can be completed within "
                                  "the approved budget.",
            "criollo": "How much it's going to cost, how much you've spent so far, and a "
                       "heads-up before the money gets away from you.",
            "como_lo_cubre": "Budget vs. actuals by project and by portfolio, the 'budget' "
                              "dimension of the health index, and alerts for projects running "
                              "over budget.",
            "lo_que_falta": None,
        },
        "pt": {
            "area": "Gerenciamento dos custos",
            "definicion_tecnica": "Planejar, estimar, orçar, financiar, gerenciar e controlar "
                                  "os custos para concluir o projeto dentro do orçamento "
                                  "aprovado.",
            "criollo": "Quanto vai custar, quanto já foi gasto, e um alerta antes que o "
                       "dinheiro escape do controle.",
            "como_lo_cubre": "Orçamento vs. executado por projeto e por portfólio, dimensão "
                              "'orçamento' do índice de saúde, alerta de projetos acima do "
                              "orçamento.",
            "lo_que_falta": None,
        },
    },
    "calidad": {
        "en": {
            "area": "Quality management",
            "definicion_tecnica": "Incorporating the organization's quality policy into "
                                  "planning, managing, and controlling the project's and "
                                  "product's quality requirements.",
            "criollo": "Making sure what you deliver actually works and does what was "
                       "promised — not just 'sort of works'.",
            "como_lo_cubre": "Management policies check operational rules against real "
                              "portfolio evidence (assigned owners, healthy dependencies, "
                              "etc).",
            "lo_que_falta": "There's no deliverable-acceptance checklist or technical quality "
                             "control — that's still on the team and its own QA tooling.",
        },
        "pt": {
            "area": "Gerenciamento da qualidade",
            "definicion_tecnica": "Incorporar a política de qualidade da organização ao "
                                  "planejar, gerenciar e controlar os requisitos de qualidade "
                                  "do projeto e do produto.",
            "criollo": "Que aquilo que você entrega sirva de verdade e cumpra o que foi "
                       "prometido, não que 'funcione mais ou menos'.",
            "como_lo_cubre": "As políticas de gestão verificam regras operacionais contra "
                              "evidência real do portfólio (responsáveis atribuídos, "
                              "dependências saudáveis, etc).",
            "lo_que_falta": "Não há checklist de aceite de entregáveis nem controle de "
                             "qualidade técnico — isso continua sendo do time e de suas "
                             "próprias ferramentas de QA.",
        },
    },
    "recursos": {
        "en": {
            "area": "Resource management",
            "definicion_tecnica": "Identifying, acquiring, and managing the resources "
                                  "(people, equipment, materials) needed to complete the "
                                  "project.",
            "criollo": "Having the people and the things you need, without overloading anyone "
                       "or leaving anyone idle.",
            "como_lo_cubre": "Team view with current load vs. weekly capacity, the 'team' "
                              "dimension of the health index, and active tasks per person.",
            "lo_que_falta": None,
        },
        "pt": {
            "area": "Gerenciamento dos recursos",
            "definicion_tecnica": "Identificar, adquirir e gerenciar os recursos (pessoas, "
                                  "equipamentos, materiais) necessários para concluir o "
                                  "projeto.",
            "criollo": "Ter as pessoas e as coisas que fazem falta, sem sobrecarregar ninguém "
                       "nem deixar ninguém de braços cruzados.",
            "como_lo_cubre": "Visão de equipe com carga atual vs. capacidade semanal, dimensão "
                              "'equipe' do índice de saúde, tarefas ativas por pessoa.",
            "lo_que_falta": None,
        },
    },
    "comunicaciones": {
        "en": {
            "area": "Communications management",
            "definicion_tecnica": "Ensuring the project's information is planned, generated, "
                                  "collected, distributed, stored, and made available in a "
                                  "timely and appropriate way.",
            "criollo": "Making sure everyone knows what they need to know, when they need to "
                       "know it — no more, no less.",
            "como_lo_cubre": "An executive report ready to share, and a shared glossary so the "
                              "whole team talks about status the same way.",
            "lo_que_falta": "There's no in-app messaging, comments, or notifications yet — for "
                             "that, integrate it with the chat tool your team already uses.",
        },
        "pt": {
            "area": "Gerenciamento das comunicações",
            "definicion_tecnica": "Garantir que as informações do projeto sejam planejadas, "
                                  "geradas, coletadas, distribuídas, armazenadas e "
                                  "disponibilizadas de forma oportuna e adequada.",
            "criollo": "Fazer com que todos saibam o que precisam saber, na hora certa — nem a "
                       "mais, nem a menos.",
            "como_lo_cubre": "Relatório executivo pronto para compartilhar e glossário "
                              "compartilhado para que toda a equipe fale a mesma língua sobre "
                              "os status.",
            "lo_que_falta": "Ainda não há mensagens, comentários nem notificações dentro do "
                             "produto — para isso, integre com o chat que sua equipe já usa.",
        },
    },
    "riesgos": {
        "en": {
            "area": "Risk management",
            "definicion_tecnica": "Planning, identifying, analyzing, responding to, and "
                                  "monitoring project risks to increase the likelihood of "
                                  "positive events and reduce that of negative ones.",
            "criollo": "Thinking ahead about what could go wrong, having a backup plan, and "
                       "staying alert to the warning signs.",
            "como_lo_cubre": "The 'risk' dimension of the health index, plus detection of "
                              "blocked tasks and orphaned dependencies pointing at nothing.",
            "lo_que_falta": None,
        },
        "pt": {
            "area": "Gerenciamento dos riscos",
            "definicion_tecnica": "Planejar, identificar, analisar, responder e monitorar os "
                                  "riscos do projeto para aumentar a probabilidade de eventos "
                                  "positivos e diminuir a de eventos negativos.",
            "criollo": "Pensar antes no que pode dar errado, ter um plano B, e ficar atento "
                       "aos sinais de fumaça.",
            "como_lo_cubre": "Dimensão 'risco' do índice de saúde, detecção de tarefas "
                              "bloqueadas e de dependências órfãs que apontam para lugar "
                              "nenhum.",
            "lo_que_falta": None,
        },
    },
    "adquisiciones": {
        "en": {
            "area": "Procurement management",
            "definicion_tecnica": "Purchasing or acquiring the products, services, or results "
                                  "needed from outside the project team: planning, conducting, "
                                  "and controlling procurements.",
            "criollo": "When something needs to be bought or contracted from outside, handling "
                       "vendors and contracts well.",
            "como_lo_cubre": None,
            "lo_que_falta": "There's no vendor, contract, or purchasing management — use your "
                             "procurement tool alongside it; the sponsor and budget do stay in "
                             "here.",
        },
        "pt": {
            "area": "Gerenciamento das aquisições",
            "definicion_tecnica": "Comprar ou adquirir os produtos, serviços ou resultados "
                                  "necessários de fora da equipe do projeto: planejar, "
                                  "conduzir e controlar as aquisições.",
            "criollo": "Quando algo precisa ser comprado ou contratado de fora, administrar "
                       "bem fornecedores e contratos.",
            "como_lo_cubre": None,
            "lo_que_falta": "Não há gestão de fornecedores, contratos nem compras — use sua "
                             "ferramenta de compras em paralelo; o patrocinador e o orçamento "
                             "continuam aqui.",
        },
    },
    "interesados": {
        "en": {
            "area": "Stakeholder management",
            "definicion_tecnica": "Identifying the people, groups, or organizations that can "
                                  "affect or be affected by the project, and developing "
                                  "strategies to engage them effectively.",
            "criollo": "Knowing who's connected to the project (for better or worse) and how "
                       "to get along with each of them.",
            "como_lo_cubre": "Every project records its sponsor, and the copilot can answer "
                              "questions about who owns each initiative.",
            "lo_que_falta": "There's no power/interest stakeholder matrix — if your portfolio "
                             "needs one, build it once in a separate sheet and reference it "
                             "here.",
        },
        "pt": {
            "area": "Gerenciamento das partes interessadas",
            "definicion_tecnica": "Identificar as pessoas, grupos ou organizações que podem "
                                  "afetar ou ser afetados pelo projeto, e desenvolver "
                                  "estratégias para envolvê-los de forma eficaz.",
            "criollo": "Saber quem tem a ver com o projeto (para o bem ou para o mal) e como "
                       "se dar bem com cada um.",
            "como_lo_cubre": "Cada projeto registra seu patrocinador, e o copiloto pode "
                              "responder perguntas sobre a quem pertence cada iniciativa.",
            "lo_que_falta": "Não há uma matriz de partes interessadas por poder/interesse — "
                             "se o seu portfólio precisar dela, monte uma vez em uma planilha "
                             "à parte e referencie aqui.",
        },
    },
}

_GRUPOS_TRADUCCION = {
    "inicio": {
        "en": {
            "nombre": "Initiating",
            "definicion_tecnica": "Processes to define a new project or phase and obtain "
                                  "authorization to start it (project charter, stakeholder "
                                  "identification).",
            "criollo": "The kickoff: deciding the project is a go, naming who's responsible, "
                       "and seeing who's involved.",
        },
        "pt": {
            "nombre": "Iniciação",
            "definicion_tecnica": "Processos para definir um novo projeto ou fase e obter "
                                  "autorização para iniciá-lo (termo de abertura, "
                                  "identificação de partes interessadas).",
            "criollo": "A largada: decidir que o projeto vai em frente, nomear o responsável "
                       "e ver quem está envolvido.",
        },
    },
    "planificacion": {
        "en": {
            "nombre": "Planning",
            "definicion_tecnica": "Processes to establish the scope, refine the objectives, "
                                  "and define the course of action needed to attain them.",
            "criollo": "Building the plan: what gets done, in what order, with what budget, "
                       "by whom, and what could go wrong.",
        },
        "pt": {
            "nombre": "Planejamento",
            "definicion_tecnica": "Processos para estabelecer o escopo, refinar os objetivos "
                                  "e definir o curso de ação necessário para alcançá-los.",
            "criollo": "Montar o plano: o que fazer, em que ordem, com que dinheiro, quem "
                       "faz, e o que pode dar errado.",
        },
    },
    "ejecucion": {
        "en": {
            "nombre": "Executing",
            "definicion_tecnica": "Processes to complete the work defined in the plan and "
                                  "satisfy the project's requirements.",
            "criollo": "Getting to work: doing the actual work and coordinating the team.",
        },
        "pt": {
            "nombre": "Execução",
            "definicion_tecnica": "Processos para concluir o trabalho definido no plano e "
                                  "satisfazer os requisitos do projeto.",
            "criollo": "Mão na massa: fazer o trabalho e coordenar a equipe.",
        },
    },
    "monitoreo": {
        "en": {
            "nombre": "Monitoring & Controlling",
            "definicion_tecnica": "Processes to track, review, and regulate progress and "
                                  "performance; identify changes and carry them out.",
            "criollo": "Keeping tabs on progress against the plan and correcting course when "
                       "needed.",
        },
        "pt": {
            "nombre": "Monitoramento e Controle",
            "definicion_tecnica": "Processos para acompanhar, revisar e regular o progresso e "
                                  "o desempenho; identificar mudanças e executá-las.",
            "criollo": "Ir medindo como está indo em relação ao plano e corrigir o rumo "
                       "quando necessário.",
        },
    },
    "cierre": {
        "en": {
            "nombre": "Closing",
            "definicion_tecnica": "Processes to formally complete or close the project, "
                                  "phase, or contract.",
            "criollo": "Wrapping up properly: delivering, settling what's owed, and writing "
                       "down the lessons learned for next time.",
        },
        "pt": {
            "nombre": "Encerramento",
            "definicion_tecnica": "Processos para concluir ou encerrar formalmente o "
                                  "projeto, fase ou contrato.",
            "criollo": "Fechar com organização: entregar, cobrar/pagar o que falta e anotar "
                       "as lições aprendidas para a próxima.",
        },
    },
}


def areas(lang: str = "es") -> list[dict]:
    resultado = []
    for a in AREAS:
        item = dict(a)
        if lang != "es":
            item.update(_AREAS_TRADUCCION.get(a["clave"], {}).get(lang, {}))
        resultado.append(item)
    return sorted(resultado, key=lambda a: _COBERTURA_ORDEN[a["cobertura"]])


def grupos_proceso(lang: str = "es") -> list[dict]:
    resultado = []
    for g in GRUPOS_PROCESO:
        item = dict(g)
        if lang != "es":
            item.update(_GRUPOS_TRADUCCION.get(g["clave"], {}).get(lang, {}))
        resultado.append(item)
    return resultado


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
