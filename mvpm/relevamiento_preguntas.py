# © 2026 Martín Viera. Todos los derechos reservados.
"""El banco de preguntas de relevamiento, separado de la lógica.

Está en su propio archivo por una razón práctica: es CONTENIDO —crece cada vez
que un relevamiento enseña algo— y la lógica que lo consume (`mvpm/
relevamiento.py`) casi no cambia. Mezclarlos obligaría a leer 700 líneas de
preguntas para tocar una función de veinte.

Cada pregunta trae su **por qué**: sin eso, un consultor nuevo la lee, no
entiende qué está buscando, y la hace de memoria sin escuchar la respuesta. El
por qué es lo que convierte un cuestionario en un relevamiento.

Las áreas siguen el pipeline del CLIENTE —de dónde sale el dato hasta quién lo
consume—, no el de este producto. Son cosas distintas: `mvpm/bitacora.py`
cuenta cómo funciona MV Project Management; esto pregunta cómo funciona
Conaprole.
"""

from __future__ import annotations

#: Las áreas, EN ORDEN de pipeline. La clave nunca se traduce: ordena, agrupa
#: y es la que se guarda en la base.
AREAS: list[dict] = [
    {
        "clave": "fuentes",
        "nombre": {"es": "1 · Fuentes y sistemas de origen",
                   "en": "1 · Sources and source systems",
                   "pt": "1 · Fontes e sistemas de origem"},
        "por_que": {
            "es": "Todo lo demás depende de acá. Un pipeline sobre una fuente que "
                  "no es la autoritativa produce números correctos de un dato "
                  "equivocado.",
            "en": "Everything else depends on this. A pipeline over a source that "
                  "is not authoritative produces correct numbers for the wrong "
                  "data.",
            "pt": "Todo o resto depende daqui. Um pipeline sobre uma fonte que não "
                  "é a autoritativa produz números corretos de um dado errado."},
    },
    {
        "clave": "ingesta",
        "nombre": {"es": "2 · Ingesta y frecuencia",
                   "en": "2 · Ingestion and frequency",
                   "pt": "2 · Ingestão e frequência"},
        "por_que": {
            "es": "Define qué se puede prometer. La mitad de las discusiones por "
                  "un tablero \"desactualizado\" son en realidad un acuerdo de "
                  "frecuencia que nunca se hizo explícito.",
            "en": "It defines what can be promised. Half the arguments about an "
                  "\"out-of-date\" dashboard are really a frequency agreement that "
                  "was never made explicit.",
            "pt": "Define o que se pode prometer. Metade das discussões por um "
                  "painel \"desatualizado\" é, na verdade, um acordo de frequência "
                  "que nunca foi explicitado."},
    },
    {
        "clave": "calidad",
        "nombre": {"es": "3 · Calidad y reglas de negocio",
                   "en": "3 · Quality and business rules",
                   "pt": "3 · Qualidade e regras de negócio"},
        "por_que": {
            "es": "Es donde el proyecto se cae tarde y caro. Las reglas que nadie "
                  "escribió existen igual: viven en la cabeza de una persona y "
                  "aparecen recién cuando el número no le cierra.",
            "en": "This is where projects fail late and expensively. The rules "
                  "nobody wrote down exist anyway: they live in one person's head "
                  "and surface only when a number looks wrong to them.",
            "pt": "É onde o projeto cai tarde e caro. As regras que ninguém "
                  "escreveu existem do mesmo jeito: vivem na cabeça de uma pessoa "
                  "e aparecem só quando o número não fecha."},
    },
    {
        "clave": "modelado",
        "nombre": {"es": "4 · Modelado y definiciones",
                   "en": "4 · Modelling and definitions",
                   "pt": "4 · Modelagem e definições"},
        "por_que": {
            "es": "Dos áreas que llaman \"venta\" a cosas distintas no discuten "
                  "sobre el tablero: discuten sobre la definición, y eso no se "
                  "arregla con SQL.",
            "en": "Two departments that call different things \"sales\" are not "
                  "arguing about the dashboard: they are arguing about the "
                  "definition, and SQL does not fix that.",
            "pt": "Duas áreas que chamam de \"venda\" coisas diferentes não "
                  "discutem sobre o painel: discutem sobre a definição, e isso não "
                  "se resolve com SQL."},
    },
    {
        "clave": "orquestacion",
        "nombre": {"es": "5 · Orquestación y dependencias",
                   "en": "5 · Orchestration and dependencies",
                   "pt": "5 · Orquestração e dependências"},
        "por_que": {
            "es": "Determina qué pasa un martes a las 3 de la mañana cuando algo "
                  "falla. Si la respuesta es \"alguien se da cuenta al otro día\", "
                  "eso es un dato del relevamiento, no un detalle.",
            "en": "It determines what happens at 3am on a Tuesday when something "
                  "breaks. If the answer is \"someone notices the next day\", that "
                  "is a finding, not a detail.",
            "pt": "Determina o que acontece numa terça às 3 da manhã quando algo "
                  "falha. Se a resposta é \"alguém percebe no dia seguinte\", isso "
                  "é um achado, não um detalhe."},
    },
    {
        "clave": "gobernanza",
        "nombre": {"es": "6 · Gobernanza y propiedad del dato",
                   "en": "6 · Governance and data ownership",
                   "pt": "6 · Governança e propriedade do dado"},
        "por_que": {
            "es": "Sin dueño no hay a quién preguntarle cuando el dato no cierra, "
                  "y el proyecto se frena esperando una decisión que nadie tiene "
                  "atribuciones para tomar.",
            "en": "With no owner there is nobody to ask when the data does not add "
                  "up, and the project stalls waiting for a decision nobody is "
                  "authorised to make.",
            "pt": "Sem dono não há a quem perguntar quando o dado não fecha, e o "
                  "projeto trava esperando uma decisão que ninguém tem alçada para "
                  "tomar."},
    },
    {
        "clave": "seguridad",
        "nombre": {"es": "7 · Seguridad y acceso",
                   "en": "7 · Security and access",
                   "pt": "7 · Segurança e acesso"},
        "por_que": {
            "es": "Se pregunta al principio o se descubre al final, cuando el "
                  "área de seguridad frena una entrega que ya estaba lista.",
            "en": "You ask this at the start, or you discover it at the end, when "
                  "the security team blocks a delivery that was already done.",
            "pt": "Pergunta-se no começo ou se descobre no fim, quando a área de "
                  "segurança trava uma entrega que já estava pronta."},
    },
    {
        "clave": "consumo",
        "nombre": {"es": "8 · Consumo: BI, reportes y usuarios",
                   "en": "8 · Consumption: BI, reports and users",
                   "pt": "8 · Consumo: BI, relatórios e usuários"},
        "por_que": {
            "es": "Es lo único que el cliente va a ver. Un pipeline impecable que "
                  "termina en un reporte que nadie abre es un proyecto fallido con "
                  "buena ingeniería.",
            "en": "It is the only part the client will ever see. A flawless "
                  "pipeline ending in a report nobody opens is a failed project "
                  "with good engineering.",
            "pt": "É a única parte que o cliente vai ver. Um pipeline impecável que "
                  "termina num relatório que ninguém abre é um projeto fracassado "
                  "com boa engenharia."},
    },
    {
        "clave": "operacion",
        "nombre": {"es": "9 · Operación, soporte y continuidad",
                   "en": "9 · Operations, support and continuity",
                   "pt": "9 · Operação, suporte e continuidade"},
        "por_que": {
            "es": "Define quién se queda con esto cuando la consultora se va. Es "
                  "la pregunta que más se saltea y la que decide si el trabajo "
                  "sobrevive seis meses.",
            "en": "It defines who keeps this running once the consultancy leaves. "
                  "It is the most skipped question and the one that decides whether "
                  "the work survives six months.",
            "pt": "Define quem fica com isto quando a consultoria sai. É a pergunta "
                  "mais pulada e a que decide se o trabalho sobrevive seis meses."},
    },
]


def _p(clave: str, area: str, es: str, en: str, pt: str,
       por_que_es: str, por_que_en: str, por_que_pt: str) -> dict:
    return {"clave": clave, "area": area,
            "pregunta": {"es": es, "en": en, "pt": pt},
            "por_que": {"es": por_que_es, "en": por_que_en, "pt": por_que_pt}}


#: Las preguntas. `clave` estable —se guarda en la base y no se traduce—, y
#: `area` apunta a AREAS. El orden dentro de cada área es el orden en que
#: conviene hacerlas en la reunión.
PREGUNTAS: list[dict] = [
    # ------------------------------------------------------------ fuentes
    _p("fuentes_maestro", "fuentes",
       "¿Qué sistema es el dueño del dato maestro de cada entidad (clientes, "
       "artículos, proveedores)?",
       "Which system owns the master data for each entity (customers, items, "
       "suppliers)?",
       "Qual sistema é dono do dado mestre de cada entidade (clientes, itens, "
       "fornecedores)?",
       "Define de dónde se lee y quién valida. Si hay dos candidatos, ya "
       "encontraste el primer conflicto del proyecto.",
       "It defines what to read from and who validates. If there are two "
       "candidates, you already found the project's first conflict.",
       "Define de onde se lê e quem valida. Se há dois candidatos, você já "
       "encontrou o primeiro conflito do projeto."),
    _p("fuentes_planillas", "fuentes",
       "¿Qué información crítica vive hoy en planillas de Excel fuera de los "
       "sistemas?",
       "What critical information lives today in spreadsheets outside the "
       "systems?",
       "Que informação crítica vive hoje em planilhas fora dos sistemas?",
       "Siempre hay alguna, y nunca aparece en el diagrama de arquitectura. "
       "Descubrirla en la etapa de pruebas cuesta semanas.",
       "There is always one, and it never appears in the architecture diagram. "
       "Finding it during testing costs weeks.",
       "Sempre há alguma, e nunca aparece no diagrama de arquitetura. "
       "Descobri-la na fase de testes custa semanas."),
    _p("fuentes_acceso", "fuentes",
       "¿Se puede leer directamente de la base, o hay que pedir extractos a un "
       "equipo?",
       "Can we read straight from the database, or do we have to request "
       "extracts from a team?",
       "Dá para ler direto da base, ou é preciso pedir extrações a uma equipe?",
       "Cambia por completo el cronograma: un extracto pedido por ticket "
       "introduce una espera humana en cada iteración.",
       "It changes the schedule completely: an extract requested by ticket puts "
       "a human wait into every iteration.",
       "Muda completamente o cronograma: uma extração pedida por chamado "
       "introduz uma espera humana em cada iteração."),
    _p("fuentes_historico", "fuentes",
       "¿Cuánto historial hay disponible y desde cuándo es confiable?",
       "How much history is available, and from when is it trustworthy?",
       "Quanto histórico está disponível e desde quando é confiável?",
       "No es lo mismo \"tenemos diez años\" que \"tenemos diez años pero antes "
       "de 2021 la carga era manual\". Lo segundo define desde dónde se puede "
       "comparar.",
       "\"We have ten years\" is not the same as \"we have ten years but before "
       "2021 it was keyed in by hand\". The second one defines how far back you "
       "can compare.",
       "Não é o mesmo \"temos dez anos\" e \"temos dez anos, mas antes de 2021 a "
       "carga era manual\". O segundo define desde quando dá para comparar."),

    # ------------------------------------------------------------ ingesta
    _p("ingesta_frecuencia", "ingesta",
       "¿Con qué frecuencia necesita el negocio ver el dato actualizado, y con "
       "cuál se conforma?",
       "How often does the business need the data refreshed, and what will it "
       "settle for?",
       "Com que frequência o negócio precisa ver o dado atualizado, e com qual "
       "se conforma?",
       "Son dos números distintos y la diferencia entre ellos es presupuesto. "
       "Preguntar sólo el primero lleva a construir tiempo real para un reporte "
       "que se mira los lunes.",
       "They are two different numbers, and the gap between them is budget. "
       "Asking only the first leads to building real-time for a report read on "
       "Mondays.",
       "São dois números diferentes e a diferença entre eles é orçamento. "
       "Perguntar só o primeiro leva a construir tempo real para um relatório "
       "que se lê nas segundas."),
    _p("ingesta_ventana", "ingesta",
       "¿Hay una ventana horaria en la que NO se puede tocar el sistema de "
       "origen?",
       "Is there a time window when the source system must not be touched?",
       "Existe uma janela de horário em que NÃO se pode tocar o sistema de "
       "origem?",
       "Una extracción pesada en hora pico de facturación es la forma más "
       "rápida de que el área de sistemas del cliente cancele el proyecto.",
       "A heavy extraction during peak invoicing hours is the fastest way to "
       "get the client's IT team to cancel the project.",
       "Uma extração pesada no pico de faturamento é a forma mais rápida de a "
       "área de TI do cliente cancelar o projeto."),
    _p("ingesta_volumen", "ingesta",
       "¿Qué volumen mueve cada carga: filas por día y crecimiento esperado?",
       "What volume does each load move: rows per day and expected growth?",
       "Que volume cada carga move: linhas por dia e crescimento esperado?",
       "Decide la arquitectura entera. Una solución que anda con un millón de "
       "filas puede no andar con cincuenta.",
       "It decides the whole architecture. A solution that works at one million "
       "rows may not work at fifty.",
       "Decide a arquitetura inteira. Uma solução que funciona com um milhão de "
       "linhas pode não funcionar com cinquenta."),
    _p("ingesta_reproceso", "ingesta",
       "Cuando una carga falla o llega mal, ¿se puede volver a correr sin "
       "duplicar datos?",
       "When a load fails or arrives wrong, can it be re-run without "
       "duplicating data?",
       "Quando uma carga falha ou chega errada, dá para rodar de novo sem "
       "duplicar dados?",
       "Si la respuesta es no, cada error va a requerir intervención manual "
       "para siempre. Es el costo oculto más caro de un pipeline.",
       "If the answer is no, every error will need manual intervention forever. "
       "It is the most expensive hidden cost of a pipeline.",
       "Se a resposta for não, cada erro vai exigir intervenção manual para "
       "sempre. É o custo oculto mais caro de um pipeline."),

    # ------------------------------------------------------------ calidad
    _p("calidad_reglas", "calidad",
       "¿Qué reglas de negocio filtran o corrigen datos hoy, aunque estén sólo "
       "en la cabeza de alguien?",
       "What business rules filter or fix data today, even if they only live in "
       "somebody's head?",
       "Que regras de negócio filtram ou corrigem dados hoje, mesmo que só "
       "vivam na cabeça de alguém?",
       "Es LA pregunta del relevamiento. Estas reglas existen igual: si no se "
       "documentan ahora, aparecen cuando el gerente dice que el número está "
       "mal y nadie sabe por qué.",
       "This is THE question. These rules exist regardless: if they are not "
       "documented now, they surface when the manager says the number is wrong "
       "and nobody knows why.",
       "É A pergunta do levantamento. Essas regras existem de qualquer jeito: se "
       "não forem documentadas agora, aparecem quando o gerente diz que o número "
       "está errado e ninguém sabe por quê."),
    _p("calidad_excepciones", "calidad",
       "¿Qué casos se excluyen habitualmente de los reportes (anulados, "
       "internos, pruebas, sucursales especiales)?",
       "Which cases are routinely excluded from reports (voided, internal, "
       "tests, special branches)?",
       "Que casos são habitualmente excluídos dos relatórios (anulados, "
       "internos, testes, filiais especiais)?",
       "Cada exclusión no declarada es una diferencia futura contra el número "
       "que el cliente ya tiene, y el que pierde credibilidad es el nuevo "
       "tablero.",
       "Every undeclared exclusion is a future gap against the number the client "
       "already has, and it is the new dashboard that loses credibility.",
       "Cada exclusão não declarada é uma diferença futura contra o número que o "
       "cliente já tem, e quem perde credibilidade é o painel novo."),
    _p("calidad_nulos", "calidad",
       "¿Qué campos vienen incompletos con frecuencia, y qué se hace hoy con "
       "esos registros?",
       "Which fields often arrive incomplete, and what is done with those "
       "records today?",
       "Que campos vêm incompletos com frequência, e o que se faz hoje com "
       "esses registros?",
       "Define si el pipeline descarta, imputa o alerta — tres decisiones de "
       "negocio distintas que nadie debería tomar por su cuenta.",
       "It defines whether the pipeline drops, imputes or alerts — three "
       "different business decisions nobody should make alone.",
       "Define se o pipeline descarta, imputa ou alerta — três decisões de "
       "negócio diferentes que ninguém deveria tomar sozinho."),
    _p("calidad_conciliacion", "calidad",
       "¿Contra qué número se va a validar que el pipeline está bien?",
       "Against which number will we validate that the pipeline is right?",
       "Contra qual número vamos validar que o pipeline está certo?",
       "Sin un número de control acordado ANTES, la validación se convierte en "
       "una discusión de opiniones el día de la entrega.",
       "Without a control figure agreed BEFOREHAND, validation turns into a "
       "battle of opinions on delivery day.",
       "Sem um número de controle acordado ANTES, a validação vira uma discussão "
       "de opiniões no dia da entrega."),

    # ----------------------------------------------------------- modelado
    _p("modelado_definiciones", "modelado",
       "¿Cómo define cada área los indicadores clave (venta, cliente activo, "
       "unidad vendida)?",
       "How does each department define the key indicators (sales, active "
       "customer, unit sold)?",
       "Como cada área define os indicadores-chave (venda, cliente ativo, "
       "unidade vendida)?",
       "Preguntarlo por separado a dos áreas es la forma más rápida de "
       "descubrir que no coinciden, que es un hallazgo del relevamiento y no un "
       "problema técnico.",
       "Asking two departments separately is the fastest way to discover they "
       "disagree — which is a finding, not a technical problem.",
       "Perguntar separadamente a duas áreas é a forma mais rápida de descobrir "
       "que não coincidem, o que é um achado e não um problema técnico."),
    _p("modelado_granularidad", "modelado",
       "¿A qué nivel de detalle se necesita el dato: transacción, día, cliente, "
       "sucursal?",
       "At what level of detail is the data needed: transaction, day, customer, "
       "branch?",
       "Em que nível de detalhe o dado é necessário: transação, dia, cliente, "
       "filial?",
       "Guardar menos detalle del necesario es irreversible sin rehacer el "
       "histórico. Guardar de más sólo cuesta disco.",
       "Storing less detail than needed is irreversible without rebuilding "
       "history. Storing more only costs disk.",
       "Guardar menos detalhe do necessário é irreversível sem refazer o "
       "histórico. Guardar demais só custa disco."),
    _p("modelado_jerarquias", "modelado",
       "¿Qué jerarquías se usan para agrupar (categorías, zonas, canales) y "
       "quién las mantiene?",
       "Which hierarchies are used for grouping (categories, regions, channels) "
       "and who maintains them?",
       "Que hierarquias são usadas para agrupar (categorias, zonas, canais) e "
       "quem as mantém?",
       "Las jerarquías cambian y casi nunca hay un proceso: enterarse de que "
       "las mantiene una persona en su planilla cambia el diseño.",
       "Hierarchies change and there is rarely a process: learning that one "
       "person maintains them in a spreadsheet changes the design.",
       "As hierarquias mudam e quase nunca há um processo: saber que uma pessoa "
       "as mantém na planilha dela muda o desenho."),
    _p("modelado_cambios", "modelado",
       "Cuando un cliente cambia de zona o un artículo de categoría, ¿el "
       "histórico se reescribe o se conserva como estaba?",
       "When a customer changes region or an item changes category, is history "
       "rewritten or kept as it was?",
       "Quando um cliente muda de zona ou um item de categoria, o histórico é "
       "reescrito ou mantido como estava?",
       "Es la pregunta que define si los reportes del año pasado van a cambiar "
       "solos. Decidirlo tarde obliga a rehacer el modelo.",
       "It is the question that decides whether last year's reports will change "
       "by themselves. Deciding late means redoing the model.",
       "É a pergunta que define se os relatórios do ano passado vão mudar "
       "sozinhos. Decidir tarde obriga a refazer o modelo."),

    # ------------------------------------------------------- orquestacion
    _p("orq_herramienta", "orquestacion",
       "¿Con qué se agendan hoy los procesos y quién tiene acceso a esa "
       "herramienta?",
       "What schedules the processes today, and who has access to that tool?",
       "Com o que os processos são agendados hoje e quem tem acesso a essa "
       "ferramenta?",
       "Si la respuesta es \"el Task Scheduler de una PC\", eso es un riesgo "
       "operativo que hay que anotar, no un detalle de implementación.",
       "If the answer is \"Task Scheduler on someone's PC\", that is an "
       "operational risk to record, not an implementation detail.",
       "Se a resposta for \"o Agendador de Tarefas de um PC\", isso é um risco "
       "operacional a registrar, não um detalhe de implementação."),
    _p("orq_dependencias", "orquestacion",
       "¿Qué procesos dependen de que este termine, aguas abajo?",
       "Which processes depend on this one finishing, downstream?",
       "Que processos dependem de este terminar, rio abaixo?",
       "Un pipeline que se atrasa media hora puede no importar, o puede dejar "
       "sin datos a la reunión de las 8. La diferencia está acá.",
       "A pipeline half an hour late may not matter, or may leave the 8am "
       "meeting with no data. The difference is here.",
       "Um pipeline meia hora atrasado pode não importar, ou pode deixar a "
       "reunião das 8 sem dados. A diferença está aqui."),
    _p("orq_fallas", "orquestacion",
       "Cuando algo falla de madrugada, ¿quién se entera y por qué medio?",
       "When something fails overnight, who finds out and through what channel?",
       "Quando algo falha de madrugada, quem fica sabendo e por qual meio?",
       "\"Nos damos cuenta al otro día cuando alguien abre el reporte\" es una "
       "respuesta muy común y define el nivel de monitoreo que hay que "
       "construir.",
       "\"We notice the next day when someone opens the report\" is a very common "
       "answer and it sets the monitoring level that has to be built.",
       "\"Percebemos no dia seguinte quando alguém abre o relatório\" é uma "
       "resposta muito comum e define o nível de monitoramento a construir."),

    # -------------------------------------------------------- gobernanza
    _p("gob_dueno", "gobernanza",
       "¿Quién es el dueño de cada dominio de dato y tiene atribuciones para "
       "decidir sobre él?",
       "Who owns each data domain, and are they authorised to decide about it?",
       "Quem é o dono de cada domínio de dado e tem alçada para decidir sobre "
       "ele?",
       "Las dos mitades importan: alguien nombrado dueño que después tiene que "
       "pedir permiso no resuelve nada, sólo agrega un paso.",
       "Both halves matter: someone named owner who then has to ask permission "
       "solves nothing, it just adds a step.",
       "As duas metades importam: alguém nomeado dono que depois precisa pedir "
       "permissão não resolve nada, só adiciona um passo."),
    _p("gob_cambios", "gobernanza",
       "¿Cómo se avisa hoy cuando cambia la estructura de un sistema de origen?",
       "How are we told today when a source system's structure changes?",
       "Como se avisa hoje quando muda a estrutura de um sistema de origem?",
       "Si la respuesta es \"no se avisa\", el pipeline se va a romper sin "
       "aviso y hay que diseñarlo defensivo desde el día uno.",
       "If the answer is \"we aren't\", the pipeline will break without warning "
       "and has to be designed defensively from day one.",
       "Se a resposta for \"não se avisa\", o pipeline vai quebrar sem aviso e "
       "precisa ser desenhado defensivo desde o primeiro dia."),
    _p("gob_glosario", "gobernanza",
       "¿Existe un glosario o diccionario de datos, y está actualizado?",
       "Is there a glossary or data dictionary, and is it current?",
       "Existe um glossário ou dicionário de dados, e está atualizado?",
       "Las dos partes de la pregunta se responden distinto muy seguido: "
       "\"existe\" y \"sirve\" no son lo mismo.",
       "The two halves are often answered differently: \"it exists\" and \"it is "
       "useful\" are not the same.",
       "As duas partes são respondidas de forma diferente com frequência: "
       "\"existe\" e \"serve\" não são o mesmo."),

    # --------------------------------------------------------- seguridad
    _p("seg_clasificacion", "seguridad",
       "¿Hay datos personales o sensibles en lo que vamos a mover, y bajo qué "
       "clasificación?",
       "Is there personal or sensitive data in what we will move, and under "
       "what classification?",
       "Há dados pessoais ou sensíveis no que vamos mover, e sob qual "
       "classificação?",
       "Define obligaciones legales y también dónde puede correr el proceso. "
       "Preguntarlo tarde puede invalidar la arquitectura entera.",
       "It sets legal obligations and also where the process may run. Asking "
       "late can invalidate the whole architecture.",
       "Define obrigações legais e também onde o processo pode rodar. Perguntar "
       "tarde pode invalidar a arquitetura inteira."),
    _p("seg_donde_corre", "seguridad",
       "¿El procesamiento puede correr fuera de la infraestructura del cliente, "
       "o tiene que quedarse adentro?",
       "May the processing run outside the client's infrastructure, or must it "
       "stay inside?",
       "O processamento pode rodar fora da infraestrutura do cliente, ou tem "
       "que ficar dentro?",
       "Decide si se puede usar un servicio en la nube o hay que instalar en "
       "una VM del cliente. Cambia costo, plazo y herramientas.",
       "It decides whether a cloud service is possible or everything must be "
       "installed on a client VM. It changes cost, timeline and tooling.",
       "Decide se dá para usar um serviço em nuvem ou se é preciso instalar numa "
       "VM do cliente. Muda custo, prazo e ferramentas."),
    _p("seg_accesos", "seguridad",
       "¿Cómo se piden y se revocan los accesos, y cuánto suele demorar?",
       "How are accesses requested and revoked, and how long does it usually "
       "take?",
       "Como os acessos são pedidos e revogados, e quanto costuma demorar?",
       "El plazo de un acceso es tiempo de proyecto. Dos semanas para una "
       "credencial de lectura mueve el cronograma entero.",
       "Access lead time is project time. Two weeks for a read credential moves "
       "the whole schedule.",
       "O prazo de um acesso é tempo de projeto. Duas semanas para uma "
       "credencial de leitura move o cronograma inteiro."),

    # ----------------------------------------------------------- consumo
    _p("cons_quien", "consumo",
       "¿Quién va a usar esto, con qué frecuencia y para tomar qué decisión?",
       "Who will use this, how often, and to make what decision?",
       "Quem vai usar isto, com que frequência e para tomar que decisão?",
       "\"Para tomar qué decisión\" es la parte que casi nunca se pregunta y la "
       "que evita construir un tablero que se mira una vez.",
       "\"To make what decision\" is the part almost never asked, and the one "
       "that prevents building a dashboard looked at once.",
       "\"Para tomar que decisão\" é a parte quase nunca perguntada e a que evita "
       "construir um painel olhado uma vez."),
    _p("cons_herramienta", "consumo",
       "¿Con qué herramienta consumen hoy y hay licencias para todos los que "
       "van a necesitarlas?",
       "What tool do they use today, and are there licences for everyone who "
       "will need one?",
       "Com que ferramenta consomem hoje e há licenças para todos os que vão "
       "precisar?",
       "La licencia faltante aparece siempre al final, cuando el tablero está "
       "listo y la mitad del área no puede abrirlo.",
       "The missing licence always shows up at the end, when the dashboard is "
       "ready and half the department cannot open it.",
       "A licença faltante sempre aparece no fim, quando o painel está pronto e "
       "metade da área não consegue abrir."),
    _p("cons_hoy", "consumo",
       "¿Qué reporte usan hoy para esto y qué le falta o le sobra?",
       "What report do they use for this today, and what does it lack or have "
       "too much of?",
       "Que relatório usam hoje para isto e o que falta ou sobra nele?",
       "Siempre hay algo previo. Entenderlo evita reconstruir lo mismo y da el "
       "número contra el cual el cliente va a comparar.",
       "There is always something already. Understanding it avoids rebuilding "
       "the same thing and gives the number the client will compare against.",
       "Sempre há algo anterior. Entendê-lo evita reconstruir a mesma coisa e dá "
       "o número contra o qual o cliente vai comparar."),

    # --------------------------------------------------------- operacion
    _p("ope_quien_mantiene", "operacion",
       "Cuando terminemos, ¿quién mantiene esto y con qué conocimientos cuenta?",
       "When we are done, who maintains this and what skills do they have?",
       "Quando terminarmos, quem mantém isto e com que conhecimentos conta?",
       "Determina en qué tecnología conviene construir. Una solución elegante "
       "que nadie del cliente sabe mantener es una dependencia permanente, y "
       "eso hay que decirlo.",
       "It determines what to build with. An elegant solution nobody at the "
       "client can maintain is a permanent dependency, and that has to be said "
       "out loud.",
       "Determina em que tecnologia convém construir. Uma solução elegante que "
       "ninguém do cliente sabe manter é uma dependência permanente, e isso "
       "precisa ser dito."),
    _p("ope_documentacion", "operacion",
       "¿Qué documentación hace falta entregar y en qué formato la consumen?",
       "What documentation must be delivered, and in what format do they "
       "consume it?",
       "Que documentação precisa ser entregue e em que formato eles consomem?",
       "Acordarlo al principio evita la discusión del último día, cuando el "
       "pago depende de un entregable que nadie definió.",
       "Agreeing at the start avoids the last-day argument, when payment depends "
       "on a deliverable nobody defined.",
       "Combinar no começo evita a discussão do último dia, quando o pagamento "
       "depende de um entregável que ninguém definiu."),
    _p("ope_soporte", "operacion",
       "¿Qué se espera de nosotros después de la entrega y por cuánto tiempo?",
       "What is expected from us after delivery, and for how long?",
       "O que se espera de nós depois da entrega, e por quanto tempo?",
       "Es una pregunta comercial disfrazada de técnica: sin respuesta, el "
       "soporte informal se come el margen del proyecto siguiente.",
       "It is a commercial question dressed as a technical one: unanswered, "
       "informal support eats the margin of the next project.",
       "É uma pergunta comercial disfarçada de técnica: sem resposta, o suporte "
       "informal come a margem do projeto seguinte."),
]
