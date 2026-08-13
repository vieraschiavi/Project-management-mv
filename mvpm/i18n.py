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
    "cfg_actualizar": {"es": "🔄 Actualizar modelos desde mi API",
                       "en": "🔄 Refresh models from my API",
                       "pt": "🔄 Atualizar modelos da minha API"},
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
}


def t(key: str, lang: str = "es") -> str:
    entry = _STRINGS.get(key)
    if not entry:
        return key
    return entry.get(lang) or entry.get("es") or key


def all_keys():
    return sorted(_STRINGS.keys())
