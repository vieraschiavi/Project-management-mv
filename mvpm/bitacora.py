# © 2026 Martín Viera. Todos los derechos reservados.
"""Bitácora técnica: qué le pasa al dato desde que entra hasta que sale.

Una etapa por transformación real del pipeline, EN ORDEN, y cada una contada
dos veces:

  · **técnico** — para quien va a leer o tocar el código: qué módulo lo hace,
    con qué estructura, con qué garantía.
  · **criollo** — para quien firma el cheque: qué significa eso en el trabajo
    de todos los días, sin una sola sigla.

Más el *por qué* (qué se rompía antes de que existiera) y la *repercusión*
(qué cambia aguas abajo). Las dos preguntas que un informe técnico suele
dejar sin responder y son justo las que decide un gerente.

Por qué vive en el motor y no en la pestaña: el contenido tiene que poder
exportarse a HTML, Word y PDF sin levantar Streamlit — `mvpm/documento.py`
lo consume igual que lo consume `app/app.py`. Y así se testea sin UI.

Lo que NO hace este módulo: inventar. Cada etapa nombra el archivo que la
implementa, y `tests/test_bitacora.py` verifica que ese archivo exista. Una
bitácora que describe un módulo que no está es peor que no tener bitácora.
"""

from __future__ import annotations

LANGS = ("es", "en", "pt")

#: Cada etapa: `clave` estable (nunca se traduce, es la que ordena y la que
#: usan los tests), `modulo` (el archivo real que la implementa) y cuatro
#: textos por idioma. Los tres idiomas van juntos a propósito: separarlos en
#: diccionarios distintos es lo que hace que una traducción quede vieja sin
#: que nadie lo note.
_ETAPAS: list[dict] = [
    {
        "clave": "ingesta",
        "modulo": "mvpm/importer.py",
        "titulo": {
            "es": "1 · Entrada del dato",
            "en": "1 · Data intake",
            "pt": "1 · Entrada do dado",
        },
        "tecnico": {
            "es": "Cuatro fuentes con una sola salida: Excel/CSV vía `importer.py`, "
                  "bases SQL vía `conectores.py` (SELECT de sólo lectura, validado "
                  "antes de ejecutarse), los tres portafolios demo, y alta manual "
                  "desde el dashboard. Todas desembocan en el mismo esquema de "
                  "columnas, así que de ahí para abajo el motor no sabe —ni le "
                  "importa— de dónde vino cada fila.",
            "en": "Four sources, one output: Excel/CSV through `importer.py`, SQL "
                  "databases through `conectores.py` (read-only SELECT, validated "
                  "before it runs), the three demo portfolios, and manual entry from "
                  "the dashboard. They all land on the same column schema, so from "
                  "there down the engine neither knows nor cares where a row came "
                  "from.",
            "pt": "Quatro fontes com uma só saída: Excel/CSV via `importer.py`, bases "
                  "SQL via `conectores.py` (SELECT somente leitura, validado antes de "
                  "executar), os três portfólios demo, e cadastro manual pelo painel. "
                  "Todas desembocam no mesmo esquema de colunas, então daí para baixo "
                  "o motor não sabe — nem precisa saber — de onde veio cada linha.",
        },
        "criollo": {
            "es": "Traés los proyectos como los tengas hoy: una planilla, la base del "
                  "ERP, o cargándolos a mano. El programa los acomoda a un formato "
                  "único. No hay que migrar nada ni cambiar cómo trabaja el equipo.",
            "en": "Bring your projects however you keep them today: a spreadsheet, the "
                  "ERP database, or typed in by hand. The program arranges them into a "
                  "single format. Nothing to migrate, and nobody has to change how they "
                  "work.",
            "pt": "Traga os projetos como você os tem hoje: uma planilha, a base do ERP, "
                  "ou digitados à mão. O programa os organiza em um formato único. Não "
                  "há nada para migrar nem é preciso mudar como a equipe trabalha.",
        },
        "porque": {
            "es": "Si cada fuente tuviera su propio camino, cada regla del motor habría "
                  "que escribirla cuatro veces — y arreglarla cuatro veces cada vez que "
                  "falla. La consulta SQL se valida como sólo lectura porque una "
                  "herramienta de análisis no tiene por qué poder escribir en el ERP.",
            "en": "If each source had its own path, every engine rule would have to be "
                  "written four times — and fixed four times whenever it broke. The SQL "
                  "query is validated as read-only because an analysis tool has no "
                  "business writing to the ERP.",
            "pt": "Se cada fonte tivesse seu próprio caminho, cada regra do motor teria "
                  "de ser escrita quatro vezes — e corrigida quatro vezes a cada falha. "
                  "A consulta SQL é validada como somente leitura porque uma ferramenta "
                  "de análise não tem por que poder escrever no ERP.",
        },
        "repercusion": {
            "es": "Todo lo que viene después —salud, dependencias, backlog, reportes— "
                  "funciona igual con datos de demo que con los tuyos. Cambiar de fuente "
                  "no rompe nada aguas abajo.",
            "en": "Everything downstream — health, dependencies, backlog, reports — "
                  "works the same on demo data as on yours. Switching sources breaks "
                  "nothing further down.",
            "pt": "Tudo o que vem depois — saúde, dependências, backlog, relatórios — "
                  "funciona igual com dados demo e com os seus. Trocar de fonte não "
                  "quebra nada rio abaixo.",
        },
    },
    {
        "clave": "persistencia",
        "modulo": "mvpm/db.py",
        "titulo": {
            "es": "2 · Guardado sin pisar historial",
            "en": "2 · Storage that never overwrites",
            "pt": "2 · Gravação sem apagar histórico",
        },
        "tecnico": {
            "es": "SQLite local. Todo dato manual (gobernanza, organigrama, notas PMBOK) "
                  "se escribe en la tabla `versiones` como FILA NUEVA vía "
                  "`guardar_version()`; el estado vigente es la más reciente por "
                  "`(empresa_id, entidad, clave)`. No hay ningún `UPDATE` que borre lo "
                  "anterior.",
            "en": "Local SQLite. Every manual entry (governance, org chart, PMBOK notes) "
                  "is written to the `versiones` table as a NEW ROW via "
                  "`guardar_version()`; the current state is the most recent one per "
                  "`(empresa_id, entidad, clave)`. There is no `UPDATE` that erases what "
                  "came before.",
            "pt": "SQLite local. Todo dado manual (governança, organograma, notas PMBOK) "
                  "é gravado na tabela `versiones` como LINHA NOVA via "
                  "`guardar_version()`; o estado vigente é o mais recente por "
                  "`(empresa_id, entidad, clave)`. Não há nenhum `UPDATE` que apague o "
                  "anterior.",
        },
        "criollo": {
            "es": "Nada se sobrescribe. Cuando alguien corrige un dato, la versión "
                  "anterior queda guardada con quién la cambió y cuándo. Se puede "
                  "reconstruir qué decía el tablero en cualquier fecha pasada.",
            "en": "Nothing gets overwritten. When someone corrects a figure, the previous "
                  "version stays on file with who changed it and when. You can "
                  "reconstruct what the board said on any past date.",
            "pt": "Nada é sobrescrito. Quando alguém corrige um dado, a versão anterior "
                  "fica guardada com quem a mudou e quando. Dá para reconstruir o que o "
                  "painel dizia em qualquer data passada.",
        },
        "porque": {
            "es": "En una auditoría, «el número cambió» sin poder decir quién ni cuándo "
                  "es indefendible. Y porque el error más caro de un tablero es el que "
                  "alguien corrigió en silencio.",
            "en": "In an audit, \"the number changed\" with no way to say who or when is "
                  "indefensible. And because the most expensive error on a dashboard is "
                  "the one somebody quietly corrected.",
            "pt": "Numa auditoria, \"o número mudou\" sem poder dizer quem nem quando é "
                  "indefensável. E porque o erro mais caro de um painel é o que alguém "
                  "corrigiu em silêncio.",
        },
        "repercusion": {
            "es": "Habilita la trazabilidad de la etapa de gobernanza: cada dato validado "
                  "arrastra su firma. Y hace que borrar sea imposible por accidente.",
            "en": "It enables the traceability of the governance stage: every validated "
                  "figure carries its signature. And it makes accidental deletion "
                  "impossible.",
            "pt": "Habilita a rastreabilidade da etapa de governança: cada dado validado "
                  "carrega sua assinatura. E torna impossível apagar por acidente.",
        },
    },
    {
        "clave": "catalogo",
        "modulo": "mvpm/catalog.py",
        "titulo": {
            "es": "3 · Catálogo y KPIs del portafolio",
            "en": "3 · Portfolio catalogue and KPIs",
            "pt": "3 · Catálogo e KPIs do portfólio",
        },
        "tecnico": {
            "es": "Primera transformación derivada: sobre los proyectos normalizados "
                  "calcula porcentaje de ejecución presupuestaria, marca de sobre-"
                  "presupuesto y agrupación por portafolio. `kpis()` devuelve el "
                  "agregado (activos, presupuesto total, ejecutado, sin dueño, sobre "
                  "presupuesto) como diccionario plano.",
            "en": "First derived transformation: over the normalized projects it computes "
                  "budget execution percentage, an over-budget flag, and grouping by "
                  "portfolio. `kpis()` returns the aggregate (active, total budget, "
                  "spent, unowned, over budget) as a flat dictionary.",
            "pt": "Primeira transformação derivada: sobre os projetos normalizados calcula "
                  "percentual de execução orçamentária, marca de acima do orçamento e "
                  "agrupamento por portfólio. `kpis()` devolve o agregado (ativos, "
                  "orçamento total, executado, sem dono, acima do orçamento) como "
                  "dicionário plano.",
        },
        "criollo": {
            "es": "La foto del portafolio en una pantalla: cuántos proyectos hay, cuánta "
                  "plata se presupuestó, cuánta se gastó, cuáles ya se pasaron y cuáles "
                  "no tienen responsable asignado.",
            "en": "The portfolio at a glance: how many projects, how much was budgeted, "
                  "how much has been spent, which ones are already over, and which have "
                  "nobody assigned.",
            "pt": "A foto do portfólio em uma tela: quantos projetos há, quanto foi "
                  "orçado, quanto foi gasto, quais já passaram e quais não têm "
                  "responsável.",
        },
        "porque": {
            "es": "Es la pregunta con la que empieza toda reunión de portafolio, y "
                  "responderla a mano cuesta abrir los proyectos uno por uno.",
            "en": "It is the question every portfolio meeting starts with, and answering "
                  "it by hand means opening the projects one by one.",
            "pt": "É a pergunta com que começa toda reunião de portfólio, e respondê-la "
                  "à mão custa abrir os projetos um por um.",
        },
        "repercusion": {
            "es": "«Sin dueño» y «sobre presupuesto» alimentan después las políticas de "
                  "gobernanza y el detector de problemas: lo que acá es una columna, más "
                  "adelante es un incumplimiento con nombre.",
            "en": "\"Unowned\" and \"over budget\" later feed the governance policies and "
                  "the problem detector: what is a column here becomes a named breach "
                  "further down.",
            "pt": "\"Sem dono\" e \"acima do orçamento\" alimentam depois as políticas de "
                  "governança e o detector de problemas: o que aqui é uma coluna, mais "
                  "adiante é um descumprimento com nome.",
        },
    },
    {
        "clave": "salud",
        "modulo": "mvpm/health.py",
        "titulo": {
            "es": "4 · Salud en seis dimensiones",
            "en": "4 · Health across six dimensions",
            "pt": "4 · Saúde em seis dimensões",
        },
        "tecnico": {
            "es": "Por proyecto se puntúan seis dimensiones —alcance, cronograma, "
                  "presupuesto, riesgo, dependencias y equipo— de 0 a 100 con funciones "
                  "separadas y auditables. El índice es el promedio; el estado sale de "
                  "dos cortes fijos: <55 riesgo, <75 observación, resto saludable.",
            "en": "Per project, six dimensions are scored — scope, schedule, budget, risk, "
                  "dependencies and team — from 0 to 100 by separate, auditable "
                  "functions. The index is their average; the status comes from two fixed "
                  "cutoffs: <55 at risk, <75 watch, otherwise healthy.",
            "pt": "Por projeto pontuam-se seis dimensões — escopo, cronograma, orçamento, "
                  "risco, dependências e equipe — de 0 a 100 com funções separadas e "
                  "auditáveis. O índice é a média; o estado sai de dois cortes fixos: "
                  "<55 risco, <75 observação, o resto saudável.",
        },
        "criollo": {
            "es": "Cada proyecto recibe una nota de 0 a 100 y un semáforo. Y se puede "
                  "abrir la nota: si da bajo, el programa dice por cuál de las seis "
                  "cosas — no es una opinión, es una cuenta que se puede revisar.",
            "en": "Each project gets a 0-100 score and a traffic light. And the score "
                  "opens up: if it is low, the program says which of the six things is "
                  "dragging it — not an opinion, an arithmetic you can check.",
            "pt": "Cada projeto recebe uma nota de 0 a 100 e um semáforo. E a nota abre: "
                  "se estiver baixa, o programa diz por qual das seis coisas — não é "
                  "opinião, é uma conta que dá para revisar.",
        },
        "porque": {
            "es": "«Este proyecto va mal» no se puede accionar. «Va mal por cronograma y "
                  "dependencias, con 47 de índice» sí. Separar las seis dimensiones es lo "
                  "que convierte una sensación en una decisión.",
            "en": "\"This project is doing badly\" cannot be acted on. \"It is doing badly "
                  "on schedule and dependencies, at 47\" can. Splitting the six dimensions "
                  "is what turns a feeling into a decision.",
            "pt": "\"Este projeto vai mal\" não dá para acionar. \"Vai mal por cronograma e "
                  "dependências, com índice 47\" dá. Separar as seis dimensões é o que "
                  "transforma uma sensação em decisão.",
        },
        "repercusion": {
            "es": "El índice ordena el portafolio, dispara la política de salud mínima y "
                  "es lo que el reporte ejecutivo pone arriba de todo.",
            "en": "The index sorts the portfolio, triggers the minimum-health policy, and "
                  "is what the executive report puts at the very top.",
            "pt": "O índice ordena o portfólio, dispara a política de saúde mínima e é o "
                  "que o relatório executivo põe no topo.",
        },
    },
    {
        "clave": "dependencias",
        "modulo": "mvpm/dependencies.py",
        "titulo": {
            "es": "5 · Grafo de dependencias y bloqueos",
            "en": "5 · Dependency and blocker graph",
            "pt": "5 · Grafo de dependências e bloqueios",
        },
        "tecnico": {
            "es": "Con el campo `depende_de` se arma un grafo dirigido de tareas. De ahí "
                  "salen tres cosas: bloqueos activos, dependencias huérfanas (apuntan a "
                  "una tarea que no existe) e `impacto_si_se_atrasa()`, que recorre el "
                  "grafo hacia adelante y devuelve a cuántas tareas arrastra un atraso.",
            "en": "The `depende_de` field builds a directed task graph. Three things come "
                  "out of it: active blockers, orphan dependencies (pointing at a task "
                  "that does not exist), and `impacto_si_se_atrasa()`, which walks the "
                  "graph forward and returns how many tasks a delay drags with it.",
            "pt": "Com o campo `depende_de` monta-se um grafo dirigido de tarefas. Dali "
                  "saem três coisas: bloqueios ativos, dependências órfãs (apontam para "
                  "uma tarefa que não existe) e `impacto_si_se_atrasa()`, que percorre o "
                  "grafo à frente e devolve quantas tarefas um atraso arrasta.",
        },
        "criollo": {
            "es": "El programa sabe qué tarea está frenando a cuáles otras. Antes de la "
                  "reunión ya se puede decir: si esta se atrasa una semana, se caen estas "
                  "otras cuatro. Y avisa cuando una tarea depende de algo que no existe.",
            "en": "The program knows which task is holding up which others. Before the "
                  "meeting you can already say: if this one slips a week, these four go "
                  "with it. And it flags tasks that depend on something that isn't there.",
            "pt": "O programa sabe qual tarefa está travando quais outras. Antes da "
                  "reunião já dá para dizer: se esta atrasar uma semana, caem estas outras "
                  "quatro. E avisa quando uma tarefa depende de algo que não existe.",
        },
        "porque": {
            "es": "El impacto de un atraso se estimaba a ojo en la reunión, y a ojo "
                  "siempre se subestima. La dependencia huérfana es peor: es un plan que "
                  "parece completo y tiene un agujero que nadie ve hasta que frena.",
            "en": "The impact of a delay used to be eyeballed in the meeting, and "
                  "eyeballing always underestimates. The orphan dependency is worse: a "
                  "plan that looks complete with a hole nobody sees until it stalls.",
            "pt": "O impacto de um atraso era estimado a olho na reunião, e a olho sempre "
                  "se subestima. A dependência órfã é pior: um plano que parece completo "
                  "com um buraco que ninguém vê até travar.",
        },
        "repercusion": {
            "es": "«A cuántas tareas impacta» entra como factor en el backlog priorizado: "
                  "una tarea que desbloquea a otras sube sola en la lista.",
            "en": "\"How many tasks it impacts\" feeds into the prioritized backlog: a task "
                  "that unblocks others rises up the list on its own.",
            "pt": "\"A quantas tarefas impacta\" entra como fator no backlog priorizado: uma "
                  "tarefa que desbloqueia outras sobe sozinha na lista.",
        },
    },
    {
        "clave": "backlog",
        "modulo": "mvpm/prioritizer.py",
        "titulo": {
            "es": "6 · Backlog priorizado por valor esperado",
            "en": "6 · Backlog ranked by expected value",
            "pt": "6 · Backlog priorizado por valor esperado",
        },
        "tecnico": {
            "es": "Cada tarea recibe un `valor_esperado` que combina prioridad "
                  "declarada, días restantes al vencimiento y cantidad de tareas que "
                  "desbloquea. El orden es el de ese número, no el de carga.",
            "en": "Each task gets an `expected value` combining declared priority, days "
                  "left to due date, and how many tasks it unblocks. The ordering is that "
                  "number's, not the order things were entered.",
            "pt": "Cada tarefa recebe um `valor esperado` que combina prioridade "
                  "declarada, dias restantes ao vencimento e quantidade de tarefas que "
                  "desbloqueia. A ordem é a desse número, não a de cadastro.",
        },
        "criollo": {
            "es": "La lista de qué hacer primero sale calculada, no discutida. Y lo que "
                  "está bloqueando a varios sube aunque nadie lo haya marcado urgente.",
            "en": "The what-to-do-first list comes out computed, not argued. And whatever "
                  "is blocking several things rises even if nobody marked it urgent.",
            "pt": "A lista do que fazer primeiro sai calculada, não discutida. E o que "
                  "está bloqueando vários sobe mesmo que ninguém o tenha marcado urgente.",
        },
        "porque": {
            "es": "Priorizar por prioridad declarada solamente premia a quien grita más "
                  "fuerte. Sumar el vencimiento y el desbloqueo hace que la lista refleje "
                  "el costo real de no hacer la tarea.",
            "en": "Ranking by declared priority alone rewards whoever shouts loudest. "
                  "Adding the due date and the unblocking effect makes the list reflect "
                  "the real cost of not doing the task.",
            "pt": "Priorizar só por prioridade declarada premia quem grita mais alto. "
                  "Somar o vencimento e o desbloqueio faz a lista refletir o custo real de "
                  "não fazer a tarefa.",
        },
        "repercusion": {
            "es": "Es la tabla que consume el tablero de BI y la que sale en el reporte "
                  "semanal: la misma lista que ve el equipo la ve la dirección.",
            "en": "It is the table the BI dashboard consumes and the one in the weekly "
                  "report: the team and the board look at the same list.",
            "pt": "É a tabela que o painel de BI consome e a que sai no relatório semanal: "
                  "a mesma lista que a equipe vê, a direção vê.",
        },
    },
    {
        "clave": "politicas",
        "modulo": "mvpm/policies.py",
        "titulo": {
            "es": "7 · Políticas de gobernanza evaluadas",
            "en": "7 · Governance policies, evaluated",
            "pt": "7 · Políticas de governança avaliadas",
        },
        "tecnico": {
            "es": "Seis reglas se evalúan sobre el portafolio entero y devuelven una "
                  "tabla con `clave` estable, estado y la evidencia concreta de cada "
                  "incumplimiento. La `clave` no se traduce nunca: es la que usa el "
                  "asesor para armar identificadores de problema que no cambian al "
                  "cambiar de idioma.",
            "en": "Six rules are evaluated over the whole portfolio and return a table "
                  "with a stable `clave`, a status, and the concrete evidence for each "
                  "breach. That `clave` is never translated: the advisor uses it to build "
                  "problem identifiers that do not change when the language does.",
            "pt": "Seis regras são avaliadas sobre todo o portfólio e devolvem uma tabela "
                  "com `clave` estável, estado e a evidência concreta de cada "
                  "descumprimento. Essa `clave` nunca é traduzida: é a que o assessor usa "
                  "para montar identificadores de problema que não mudam com o idioma.",
        },
        "criollo": {
            "es": "Las reglas de la casa —todo proyecto tiene dueño, ninguno sin fecha "
                  "de fin, los críticos se revisan— dejan de ser un documento que nadie "
                  "abre y pasan a ser un chequeo automático con la lista de quién no la "
                  "cumple.",
            "en": "The house rules — every project has an owner, none without an end date, "
                  "critical ones get reviewed — stop being a document nobody opens and "
                  "become an automatic check with the list of who is not meeting them.",
            "pt": "As regras da casa — todo projeto tem dono, nenhum sem data de fim, os "
                  "críticos são revisados — deixam de ser um documento que ninguém abre e "
                  "viram uma checagem automática com a lista de quem não cumpre.",
        },
        "porque": {
            "es": "La clave estable no es un detalle: cuando el identificador salía del "
                  "nombre traducido de la política, cambiar de idioma duplicaba los "
                  "seguimientos — el mismo problema aparecía dos veces, como si fueran "
                  "dos.",
            "en": "The stable key is not a detail: when the identifier came from the "
                  "policy's translated name, switching languages duplicated the "
                  "follow-ups — the same problem showed up twice, as if there were two.",
            "pt": "A chave estável não é detalhe: quando o identificador saía do nome "
                  "traduzido da política, mudar de idioma duplicava os acompanhamentos — "
                  "o mesmo problema aparecia duas vezes, como se fossem dois.",
        },
        "repercusion": {
            "es": "Cada incumplimiento entra al detector de problemas con su evidencia, "
                  "así que la recomendación que se ve después nunca es genérica.",
            "en": "Every breach enters the problem detector with its evidence, so the "
                  "recommendation you see later is never generic.",
            "pt": "Cada descumprimento entra no detector de problemas com sua evidência, "
                  "então a recomendação que se vê depois nunca é genérica.",
        },
    },
    {
        "clave": "asesor",
        "modulo": "mvpm/advisor.py",
        "titulo": {
            "es": "8 · Detección de problemas y recomendación",
            "en": "8 · Problem detection and recommendation",
            "pt": "8 · Detecção de problemas e recomendação",
        },
        "tecnico": {
            "es": "Cruza todo lo anterior —bloqueos, huérfanas, proyectos en riesgo, "
                  "sobre presupuesto, sobrecarga de personas, políticas incumplidas— y "
                  "emite una lista de problemas con id estable por tipo y entidad. La "
                  "sugerencia sale de reglas; la IA es opcional y sólo redacta.",
            "en": "It crosses everything above — blockers, orphans, at-risk projects, "
                  "over budget, overloaded people, breached policies — and emits a list of "
                  "problems with a stable id per type and entity. The suggestion comes "
                  "from rules; AI is optional and only does the wording.",
            "pt": "Cruza tudo o anterior — bloqueios, órfãs, projetos em risco, acima do "
                  "orçamento, sobrecarga de pessoas, políticas descumpridas — e emite uma "
                  "lista de problemas com id estável por tipo e entidade. A sugestão sai "
                  "de regras; a IA é opcional e só redige.",
        },
        "criollo": {
            "es": "En vez de mirar seis pantallas, una lista de qué está mal hoy, con el "
                  "nombre del proyecto o de la persona. Y si la misma cosa sigue mal la "
                  "semana que viene, es el mismo ítem — no uno nuevo.",
            "en": "Instead of scanning six screens, one list of what is wrong today, with "
                  "the project's or person's name on it. And if the same thing is still "
                  "wrong next week, it is the same item — not a new one.",
            "pt": "Em vez de olhar seis telas, uma lista do que está mal hoje, com o nome "
                  "do projeto ou da pessoa. E se a mesma coisa continuar mal na semana que "
                  "vem, é o mesmo item — não um novo.",
        },
        "porque": {
            "es": "El id estable es lo que permite hacer seguimiento de verdad: sin él, "
                  "cada corrida generaba ítems nuevos y era imposible saber si un "
                  "problema se estaba resolviendo o repitiendo.",
            "en": "The stable id is what makes real follow-up possible: without it, every "
                  "run produced new items and there was no telling whether a problem was "
                  "being solved or just repeating.",
            "pt": "O id estável é o que permite acompanhamento de verdade: sem ele, cada "
                  "execução gerava itens novos e era impossível saber se um problema "
                  "estava sendo resolvido ou se repetindo.",
        },
        "repercusion": {
            "es": "Es la entrada del copiloto y del reporte ejecutivo. Todo lo que la IA "
                  "comenta más adelante sale de acá, no de su imaginación.",
            "en": "It is the input to the copilot and the executive report. Everything the "
                  "AI comments on later comes from here, not from its imagination.",
            "pt": "É a entrada do copiloto e do relatório executivo. Tudo o que a IA "
                  "comenta mais adiante sai daqui, não da sua imaginação.",
        },
    },
    {
        "clave": "ia",
        "modulo": "mvpm/ai.py",
        "titulo": {
            "es": "9 · Copiloto de IA: aditivo, nunca bloqueante",
            "en": "9 · AI copilot: additive, never blocking",
            "pt": "9 · Copiloto de IA: aditivo, nunca bloqueante",
        },
        "tecnico": {
            "es": "El motor de reglas —catálogo, salud, dependencias, backlog, "
                  "políticas— no llama a ninguna IA. El asistente sólo ofrece el "
                  "proveedor cuya clave de entorno esté configurada, y si no hay "
                  "ninguna, el producto funciona completo igual. Ninguna clave se "
                  "hardcodea.",
            "en": "The rules engine — catalogue, health, dependencies, backlog, policies — "
                  "calls no AI at all. The assistant only offers the provider whose "
                  "environment key is configured, and with none configured the product "
                  "still works in full. No key is ever hardcoded.",
            "pt": "O motor de regras — catálogo, saúde, dependências, backlog, políticas — "
                  "não chama nenhuma IA. O assistente só oferece o provedor cuja chave de "
                  "ambiente esteja configurada, e sem nenhuma o produto funciona completo "
                  "do mesmo jeito. Nenhuma chave é fixada no código.",
        },
        "criollo": {
            "es": "La IA suma, nunca es el cuello de botella. Si se cae el proveedor, si "
                  "no se contrató, o si la empresa no quiere mandar datos afuera, el "
                  "programa sigue dando exactamente los mismos números.",
            "en": "The AI adds, it is never the bottleneck. If the provider goes down, if "
                  "it was never contracted, or if the company will not send data outside, "
                  "the program still gives exactly the same numbers.",
            "pt": "A IA soma, nunca é o gargalo. Se o provedor cair, se não foi "
                  "contratado, ou se a empresa não quer mandar dados para fora, o programa "
                  "continua dando exatamente os mesmos números.",
        },
        "porque": {
            "es": "Un producto de gestión que sin IA no responde es un producto que "
                  "depende de un tercero para funcionar — y de su factura, su latencia y "
                  "su política de datos. Acá la IA es una mejora, no un requisito.",
            "en": "A management product that answers nothing without AI is one that "
                  "depends on a third party to work — and on its invoice, its latency and "
                  "its data policy. Here AI is an improvement, not a requirement.",
            "pt": "Um produto de gestão que sem IA não responde é um produto que depende "
                  "de um terceiro para funcionar — e da sua fatura, sua latência e sua "
                  "política de dados. Aqui a IA é uma melhoria, não um requisito.",
        },
        "repercusion": {
            "es": "Es lo que hace vendible el producto en una empresa con política "
                  "estricta de datos: se puede instalar y usar entero sin que salga una "
                  "sola fila a internet.",
            "en": "It is what makes the product sellable in a company with a strict data "
                  "policy: it can be installed and used in full without a single row "
                  "leaving the building.",
            "pt": "É o que torna o produto vendável numa empresa com política estrita de "
                  "dados: dá para instalar e usar inteiro sem que uma única linha saia "
                  "para a internet.",
        },
    },
    {
        "clave": "gobernanza",
        "modulo": "mvpm/governance.py",
        "titulo": {
            "es": "10 · Validación humana con firma",
            "en": "10 · Human validation, signed",
            "pt": "10 · Validação humana com assinatura",
        },
        "tecnico": {
            "es": "Todo dato manual entra primero como propuesta (de IA o de plantilla), "
                  "y recién queda vigente cuando el data owner lo valida. Lo validado se "
                  "guarda por la vía versionada de la etapa 2, con nombre y cargo de "
                  "quien firmó.",
            "en": "Every manual entry arrives first as a proposal (from AI or a template), "
                  "and only takes effect once the data owner validates it. What is "
                  "validated is stored through the versioned path from stage 2, with the "
                  "name and role of whoever signed.",
            "pt": "Todo dado manual entra primeiro como proposta (de IA ou de modelo), e "
                  "só fica vigente quando o data owner valida. O validado é gravado pela "
                  "via versionada da etapa 2, com nome e cargo de quem assinou.",
        },
        "criollo": {
            "es": "La máquina propone, la persona decide, y queda escrito quién decidió. "
                  "Es la diferencia entre «lo dijo el sistema» y «lo aprobó Fulano el "
                  "martes».",
            "en": "The machine proposes, a person decides, and who decided is on the "
                  "record. That is the difference between \"the system said so\" and "
                  "\"So-and-so approved it on Tuesday\".",
            "pt": "A máquina propõe, a pessoa decide, e fica escrito quem decidiu. É a "
                  "diferença entre \"foi o sistema que disse\" e \"Fulano aprovou na "
                  "terça\".",
        },
        "porque": {
            "es": "Sin esta etapa, una sugerencia automática se vuelve dato oficial sin "
                  "que nadie se haga cargo. Con ella, la responsabilidad tiene nombre.",
            "en": "Without this stage, an automated suggestion becomes official data with "
                  "nobody accountable. With it, responsibility has a name.",
            "pt": "Sem esta etapa, uma sugestão automática vira dado oficial sem ninguém "
                  "se responsabilizar. Com ela, a responsabilidade tem nome.",
        },
        "repercusion": {
            "es": "Es lo que hace que el reporte exportado se pueda presentar en un "
                  "comité: cada dato sensible tiene detrás una persona que lo validó.",
            "en": "It is what makes the exported report presentable to a committee: every "
                  "sensitive figure has a person behind it who validated it.",
            "pt": "É o que faz o relatório exportado poder ser apresentado num comitê: "
                  "cada dado sensível tem atrás uma pessoa que o validou.",
        },
    },
    {
        "clave": "salidas",
        "modulo": "api/main.py",
        "titulo": {
            "es": "11 · Tres bocas sobre el mismo motor",
            "en": "11 · Three mouths on one engine",
            "pt": "11 · Três bocas sobre o mesmo motor",
        },
        "tecnico": {
            "es": "El mismo motor sale por tres lados: el dashboard Streamlit, la API "
                  "REST local que sirve las tablas a Power BI/Tableau, y un servidor MCP "
                  "de sólo lectura. Ninguna de las tres recalcula nada: las tres piden "
                  "los mismos números a `mvpm/`.",
            "en": "The same engine comes out three ways: the Streamlit dashboard, the "
                  "local REST API that serves the tables to Power BI/Tableau, and a "
                  "read-only MCP server. None of the three recomputes anything: all three "
                  "ask `mvpm/` for the same numbers.",
            "pt": "O mesmo motor sai por três lados: o painel Streamlit, a API REST local "
                  "que serve as tabelas ao Power BI/Tableau, e um servidor MCP somente "
                  "leitura. Nenhuma das três recalcula nada: as três pedem os mesmos "
                  "números a `mvpm/`.",
        },
        "criollo": {
            "es": "El número que ve el equipo en la pantalla es el mismo que llega al "
                  "tablero de dirección y el mismo que responde el asistente. No hay dos "
                  "versiones de la verdad discutiéndose en una reunión.",
            "en": "The number the team sees on screen is the same one that reaches the "
                  "board's dashboard and the same one the assistant answers with. No two "
                  "versions of the truth arguing in a meeting.",
            "pt": "O número que a equipe vê na tela é o mesmo que chega ao painel da "
                  "direção e o mesmo que o assistente responde. Não há duas versões da "
                  "verdade discutindo numa reunião.",
        },
        "porque": {
            "es": "Es el error clásico de BI: el tablero reimplementa el cálculo y "
                  "empieza a diferir del sistema de origen. Acá el conector pide la tabla "
                  "ya calculada, no los datos crudos para recalcular.",
            "en": "It is the classic BI failure: the dashboard reimplements the "
                  "calculation and starts to diverge from the source system. Here the "
                  "connector asks for the finished table, not raw data to recompute.",
            "pt": "É o erro clássico de BI: o painel reimplementa o cálculo e começa a "
                  "divergir do sistema de origem. Aqui o conector pede a tabela já "
                  "calculada, não os dados crus para recalcular.",
        },
        "repercusion": {
            "es": "Agregar una salida nueva no obliga a reescribir ninguna regla, y una "
                  "corrección en el motor llega a las tres al mismo tiempo.",
            "en": "Adding a new output forces no rule to be rewritten, and a fix in the "
                  "engine reaches all three at once.",
            "pt": "Adicionar uma saída nova não obriga a reescrever nenhuma regra, e uma "
                  "correção no motor chega às três ao mesmo tempo.",
        },
    },
    {
        "clave": "distribucion",
        "modulo": "mvpm/licensing.py",
        "titulo": {
            "es": "12 · Prueba, licencia y entrega",
            "en": "12 · Trial, licence and delivery",
            "pt": "12 · Teste, licença e entrega",
        },
        "tecnico": {
            "es": "Prueba completa de 7 días sin pedir nada; al vencer se bloquea el "
                  "acceso pero NO se borra un solo dato. La licencia es un token firmado "
                  "que el servidor emite recién después de verificar el pago contra el "
                  "proveedor — nunca confiando en lo que dice el cliente. El instalador "
                  "sale de un único build con dos ediciones.",
            "en": "A full 7-day trial with nothing asked up front; when it expires access "
                  "locks but NOT one row is deleted. The licence is a signed token the "
                  "server issues only after verifying the payment against the provider — "
                  "never trusting what the client claims. The installer comes from a "
                  "single build with two editions.",
            "pt": "Teste completo de 7 dias sem pedir nada; ao vencer, o acesso é "
                  "bloqueado mas NÃO se apaga um único dado. A licença é um token assinado "
                  "que o servidor emite só depois de verificar o pagamento junto ao "
                  "provedor — nunca confiando no que o cliente diz. O instalador sai de um "
                  "único build com duas edições.",
        },
        "criollo": {
            "es": "Se prueba entero una semana sin tarjeta. Si no se paga, se cierra la "
                  "puerta pero el trabajo cargado sigue ahí: el día que se activa la "
                  "licencia, está todo como se dejó.",
            "en": "You try the whole thing for a week with no card. If it is not paid, the "
                  "door closes but the work you loaded stays: the day the licence is "
                  "activated, everything is as you left it.",
            "pt": "Testa-se inteiro por uma semana sem cartão. Se não pagar, a porta "
                  "fecha, mas o trabalho carregado continua lá: no dia em que a licença é "
                  "ativada, está tudo como foi deixado.",
        },
        "porque": {
            "es": "Borrar los datos de quien no renovó convierte una venta perdida en un "
                  "cliente enojado. Y verificar el pago del lado del servidor es lo único "
                  "que evita que alguien se emita su propia licencia.",
            "en": "Deleting the data of someone who did not renew turns a lost sale into "
                  "an angry customer. And verifying payment server-side is the only thing "
                  "stopping someone from issuing their own licence.",
            "pt": "Apagar os dados de quem não renovou transforma uma venda perdida num "
                  "cliente irritado. E verificar o pagamento no servidor é a única coisa "
                  "que impede alguém de emitir a própria licença.",
        },
        "repercusion": {
            "es": "Cierra el circuito: el mismo motor que calcula es el que se empaqueta, "
                  "se licencia y se entrega, sin una segunda versión del producto para la "
                  "demo.",
            "en": "It closes the loop: the same engine that computes is the one packaged, "
                  "licensed and delivered, with no second version of the product for the "
                  "demo.",
            "pt": "Fecha o circuito: o mesmo motor que calcula é o que se empacota, "
                  "licencia e entrega, sem uma segunda versão do produto para a demo.",
        },
    },
]

#: Los campos traducibles de cada etapa, en el orden en que se leen.
CAMPOS = ("titulo", "tecnico", "criollo", "porque", "repercusion")

for _e in _ETAPAS:
    for _campo in CAMPOS:
        _faltan = set(LANGS) - set(_e[_campo])
        assert not _faltan, f"{_e['clave']}.{_campo} sin traducir a {_faltan}"


def etapas(lang: str = "es") -> list[dict]:
    """Las etapas del pipeline en orden, resueltas a un idioma.

    `clave` y `modulo` salen sin traducir a propósito: la primera ordena y la
    usan los tests, el segundo es una ruta de archivo real."""
    lang = lang if lang in LANGS else "es"
    return [
        {"clave": e["clave"], "modulo": e["modulo"],
         **{c: e[c][lang] for c in CAMPOS}}
        for e in _ETAPAS
    ]


def etapa(clave: str, lang: str = "es") -> dict:
    """Una etapa puntual. Lanza KeyError si no existe, a propósito: un enlace
    a una etapa que se borró tiene que romper acá y no mostrar una pantalla
    vacía."""
    for e in etapas(lang):
        if e["clave"] == clave:
            return e
    raise KeyError(f"no existe la etapa {clave!r}")


def claves() -> list[str]:
    return [e["clave"] for e in _ETAPAS]
