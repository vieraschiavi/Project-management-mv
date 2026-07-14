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

FUENTE = ("IPA / Cabinet Office — Annual Report on Major Projects 2021-22 (Government "
          "Major Projects Portfolio). Open Government Licence v3.0.")
FUENTE_URL = "https://www.gov.uk/government/collections/major-projects-data"

# Los dos casos narrados en detalle — texto real tomado del informe anual
# (recortado; el original incluye más detalle departamental).
CASOS = {
    "Social Housing Decarbonisation Fund": {
        "depto": "BEIS (hoy DESNZ)",
        "rag": "Amber",
        "resumen": "Fondo de £3.800M a 10 años para descarbonizar vivienda social. La Ola 1 "
                   "recibió muchas más postulaciones válidas de lo previsto.",
        "narrativa_real": "El desvío de presupuesto supera el 5%. Se debe principalmente a que el "
                          "baseline original para el año fiscal 21/22 era de £160M, pero en "
                          "septiembre de 2021 — por la alta cantidad de buenas postulaciones "
                          "recibidas para la Ola 1 — el monto subió a c.£180M. Se acordó que el "
                          "subgasto de otros programas EEL cubriera el sobregasto de SHDF.",
        "revision_real": "El proyecto de la Ola 1 tuvo una revisión IPA Gate 3 en noviembre de "
                         "2021 y recibió calificación Roja. Se armó un plan de acción con 9 "
                         "recomendaciones y 3 bloqueos. En la re-revisión de enero de 2022 pasó a "
                         "Ámbar.",
    },
    "Borders & Trade Programme": {
        "depto": "HMRC",
        "rag": "Green",
        "resumen": "Programa post-Brexit para estabilizar y operar el control fronterizo del "
                   "Reino Unido tras el fin del período de transición con la UE.",
        "narrativa_real": "El subgasto del año 21/22 se debe principalmente a menor demanda de la "
                          "esperada en las ayudas para que pequeñas y medianas empresas se "
                          "adapten a las nuevas reglas aduaneras, y a cambios de alcance en los "
                          "sistemas de TI de frontera.",
        "revision_real": "La calificación de confianza de entrega de la IPA a 21/22-Q4 es Verde. "
                         "El objetivo estratégico principal (implementar controles fronterizos "
                         "completos) se logró el 1 de enero de 2022. El programa inició cierre "
                         "formal.",
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


def caso(nombre: str) -> dict:
    """Detalle de uno de los dos casos narrados, con el número real que el
    motor calcula sobre ese proyecto puntual."""
    proj = cargar_portafolio_real()
    fila = proj[proj["nombre"] == nombre].iloc[0]
    cat = catalog.catalog(proj)
    fila_cat = cat[cat["nombre"] == nombre].iloc[0]
    info = CASOS[nombre]
    return {
        "nombre": nombre,
        "depto": info["depto"],
        "rag": info["rag"],
        "resumen": info["resumen"],
        "narrativa_real": info["narrativa_real"],
        "revision_real": info["revision_real"],
        "presupuesto_m": fila["presupuesto"],
        "ejecutado_m": fila["ejecutado"],
        "ejecucion_pct": fila_cat["ejecucion_pct"],
        "sobre_presupuesto": bool(fila_cat["sobre_presupuesto"]),
        "criticidad": fila["criticidad"],
    }
