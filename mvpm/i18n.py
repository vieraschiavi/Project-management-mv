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
    "nav_reports": {"es": "Reportes", "en": "Reports", "pt": "Relatórios"},
    "nav_reviews": {"es": "Reseñas", "en": "Reviews", "pt": "Avaliações"},
    "nav_glossary": {"es": "Glosario", "en": "Glossary", "pt": "Glossário"},
    "nav_policies": {"es": "Políticas", "en": "Policies", "pt": "Políticas"},
    "nav_import": {"es": "Importar datos", "en": "Import data", "pt": "Importar dados"},
    "nav_tutorial": {"es": "Tutorial", "en": "Tutorial", "pt": "Tutorial"},
    "nav_pmbok": {"es": "Metodología PMBOK", "en": "PMBOK methodology", "pt": "Metodologia PMBOK"},
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
