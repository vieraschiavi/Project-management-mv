# © 2026 Martín Viera. Todos los derechos reservados.
"""Diccionario de traducciones de la app (ES/EN/PT) con fallback a español."""

_STRINGS = {
    "app_title": {"es": "MV Project Management", "en": "MV Project Management", "pt": "MV Project Management"},
    "nav_portfolio": {"es": "Portafolio", "en": "Portfolio", "pt": "Portfólio"},
    "nav_tasks": {"es": "Tareas", "en": "Tasks", "pt": "Tarefas"},
    "nav_users": {"es": "Usuarios", "en": "Users", "pt": "Usuários"},
    "nav_health": {"es": "Salud de proyecto", "en": "Project health", "pt": "Saúde do projeto"},
    "nav_dependencies": {"es": "Dependencias", "en": "Dependencies", "pt": "Dependências"},
    "nav_backlog": {"es": "Backlog priorizado", "en": "Prioritized backlog", "pt": "Backlog priorizado"},
    "nav_copilot": {"es": "Copiloto", "en": "Copilot", "pt": "Copiloto"},
    "nav_advisor": {"es": "Asistente IA", "en": "AI Advisor", "pt": "Assistente IA"},
    "nav_reports": {"es": "Reportes", "en": "Reports", "pt": "Relatórios"},
    "nav_reviews": {"es": "Reseñas", "en": "Reviews", "pt": "Avaliações"},
    "nav_glossary": {"es": "Glosario", "en": "Glossary", "pt": "Glossário"},
    "nav_policies": {"es": "Políticas", "en": "Policies", "pt": "Políticas"},
    "nav_import": {"es": "Importar datos", "en": "Import data", "pt": "Importar dados"},
    "nav_tutorial": {"es": "Tutorial", "en": "Tutorial", "pt": "Tutorial"},
    "nav_case_study": {"es": "Caso de uso completo", "en": "Full use case", "pt": "Caso de uso completo"},
    "nav_real_demo": {"es": "Demo con datos reales", "en": "Real-data demo", "pt": "Demo com dados reais"},
    "nav_pharma": {"es": "Demo laboratorio (Pharma)", "en": "Pharma lab demo", "pt": "Demo laboratório (Pharma)"},
    "nav_pmbok": {"es": "Metodología PMBOK", "en": "PMBOK methodology", "pt": "Metodologia PMBOK"},
    "nav_governance": {"es": "Gobernanza de datos", "en": "Data governance", "pt": "Governança de dados"},
    "nav_organigrama": {"es": "Organigrama y responsables", "en": "Org chart & owners", "pt": "Organograma e responsáveis"},
    "nav_plantillas": {"es": "Plantillas por rubro", "en": "Industry templates", "pt": "Modelos por setor"},
    "nav_conectores": {"es": "Conectores ERP", "en": "ERP connectors", "pt": "Conectores ERP"},
    "nav_data_eng": {"es": "Ingeniería de datos", "en": "Data engineering", "pt": "Engenharia de dados"},
    "nav_capacitacion": {"es": "Capacitación por rol", "en": "Training by role", "pt": "Treinamento por função"},
    "nav_config_ia": {"es": "Configuración de IA", "en": "AI settings", "pt": "Configuração de IA"},
    "cfg_titulo": {"es": "Configuración de IA",
                   "en": "AI settings",
                   "pt": "Configuração de IA"},
    "cfg_intro": {
        "es": "Elegí qué modelo usa cada proveedor de IA que tengas configurado. El modelo es "
              "la palanca principal del gasto: dentro de un mismo proveedor, el más caro y el "
              "más barato se llevan más de un orden de magnitud por token. El motor de reglas "
              "no gasta nada y sigue funcionando igual sin importar lo que elijas acá.",
        "en": "Choose which model each configured AI provider uses. The model is the main cost "
              "lever: within one provider, the priciest and the cheapest differ by more than an "
              "order of magnitude per token. The rules engine costs nothing and works the same "
              "regardless of what you pick here.",
        "pt": "Escolha qual modelo cada provedor de IA configurado usa. O modelo é a principal "
              "alavanca de custo: dentro de um mesmo provedor, o mais caro e o mais barato "
              "diferem em mais de uma ordem de grandeza por token. O motor de regras não custa "
              "nada e funciona igual, independentemente do que você escolher aqui.",
    },
    "cfg_sin_proveedores": {
        "es": "No hay ninguna clave de IA configurada, así que no hay nada que elegir. "
              "El producto funciona completo sin IA: la IA sólo redacta mejor lo que el motor "
              "de reglas ya calculó. Para habilitar un proveedor, exportá su variable de "
              "entorno antes de abrir el programa:",
        "en": "No AI key is configured, so there is nothing to choose. The product works fully "
              "without AI: AI only rewords what the rules engine already computed. To enable a "
              "provider, export its environment variable before launching:",
        "pt": "Nenhuma chave de IA está configurada, então não há o que escolher. O produto "
              "funciona por completo sem IA: a IA apenas redige melhor o que o motor de regras "
              "já calculou. Para habilitar um provedor, exporte sua variável de ambiente antes "
              "de abrir o programa:",
    },
    "cfg_actualizar": {"es": "Actualizar modelos desde mi API",
                       "en": "Refresh models from my API",
                       "pt": "Atualizar modelos da minha API"},
    "cfg_actualizar_ayuda": {
        "es": "Le pregunta a tu API qué modelos tiene habilitados TU clave. No hay ninguna "
              "lista precargada en el programa: los catálogos cambian todos los meses y no "
              "todas las claves tienen habilitados los mismos modelos.",
        "en": "Asks your API which models YOUR key has enabled. Nothing is preloaded in the "
              "program: catalogs change every month and not every key has the same models "
              "enabled.",
        "pt": "Pergunta à sua API quais modelos SUA chave tem habilitados. Nada vem pré-carregado "
              "no programa: os catálogos mudam todo mês e nem toda chave tem os mesmos modelos "
              "habilitados.",
    },
    "cfg_sin_catalogo": {
        "es": "Todavía no le preguntamos nada a tu API. Tocá «Actualizar modelos» para traer "
              "los que tu clave tiene habilitados, o escribí el identificador a mano.",
        "en": "We have not asked your API anything yet. Hit “Refresh models” to fetch the ones "
              "your key has enabled, or type the identifier manually.",
        "pt": "Ainda não perguntamos nada à sua API. Toque em “Atualizar modelos” para trazer os "
              "que sua chave tem habilitados, ou digite o identificador manualmente.",
    },
    "cfg_modelo": {"es": "Modelo", "en": "Model", "pt": "Modelo"},
    "cfg_modelo_manual": {"es": "…o escribí el identificador a mano",
                          "en": "…or type the identifier manually",
                          "pt": "…ou digite o identificador manualmente"},
    "cfg_guardar": {"es": "Guardar elección", "en": "Save choice", "pt": "Salvar escolha"},
    "cfg_guardado": {"es": "Guardado. Se aplica al Asistente IA y al Copiloto desde ahora.",
                     "en": "Saved. It applies to the AI Advisor and the Copilot from now on.",
                     "pt": "Salvo. Vale para o Assistente IA e o Copiloto a partir de agora."},
    "cfg_traidos": {"es": "modelo(s) traído(s) de tu API",
                    "en": "model(s) fetched from your API",
                    "pt": "modelo(s) trazido(s) da sua API"},
    "cfg_en_uso": {"es": "En uso ahora", "en": "In use now", "pt": "Em uso agora"},
    "cfg_sin_elegir": {"es": "sin elegir", "en": "not chosen", "pt": "sem escolher"},
    "cfg_historial": {"es": "Historial de cambios",
                      "en": "Change history",
                      "pt": "Histórico de alterações"},
    "kpi_projects": {"es": "Proyectos activos", "en": "Active projects", "pt": "Projetos ativos"},
    "kpi_health": {"es": "Índice de salud", "en": "Health index", "pt": "Índice de saúde"},
    "kpi_at_risk": {"es": "Proyectos en riesgo", "en": "Projects at risk", "pt": "Projetos em risco"},
    "kpi_budget": {"es": "Presupuesto ejecutado", "en": "Budget executed", "pt": "Orçamento executado"},
    "kpi_blocked": {"es": "Tareas bloqueadas", "en": "Blocked tasks", "pt": "Tarefas bloqueadas"},
    "kpi_on_time": {"es": "A tiempo", "en": "On time", "pt": "No prazo"},
    "status_ok": {"es": "Saludable", "en": "Healthy", "pt": "Saudável"},
    "status_warn": {"es": "En observación", "en": "Watch", "pt": "Em observação"},
    "status_risk": {"es": "En riesgo", "en": "At risk", "pt": "Em risco"},
    "dim_scope": {"es": "Alcance", "en": "Scope", "pt": "Escopo"},
    "dim_schedule": {"es": "Cronograma", "en": "Schedule", "pt": "Cronograma"},
    "dim_budget": {"es": "Presupuesto", "en": "Budget", "pt": "Orçamento"},
    "dim_risk": {"es": "Riesgos", "en": "Risk", "pt": "Riscos"},
    "dim_dependencies": {"es": "Dependencias", "en": "Dependencies", "pt": "Dependências"},
    "dim_team": {"es": "Equipo", "en": "Team", "pt": "Equipe"},
    "reviews_empty_title": {
        "es": "Programa en fase beta",
        "en": "Program in beta",
        "pt": "Programa em fase beta",
    },
    "reviews_empty_body": {
        "es": "Todavía no tenemos reseñas de clientes reales — sé de los primeros en dejar la tuya cuando pruebes el producto.",
        "en": "We don't have real customer reviews yet — be one of the first to leave yours after trying the product.",
        "pt": "Ainda não temos avaliações de clientes reais — seja um dos primeiros a deixar a sua depois de testar o produto.",
    },

    # ---------------------------------------------------------- login / alta
    "login_try_now_header": {
        "es": "Probalo ahora, sin crear cuenta", "en": "Try it now, no account needed",
        "pt": "Experimente agora, sem criar conta"},
    "login_btn_upload_excel": {
        "es": "Subir mi Excel de proyectos", "en": "Upload my projects Excel",
        "pt": "Enviar minha planilha de projetos"},
    "login_btn_uk_demo": {
        "es": "Probar con datos reales del gobierno británico (132 proyectos)",
        "en": "Try it with real UK government data (132 projects)",
        "pt": "Testar com dados reais do governo britânico (132 projetos)"},
    "login_guest_caption": {
        "es": "Sin registro y sin tarjeta. En modo invitado los datos quedan en esta sesión "
              "del navegador y no se guardan — cuando quieras conservarlos, creás la cuenta "
              "y los volvés a subir.",
        "en": "No sign-up and no card. In guest mode your data stays in this browser session "
              "and isn't saved — when you want to keep it, create an account and upload it again.",
        "pt": "Sem cadastro e sem cartão. No modo convidado os dados ficam nesta sessão do "
              "navegador e não são salvos — quando quiser mantê-los, crie a conta e envie de novo."},
    "login_create_admin_header": {
        "es": "Creá la cuenta de administrador", "en": "Create the administrator account",
        "pt": "Crie a conta de administrador"},
    "login_create_admin_caption": {
        "es": "Sos la primera persona en usar este servidor — tu cuenta va a ser admin. El "
              "resto del equipo se registra después con su propio usuario y contraseña.",
        "en": "You're the first person using this server — your account will be admin. The "
              "rest of the team registers afterward with their own username and password.",
        "pt": "Você é a primeira pessoa a usar este servidor — sua conta vai ser admin. O "
              "resto da equipe se cadastra depois com usuário e senha próprios."},
    "field_name": {"es": "Nombre", "en": "Name", "pt": "Nome"},
    "field_email": {"es": "Email", "en": "Email", "pt": "E-mail"},
    "field_password_min8": {
        "es": "Contraseña (mín. 8 caracteres)", "en": "Password (min. 8 characters)",
        "pt": "Senha (mín. 8 caracteres)"},
    "field_password": {"es": "Contraseña", "en": "Password", "pt": "Senha"},
    "login_btn_create_admin": {
        "es": "Crear cuenta de administrador", "en": "Create administrator account",
        "pt": "Criar conta de administrador"},
    "tab_login": {"es": "Ingresar", "en": "Log in", "pt": "Entrar"},
    "tab_register": {"es": "Crear cuenta", "en": "Create account", "pt": "Criar conta"},
    "login_err_bad_credentials": {
        "es": "Email o contraseña incorrectos.", "en": "Incorrect email or password.",
        "pt": "E-mail ou senha incorretos."},

    # -------------------------------------------------- sidebar / licencia
    "license_token_label": {"es": "Token de licencia", "en": "License token", "pt": "Token de licença"},
    "license_token_help": {
        "es": "Se emite automáticamente al pagar el plan Professional. Se pega una sola vez: "
              "queda guardado en esta computadora. Sin token, corrés la prueba completa de 7 "
              "días con todo desbloqueado.",
        "en": "Issued automatically when you pay for the Professional plan. Paste it once: it "
              "stays saved on this computer. Without a token, you run the full 7-day trial "
              "with everything unlocked.",
        "pt": "Emitido automaticamente ao pagar o plano Professional. Cole uma única vez: fica "
              "salvo neste computador. Sem token, você roda o teste completo de 7 dias com "
              "tudo desbloqueado."},
    "owner_no_key_error": {
        "es": "Esta máquina no tiene tu clave de licencias, así que no puedo firmar el modo "
              "dueño. Corré una vez MV_ProjectManagement_OWNER.bat y pegá tu clave privada: "
              "después no se pide nunca más.",
        "en": "This machine doesn't have your license key, so I can't sign owner mode. Run "
              "MV_ProjectManagement_OWNER.bat once and paste your private key: after that "
              "it's never asked again.",
        "pt": "Esta máquina não tem sua chave de licenças, então não posso assinar o modo "
              "dono. Rode uma vez o MV_ProjectManagement_OWNER.bat e cole sua chave privada: "
              "depois disso não é mais pedida."},
    "btn_logout": {"es": "Cerrar sesión", "en": "Log out", "pt": "Sair"},
    "role_admin": {"es": "admin", "en": "admin", "pt": "admin"},
    "role_miembro": {"es": "miembro", "en": "member", "pt": "membro"},
    "role_invitado": {"es": "invitado", "en": "guest", "pt": "convidado"},
    "msg_licencia_activa": {
        "es": "Licencia {plan} activa.", "en": "{plan} license active.",
        "pt": "Licença {plan} ativa."},
    "msg_trial_dias": {
        "es": "Prueba completa: te quedan {dias} día(s) con todo desbloqueado.",
        "en": "Full trial: {dias} day(s) left with everything unlocked.",
        "pt": "Teste completo: faltam {dias} dia(s) com tudo desbloqueado."},
    "msg_trial_vencida": {
        "es": "La prueba de 7 días venció. Tus datos están guardados: activá una licencia "
              "Professional para seguir usándolos.",
        "en": "The 7-day trial expired. Your data is saved: activate a Professional license "
              "to keep using it.",
        "pt": "O teste de 7 dias venceu. Seus dados estão salvos: ative uma licença "
              "Professional para continuar usando."},
    "msg_modo_owner": {
        "es": "Modo owner — sin restricciones de licencia.",
        "en": "Owner mode — no license restrictions.",
        "pt": "Modo owner — sem restrições de licença."},
    "msg_modo_invitado": {
        "es": "Modo invitado — nada se guarda", "en": "Guest mode — nothing is saved",
        "pt": "Modo convidado — nada é salvo"},
    "trial_dias_restantes": {
        "es": "Prueba: quedan {dias} día(s)", "en": "Trial: {dias} day(s) left",
        "pt": "Teste: faltam {dias} dia(s)"},
    "trial_vencida_title": {
        "es": "La prueba de 7 días venció", "en": "The 7-day trial expired",
        "pt": "O teste de 7 dias venceu"},
    "trial_vencida_data_ok": {
        "es": "**Tus datos siguen guardados.** Nada se borró: apenas cargues una licencia "
              "Professional válida, seguís exactamente donde estabas, con todos los "
              "proyectos, tareas, definiciones y responsables que cargaste.",
        "en": "**Your data is still saved.** Nothing was deleted: as soon as you load a valid "
              "Professional license, you're right back where you were, with every project, "
              "task, definition and owner you loaded.",
        "pt": "**Seus dados continuam salvos.** Nada foi apagado: assim que você carregar uma "
              "licença Professional válida, continua exatamente de onde parou, com todos os "
              "projetos, tarefas, definições e responsáveis que carregou."},
    "trial_vencida_steps": {
        "es": "1. Comprá el plan **Professional (US$9/usuario/mes)** desde la web.\n"
              "2. Al aprobarse el pago recibís un **token de licencia**.\n"
              "3. Pegalo en **«Token de licencia»** en la barra lateral y listo.",
        "en": "1. Buy the **Professional plan (US$9/user/month)** from the website.\n"
              "2. Once the payment is approved you get a **license token**.\n"
              "3. Paste it into **\"License token\"** in the sidebar and you're set.",
        "pt": "1. Compre o plano **Professional (US$9/usuário/mês)** pelo site.\n"
              "2. Ao aprovar o pagamento você recebe um **token de licença**.\n"
              "3. Cole em **\"Token de licença\"** na barra lateral e pronto."},
    "trial_vencida_contact": {
        "es": "¿Ya pagaste y no te llegó el token? Escribinos a vieraschiavi@gmail.com.",
        "en": "Already paid and didn't get the token? Write to us at vieraschiavi@gmail.com.",
        "pt": "Já pagou e não recebeu o token? Escreva para vieraschiavi@gmail.com."},

    # ------------------------------------------------------------- empresa
    "empresa_expander": {"es": "Empresa", "en": "Company", "pt": "Empresa"},
    "empresa_activa_label": {"es": "Empresa activa", "en": "Active company", "pt": "Empresa ativa"},
    "empresa_nueva_label": {"es": "Nueva empresa", "en": "New company", "pt": "Nova empresa"},
    "empresa_crear_btn": {"es": "Crear empresa", "en": "Create company", "pt": "Criar empresa"},
    "sidebar_section_label": {"es": "Sección", "en": "Section", "pt": "Seção"},

    # ------------------------------------------------------------- tutorial
    "tutorial_caption": {
        "es": "Guía operativa de cada herramienta del programa — cómo usarla, no solo qué es.",
        "en": "An operating guide for every tool in the program — how to use it, not just what it is.",
        "pt": "Guia operacional de cada ferramenta do programa — como usá-la, não só o que é."},
    "tutorial_como_usarlo": {"es": "**Cómo usarlo:**", "en": "**How to use it:**", "pt": "**Como usar:**"},
    "tutorial_tips": {"es": "**Tips:**", "en": "**Tips:**", "pt": "**Dicas:**"},

    # ---------------------------------------------------------- case_study
    "case_study_caption": {
        "es": "Un proyecto simulado completo, recorrido por las herramientas del programa paso a "
              "paso — con los números reales que calcula el motor sobre el dato de ejemplo, no un "
              "guion inventado para la demo.",
        "en": "One complete simulated project, walked through the program's tools step by step — "
              "with the real numbers the engine calculates on the sample data, not a script "
              "invented for the demo.",
        "pt": "Um projeto simulado completo, percorrido pelas ferramentas do programa passo a "
              "passo — com os números reais que o motor calcula sobre o dado de exemplo, não um "
              "roteiro inventado para a demo."},
    "case_study_chosen": {
        "es": "**Proyecto elegido:** {nombre} ({id}) — índice de salud {indice}/100, estado *{estado}*.",
        "en": "**Chosen project:** {nombre} ({id}) — health index {indice}/100, status *{estado}*.",
        "pt": "**Projeto escolhido:** {nombre} ({id}) — índice de saúde {indice}/100, status *{estado}*."},
    "case_study_no_data": {
        "es": "Todavía no cargaste tus propios proyectos — este recorrido usa el dato de ejemplo "
              "para que veas el flujo completo antes de cargar los tuyos.",
        "en": "You haven't loaded your own projects yet — this walkthrough uses the sample data "
              "so you can see the full flow before loading yours.",
        "pt": "Você ainda não carregou seus próprios projetos — este passo a passo usa o dado de "
              "exemplo para você ver o fluxo completo antes de carregar os seus."},

    # ---------------------------------------------------------- real_demo (UK)
    "real_demo_source_prefix": {"es": "Fuente: {fuente}", "en": "Source: {fuente}", "pt": "Fonte: {fuente}"},
    "real_demo_caption": {
        "es": "No son datos sintéticos — son 132 proyectos reales de gobierno, filtrados a los "
              "que tienen calificación de confianza y presupuesto numérico completos en el "
              "informe original. [Descargar el dataset original]({url}).",
        "en": "Not synthetic data — these are 132 real government projects, filtered to the ones "
              "with a complete confidence rating and numeric budget in the original report. "
              "[Download the original dataset]({url}).",
        "pt": "Não são dados sintéticos — são 132 projetos reais de governo, filtrados aos que "
              "têm classificação de confiança e orçamento numérico completos no relatório "
              "original. [Baixar o dataset original]({url})."},
    "real_demo_kpi_total": {"es": "Proyectos reales analizados", "en": "Real projects analyzed",
                            "pt": "Projetos reais analisados"},
    "real_demo_kpi_over": {"es": "Sobre presupuesto (año fiscal)", "en": "Over budget (fiscal year)",
                           "pt": "Acima do orçamento (ano fiscal)"},
    "real_demo_kpi_budget": {"es": "Presupuesto total", "en": "Total budget", "pt": "Orçamento total"},
    "real_demo_kpi_spent": {"es": "Ejecutado total", "en": "Total spent", "pt": "Total executado"},
    "real_demo_over_caption": {
        "es": "'Sobre presupuesto' compara el baseline y el ejecutado del año fiscal 2021/22 "
              "reportado por cada departamento — no el costo total a lo largo de vida del proyecto.",
        "en": "\"Over budget\" compares the baseline and actual spend for fiscal year 2021/22 as "
              "reported by each department — not the project's total lifetime cost.",
        "pt": "'Acima do orçamento' compara o baseline e o executado do ano fiscal 2021/22 "
              "reportado por cada departamento — não o custo total ao longo da vida do projeto."},
    "real_demo_ahorro": {
        "es": "**Ahorro estimado de tiempo**: revisar a mano estos {n} proyectos para encontrar "
              "cuáles están sobre presupuesto — a un supuesto de {min} minutos por proyecto, un "
              "número explícito, no medido — tomaría ~{hs} horas de trabajo manual de un PMO. El "
              "motor los detecta a todos en segundos, cada vez que se le pide.",
        "en": "**Estimated time saved**: manually reviewing these {n} projects to find which are "
              "over budget — at an assumed {min} minutes per project, an explicit, unmeasured "
              "figure — would take ~{hs} hours of manual PMO work. The engine detects them all in "
              "seconds, every time it's asked.",
        "pt": "**Economia de tempo estimada**: revisar à mão estes {n} projetos para encontrar "
              "quais estão acima do orçamento — a um suposto de {min} minutos por projeto, um "
              "número explícito, não medido — levaria ~{hs} horas de trabalho manual de um PMO. O "
              "motor os detecta todos em segundos, cada vez que solicitado."},
    "real_demo_top10": {"es": "Los 10 más desviados, detectados por el motor",
                        "en": "The 10 most off-track, detected by the engine",
                        "pt": "Os 10 mais desviados, detectados pelo motor"},
    "real_demo_two_cases": {"es": "Dos casos, con el texto real del informe anual",
                            "en": "Two cases, with real text from the annual report",
                            "pt": "Dois casos, com o texto real do relatório anual"},
    "real_demo_case_calc": {
        "es": "**Lo que calcula el motor sobre este proyecto:** presupuesto £{pres:.1f}M, "
              "ejecutado £{ejec:.1f}M ({pct}%) — {estado}",
        "en": "**What the engine calculates for this project:** budget £{pres:.1f}M, spent "
              "£{ejec:.1f}M ({pct}%) — {estado}",
        "pt": "**O que o motor calcula sobre este projeto:** orçamento £{pres:.1f}M, executado "
              "£{ejec:.1f}M ({pct}%) — {estado}"},
    "real_demo_over_flag": {"es": "marcado sobre presupuesto.", "en": "flagged as over budget.",
                            "pt": "marcado como acima do orçamento."},
    "real_demo_under_flag": {"es": "dentro de presupuesto.", "en": "within budget.",
                             "pt": "dentro do orçamento."},
    "real_demo_narrativa_h": {"es": "**Texto real del informe anual sobre el presupuesto:**",
                              "en": "**Real text from the annual report on budget:**",
                              "pt": "**Texto real do relatório anual sobre o orçamento:**"},
    "real_demo_revision_h": {"es": "**Texto real del informe anual sobre la revisión de entrega:**",
                             "en": "**Real text from the annual report on the delivery review:**",
                             "pt": "**Texto real do relatório anual sobre a revisão de entrega:**"},

    # -------------------------------------------------------------- pharma
    "pharma_caption1": {
        "es": "Fuente: {fuente} — [ClinicalTrials.gov]({url}). Un ensayo clínico es un proyecto: "
              "tiene sponsor (un laboratorio multinacional), fechas, fase y un estado que se "
              "comporta igual que el estado de un proyecto.",
        "en": "Source: {fuente} — [ClinicalTrials.gov]({url}). A clinical trial IS a project: it "
              "has a sponsor (a multinational lab), dates, a phase, and a status that behaves "
              "just like a project's status.",
        "pt": "Fonte: {fuente} — [ClinicalTrials.gov]({url}). Um ensaio clínico É um projeto: tem "
              "sponsor (um laboratório multinacional), datas, fase e um status que se comporta "
              "igual ao status de um projeto."},
    "pharma_caption2": {
        "es": "ClinicalTrials.gov no publica presupuesto, así que la señal de PM acá es el "
              "estado del ensayo (no la plata) — no se inventan cifras de presupuesto.",
        "en": "ClinicalTrials.gov doesn't publish budget data, so the PM signal here is the "
              "trial's status (not money) — no budget figures are invented.",
        "pt": "ClinicalTrials.gov não publica orçamento, então o sinal de PM aqui é o status do "
              "ensaio (não o dinheiro) — não se inventam valores de orçamento."},
    "pharma_kpi_total": {"es": "Ensayos reales analizados", "en": "Real trials analyzed",
                         "pt": "Ensaios reais analisados"},
    "pharma_kpi_risk": {"es": "En riesgo (terminados/suspendidos)", "en": "At risk (terminated/suspended)",
                        "pt": "Em risco (encerrados/suspensos)"},
    "pharma_kpi_labs": {"es": "Laboratorios", "en": "Labs", "pt": "Laboratórios"},
    "pharma_ahorro": {
        "es": "**Ahorro estimado**: revisar a mano estos {n} ensayos para marcar cuáles están "
              "frenados — a un supuesto explícito de {min} minutos por ensayo — serían ~{hs} horas "
              "de trabajo manual. El motor los clasifica a todos en segundos.",
        "en": "**Estimated savings**: manually reviewing these {n} trials to flag which are "
              "stalled — at an explicit assumed {min} minutes per trial — would be ~{hs} hours of "
              "manual work. The engine classifies them all in seconds.",
        "pt": "**Economia estimada**: revisar à mão estes {n} ensaios para marcar quais estão "
              "parados — a um suposto explícito de {min} minutos por ensaio — seriam ~{hs} horas "
              "de trabalho manual. O motor os classifica todos em segundos."},
    "pharma_by_status": {"es": "**Por estado (dato real del ensayo)**", "en": "**By status (real trial data)**",
                         "pt": "**Por status (dado real do ensaio)**"},
    "pharma_by_lab": {"es": "**Por laboratorio**", "en": "**By lab**", "pt": "**Por laboratório**"},
    "pharma_at_risk_h": {"es": "Ensayos que el motor marca en riesgo", "en": "Trials the engine flags as at risk",
                         "pt": "Ensaios que o motor marca em risco"},
    "pharma_to_bi_h": {"es": "De acá a Power BI, end-to-end", "en": "From here to Power BI, end to end",
                       "pt": "Daqui até o Power BI, de ponta a ponta"},
    "pharma_to_bi_body": {
        "es": "El mismo motor sirve estos ensayos por la **API REST local** (`./run.sh api`), así "
              "que Power BI se conecta al dato en vivo sin exportar planillas:\n\n"
              "1. Levantá la API: `./run.sh api` (queda en `http://127.0.0.1:8600`).\n"
              "2. Doble clic en `distribucion/powerbi/MV_ProjectManagement_Pharma.pbids` — Power "
              "BI Desktop abre ya conectado a `/api/demo/pharma`.\n"
              "3. Cargá y armá el tablero (ensayos por laboratorio, por estado, semáforo por "
              "criticidad).\n\nGuía completa: `distribucion/powerbi/README.md`.",
        "en": "The same engine serves these trials over the **local REST API** (`./run.sh api`), "
              "so Power BI connects to live data with no spreadsheet exports:\n\n"
              "1. Start the API: `./run.sh api` (runs at `http://127.0.0.1:8600`).\n"
              "2. Double-click `distribucion/powerbi/MV_ProjectManagement_Pharma.pbids` — Power "
              "BI Desktop opens already connected to `/api/demo/pharma`.\n"
              "3. Load and build the dashboard (trials by lab, by status, criticality traffic "
              "light).\n\nFull guide: `distribucion/powerbi/README.md`.",
        "pt": "O mesmo motor serve estes ensaios pela **API REST local** (`./run.sh api`), então o "
              "Power BI se conecta ao dado ao vivo sem exportar planilhas:\n\n"
              "1. Suba a API: `./run.sh api` (fica em `http://127.0.0.1:8600`).\n"
              "2. Clique duplo em `distribucion/powerbi/MV_ProjectManagement_Pharma.pbids` — o "
              "Power BI Desktop abre já conectado a `/api/demo/pharma`.\n"
              "3. Carregue e monte o painel (ensaios por laboratório, por status, semáforo por "
              "criticidade).\n\nGuia completo: `distribucion/powerbi/README.md`."},
    "pharma_download_bi": {"es": "Descargar la tabla lista para BI (CSV)",
                           "en": "Download the BI-ready table (CSV)",
                           "pt": "Baixar a tabela pronta para BI (CSV)"},

    # -------------------------------------------------------- portafolio/tareas
    "field_project_name": {"es": "Nombre del proyecto", "en": "Project name", "pt": "Nome do projeto"},
    "field_portfolio": {"es": "Portafolio", "en": "Portfolio", "pt": "Portfólio"},
    "field_sponsor": {"es": "Sponsor", "en": "Sponsor", "pt": "Sponsor"},
    "field_owner": {"es": "Dueño", "en": "Owner", "pt": "Responsável"},
    "field_segment": {"es": "Segmento", "en": "Segment", "pt": "Segmento"},
    "field_start_date": {"es": "Fecha de inicio", "en": "Start date", "pt": "Data de início"},
    "field_end_date": {"es": "Fecha de fin", "en": "End date", "pt": "Data de término"},
    "field_budget": {"es": "Presupuesto", "en": "Budget", "pt": "Orçamento"},
    "field_spent": {"es": "Ejecutado", "en": "Spent", "pt": "Executado"},
    "field_criticality": {"es": "Criticidad", "en": "Criticality", "pt": "Criticidade"},
    "btn_create_project": {"es": "Crear proyecto", "en": "Create project", "pt": "Criar projeto"},
    "err_name_required": {"es": "El nombre es obligatorio.", "en": "Name is required.",
                          "pt": "O nome é obrigatório."},
    "msg_project_created": {"es": "Proyecto '{nombre}' creado.", "en": "Project '{nombre}' created.",
                            "pt": "Projeto '{nombre}' criado."},
    "action_edit_or_archive_project": {"es": "Editar o archivar un proyecto",
                                       "en": "Edit or archive a project",
                                       "pt": "Editar ou arquivar um projeto"},
    "project_card_expander": {"es": "Ficha de proyecto (editar / archivar / eliminar)",
                              "en": "Project record (edit / archive / delete)",
                              "pt": "Ficha do projeto (editar / arquivar / excluir)"},
    "pick_a_project": {"es": "Elegí un proyecto", "en": "Pick a project", "pt": "Escolha um projeto"},
    "btn_save_changes": {"es": "Guardar cambios", "en": "Save changes", "pt": "Salvar alterações"},
    "msg_changes_saved": {"es": "Cambios guardados.", "en": "Changes saved.", "pt": "Alterações salvas."},
    "btn_archive_project": {"es": "Archivar proyecto", "en": "Archive project", "pt": "Arquivar projeto"},
    "msg_project_archived": {"es": "Proyecto archivado.", "en": "Project archived.", "pt": "Projeto arquivado."},
    "btn_delete_permanently": {"es": "Eliminar definitivamente", "en": "Delete permanently",
                               "pt": "Excluir definitivamente"},
    "msg_project_deleted": {"es": "Proyecto eliminado.", "en": "Project deleted.", "pt": "Projeto excluído."},
    "by_portfolio_h": {"es": "Por portafolio", "en": "By portfolio", "pt": "Por portfólio"},
    "new_task_expander": {"es": "Nueva tarea", "en": "New task", "pt": "Nova tarefa"},
    "warn_create_project_first": {"es": "Creá un proyecto primero.", "en": "Create a project first.",
                                  "pt": "Crie um projeto primeiro."},
    "field_project": {"es": "Proyecto", "en": "Project", "pt": "Projeto"},
    "field_task_title": {"es": "Título de la tarea", "en": "Task title", "pt": "Título da tarefa"},
    "field_assignee": {"es": "Responsable", "en": "Assignee", "pt": "Responsável"},
    "field_status": {"es": "Estado", "en": "Status", "pt": "Status"},
    "field_priority": {"es": "Prioridad", "en": "Priority", "pt": "Prioridade"},
    "field_due_date": {"es": "Vencimiento", "en": "Due date", "pt": "Vencimento"},
    "field_depends_on": {"es": "Depende de", "en": "Depends on", "pt": "Depende de"},
    "opt_none_fem": {"es": "(ninguna)", "en": "(none)", "pt": "(nenhuma)"},
    "btn_create_task": {"es": "Crear tarea", "en": "Create task", "pt": "Criar tarefa"},
    "err_title_required": {"es": "El título es obligatorio.", "en": "Title is required.",
                           "pt": "O título é obrigatório."},
    "msg_task_created": {"es": "Tarea '{titulo}' creada.", "en": "Task '{titulo}' created.",
                         "pt": "Tarefa '{titulo}' criada."},
    "action_edit_or_delete_task": {"es": "Editar o eliminar una tarea", "en": "Edit or delete a task",
                                   "pt": "Editar ou excluir uma tarefa"},
    "task_card_expander": {"es": "Ficha de tarea (editar / eliminar)", "en": "Task record (edit / delete)",
                           "pt": "Ficha da tarefa (editar / excluir)"},
    "pick_a_task": {"es": "Elegí una tarea", "en": "Pick a task", "pt": "Escolha uma tarefa"},
    "btn_delete_task": {"es": "Eliminar tarea", "en": "Delete task", "pt": "Excluir tarefa"},
    "msg_task_deleted": {"es": "Tarea eliminada.", "en": "Task deleted.", "pt": "Tarefa excluída."},

    # ---------------------------------------------------------------- salud
    "health_global_index": {"es": "{nav} — índice global: {n}/100", "en": "{nav} — overall index: {n}/100",
                            "pt": "{nav} — índice global: {n}/100"},
    "dim_matrix_h": {"es": "Matriz por dimensión", "en": "Matrix by dimension", "pt": "Matriz por dimensão"},

    # --------------------------------------------------------- dependencias
    "no_blocked_tasks": {"es": "No hay tareas bloqueadas activas.", "en": "No active blocked tasks.",
                         "pt": "Não há tarefas bloqueadas ativas."},
    "inconsistent_deps_h": {"es": "Dependencias inconsistentes", "en": "Inconsistent dependencies",
                            "pt": "Dependências inconsistentes"},
    "no_orphan_deps": {"es": "Sin dependencias huérfanas.", "en": "No orphan dependencies.",
                       "pt": "Sem dependências órfãs."},
    "orphan_deps_warn": {"es": "{n} dependencia(s) apuntan a una tarea inexistente.",
                         "en": "{n} dependenc(y/ies) point to a task that doesn't exist.",
                         "pt": "{n} dependência(s) apontam para uma tarefa inexistente."},

    # ---------------------------------------------------------------- backlog
    "backlog_caption": {
        "es": "Ordenado por valor esperado = criticidad × prioridad × urgencia × impacto en dependencias.",
        "en": "Sorted by expected value = criticality × priority × urgency × dependency impact.",
        "pt": "Ordenado por valor esperado = criticidade × prioridade × urgência × impacto em dependências."},

    # --------------------------------------------------------------- copiloto
    "copilot_caption": {
        "es": "El motor de reglas responde siempre. Si hay ANTHROPIC_API_KEY configurada y "
              "todavía hay cupo de IA en tu plan, Claude pule el lenguaje sin inventar cifras nuevas.",
        "en": "The rules engine always answers. If ANTHROPIC_API_KEY is configured and your plan "
              "still has AI quota, Claude polishes the language without inventing new figures.",
        "pt": "O motor de regras sempre responde. Se houver ANTHROPIC_API_KEY configurada e "
              "ainda houver cota de IA no seu plano, o Claude refina a linguagem sem inventar números."},
    "copilot_cupo_owner": {"es": "ilimitado (owner)", "en": "unlimited (owner)", "pt": "ilimitado (owner)"},
    "copilot_cupo_no_plan": {"es": "tu plan no incluye el copiloto con IA",
                             "en": "your plan doesn't include the AI copilot",
                             "pt": "seu plano não inclui o copiloto com IA"},
    "copilot_cupo_label": {"es": "Cupo de IA: {detalle}", "en": "AI quota: {detalle}",
                           "pt": "Cota de IA: {detalle}"},
    "copilot_ask_label": {"es": "Preguntá sobre el portafolio", "en": "Ask about the portfolio",
                          "pt": "Pergunte sobre o portfólio"},
    "copilot_ask_default": {"es": "¿Qué está bloqueando los proyectos?",
                            "en": "What's blocking the projects?",
                            "pt": "O que está bloqueando os projetos?"},
    "btn_ask": {"es": "Preguntar", "en": "Ask", "pt": "Perguntar"},
    "copilot_ai_enriched": {"es": "Respuesta enriquecida con IA", "en": "AI-enriched answer",
                            "pt": "Resposta enriquecida com IA"},
    "copilot_rules_only": {"es": "Respuesta del motor de reglas (sin IA)",
                           "en": "Rules-engine answer (no AI)", "pt": "Resposta do motor de regras (sem IA)"},

    # --------------------------------------------------------------- advisor
    "advisor_caption": {
        "es": "El motor de reglas detecta los problemas siempre. La redacción de la sugerencia se "
              "puede pulir con el proveedor de IA que tengas configurado — nunca inventa el "
              "problema ni el número que lo sustenta, sólo redacta mejor la acción sugerida.",
        "en": "The rules engine always detects the problems. The suggestion's wording can be "
              "polished with whichever AI provider you have configured — it never invents the "
              "problem or the number behind it, it only writes the suggested action more clearly.",
        "pt": "O motor de regras sempre detecta os problemas. A redação da sugestão pode ser "
              "refinada com o provedor de IA que você tiver configurado — nunca inventa o "
              "problema nem o número que o sustenta, só redige melhor a ação sugerida."},
    "advisor_rules_only": {"es": "Motor de reglas (sin IA)", "en": "Rules engine (no AI)",
                           "pt": "Motor de regras (sem IA)"},
    "advisor_no_providers": {
        "es": "Sin proveedores de IA configurados — corriendo 100% con el motor de reglas. Para "
              "sumar redacción con IA, configurá ANTHROPIC_API_KEY (Claude), o OPENAI_API_KEY + "
              "OPENAI_MODEL (ChatGPT), o GEMINI_API_KEY + GEMINI_MODEL (Gemini).",
        "en": "No AI providers configured — running 100% on the rules engine. To add AI-polished "
              "wording, set ANTHROPIC_API_KEY (Claude), or OPENAI_API_KEY + OPENAI_MODEL "
              "(ChatGPT), or GEMINI_API_KEY + GEMINI_MODEL (Gemini).",
        "pt": "Sem provedores de IA configurados — rodando 100% com o motor de regras. Para "
              "somar redação com IA, configure ANTHROPIC_API_KEY (Claude), ou OPENAI_API_KEY + "
              "OPENAI_MODEL (ChatGPT), ou GEMINI_API_KEY + GEMINI_MODEL (Gemini)."},
    "advisor_suggestion_label": {"es": "Redacción de la sugerencia", "en": "Suggestion wording",
                                 "pt": "Redação da sugestão"},
    "advisor_none_found": {
        "es": "El motor de reglas no detectó problemas activos en el portafolio ahora mismo.",
        "en": "The rules engine didn't detect any active problems in the portfolio right now.",
        "pt": "O motor de regras não detectou problemas ativos no portfólio agora."},
    "advisor_written_by": {"es": "Redactado por {proveedor}", "en": "Written by {proveedor}",
                           "pt": "Redigido por {proveedor}"},
    "field_followup_status": {"es": "Estado del seguimiento", "en": "Follow-up status",
                              "pt": "Status do acompanhamento"},
    "btn_track": {"es": "Poner en seguimiento", "en": "Track it", "pt": "Colocar em acompanhamento"},
    "followups_h": {"es": "Seguimientos", "en": "Follow-ups", "pt": "Acompanhamentos"},
    "followups_caption": {
        "es": "Se mantienen acá aunque el problema original ya no se detecte — así queda el "
              "historial de qué se resolvió y cuándo.",
        "en": "These stay here even after the original problem is no longer detected — this "
              "keeps a history of what was resolved and when.",
        "pt": "Ficam aqui mesmo depois que o problema original não é mais detectado — assim fica "
              "o histórico do que foi resolvido e quando."},

    # --------------------------------------------------------------- reports
    "reports_no_plan": {"es": "Tu plan no incluye los reportes automáticos. El plan "
                              "Professional sí los incluye.",
                        "en": "Your plan doesn't include automatic reports. The Professional "
                             "plan does.",
                        "pt": "Seu plano não inclui os relatórios automáticos. O plano "
                             "Professional inclui."},
    "download_json": {"es": "Descargar JSON del portafolio", "en": "Download portfolio JSON",
                      "pt": "Baixar JSON do portfólio"},
    "download_excel": {"es": "Descargar Excel del portafolio", "en": "Download portfolio Excel",
                       "pt": "Baixar Excel do portfólio"},

    # --------------------------------------------------------------- reviews
    "avg_rating": {"es": "Calificación promedio", "en": "Average rating", "pt": "Avaliação média"},
    "rating_value": {"es": "{n} / 5 ({total} reseñas)", "en": "{n} / 5 ({total} reviews)",
                     "pt": "{n} / 5 ({total} avaliações)"},
    "leave_a_review": {"es": "Dejar una reseña", "en": "Leave a review", "pt": "Deixar uma avaliação"},
    "field_your_name": {"es": "Tu nombre", "en": "Your name", "pt": "Seu nome"},
    "field_company": {"es": "Empresa", "en": "Company", "pt": "Empresa"},
    "field_role": {"es": "Rol", "en": "Role", "pt": "Cargo"},
    "field_rating": {"es": "Calificación", "en": "Rating", "pt": "Avaliação"},
    "field_comment": {"es": "Comentario", "en": "Comment", "pt": "Comentário"},
    "btn_submit_review": {"es": "Enviar reseña", "en": "Submit review", "pt": "Enviar avaliação"},
    "msg_review_thanks": {
        "es": "¡Gracias! Tu reseña queda pendiente de verificación antes de publicarse.",
        "en": "Thank you! Your review is pending verification before it's published.",
        "pt": "Obrigado! Sua avaliação fica pendente de verificação antes de publicar."},

    # -------------------------------------------------------- policies/help
    "automation_matrix_h": {"es": "Matriz de automatización y adopción",
                            "en": "Automation & adoption matrix",
                            "pt": "Matriz de automação e adoção"},
    "nivel_auto": {"es": "automático", "en": "automatic", "pt": "automático"},
    "nivel_parcial": {"es": "parcial", "en": "partial", "pt": "parcial"},
    "nivel_humano": {"es": "humano", "en": "human", "pt": "humano"},

    # ----------------------------------------------------------------- pmbok
    "pmbok_caption": {
        "es": "El PMBOK (guía del PMI) en dos registros: **técnico** (como lo diría un PMP) y "
              "**en criollo** (castellano de todos los días). No es una certificación oficial — "
              "es una referencia honesta de qué cubre el producto y qué no.",
        "en": "PMBOK (the PMI guide) in two registers: **technical** (as a PMP would say it) and "
              "**plain-spoken** (everyday language). Not an official certification — it's an "
              "honest reference of what the product covers and what it doesn't.",
        "pt": "O PMBOK (guia do PMI) em dois registros: **técnico** (como diria um PMP) e "
              "**em linguagem simples** (português do dia a dia). Não é uma certificação "
              "oficial — é uma referência honesta do que o produto cobre e do que não cobre."},
    "pmbok_kpi_areas": {"es": "Áreas de conocimiento", "en": "Knowledge areas", "pt": "Áreas de conhecimento"},
    "pmbok_kpi_groups": {"es": "Grupos de procesos", "en": "Process groups", "pt": "Grupos de processo"},
    "pmbok_kpi_full": {"es": "Cobertura completa", "en": "Full coverage", "pt": "Cobertura completa"},
    "pmbok_kpi_none": {"es": "No cubierta", "en": "Not covered", "pt": "Não coberta"},
    "pmbok_tab_areas": {"es": "10 áreas de conocimiento", "en": "10 knowledge areas", "pt": "10 áreas de conhecimento"},
    "pmbok_tab_groups": {"es": "5 grupos de procesos", "en": "5 process groups", "pt": "5 grupos de processo"},
    "pmbok_technical_h": {"es": "**Técnico (PMBOK):**", "en": "**Technical (PMBOK):**", "pt": "**Técnico (PMBOK):**"},
    "pmbok_plain_h": {"es": "**En criollo:**", "en": "**Plain-spoken:**", "pt": "**Em linguagem simples:**"},
    "pmbok_how_covered": {"es": "**Cómo lo cubre este producto:** {texto}",
                          "en": "**How this product covers it:** {texto}",
                          "pt": "**Como este produto cobre isso:** {texto}"},
    "pmbok_whats_missing": {"es": "Lo que falta: {texto}", "en": "What's missing: {texto}",
                            "pt": "O que falta: {texto}"},
    "pmbok_company_note": {
        "es": "Nota de la empresa (validada por {nombre}, {cargo}): {texto}",
        "en": "Company note (validated by {nombre}, {cargo}): {texto}",
        "pt": "Nota da empresa (validada por {nombre}, {cargo}): {texto}"},
    "pmbok_note_caption": {
        "es": "Nota interna de tu empresa (algo que no se automatiza) — se guarda versionada "
              "para esta empresa.",
        "en": "Your company's internal note (something that isn't automated) — saved as a "
              "version for this company.",
        "pt": "Nota interna da sua empresa (algo que não é automatizado) — salva com versão "
              "para esta empresa."},
    "field_note": {"es": "Nota", "en": "Note", "pt": "Nota"},
    "field_validated_by_name": {"es": "Validado por (nombre)", "en": "Validated by (name)",
                                "pt": "Validado por (nome)"},
    "field_role_or_title": {"es": "Cargo", "en": "Title", "pt": "Cargo"},
    "btn_save_note": {"es": "Guardar nota", "en": "Save note", "pt": "Salvar nota"},
    "msg_note_saved": {"es": "Nota guardada.", "en": "Note saved.", "pt": "Nota salva."},
    "pmbok_lifecycle_caption": {
        "es": "El ciclo de vida de la dirección de proyectos, en orden.",
        "en": "The project management lifecycle, in order.",
        "pt": "O ciclo de vida do gerenciamento de projetos, em ordem."},
    "pmbok_resp_assigned": {
        "es": "Responsable asignado: {persona} ({cargo}) — validado por {nombre}, {cargo_val}. "
              "Se asigna desde la pestaña Organigrama.",
        "en": "Assigned owner: {persona} ({cargo}) — validated by {nombre}, {cargo_val}. "
              "Assigned from the Org Chart tab.",
        "pt": "Responsável atribuído: {persona} ({cargo}) — validado por {nombre}, {cargo_val}. "
              "Atribuído na aba Organograma."},
    "sd_none": {"es": "s/d", "en": "n/a", "pt": "s/d"},

    # ------------------------------------------------------------ governance
    "governance_caption": {
        "es": "Cada concepto ya viene con una definición preestablecida (de fábrica). La IA "
              "puede recomendar una versión mejorada, y el **Data Owner / Data Steward** la "
              "valida o la edita y la guarda. Cada cambio queda versionado para esta empresa.",
        "en": "Every concept already ships with a preset (factory) definition. AI can recommend "
              "an improved version, and the **Data Owner / Data Steward** validates or edits it "
              "and saves it. Every change stays versioned for this company.",
        "pt": "Cada conceito já vem com uma definição preestabelecida (de fábrica). A IA pode "
              "recomendar uma versão melhorada, e o **Data Owner / Data Steward** a valida ou "
              "edita e salva. Cada mudança fica versionada para esta empresa."},
    "governance_who_recommends": {"es": "¿Quién recomienda la definición?",
                                  "en": "Who recommends the definition?",
                                  "pt": "Quem recomenda a definição?"},
    "governance_no_providers": {
        "es": "Sin proveedores de IA configurados — las recomendaciones salen del motor de "
              "reglas (la definición de fábrica). Para que la IA pula las definiciones, "
              "configurá ANTHROPIC_API_KEY (Claude), OPENAI_API_KEY+OPENAI_MODEL (ChatGPT) "
              "o GEMINI_API_KEY+GEMINI_MODEL (Gemini).",
        "en": "No AI providers configured — recommendations come from the rules engine (the "
              "factory definition). For AI to polish definitions, set ANTHROPIC_API_KEY "
              "(Claude), OPENAI_API_KEY+OPENAI_MODEL (ChatGPT), or GEMINI_API_KEY+GEMINI_MODEL "
              "(Gemini).",
        "pt": "Sem provedores de IA configurados — as recomendações saem do motor de regras (a "
              "definição de fábrica). Para a IA refinar as definições, configure "
              "ANTHROPIC_API_KEY (Claude), OPENAI_API_KEY+OPENAI_MODEL (ChatGPT) ou "
              "GEMINI_API_KEY+GEMINI_MODEL (Gemini)."},
    "governance_current_def": {"es": "**Definición vigente** ({origen}):",
                               "en": "**Current definition** ({origen}):",
                               "pt": "**Definição vigente** ({origen}):"},
    "governance_validated_by": {
        "es": "Validada por {nombre} ({cargo}) · recomendada por {rec}",
        "en": "Validated by {nombre} ({cargo}) · recommended by {rec}",
        "pt": "Validada por {nombre} ({cargo}) · recomendada por {rec}"},
    "governance_recommended_by": {
        "es": "Recomendado por {rec} — validá, editá y guardá:",
        "en": "Recommended by {rec} — validate, edit and save:",
        "pt": "Recomendado por {rec} — valide, edite e salve:"},
    "governance_definition_field": {"es": "Definición", "en": "Definition", "pt": "Definição"},
    "governance_owner_validates": {"es": "Data Owner que valida (nombre)",
                                   "en": "Data Owner who validates (name)",
                                   "pt": "Data Owner que valida (nome)"},
    "btn_validate_save": {"es": "Validar y guardar", "en": "Validate and save", "pt": "Validar e salvar"},
    "msg_definition_saved": {"es": "Definición validada y guardada (nueva versión).",
                             "en": "Definition validated and saved (new version).",
                             "pt": "Definição validada e salva (nova versão)."},
    "governance_history_count": {
        "es": "{n} versión(es) guardada(s) — la historia completa queda.",
        "en": "{n} version(s) saved — the full history stays.",
        "pt": "{n} versão(ões) salva(s) — o histórico completo fica."},

    # --------------------------------------------------------- organigrama
    "org_upload_expander": {"es": "Cargar / actualizar organigrama",
                            "en": "Upload / update org chart", "pt": "Carregar / atualizar organograma"},
    "org_upload_caption": {
        "es": "Reconoce columnas comunes (nombre, cargo, área, reporta a) sin exigir un "
              "formato exacto.",
        "en": "Recognizes common columns (name, title, area, reports to) with no exact format required.",
        "pt": "Reconhece colunas comuns (nome, cargo, área, reporta a) sem exigir um formato exato."},
    "field_source": {"es": "Origen", "en": "Source", "pt": "Origem"},
    "org_source_excel": {"es": "Excel/CSV", "en": "Excel/CSV", "pt": "Excel/CSV"},
    "org_source_sqlite": {"es": "Base SQLite (.db)", "en": "SQLite database (.db)", "pt": "Base SQLite (.db)"},
    "org_upload_file": {"es": "Subí el organigrama (CSV/Excel)", "en": "Upload the org chart (CSV/Excel)",
                        "pt": "Envie o organograma (CSV/Excel)"},
    "org_people_detected": {"es": "{n} persona(s) detectada(s):", "en": "{n} person/people detected:",
                            "pt": "{n} pessoa(s) detectada(s):"},
    "org_save_btn": {"es": "Guardar este organigrama", "en": "Save this org chart",
                     "pt": "Salvar este organograma"},
    "org_saved": {"es": "Organigrama guardado ({n} personas).", "en": "Org chart saved ({n} people).",
                 "pt": "Organograma salvo ({n} pessoas)."},
    "org_upload_sqlite": {"es": "Subí una base SQLite (.db)", "en": "Upload a SQLite database (.db)",
                          "pt": "Envie uma base SQLite (.db)"},
    "org_table_name": {"es": "Nombre de la tabla con el organigrama", "en": "Name of the table with the org chart",
                       "pt": "Nome da tabela com o organograma"},
    "org_table_read_err": {"es": "No pude leer la tabla '{tabla}': {e}",
                           "en": "Couldn't read table '{tabla}': {e}",
                           "pt": "Não consegui ler a tabela '{tabla}': {e}"},
    "org_photo_caption": {
        "es": "¿Tenés el organigrama como foto? Se puede, pero extraer texto de una imagen "
              "necesita un proveedor de IA con visión configurado. Sin eso, exportalo a "
              "Excel/CSV y subilo acá.",
        "en": "Have the org chart as a photo? You can, but extracting text from an image needs "
              "a vision-capable AI provider configured. Without that, export it to Excel/CSV "
              "and upload it here.",
        "pt": "Tem o organograma como foto? Dá para usar, mas extrair texto de uma imagem "
              "precisa de um provedor de IA com visão configurado. Sem isso, exporte para "
              "Excel/CSV e envie aqui."},
    "org_current_h": {"es": "Organigrama actual", "en": "Current org chart", "pt": "Organograma atual"},
    "org_resp_by_stage_h": {"es": "Responsables por etapa (pre-recomendados por IA)",
                            "en": "Owners by stage (AI pre-recommended)",
                            "pt": "Responsáveis por etapa (pré-recomendados por IA)"},
    "org_assigned": {
        "es": "Asignado: {nombre} ({cargo}) — validado por {val_n}, {val_c}",
        "en": "Assigned: {nombre} ({cargo}) — validated by {val_n}, {val_c}",
        "pt": "Atribuído: {nombre} ({cargo}) — validado por {val_n}, {val_c}"},
    "org_recommended": {"es": "**Recomendado ({rec}):** {nombre} — {cargo}",
                        "en": "**Recommended ({rec}):** {nombre} — {cargo}",
                        "pt": "**Recomendado ({rec}):** {nombre} — {cargo}"},
    "org_no_fit": {"es": "El organigrama no tiene un cargo que encaje — asignalo a mano.",
                  "en": "The org chart has no title that fits — assign it by hand.",
                  "pt": "O organograma não tem um cargo que se encaixe — atribua manualmente."},
    "org_responsible_label": {"es": "Responsable", "en": "Owner", "pt": "Responsável"},
    "org_validated_by_name": {"es": "Validado por (nombre)", "en": "Validated by (name)",
                              "pt": "Validado por (nome)"},
    "org_validator_role": {"es": "Cargo de quien valida", "en": "Validator's title", "pt": "Cargo de quem valida"},
    "org_validate_btn": {"es": "Validar responsable", "en": "Validate owner", "pt": "Validar responsável"},
    "org_resp_saved": {"es": "Responsable validado y guardado.", "en": "Owner validated and saved.",
                       "pt": "Responsável validado e salvo."},

    # -------------------------------------------------------------- import
    "import_caption": {
        "es": "Subí tu archivo tal como lo tenés. El sistema reconoce solo cómo se llaman tus "
              "columnas y traduce los valores — no hace falta que lo prepares antes.",
        "en": "Upload your file as-is. The system recognizes your column names on its own and "
              "translates the values — no need to prep it beforehand.",
        "pt": "Envie seu arquivo como está. O sistema reconhece sozinho os nomes das suas "
              "colunas e traduz os valores — não precisa preparar antes."},
    "import_what_label": {"es": "¿Qué estás importando?", "en": "What are you importing?",
                          "pt": "O que você está importando?"},
    "import_opt_projects": {"es": "Proyectos", "en": "Projects", "pt": "Projetos"},
    "import_opt_tasks": {"es": "Tareas", "en": "Tasks", "pt": "Tarefas"},
    "import_template_expander": {"es": "¿No sabés cómo armar el archivo? Descargá la plantilla",
                                 "en": "Not sure how to build the file? Download the template",
                                 "pt": "Não sabe como montar o arquivo? Baixe o modelo"},
    "import_template_btn": {"es": "Plantilla de {tipo} (CSV)", "en": "{tipo} template (CSV)",
                            "pt": "Modelo de {tipo} (CSV)"},
    "import_template_caption": {
        "es": "La plantilla es una ayuda, no un requisito: el importador acepta cualquier "
              "nombre de columna.",
        "en": "The template is a help, not a requirement: the importer accepts any column name.",
        "pt": "O modelo é uma ajuda, não um requisito: o importador aceita qualquer nome de coluna."},
    "import_upload_label": {"es": "Subí un CSV/Excel", "en": "Upload a CSV/Excel", "pt": "Envie um CSV/Excel"},
    "import_no_rows": {"es": "El archivo no tiene filas.", "en": "The file has no rows.",
                       "pt": "O arquivo não tem linhas."},
    "import_rows_cols": {"es": "**{filas} filas, {cols} columnas.**", "en": "**{filas} rows, {cols} columns.**",
                         "pt": "**{filas} linhas, {cols} colunas.**"},
    "import_step1": {"es": "#### 1. Revisá a qué corresponde cada columna",
                     "en": "#### 1. Review what each column maps to",
                     "pt": "#### 1. Revise a que cada coluna corresponde"},
    "import_opt_unused": {"es": "— sin usar —", "en": "— unused —", "pt": "— não usada —"},
    "import_detected": {"es": "{icono} detectado: {motivo}", "en": "{icono} detected: {motivo}",
                        "pt": "{icono} detectado: {motivo}"},
    "import_needs_column": {"es": "hace falta elegir una columna", "en": "a column needs to be chosen",
                            "pt": "é preciso escolher uma coluna"},
    "import_step2": {"es": "#### 2. Opciones", "en": "#### 2. Options", "pt": "#### 2. Opções"},
    "import_skip_dup": {"es": "Omitir filas repetidas y las que ya existen en el sistema",
                        "en": "Skip repeated rows and ones that already exist in the system",
                        "pt": "Omitir linhas repetidas e as que já existem no sistema"},
    "import_no_projects_err": {
        "es": "Todavía no hay proyectos cargados. Importá primero los proyectos para poder "
              "asociarles las tareas.",
        "en": "There are no projects loaded yet. Import projects first so tasks can be "
              "associated with them.",
        "pt": "Ainda não há projetos carregados. Importe primeiro os projetos para poder "
              "associar as tarefas."},
    "import_use_default_project": {
        "es": "Si una tarea no coincide con ningún proyecto, mandarla igual a uno",
        "en": "If a task doesn't match any project, send it to one anyway",
        "pt": "Se uma tarefa não corresponder a nenhum projeto, enviá-la mesmo assim para um"},
    "import_default_project": {"es": "Proyecto por defecto", "en": "Default project", "pt": "Projeto padrão"},
    "import_step3": {"es": "#### 3. Qué va a pasar", "en": "#### 3. What's going to happen",
                     "pt": "#### 3. O que vai acontecer"},
    "import_will_create": {"es": "Se van a crear", "en": "Will be created", "pt": "Serão criados"},
    "import_will_discard": {"es": "Se descartan", "en": "Discarded", "pt": "Descartados"},
    "import_duplicates": {"es": "Repetidas", "en": "Duplicates", "pt": "Repetidos"},
    "import_details_expander": {"es": "Ver detalle de {n} observación(es)",
                                "en": "See detail of {n} observation(s)",
                                "pt": "Ver detalhe de {n} observação(ões)"},
    "import_severity_caption": {
        "es": "Severidad «error» descarta la fila; «aviso» la importa igual, dejando ese dato "
              "vacío o con el valor por defecto.",
        "en": "\"Error\" severity discards the row; \"warning\" imports it anyway, leaving that "
              "field empty or at its default value.",
        "pt": "Severidade «erro» descarta a linha; «aviso» a importa mesmo assim, deixando esse "
              "dado vazio ou com o valor padrão."},
    "import_preview": {"es": "Vista previa de lo que se va a guardar:",
                       "en": "Preview of what will be saved:", "pt": "Prévia do que será salvo:"},
    "import_step4": {"es": "#### 4. Confirmar", "en": "#### 4. Confirm", "pt": "#### 4. Confirmar"},
    "import_no_rows_left": {"es": "No queda ninguna fila para importar con estas opciones.",
                            "en": "No rows are left to import with these options.",
                            "pt": "Não sobrou nenhuma linha para importar com estas opções."},
    "import_btn": {"es": "Importar {n} {tipo}", "en": "Import {n} {tipo}", "pt": "Importar {n} {tipo}"},
    "import_done": {"es": "Listo: se importaron {n} {tipo}. Ya podés verlos en {seccion}.",
                    "en": "Done: {n} {tipo} imported. You can see them in {seccion} now.",
                    "pt": "Pronto: foram importados {n} {tipo}. Já pode vê-los em {seccion}."},

    # ------------------------------------------------------------ plantillas
    "plantillas_caption": {
        "es": "Gobernanza lista para el rubro del cliente: etapas con puerta de salida, quién "
              "aprueba cada una, riesgos típicos y normativa. Es un punto de partida para "
              "discutir, no una norma.",
        "en": "Governance ready for the client's industry: stages with an exit gate, who "
              "approves each one, typical risks and regulations. A starting point for "
              "discussion, not a standard.",
        "pt": "Governança pronta para o ramo do cliente: etapas com porta de saída, quem "
              "aprova cada uma, riscos típicos e normativa. É um ponto de partida para "
              "discutir, não uma norma."},
    "plantillas_adopted": {"es": "Esta empresa adoptó **{rubro}**{firma}.",
                           "en": "This company adopted **{rubro}**{firma}.",
                           "pt": "Esta empresa adotou **{rubro}**{firma}."},
    "plantillas_validated_by": {"es": " · validada por {nombre}", "en": " · validated by {nombre}",
                                "pt": " · validada por {nombre}"},
    "plantillas_draft": {"es": " · en borrador", "en": " · draft", "pt": " · rascunho"},
    "field_industry": {"es": "Rubro", "en": "Industry", "pt": "Ramo"},
    "plantillas_tab_stages": {"es": "Etapas", "en": "Stages", "pt": "Etapas"},
    "plantillas_tab_roles": {"es": "Roles y riesgos", "en": "Roles & risks", "pt": "Papéis e riscos"},
    "plantillas_tab_kpi": {"es": "Indicadores y normativa", "en": "KPIs & regulations",
                           "pt": "Indicadores e normativa"},
    "plantillas_tab_adopt": {"es": "Adoptar", "en": "Adopt", "pt": "Adotar"},
    "plantillas_deliverables": {"es": "**Entregables:**", "en": "**Deliverables:**", "pt": "**Entregáveis:**"},
    "plantillas_exit_gate": {"es": "**Puerta de salida:** {texto}", "en": "**Exit gate:** {texto}",
                             "pt": "**Porta de saída:** {texto}"},
    "plantillas_approves": {"es": "**Aprueba:** {texto}", "en": "**Approves:** {texto}",
                            "pt": "**Aprova:** {texto}"},
    "plantillas_download_gov": {"es": "Descargar la gobernanza completa (Markdown)",
                                "en": "Download the full governance doc (Markdown)",
                                "pt": "Baixar a governança completa (Markdown)"},
    "plantillas_roles_h": {"es": "**Roles y qué decide cada uno**", "en": "**Roles and what each decides**",
                           "pt": "**Papéis e o que cada um decide**"},
    "col_role": {"es": "Rol", "en": "Role", "pt": "Papel"},
    "col_what_decides": {"es": "Qué decide", "en": "What decides", "pt": "O que decide"},
    "plantillas_risks_h": {"es": "**Riesgos típicos del rubro**", "en": "**Typical risks in this industry**",
                           "pt": "**Riscos típicos do ramo**"},
    "col_risk": {"es": "Riesgo", "en": "Risk", "pt": "Risco"},
    "col_pmbok_area": {"es": "Área PMBOK", "en": "PMBOK area", "pt": "Área PMBOK"},
    "col_early_signal": {"es": "Señal temprana", "en": "Early signal", "pt": "Sinal precoce"},
    "col_mitigation": {"es": "Mitigación", "en": "Mitigation", "pt": "Mitigação"},
    "plantillas_focus_areas_h": {
        "es": "**Áreas de PMBOK donde poner el esfuerzo en este rubro**",
        "en": "**PMBOK areas to focus effort on in this industry**",
        "pt": "**Áreas do PMBOK onde concentrar esforço neste ramo**"},
    "plantillas_focus_caption": {
        "es": "Que estas áreas pesen más no significa ignorar las otras: las diez aplican siempre.",
        "en": "These areas weighing more doesn't mean ignoring the others: all ten always apply.",
        "pt": "Estas áreas pesarem mais não significa ignorar as outras: as dez sempre se aplicam."},
    "plantillas_kpi_h": {"es": "**Indicadores que en este rubro se miran de verdad**",
                         "en": "**KPIs that actually get watched in this industry**",
                         "pt": "**Indicadores que de verdade se acompanham neste ramo**"},
    "plantillas_regs_h": {"es": "**Normativa de referencia**", "en": "**Reference regulations**",
                          "pt": "**Normativa de referência**"},
    "plantillas_legal_warning": {
        "es": "Las referencias normativas son orientativas y están tomadas de Uruguay salvo que "
              "digan otra cosa. Confirmalas con quien lleva calidad, legales o compliance en la "
              "empresa: cambian, y cada empresa tiene su interpretación. Esto no es "
              "asesoramiento legal.",
        "en": "Regulatory references are indicative and taken from Uruguay unless stated "
              "otherwise. Confirm them with whoever handles quality, legal or compliance at the "
              "company: they change, and every company interprets them differently. This is "
              "not legal advice.",
        "pt": "As referências normativas são orientativas e tiradas do Uruguai, salvo indicação "
              "contrária. Confirme-as com quem cuida de qualidade, jurídico ou compliance na "
              "empresa: elas mudam, e cada empresa tem sua interpretação. Isto não é "
              "aconselhamento jurídico."},
    "plantillas_adopt_body": {
        "es": "Adoptar la plantilla la deja registrada como la gobernanza de esta empresa, con "
              "quién la validó. Queda versionada: cambiarla más adelante no borra la historia.",
        "en": "Adopting the template registers it as this company's governance, along with who "
              "validated it. It stays versioned: changing it later doesn't erase the history.",
        "pt": "Adotar o modelo o registra como a governança desta empresa, com quem o validou. "
              "Fica versionado: mudar depois não apaga o histórico."},
    "plantillas_validated_by_field": {"es": "Validada por (nombre)", "en": "Validated by (name)",
                                      "pt": "Validada por (nome)"},
    "plantillas_validator_role": {"es": "Cargo de quien valida", "en": "Validator's title",
                                  "pt": "Cargo de quem valida"},
    "plantillas_adopt_btn": {"es": "Adoptar «{rubro}»", "en": "Adopt \"{rubro}\"", "pt": "Adotar «{rubro}»"},
    "plantillas_adopted_msg": {"es": "Plantilla adoptada y registrada.", "en": "Template adopted and registered.",
                               "pt": "Modelo adotado e registrado."},
    "plantillas_adopt_caption": {
        "es": "Se puede adoptar sin validar: queda en borrador hasta que alguien de la empresa la firme.",
        "en": "It can be adopted without validating: it stays a draft until someone at the "
              "company signs off.",
        "pt": "Pode ser adotado sem validar: fica em rascunho até que alguém da empresa assine."},

    # ------------------------------------------------------- conectores (ERP)
    "conectores_erp_result": {"es": "Se trajeron {n} fila(s) del ERP.", "en": "{n} row(s) were fetched from the ERP.",
                              "pt": "Foram trazidas {n} linha(s) do ERP."},
    "conectores_query_failed": {"es": "Falló la consulta: {e}", "en": "The query failed: {e}",
                                "pt": "A consulta falhou: {e}"},
    "conectores_erp_converted": {"es": "**Lo que llegó del ERP, ya convertido:**",
                                 "en": "**What came from the ERP, already converted:**",
                                 "pt": "**O que veio do ERP, já convertido:**"},
    "conectores_check_caption": {
        "es": "Revisá un par de fechas e importes contra el ERP antes de importar. Es el "
              "control que evita una carga silenciosamente equivocada.",
        "en": "Check a couple of dates and amounts against the ERP before importing. This is "
              "the control that prevents a silently wrong load.",
        "pt": "Revise algumas datas e valores contra o ERP antes de importar. É o controle que "
              "evita uma carga silenciosamente errada."},
    "erp_details_expander": {"es": "Ver {n} observación(es)", "en": "See {n} observation(s)",
                             "pt": "Ver {n} observação(ões)"},
    "erp_import_btn": {"es": "Importar {n} {tipo}", "en": "Import {n} {tipo}", "pt": "Importar {n} {tipo}"},
    "erp_import_done": {"es": "Listo: se importaron {n} {tipo} desde el ERP.",
                        "en": "Done: {n} {tipo} imported from the ERP.",
                        "pt": "Pronto: foram importados {n} {tipo} do ERP."},

    # ---------------------------------------------------------- data engineering
    "dataeng_no_plan": {"es": "Tu plan no incluye la ingeniería de datos. El plan "
                              "Professional sí la incluye.",
                        "en": "Your plan doesn't include data engineering. The Professional "
                             "plan does.",
                        "pt": "Seu plano não inclui engenharia de dados. O plano Professional inclui."},
    "dataeng_caption": {
        "es": "Perfilá cualquier tabla —no sólo proyectos y tareas— antes de importarla o de "
              "conectarla a un ERP: nulos, duplicados, outliers, la clave primaria candidata y "
              "un `CREATE TABLE` de partida. Sin cargo aparte, incluido en el mismo plan que "
              "los reportes automáticos.",
        "en": "Profile any table —not just projects and tasks— before importing it or "
              "connecting it to an ERP: nulls, duplicates, outliers, the candidate primary key, "
              "and a starting `CREATE TABLE`. No extra charge, included in the same plan as "
              "automatic reports.",
        "pt": "Perfile qualquer tabela —não só projetos e tarefas— antes de importá-la ou "
              "conectá-la a um ERP: nulos, duplicados, outliers, a chave primária candidata e "
              "um `CREATE TABLE` de partida. Sem cobrança à parte, incluído no mesmo plano dos "
              "relatórios automáticos."},
    "dataeng_source_label": {"es": "¿De dónde vienen los datos?", "en": "Where does the data come from?",
                             "pt": "De onde vêm os dados?"},
    "dataeng_source_file": {"es": "Archivo (CSV/Excel)", "en": "File (CSV/Excel)", "pt": "Arquivo (CSV/Excel)"},
    "dataeng_source_sql": {"es": "Base de datos (SQL)", "en": "Database (SQL)", "pt": "Banco de dados (SQL)"},
    "dataeng_upload_label": {"es": "Subí un CSV/Excel — cualquier esquema",
                             "en": "Upload a CSV/Excel — any schema", "pt": "Envie um CSV/Excel — qualquer esquema"},
    "dataeng_read_err": {"es": "No pude leer el archivo: {e}", "en": "Couldn't read the file: {e}",
                         "pt": "Não consegui ler o arquivo: {e}"},
    "dataeng_sql_caption": {
        "es": "Sólo lectura: la consulta tiene que empezar con SELECT. La cadena de conexión "
              "no se guarda en ningún lado — vive únicamente en esta sesión.",
        "en": "Read-only: the query has to start with SELECT. The connection string isn't "
              "saved anywhere — it lives only in this session.",
        "pt": "Somente leitura: a consulta tem que começar com SELECT. A cadeia de conexão não "
              "é salva em lugar nenhum — vive apenas nesta sessão."},
    "dataeng_conn_string": {"es": "Cadena de conexión", "en": "Connection string", "pt": "Cadeia de conexão"},
    "dataeng_conn_help": {
        "es": "Usá un usuario de solo lectura. Es la protección de verdad: el candado del "
              "software es sólo la segunda línea.",
        "en": "Use a read-only user. That's the real protection: the software's lock is only "
              "the second line of defense.",
        "pt": "Use um usuário de somente leitura. É a proteção de verdade: o cadeado do "
              "software é só a segunda linha."},
    "dataeng_select_query": {"es": "Consulta SELECT", "en": "SELECT query", "pt": "Consulta SELECT"},
    "dataeng_report_name": {"es": "Nombre para el reporte", "en": "Name for the report", "pt": "Nome para o relatório"},
    "btn_profile": {"es": "Perfilar", "en": "Profile", "pt": "Perfilar"},
    "dataeng_result_h": {"es": "### Resultado — {nombre}", "en": "### Result — {nombre}", "pt": "### Resultado — {nombre}"},
    "col_rows": {"es": "Filas", "en": "Rows", "pt": "Linhas"},
    "col_columns": {"es": "Columnas", "en": "Columns", "pt": "Colunas"},
    "dataeng_quality_score": {"es": "Score de calidad", "en": "Quality score", "pt": "Score de qualidade"},
    "dataeng_issues_found": {"es": "Problemas detectados", "en": "Issues detected", "pt": "Problemas detectados"},
    "dataeng_types_fixed": {"es": "Tipos corregidos antes de perfilar ({n})",
                            "en": "Types fixed before profiling ({n})",
                            "pt": "Tipos corrigidos antes de perfilar ({n})"},
    "col_column": {"es": "Columna", "en": "Column", "pt": "Coluna"},
    "col_type_before": {"es": "Tipo antes", "en": "Type before", "pt": "Tipo antes"},
    "col_type_after": {"es": "Tipo después", "en": "Type after", "pt": "Tipo depois"},
    "dataeng_profile_by_col": {"es": "#### Perfil por columna", "en": "#### Profile by column", "pt": "#### Perfil por coluna"},
    "dataeng_quality_issues": {"es": "#### Problemas de calidad", "en": "#### Quality issues", "pt": "#### Problemas de qualidade"},
    "dataeng_no_issues": {"es": "No se detectaron problemas de calidad.", "en": "No quality issues detected.",
                          "pt": "Não foram detectados problemas de qualidade."},
    "dataeng_candidate_pk": {"es": "#### Clave primaria candidata", "en": "#### Candidate primary key",
                             "pt": "#### Chave primária candidata"},
    "dataeng_time_coverage": {"es": "#### Cobertura temporal", "en": "#### Time coverage", "pt": "#### Cobertura temporal"},
    "col_from": {"es": "Desde", "en": "From", "pt": "Desde"},
    "col_to": {"es": "Hasta", "en": "To", "pt": "Até"},
    "dataeng_days_no_data": {"es": "Días sin datos", "en": "Days with no data", "pt": "Dias sem dados"},
    "dataeng_future_dates": {"es": "{n} fecha(s) en el futuro en «{col}».",
                             "en": "{n} future date(s) in \"{col}\".",
                             "pt": "{n} data(s) no futuro em «{col}»."},
    "dataeng_downloads_h": {"es": "#### Descargas", "en": "#### Downloads", "pt": "#### Downloads"},
    "dataeng_ddl_btn": {"es": "DDL sugerido (.sql)", "en": "Suggested DDL (.sql)", "pt": "DDL sugerido (.sql)"},
    "dataeng_excel_btn": {"es": "Informe completo (Excel)", "en": "Full report (Excel)", "pt": "Relatório completo (Excel)"},

    # -------------------------------------------------------- capacitacion
    "capacitacion_caption": {
        "es": "Cada rol necesita cosas distintas. Al sponsor no le sirve aprender a cargar "
              "dependencias — y si le hacés mirar una hora de video, no mira nada. Cada módulo "
              "está listo para grabar una vez y reusar.",
        "en": "Every role needs different things. The sponsor gets nothing from learning to "
              "load dependencies — and if you make them watch an hour of video, they watch "
              "none of it. Every module is ready to record once and reuse.",
        "pt": "Cada papel precisa de coisas diferentes. Ao sponsor não serve aprender a "
              "carregar dependências — e se você o fizer assistir uma hora de vídeo, ele não "
              "assiste nada. Cada módulo está pronto para gravar uma vez e reusar."},
    "field_role_select": {"es": "Rol", "en": "Role", "pt": "Papel"},
    "capacitacion_summary": {"es": "**{rol}** · {min} minutos en {n} módulos",
                             "en": "**{rol}** · {min} minutes across {n} modules",
                             "pt": "**{rol}** · {min} minutos em {n} módulos"},
    "capacitacion_for_whom": {"es": "**Para quién:** {texto}", "en": "**Who it's for:** {texto}",
                              "pt": "**Para quem:** {texto}"},
    "capacitacion_promise": {"es": "**Al terminar va a poder:** {texto}", "en": "**By the end you'll be able to:** {texto}",
                             "pt": "**Ao terminar vai poder:** {texto}"},
    "capacitacion_prereq": {"es": "Antes de esto: {lista}", "en": "Before this: {lista}",
                            "pt": "Antes disso: {lista}"},
    "capacitacion_tab_modules": {"es": "Módulos", "en": "Modules", "pt": "Módulos"},
    "capacitacion_tab_verify": {"es": "Verificación", "en": "Verification", "pt": "Verificação"},
    "capacitacion_tab_plan": {"es": "Plan de grabación", "en": "Recording plan", "pt": "Plano de gravação"},
    "capacitacion_where": {"es": "*{obj}* — se hace en «{seccion}».", "en": "*{obj}* — done in \"{seccion}\".",
                           "pt": "*{obj}* — feito em «{seccion}»."},
    "capacitacion_script_h": {"es": "**Guion:**", "en": "**Script:**", "pt": "**Roteiro:**"},
    "capacitacion_practice": {"es": "**Práctica:** {texto}", "en": "**Practice:** {texto}", "pt": "**Prática:** {texto}"},
    "capacitacion_verify_h": {"es": "**Verificación:**", "en": "**Verification:**", "pt": "**Verificação:**"},
    "capacitacion_download_script": {"es": "Descargar el guion completo (Markdown)",
                                     "en": "Download the full script (Markdown)",
                                     "pt": "Baixar o roteiro completo (Markdown)"},
    "capacitacion_verify_caption": {
        "es": "Preguntas de toda la ruta, incluidos los requisitos previos. Si la persona las "
              "contesta, puede trabajar sola.",
        "en": "Questions covering the whole path, including prerequisites. If the person "
              "answers them, they can work on their own.",
        "pt": "Perguntas de todo o caminho, incluindo os pré-requisitos. Se a pessoa as "
              "responde, pode trabalhar sozinha."},
    "col_module": {"es": "Módulo", "en": "Module", "pt": "Módulo"},
    "col_min": {"es": "Min", "en": "Min", "pt": "Min"},
    "col_where": {"es": "Dónde", "en": "Where", "pt": "Onde"},
    "col_roles": {"es": "Roles", "en": "Roles", "pt": "Papéis"},
    "capacitacion_plan_summary": {
        "es": "**{n} módulos, {min} minutos** para cubrir los seis roles. Un módulo que usan "
              "varios roles se graba una sola vez.",
        "en": "**{n} modules, {min} minutes** to cover all six roles. A module used by "
              "multiple roles is recorded only once.",
        "pt": "**{n} módulos, {min} minutos** para cobrir os seis papéis. Um módulo usado por "
              "vários papéis é gravado uma única vez."},

    # -------------------------------------------------------------- users
    "import_read_err": {"es": "No pude leer el archivo: {e}", "en": "Couldn't read the file: {e}",
                        "pt": "Não consegui ler o arquivo: {e}"},

    # ------------------------------------------------------- conectores (ERP UI)
    "conectores_caption": {
        "es": "Traer proyectos y tareas directo del ERP. Siempre de solo lectura: el sistema "
              "rechaza cualquier consulta que no sea un SELECT.",
        "en": "Bring projects and tasks straight from the ERP. Always read-only: the system "
              "rejects any query that isn't a SELECT.",
        "pt": "Trazer projetos e tarefas direto do ERP. Sempre somente leitura: o sistema "
              "rejeita qualquer consulta que não seja um SELECT."},
    "field_family": {"es": "Familia", "en": "Family", "pt": "Família"},
    "field_system": {"es": "Sistema", "en": "System", "pt": "Sistema"},
    "conectores_how": {"es": "**Cómo se conecta:** {texto}", "en": "**How to connect:** {texto}",
                       "pt": "**Como se conecta:** {texto}"},
    "conectores_no_queries": {
        "es": "Este perfil no trae consultas de fábrica: escribí la tuya y el resultado entra "
              "por el mismo informe previo que un archivo.",
        "en": "This profile has no built-in queries: write your own and the result goes "
              "through the same preview report as a file.",
        "pt": "Este perfil não traz consultas de fábrica: escreva a sua e o resultado entra "
              "pelo mesmo relatório prévio que um arquivo."},
    "conectores_what_to_bring": {"es": "¿Qué querés traer?", "en": "What do you want to bring?",
                                 "pt": "O que você quer trazer?"},
    "field_schema": {"es": "Esquema", "en": "Schema", "pt": "Esquema"},
    "conectores_schema_help": {
        "es": "Cambia según la instalación. Si el sondeo no encuentra las tablas, suele ser esto.",
        "en": "Varies by installation. If the probe can't find the tables, this is usually why.",
        "pt": "Muda conforme a instalação. Se o sondeio não encontra as tabelas, geralmente é isso."},
    "conectores_company_field": {"es": "Empresa (sólo NAV/Business Central)",
                                 "en": "Company (NAV/Business Central only)",
                                 "pt": "Empresa (somente NAV/Business Central)"},
    "conectores_company_help": {
        "es": "En NAV las tablas llevan la empresa adelante: «CRONUS$Job».",
        "en": "In NAV, tables carry the company name up front: \"CRONUS$Job\".",
        "pt": "No NAV, as tabelas levam a empresa na frente: «CRONUS$Job»."},
    "conectores_query_to_run": {
        "es": "**Consulta que se va a ejecutar** — editable si tu instalación tiene otros nombres:",
        "en": "**Query that will run** — editable if your installation uses different names:",
        "pt": "**Consulta que será executada** — editável se sua instalação tiver outros nomes:"},
    "conectores_col_interpretation": {"es": "**Cómo se interpreta cada columna:**",
                                      "en": "**How each column is interpreted:**",
                                      "pt": "**Como cada coluna é interpretada:**"},
    "col_column_name": {"es": "Columna", "en": "Column", "pt": "Coluna"},
    "col_goes_to": {"es": "Va a", "en": "Goes to", "pt": "Vai para"},
    "col_conversion": {"es": "Conversión", "en": "Conversion", "pt": "Conversão"},
    "col_note": {"es": "Nota", "en": "Note", "pt": "Nota"},
    "conectores_connect_h": {"es": "#### Conectarse", "en": "#### Connect", "pt": "#### Conectar"},
    "conectores_conn_string_help": {
        "es": "Usá un usuario de solo lectura. Es la protección de verdad: el candado del "
              "software es sólo la segunda línea.",
        "en": "Use a read-only user. That's the real protection: the software's lock is only "
              "the second line of defense.",
        "pt": "Use um usuário de somente leitura. É a proteção de verdade: o cadeado do "
              "software é só a segunda linha."},
    "conectores_probe_btn": {"es": "Sondear el esquema", "en": "Probe the schema", "pt": "Sondar o esquema"},
    "conectores_engine_error_expander": {"es": "Detalle del error del motor",
                                         "en": "Engine error detail", "pt": "Detalhe do erro do motor"},
    "conectores_connect_failed": {"es": "No se pudo conectar: {e}", "en": "Couldn't connect: {e}",
                                  "pt": "Não foi possível conectar: {e}"},
    "conectores_fetch_btn": {"es": "Traer los datos", "en": "Fetch the data", "pt": "Trazer os dados"},

    # -------------------------------------------------------- estado vacío
    "empty_guest_caption": {"es": "Todavía no cargaste proyectos en esta sesión.",
                            "en": "You haven't loaded any projects in this session yet.",
                            "pt": "Você ainda não carregou projetos nesta sessão."},
    "empty_guest_btn": {"es": "Cargar el portafolio real del gobierno británico (132 proyectos)",
                        "en": "Load the real UK government portfolio (132 projects)",
                        "pt": "Carregar o portfólio real do governo britânico (132 projetos)"},
    "empty_server_caption": {"es": "Todavía no cargaste proyectos en este servidor.",
                             "en": "You haven't loaded any projects on this server yet.",
                             "pt": "Você ainda não carregou projetos neste servidor."},
    "empty_server_btn": {"es": "Cargar datos de ejemplo para explorar",
                         "en": "Load sample data to explore", "pt": "Carregar dados de exemplo para explorar"},
    "new_project_expander": {"es": "Nuevo proyecto", "en": "New project", "pt": "Novo projeto"},
    "org_caption": {
        "es": "Cargá el organigrama (Excel/CSV o base SQLite) y la IA autocompleta por defecto "
              "quién es responsable de cada etapa del proyecto — según su cargo. Todo editable "
              "y guardado versionado por empresa.",
        "en": "Upload the org chart (Excel/CSV or SQLite database) and AI auto-fills, by "
              "default, who's responsible for each project stage — based on their title. "
              "Everything editable and saved versioned per company.",
        "pt": "Carregue o organograma (Excel/CSV ou base SQLite) e a IA autocompleta por "
              "padrão quem é responsável por cada etapa do projeto — conforme seu cargo. Tudo "
              "editável e salvo versionado por empresa."},
    "users_caption": {
        "es": "Para sumar gente al equipo, pedile que se registre desde la pantalla de login "
              "de este mismo servidor con 'Crear cuenta'.",
        "en": "To add people to the team, ask them to register from this same server's login "
              "screen with \"Create account\".",
        "pt": "Para somar gente à equipe, peça que se cadastre na tela de login deste mesmo "
              "servidor com 'Criar conta'."},
}


def t(key: str, lang: str = "es") -> str:
    entry = _STRINGS.get(key)
    if not entry:
        return key
    return entry.get(lang) or entry.get("es") or key


def all_keys():
    return sorted(_STRINGS.keys())
