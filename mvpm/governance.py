# © 2026 Martín Viera. Todos los derechos reservados.
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
# "termino"/"definicion" llevan es/en/pt; "clave" y "categoria" son
# identificadores internos (categoria se usa para agrupar en pantalla, no se
# compara por código en ningún lado, así que también se traduce).
CONCEPTOS_BASE = [
    {"clave": "alcance",
     "termino": {"es": "Alcance (Scope)", "en": "Scope", "pt": "Escopo (Scope)"},
     "categoria": {"es": "Alcance", "en": "Scope", "pt": "Escopo"},
     "definicion": {
        "es": "Todo el trabajo requerido — y sólo ese trabajo — para entregar el producto o "
              "resultado del proyecto con las características acordadas. Define qué está "
              "dentro y qué está fuera del proyecto.",
        "en": "All the work required — and only that work — to deliver the project's product "
              "or result with the agreed characteristics. Defines what's in and out of the project.",
        "pt": "Todo o trabalho necessário — e somente esse trabalho — para entregar o produto "
              "ou resultado do projeto com as características acordadas. Define o que está "
              "dentro e o que está fora do projeto."}},
    {"clave": "linea_base",
     "termino": {"es": "Línea base (Baseline)", "en": "Baseline", "pt": "Linha de base (Baseline)"},
     "categoria": {"es": "Integración", "en": "Integration", "pt": "Integração"},
     "definicion": {
        "es": "La versión aprobada de un plan (alcance, cronograma o costo) contra la cual se "
              "mide el desempeño real. Sólo se cambia por control formal de cambios.",
        "en": "The approved version of a plan (scope, schedule or cost) against which actual "
              "performance is measured. Only changes through formal change control.",
        "pt": "A versão aprovada de um plano (escopo, cronograma ou custo) contra a qual se mede "
              "o desempenho real. Só muda por controle formal de mudanças."}},
    {"clave": "criticidad",
     "termino": {"es": "Criticidad", "en": "Criticality", "pt": "Criticidade"},
     "categoria": {"es": "Riesgos", "en": "Risk", "pt": "Riscos"},
     "definicion": {
        "es": "Qué tan importante es un proyecto para la organización. En este producto "
              "pondera el índice de salud y el orden del backlog: Alta pesa más que Media, "
              "que pesa más que Baja.",
        "en": "How important a project is to the organization. In this product it weighs the "
              "health index and the backlog order: High weighs more than Medium, which weighs "
              "more than Low.",
        "pt": "O quanto um projeto importa para a organização. Neste produto pondera o índice "
              "de saúde e a ordem do backlog: Alta pesa mais que Média, que pesa mais que Baixa."}},
    {"clave": "salud",
     "termino": {"es": "Índice de salud", "en": "Health index", "pt": "Índice de saúde"},
     "categoria": {"es": "Monitoreo", "en": "Monitoring", "pt": "Monitoramento"},
     "definicion": {
        "es": "Puntaje 0-100 que resume el estado de un proyecto en 6 dimensiones (alcance, "
              "cronograma, presupuesto, riesgo, dependencias, equipo). ≥75 saludable, 55-75 en "
              "observación, <55 en riesgo.",
        "en": "A 0-100 score that summarizes a project's status across 6 dimensions (scope, "
              "schedule, budget, risk, dependencies, team). ≥75 healthy, 55-75 watch, <55 at risk.",
        "pt": "Pontuação 0-100 que resume o status de um projeto em 6 dimensões (escopo, "
              "cronograma, orçamento, risco, dependências, equipe). ≥75 saudável, 55-75 em "
              "observação, <55 em risco."}},
    {"clave": "dependencia",
     "termino": {"es": "Dependencia", "en": "Dependency", "pt": "Dependência"},
     "categoria": {"es": "Cronograma", "en": "Schedule", "pt": "Cronograma"},
     "definicion": {
        "es": "Relación en la que una tarea no puede empezar o terminar hasta que otra avance. "
              "Una dependencia a una tarea inexistente es 'huérfana' y distorsiona el cronograma.",
        "en": "A relationship where a task can't start or finish until another one progresses. "
              "A dependency pointing to a task that doesn't exist is \"orphan\" and distorts the schedule.",
        "pt": "Relação em que uma tarefa não pode começar ou terminar até que outra avance. Uma "
              "dependência para uma tarefa inexistente é 'órfã' e distorce o cronograma."}},
    {"clave": "bloqueo",
     "termino": {"es": "Bloqueo", "en": "Blocker", "pt": "Bloqueio"},
     "categoria": {"es": "Riesgos", "en": "Risk", "pt": "Riscos"},
     "definicion": {
        "es": "Una tarea que no puede avanzar hasta resolver una dependencia u obstáculo "
              "externo. Cuantas más tareas dependan de ella, mayor su impacto.",
        "en": "A task that can't move forward until a dependency or external obstacle is "
              "resolved. The more tasks depend on it, the bigger its impact.",
        "pt": "Uma tarefa que não pode avançar até resolver uma dependência ou obstáculo "
              "externo. Quanto mais tarefas dependem dela, maior seu impacto."}},
    {"clave": "backlog",
     "termino": {"es": "Backlog priorizado", "en": "Prioritized backlog", "pt": "Backlog priorizado"},
     "categoria": {"es": "Alcance", "en": "Scope", "pt": "Escopo"},
     "definicion": {
        "es": "Lista ordenada de tareas pendientes por valor esperado = criticidad × prioridad "
              "× urgencia × impacto en dependencias. No es orden de llegada.",
        "en": "Pending tasks ordered by expected value = criticality × priority × urgency × "
              "dependency impact. Not first-come-first-served.",
        "pt": "Lista ordenada de tarefas pendentes por valor esperado = criticidade × "
              "prioridade × urgência × impacto em dependências. Não é ordem de chegada."}},
    {"clave": "sponsor",
     "termino": {"es": "Sponsor (Patrocinador)", "en": "Sponsor", "pt": "Sponsor (Patrocinador)"},
     "categoria": {"es": "Interesados", "en": "Stakeholders", "pt": "Interessados"},
     "definicion": {
        "es": "La persona o área que provee los recursos y el respaldo político del proyecto, y "
              "a quien rinde cuentas el líder de proyecto. Sin sponsor visible, el proyecto "
              "pierde prioridad.",
        "en": "The person or area that provides the project's resources and political backing, "
              "and to whom the project lead answers. Without a visible sponsor, the project "
              "loses priority.",
        "pt": "A pessoa ou área que fornece os recursos e o respaldo político do projeto, e a "
              "quem o líder de projeto presta contas. Sem sponsor visível, o projeto perde "
              "prioridade."}},
    {"clave": "dueno",
     "termino": {"es": "Dueño de proyecto", "en": "Project owner", "pt": "Responsável pelo projeto"},
     "categoria": {"es": "Recursos", "en": "Resources", "pt": "Recursos"},
     "definicion": {
        "es": "El responsable de que el proyecto avance y de reportar su estado real. Un "
              "proyecto sin dueño asignado baja su dimensión de alcance.",
        "en": "The person responsible for making the project move forward and for reporting its "
              "real status. A project with no assigned owner lowers its scope dimension.",
        "pt": "O responsável por fazer o projeto avançar e reportar seu status real. Um projeto "
              "sem responsável atribuído reduz sua dimensão de escopo."}},
    {"clave": "data_owner",
     "termino": {"es": "Data Owner", "en": "Data Owner", "pt": "Data Owner"},
     "categoria": {"es": "Gobernanza", "en": "Governance", "pt": "Governança"},
     "definicion": {
        "es": "El responsable último de un dato o definición en la organización: aprueba su "
              "significado y su uso. En este producto, quien valida una definición.",
        "en": "The ultimate owner of a data element or definition in the organization: approves "
              "its meaning and use. In this product, whoever validates a definition.",
        "pt": "O responsável final por um dado ou definição na organização: aprova seu "
              "significado e uso. Neste produto, quem valida uma definição."}},
    {"clave": "data_steward",
     "termino": {"es": "Data Steward", "en": "Data Steward", "pt": "Data Steward"},
     "categoria": {"es": "Gobernanza", "en": "Governance", "pt": "Governança"},
     "definicion": {
        "es": "Quien administra el dato en el día a día: mantiene la definición al día, propone "
              "cambios y los lleva al Data Owner para su aprobación.",
        "en": "Whoever manages the data day to day: keeps the definition up to date, proposes "
              "changes and takes them to the Data Owner for approval.",
        "pt": "Quem administra o dado no dia a dia: mantém a definição atualizada, propõe "
              "mudanças e as leva ao Data Owner para aprovação."}},
    {"clave": "sobre_presupuesto",
     "termino": {"es": "Sobre presupuesto", "en": "Over budget", "pt": "Acima do orçamento"},
     "categoria": {"es": "Costos", "en": "Costs", "pt": "Custos"},
     "definicion": {
        "es": "Cuando lo ejecutado supera el presupuesto asignado al proyecto. Se detecta "
              "automáticamente comparando ejecutado vs. presupuesto.",
        "en": "When actual spend exceeds the project's assigned budget. Detected automatically "
              "by comparing spent vs. budget.",
        "pt": "Quando o executado supera o orçamento atribuído ao projeto. Detectado "
              "automaticamente comparando executado vs. orçamento."}},
    {"clave": "riesgo",
     "termino": {"es": "Riesgo", "en": "Risk", "pt": "Risco"},
     "categoria": {"es": "Riesgos", "en": "Risk", "pt": "Riscos"},
     "definicion": {
        "es": "Evento incierto que, de ocurrir, afecta objetivos del proyecto. La dimensión "
              "'riesgo' del índice de salud lo aproxima por tareas bloqueadas.",
        "en": "An uncertain event that, if it occurs, affects the project's objectives. The "
              "health index's \"risk\" dimension approximates it via blocked tasks.",
        "pt": "Evento incerto que, se ocorrer, afeta os objetivos do projeto. A dimensão "
              "'risco' do índice de saúde o aproxima por tarefas bloqueadas."}},
    {"clave": "interesado",
     "termino": {"es": "Interesado (Stakeholder)", "en": "Stakeholder", "pt": "Interessado (Stakeholder)"},
     "categoria": {"es": "Interesados", "en": "Stakeholders", "pt": "Interessados"},
     "definicion": {
        "es": "Cualquier persona o grupo que afecta o es afectado por el proyecto. Se gestionan "
              "según su poder e interés.",
        "en": "Any person or group that affects or is affected by the project. Managed "
              "according to their power and interest.",
        "pt": "Qualquer pessoa ou grupo que afeta ou é afetado pelo projeto. Gerenciados "
              "conforme seu poder e interesse."}},
]

_POR_CLAVE = {c["clave"]: c for c in CONCEPTOS_BASE}

_MOTOR_DE_REGLAS = {"es": "motor de reglas (definición de fábrica)",
                    "en": "rules engine (factory definition)",
                    "pt": "motor de regras (definição de fábrica)"}


def _traducido(c: dict, lang: str) -> dict:
    return {"clave": c["clave"], "termino": c["termino"].get(lang, c["termino"]["es"]),
           "categoria": c["categoria"].get(lang, c["categoria"]["es"]),
           "definicion": c["definicion"].get(lang, c["definicion"]["es"])}


def catalogo(lang: str = "es") -> list[dict]:
    """Siempre devuelve `termino`/`categoria`/`definicion` como texto plano en
    el idioma pedido — nunca el dict {es,en,pt} interno de CONCEPTOS_BASE, ni
    siquiera con lang="es" default, para que quien lea `c["definicion"]` no
    tenga que saber que por dentro es multilingüe."""
    lang = lang if lang in ("es", "en", "pt") else "es"
    return [_traducido(c, lang) for c in CONCEPTOS_BASE]


def concepto_base(clave: str, lang: str = "es") -> dict | None:
    c = _POR_CLAVE.get(clave)
    if c is None:
        return None
    lang = lang if lang in ("es", "en", "pt") else "es"
    return _traducido(c, lang)


def definicion_vigente(empresa_id: int, clave: str, lang: str = "es") -> dict:
    """La definición que rige hoy para esta empresa: la última versión guardada,
    o la preestablecida de fábrica si nunca se tocó."""
    lang = lang if lang in ("es", "en", "pt") else "es"
    base = _POR_CLAVE.get(clave, {})
    version = db.obtener_version_actual(empresa_id, ENTIDAD, clave)
    if version:
        # El texto validado es lo que escribió el data owner/steward de esta
        # empresa: dato de usuario, nunca se traduce.
        return {
            "texto": version["contenido"],
            "estado": version["estado"],
            "recomendado_por": version["recomendado_por"],
            "validado_por_nombre": version["validado_por_nombre"],
            "validado_por_cargo": version["validado_por_cargo"],
            "origen": "versionada",
        }
    return {
        "texto": base.get("definicion", {}).get(lang, base.get("definicion", {}).get("es", "")),
        "estado": "preestablecida",
        "recomendado_por": _MOTOR_DE_REGLAS.get(lang, _MOTOR_DE_REGLAS["es"]),
        "validado_por_nombre": None,
        "validado_por_cargo": None,
        "origen": "preestablecida",
    }


_IA_SYSTEM = {
    "es": "Sos un experto en gestión de proyectos (PMBOK). Redactás en español rioplatense, "
          "claro y preciso. Mejorás definiciones sin cambiar su significado técnico ni "
          "inventar conceptos nuevos.",
    "en": "You are a project management (PMBOK) expert. You write in clear, precise "
          "professional English. You improve definitions without changing their technical "
          "meaning or inventing new concepts.",
    "pt": "Você é um especialista em gestão de projetos (PMBOK). Você escreve em português "
          "claro e preciso. Você melhora definições sem mudar seu significado técnico nem "
          "inventar conceitos novos.",
}
_IA_USER = {
    "es": "Concepto: {termino}\nDefinición actual: {texto}\nDevolvé UNA definición mejorada, "
          "más clara, en 1-3 frases. Sólo la definición.",
    "en": "Concept: {termino}\nCurrent definition: {texto}\nReturn ONE improved, clearer "
          "definition, in 1-3 sentences. Only the definition.",
    "pt": "Conceito: {termino}\nDefinição atual: {texto}\nDevolva UMA definição melhorada, "
          "mais clara, em 1-3 frases. Somente a definição.",
}


def recomendar_definicion(clave: str, proveedor: str | None = None, lang: str = "es") -> dict:
    """Devuelve una definición RECOMENDADA como punto de partida (nunca en
    blanco): la de fábrica pulida por IA si hay proveedor, o la de fábrica tal
    cual. El usuario después la valida o la edita. `lang` decide en qué idioma
    se le pide a la IA que redacte — antes siempre le pedía español, sin
    importar el idioma elegido en la sesión."""
    lang = lang if lang in ("es", "en", "pt") else "es"
    base = _POR_CLAVE.get(clave, {})
    termino_base = base.get("termino", {}).get(lang, base.get("termino", {}).get("es", clave))
    texto_base = base.get("definicion", {}).get(lang, base.get("definicion", {}).get("es", ""))
    motor = _MOTOR_DE_REGLAS.get(lang, _MOTOR_DE_REGLAS["es"])
    resultado = {"texto": texto_base, "recomendado_por": motor}
    if proveedor:
        pulida = ai.completar(
            system=_IA_SYSTEM.get(lang, _IA_SYSTEM["es"]),
            user=_IA_USER.get(lang, _IA_USER["es"]).format(termino=termino_base, texto=texto_base),
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
