# © 2026 Martín Viera. Todos los derechos reservados.
"""Pestaña "Demo reales": corre el motor sobre datos públicos reales, no
sintéticos — para que se vea cómo se comporta con proyectos que existieron
de verdad, con sus propios problemas documentados.

Fuente: Infrastructure and Projects Authority (IPA) / Cabinet Office (Reino
Unido) — Annual Report on Major Projects 2021-22, datos del Government Major
Projects Portfolio (GMPP). Publicados bajo Open Government Licence v3.0
(uso comercial permitido con atribución). 132 proyectos reales del portafolio
público británico, con calificación de confianza de entrega (RAG) y
presupuesto base vs. ejecutado reportados por cada departamento.

Es un dataset real de portafolio (nivel proyecto) — no incluye tareas ni
equipo, así que sólo se corren las herramientas que no dependen de eso
(catálogo, KPIs, detección de sobrepresupuesto). No se inventan tareas para
simular lo que el dataset no tiene.
"""

from pathlib import Path

import pandas as pd

from . import catalog

_CSV_PATH = Path(__file__).parent / "data" / "gmpp_real.csv"

_RAG_A_CRITICIDAD = {"Red": "Alta", "Amber": "Media", "Green": "Baja"}

_FUENTE_TXT = {
    "es": "IPA / Cabinet Office — Annual Report on Major Projects 2021-22 (Government "
          "Major Projects Portfolio). Open Government Licence v3.0.",
    "en": "IPA / Cabinet Office — Annual Report on Major Projects 2021-22 (Government "
          "Major Projects Portfolio). Open Government Licence v3.0.",
    "pt": "IPA / Cabinet Office — Annual Report on Major Projects 2021-22 (Government "
          "Major Projects Portfolio, Reino Unido). Open Government Licence v3.0.",
}
FUENTE = _FUENTE_TXT["es"]  # compatibilidad: quien no pida idioma sigue viendo esto
FUENTE_URL = "https://www.gov.uk/government/collections/major-projects-data"


def fuente(lang: str = "es") -> str:
    return _FUENTE_TXT.get(lang, _FUENTE_TXT["es"])


# Los dos casos narrados en detalle — resumen del informe anual real (el
# informe original está en inglés; "narrativa_real"/"revision_real" son un
# recorte/paráfrasis, no una cita legal textual, en las tres versiones).
# Nombres de fondo/programa, departamento, fechas y montos son datos reales:
# no se traducen. RAG (Red/Amber/Green) es la escala oficial del gobierno
# británico — se mantiene tal cual, universal, en los tres idiomas.
CASOS = {
    "Social Housing Decarbonisation Fund": {
        "depto": "BEIS (hoy DESNZ)",
        "rag": "Amber",
        "resumen": {
            "es": "Fondo de £3.800M a 10 años para descarbonizar vivienda social. La Ola 1 "
                  "recibió muchas más postulaciones válidas de lo previsto.",
            "en": "A £3.8bn, 10-year fund to decarbonise social housing. Wave 1 received far "
                  "more valid applications than expected.",
            "pt": "Fundo de £3,8 bilhões em 10 anos para descarbonizar moradia social. A Onda 1 "
                  "recebeu muito mais inscrições válidas do que o previsto.",
        },
        "narrativa_real": {
            "es": "El desvío de presupuesto supera el 5%. Se debe principalmente a que el "
                  "baseline original para el año fiscal 21/22 era de £160M, pero en "
                  "septiembre de 2021 — por la alta cantidad de buenas postulaciones "
                  "recibidas para la Ola 1 — el monto subió a c.£180M. Se acordó que el "
                  "subgasto de otros programas EEL cubriera el sobregasto de SHDF.",
            "en": "The budget variance is above 5%. It's mainly because the original baseline "
                  "for fiscal year 21/22 was £160M, but in September 2021 — due to the high "
                  "volume of strong Wave 1 applications received — the figure rose to c.£180M. "
                  "It was agreed that underspend from other EEL programmes would cover SHDF's "
                  "overspend.",
            "pt": "O desvio de orçamento supera 5%. Deve-se principalmente a que o baseline "
                  "original para o ano fiscal 21/22 era de £160 milhões, mas em setembro de "
                  "2021 — pela alta quantidade de boas inscrições recebidas na Onda 1 — o valor "
                  "subiu para cerca de £180 milhões. Foi acordado que o subgasto de outros "
                  "programas EEL cobrisse o sobregasto do SHDF.",
        },
        "revision_real": {
            "es": "El proyecto de la Ola 1 tuvo una revisión IPA Gate 3 en noviembre de "
                  "2021 y recibió calificación Roja. Se armó un plan de acción con 9 "
                  "recomendaciones y 3 bloqueos. En la re-revisión de enero de 2022 pasó a "
                  "Ámbar.",
            "en": "The Wave 1 project had an IPA Gate 3 review in November 2021 and received a "
                  "Red rating. An action plan with 9 recommendations and 3 blockers was put "
                  "together. In the January 2022 re-review it moved to Amber.",
            "pt": "O projeto da Onda 1 teve uma revisão IPA Gate 3 em novembro de 2021 e "
                  "recebeu classificação Vermelha. Foi montado um plano de ação com 9 "
                  "recomendações e 3 bloqueios. Na nova revisão de janeiro de 2022 passou "
                  "para Âmbar.",
        },
    },
    "Borders & Trade Programme": {
        "depto": "HMRC",
        "rag": "Green",
        "resumen": {
            "es": "Programa post-Brexit para estabilizar y operar el control fronterizo del "
                  "Reino Unido tras el fin del período de transición con la UE.",
            "en": "A post-Brexit programme to stabilise and operate the UK's border controls "
                  "after the end of the EU transition period.",
            "pt": "Programa pós-Brexit para estabilizar e operar o controle de fronteiras do "
                  "Reino Unido após o fim do período de transição com a UE.",
        },
        "narrativa_real": {
            "es": "El subgasto del año 21/22 se debe principalmente a menor demanda de la "
                  "esperada en las ayudas para que pequeñas y medianas empresas se "
                  "adapten a las nuevas reglas aduaneras, y a cambios de alcance en los "
                  "sistemas de TI de frontera.",
            "en": "The 21/22 underspend is mainly due to lower-than-expected demand for support "
                  "helping small and medium businesses adapt to the new customs rules, and to "
                  "scope changes in the border IT systems.",
            "pt": "O subgasto do ano 21/22 se deve principalmente à menor demanda do que a "
                  "esperada pelas ajudas para que pequenas e médias empresas se adaptem às "
                  "novas regras aduaneiras, e a mudanças de escopo nos sistemas de TI de "
                  "fronteira.",
        },
        "revision_real": {
            "es": "La calificación de confianza de entrega de la IPA a 21/22-Q4 es Verde. "
                  "El objetivo estratégico principal (implementar controles fronterizos "
                  "completos) se logró el 1 de enero de 2022. El programa inició cierre "
                  "formal.",
            "en": "The IPA's delivery confidence rating as of 21/22-Q4 is Green. The main "
                  "strategic objective (implementing full border controls) was achieved on "
                  "1 January 2022. The programme began formal closure.",
            "pt": "A classificação de confiança de entrega da IPA em 21/22-T4 é Verde. O "
                  "principal objetivo estratégico (implementar controles de fronteira "
                  "completos) foi alcançado em 1º de janeiro de 2022. O programa iniciou o "
                  "encerramento formal.",
        },
    },
}


def cargar_portafolio_real() -> pd.DataFrame:
    """Devuelve un DataFrame con el mismo esquema que `demo_data.projects()`,
    pero construido a partir de los 132 proyectos reales y limpios del GMPP
    (se descartaron filas sin calificación RAG válida o sin presupuesto
    numérico — no se completan huecos con datos inventados)."""
    df = pd.read_csv(_CSV_PATH)
    return pd.DataFrame({
        "proyecto_id": [f"GMPP-{i+1:03d}" for i in range(len(df))],
        "nombre": df["nombre"],
        "portafolio": df["portafolio"],
        "sponsor": df["sponsor"],
        "dueno": None,
        "segmento": "Gobierno (Reino Unido)",
        "fecha_inicio": df["fecha_inicio"],
        "fecha_fin": df["fecha_fin"],
        "presupuesto": df["presupuesto_m"],
        "ejecutado": df["ejecutado_m"],
        "criticidad": df["rag"].map(_RAG_A_CRITICIDAD).fillna("Media"),
    })


def resumen_portafolio() -> dict:
    """KPIs reales del motor corriendo sobre los 132 proyectos — sin tareas
    ni equipo, sólo lo que el dataset realmente tiene."""
    proj = cargar_portafolio_real()
    kpis = catalog.kpis(proj)
    cat = catalog.catalog(proj)
    minutos_por_revision_manual = 15  # supuesto explícito, no medido — declarado, no oculto
    horas_ahorradas = round(len(proj) * minutos_por_revision_manual / 60, 1)
    return {
        "total_proyectos": len(proj),
        "sobre_presupuesto": kpis["sobre_presupuesto"],
        "presupuesto_total_m": round(kpis["presupuesto_total"], 1),
        "ejecutado_total_m": round(kpis["ejecutado_total"], 1),
        "minutos_por_revision_manual_supuesto": minutos_por_revision_manual,
        "horas_ahorradas_estimadas": horas_ahorradas,
        "proyectos_sobre_presupuesto_detalle": cat[cat["sobre_presupuesto"]][
            ["nombre", "presupuesto", "ejecutado", "ejecucion_pct"]
        ].sort_values("ejecucion_pct", ascending=False).head(10),
    }


def caso(nombre: str, lang: str = "es") -> dict:
    """Detalle de uno de los dos casos narrados, con el número real que el
    motor calcula sobre ese proyecto puntual."""
    lang = lang if lang in ("es", "en", "pt") else "es"
    proj = cargar_portafolio_real()
    fila = proj[proj["nombre"] == nombre].iloc[0]
    cat = catalog.catalog(proj)
    fila_cat = cat[cat["nombre"] == nombre].iloc[0]
    info = CASOS[nombre]
    return {
        "nombre": nombre,
        "depto": info["depto"],
        "rag": info["rag"],
        "resumen": info["resumen"].get(lang, info["resumen"]["es"]),
        "narrativa_real": info["narrativa_real"].get(lang, info["narrativa_real"]["es"]),
        "revision_real": info["revision_real"].get(lang, info["revision_real"]["es"]),
        "presupuesto_m": fila["presupuesto"],
        "ejecutado_m": fila["ejecutado"],
        "ejecucion_pct": fila_cat["ejecucion_pct"],
        "sobre_presupuesto": bool(fila_cat["sobre_presupuesto"]),
        "criticidad": fila["criticidad"],
    }
