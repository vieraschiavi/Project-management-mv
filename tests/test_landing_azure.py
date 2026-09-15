# © 2026 Martín Viera. Todos los derechos reservados.
"""Las cifras de la sección Azure DevOps de la landing salen del motor.

La regla de la landing es la misma que la del video: ningún número escrito a
mano. Si `backlog_calidad` cambia una regla y la demo empieza a dar otra cosa,
la página queda mintiendo — y una cifra inflada en la página de ventas es
exactamente lo que no se puede permitir un producto cuyo argumento es que no
inventa dato. Este test compara lo que dice el HTML contra lo que calcula el
motor, y falla si se separan.
"""

from __future__ import annotations

import pathlib
import re
from datetime import date

import pytest

from mvpm import backlog_calidad as bc
from mvpm.demo_azure import backlog_demo

RAIZ = pathlib.Path(__file__).resolve().parent.parent
LANDING = RAIZ / "landing" / "index.html"
HOY = date(2026, 9, 15)


@pytest.fixture(scope="module")
def html() -> str:
    return LANDING.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def cifras() -> dict:
    """Lo que el motor calcula hoy sobre el backlog de demo."""
    df = backlog_demo()
    antes = bc.resumen(bc.revisar(df, hoy=HOY))
    corregido, cambios = bc.corregir(df, hoy=HOY)
    despues = bc.resumen(bc.revisar(corregido, hoy=HOY))
    return {
        "hallazgos": f"{antes['total']} → {despues['total']}",
        "altas": f"{antes['por_severidad'][bc.ALTA]} → "
                 f"{despues['por_severidad'][bc.ALTA]}",
        "correcciones": str(len(cambios)),
        "reglas": str(len(bc.REGLAS)),
        "resueltas": antes["total"] - despues["total"],
    }


def _valor(html: str, nombre: str) -> str:
    m = re.search(rf'<b data-n="{nombre}">([^<]+)</b>', html)
    assert m, f"no está el dato '{nombre}' en la landing"
    return m.group(1).strip()


@pytest.mark.parametrize("nombre", ["hallazgos", "altas", "correcciones", "reglas"])
def test_la_cifra_de_la_landing_es_la_que_da_el_motor(html, cifras, nombre):
    assert _valor(html, nombre) == cifras[nombre], (
        f"la landing dice '{_valor(html, nombre)}' y el motor da "
        f"'{cifras[nombre]}'. Actualizá landing/index.html.")


def test_el_texto_dice_cuantas_se_resuelven_de_verdad(html, cifras):
    # "Las 28 que se van" aparece en los tres idiomas. Es la cifra más fácil de
    # dejar vieja porque va en prosa, no en un cuadro.
    esperado = cifras["resueltas"]
    for patron in (rf"Las {esperado} que se van",
                   rf"The {esperado} that go",
                   rf"As {esperado} que saem"):
        assert re.search(patron, html), f"no coincide la prosa: falta «{patron}»"


def test_la_seccion_no_promete_que_el_backlog_queda_perfecto(html):
    # El argumento del producto es que NO inventa. Si alguna vez alguien
    # escribe acá "backlog impecable" o "cero problemas", se rompió el pitch.
    seccion = html.split('<section id="ado-ad"')[1].split("</section>")[0].lower()
    for prohibido in ("cero problemas", "sin errores", "impecable", "perfecto",
                      "100% limpio", "todos los problemas"):
        assert prohibido not in seccion, f"promesa que el producto no cumple: {prohibido}"


def test_las_filas_del_antes_y_del_despues_estan_pareadas(html):
    seccion = html.split('<section id="ado-ad"')[1].split("</section>")[0]
    antes = set(re.findall(r'data-i="ado_r(\d+)_a"', seccion))
    despues = set(re.findall(r'data-i="ado_r(\d+)_d"', seccion))
    assert antes == despues and antes, \
        f"filas desparejas: antes={sorted(antes)}, después={sorted(despues)}"


def test_las_claves_nuevas_estan_en_los_tres_idiomas(html):
    """La landing traduce con un diccionario por idioma; una clave que falta
    deja el texto en español en medio de la página en inglés."""
    seccion = html.split('<section id="ado-ad"')[1].split("</section>")[0]
    claves = set(re.findall(r'data-i="(ado_[a-z0-9_]+)"', seccion))
    assert claves, "la sección perdió los data-i"
    for clave in sorted(claves):
        # Cada clave tiene que aparecer además en los dos diccionarios (en, pt),
        # o sea al menos tres veces en total contando el HTML.
        veces = len(re.findall(rf'\b{clave}\s*:', html))
        assert veces >= 2, f"la clave {clave} falta en algún diccionario ({veces}/2)"
