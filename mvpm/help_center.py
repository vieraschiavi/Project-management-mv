# © 2026 Martín Viera. Todos los derechos reservados.
"""Centro de adopción: qué se automatiza solo, qué necesita un empujón, y qué
es puramente humano — más los guiones (speeches) que cierran esa parte humana
que ningún software resuelve solo. Mismo patrón que `help_center.py` de
Data Governance MV, adaptado a gestión de proyectos.
"""

# "nivel" (auto/parcial/humano) y "speech_id" son identificadores internos —
# nunca se traducen: "nivel" decide el ícono/color en app.py, "speech_id" es
# la clave para buscar en SPEECHES.
AUTOMATION = [
    {"area": {"es": "Rollup de estado tarea → proyecto → portafolio",
              "en": "Status rollup: task → project → portfolio",
              "pt": "Rollup de status: tarefa → projeto → portfólio"},
     "nivel": "auto",
     "detalle": {"es": "Se recalcula solo en cada cambio de estado de una tarea.",
                 "en": "Recalculates itself on every task status change.",
                 "pt": "Recalcula sozinho a cada mudança de status de uma tarefa."}},
    {"area": {"es": "Reporte ejecutivo semanal", "en": "Weekly executive report",
              "pt": "Relatório executivo semanal"},
     "nivel": "auto",
     "detalle": {"es": "Se genera solo a partir del dato real del portafolio.",
                 "en": "Generates itself from the portfolio's real data.",
                 "pt": "É gerado sozinho a partir do dado real do portfólio."}},
    {"area": {"es": "Detección de riesgo y tareas bloqueadas",
              "en": "Risk and blocked-task detection",
              "pt": "Detecção de risco e tarefas bloqueadas"},
     "nivel": "parcial",
     "detalle": {"es": "El sistema las detecta; alguien confirma la causa raíz.",
                 "en": "The system detects them; someone confirms the root cause.",
                 "pt": "O sistema as detecta; alguém confirma a causa raiz."},
     "speech_id": "dueno"},
    {"area": {"es": "Creación de tareas desde reunión o email",
              "en": "Creating tasks from a meeting or email",
              "pt": "Criação de tarefas a partir de reunião ou e-mail"},
     "nivel": "parcial",
     "detalle": {"es": "El copiloto sugiere; un clic humano las crea de verdad.",
                 "en": "The copilot suggests them; a human click actually creates them.",
                 "pt": "O copiloto sugere; um clique humano as cria de verdade."},
     "speech_id": "equipo"},
    {"area": {"es": "Asignación de dueño de proyecto", "en": "Assigning a project owner",
              "pt": "Atribuição de responsável do projeto"},
     "nivel": "humano",
     "detalle": {"es": "Decisión organizacional, no técnica.",
                 "en": "An organizational decision, not a technical one.",
                 "pt": "Decisão organizacional, não técnica."},
     "speech_id": "direccion"},
    {"area": {"es": "Definir qué significa 'en riesgo' para el equipo",
              "en": "Defining what \"at risk\" means for the team",
              "pt": "Definir o que \"em risco\" significa para a equipe"},
     "nivel": "humano",
     "detalle": {"es": "Acuerdo breve de criterios, una vez, en el glosario.",
                 "en": "A short one-time agreement on criteria, in the glossary.",
                 "pt": "Um acordo breve de critérios, uma vez, no glossário."},
     "speech_id": "comite"},
    {"area": {"es": "Adopción y patrocinio del cambio", "en": "Change adoption and sponsorship",
              "pt": "Adoção e patrocínio da mudança"},
     "nivel": "humano",
     "detalle": {"es": "Ningún software reemplaza al sponsor.",
                 "en": "No software replaces the sponsor.",
                 "pt": "Nenhum software substitui o sponsor."},
     "speech_id": "direccion"},
]

SPEECHES = {
    "direccion": {
        "titulo": {"es": "Guion para dirección / sponsor", "en": "Script for leadership / sponsor",
                   "pt": "Roteiro para diretoria / sponsor"},
        "audiencia": {"es": "Gerencia general, directorio", "en": "Senior management, the board",
                      "pt": "Gerência geral, diretoria"},
        "texto": {
            "es": "Necesito 30 minutos al mes de comité de portafolio y un sponsor visible. "
                  "A cambio, en 90 días vas a tener una sola versión de la verdad del estado "
                  "de todos los proyectos, sin pedirle un informe manual a nadie.",
            "en": "I need 30 minutes a month for a portfolio committee and a visible sponsor. "
                  "In exchange, in 90 days you'll have a single source of truth for the status "
                  "of every project, without asking anyone for a manual report.",
            "pt": "Preciso de 30 minutos por mês de comitê de portfólio e um sponsor visível. "
                  "Em troca, em 90 dias você vai ter uma única versão da verdade sobre o status "
                  "de todos os projetos, sem pedir relatório manual a ninguém.",
        },
    },
    "dueno": {
        "titulo": {"es": "Guion para dueños de proyecto", "en": "Script for project owners",
                   "pt": "Roteiro para responsáveis de projeto"},
        "audiencia": {"es": "Líderes de proyecto, PMs", "en": "Project leads, PMs",
                      "pt": "Líderes de projeto, PMs"},
        "texto": {
            "es": "Ser dueño del proyecto en la herramienta no es carga extra, es control: "
                  "10 minutos por semana confirmando el estado real evitan que alguien más "
                  "decida por vos con datos viejos.",
            "en": "Owning the project in the tool isn't extra work, it's control: 10 minutes a "
                  "week confirming the real status keeps someone else from deciding for you "
                  "with stale data.",
            "pt": "Ser o responsável do projeto na ferramenta não é carga extra, é controle: "
                  "10 minutos por semana confirmando o status real evita que outra pessoa "
                  "decida por você com dados velhos.",
        },
    },
    "equipo": {
        "titulo": {"es": "Guion para el equipo", "en": "Script for the team", "pt": "Roteiro para a equipe"},
        "audiencia": {"es": "Equipo operativo", "en": "The operating team", "pt": "Equipe operacional"},
        "texto": {
            "es": "El standup de 5 minutos alimenta el sistema solo. No estás 'cargando datos "
                  "para un jefe', estás evitando que alguien te pregunte lo mismo tres veces.",
            "en": "The 5-minute standup feeds the system on its own. You're not \"entering data "
                  "for a boss\" — you're avoiding being asked the same thing three times.",
            "pt": "O standup de 5 minutos alimenta o sistema sozinho. Você não está 'carregando "
                  "dado para um chefe', está evitando que alguém te pergunte a mesma coisa três vezes.",
        },
    },
    "comite": {
        "titulo": {"es": "Guion para el comité de definiciones", "en": "Script for the definitions committee",
                   "pt": "Roteiro para o comitê de definições"},
        "audiencia": {"es": "Comité de portafolio", "en": "The portfolio committee",
                      "pt": "Comitê de portfólio"},
        "texto": {
            "es": "Diez minutos de discusión por término del glosario alcanzan: el dueño del "
                  "área decide, se publica, y listo — nadie vuelve a discutir qué es 'en riesgo'.",
            "en": "Ten minutes of discussion per glossary term is enough: the area owner "
                  "decides, it gets published, done — nobody argues again about what \"at risk\" means.",
            "pt": "Dez minutos de discussão por termo do glossário bastam: o responsável da "
                  "área decide, publica, e pronto — ninguém mais discute o que é 'em risco'.",
        },
    },
}


def automation_rows(lang: str = "es"):
    lang = lang if lang in ("es", "en", "pt") else "es"
    filas = []
    for row in AUTOMATION:
        fila = {"area": row["area"].get(lang, row["area"]["es"]), "nivel": row["nivel"],
               "detalle": row["detalle"].get(lang, row["detalle"]["es"])}
        if "speech_id" in row:
            fila["speech_id"] = row["speech_id"]
        filas.append(fila)
    return filas


def speeches(lang: str = "es"):
    lang = lang if lang in ("es", "en", "pt") else "es"
    return {
        clave: {"titulo": s["titulo"].get(lang, s["titulo"]["es"]),
               "audiencia": s["audiencia"].get(lang, s["audiencia"]["es"]),
               "texto": s["texto"].get(lang, s["texto"]["es"])}
        for clave, s in SPEECHES.items()
    }
