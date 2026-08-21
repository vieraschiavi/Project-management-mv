# © 2026 Martín Viera. Todos los derechos reservados.
"""Qué desbloquea realmente cada plan — y qué se promete sin tenerlo.

`PLANES` declara una lista de `features` por plan desde el primer día. Estaba
muerta: ninguna línea del programa la consultaba, así que el plan no cambiaba
absolutamente nada más allá del cupo de IA y de la vigencia. Una lista de
funciones que nadie lee es peor que no tenerla — parece que el producto
distingue planes y no distingue nada.

Lo que se fija acá:

* que `tiene_feature` respete el modelo real (prueba completa → todo; licencia
  → lo del plan; sin licencia y vencido → nada);
* que toda feature declarada esté implementada o esté ADMITIDA como pendiente,
  para que no se pueda vender en la landing algo que el código no hace.
"""

import json
import time

import pytest

from mvpm import licensing, owner

DIA = 86400


@pytest.fixture
def instalacion(monkeypatch, tmp_path):
    """Una instalación de cliente aislada, con la prueba de 7 días vencida.

    `es_owner` se fuerza a False a propósito. Sin eso, este archivo pasaba solo
    y fallaba en la suite completa: otro test deja el modo dueño activo, el
    dueño entra a todo sin licencia, y el gate que se quiere probar ni se
    ejecuta — el test daba verde por el motivo equivocado, que es peor que
    fallar.
    """
    monkeypatch.setattr(owner, "es_owner", lambda: False)
    monkeypatch.setattr(licensing, "_RUTA_LICENCIA", tmp_path / "licencia")
    monkeypatch.setattr(licensing, "_RUTAS_TRIAL", (tmp_path / "trial.json",))
    (tmp_path / "trial.json").write_text(
        json.dumps({"primer_uso": time.time() - 30 * DIA}), encoding="utf-8")
    return tmp_path


@pytest.fixture
def en_prueba(monkeypatch, tmp_path):
    """Una instalación recién abierta: dentro de los 7 días."""
    monkeypatch.setattr(licensing, "_RUTA_LICENCIA", tmp_path / "licencia")
    monkeypatch.setattr(licensing, "_RUTAS_TRIAL", (tmp_path / "trial.json",))
    (tmp_path / "trial.json").write_text(
        json.dumps({"primer_uso": time.time() - 1 * DIA}), encoding="utf-8")
    return tmp_path


def test_durante_la_prueba_esta_todo(en_prueba):
    """El producto se descarga completo. Recortar funciones durante la prueba
    sería otro modelo de negocio."""
    for feature in ("catalogo", "copiloto_ia", "integraciones", "reportes_automaticos"):
        assert licensing.tiene_feature(None, feature) is True, feature


def test_con_la_prueba_vencida_y_sin_licencia_no_hay_nada(instalacion):
    for feature in ("catalogo", "copiloto_ia", "integraciones"):
        assert licensing.tiene_feature(None, feature) is False, feature


def test_una_licencia_paga_da_exactamente_lo_de_su_plan(instalacion):
    token = licensing.issue_license("professional", "c@e.com", "mp-1")
    for feature in licensing.PLANES["professional"]["features"]:
        assert licensing.tiene_feature(token, feature) is True, feature
    # Y no lo del plan de arriba.
    assert licensing.tiene_feature(token, "sso") is False


def test_enterprise_llega_mas_lejos_que_professional(instalacion):
    token = licensing.issue_license("enterprise", "c@e.com", "mp-1")
    assert licensing.tiene_feature(token, "sso") is True


def test_una_licencia_vencida_no_desbloquea_nada(instalacion, monkeypatch):
    token = licensing.issue_license("professional", "c@e.com", "mp-1")
    assert licensing.tiene_feature(token, "integraciones") is True
    vencida = time.time() + (licensing.PLANES["professional"]["vigencia_dias"] + 5) * DIA
    assert licensing.tiene_feature(token, "integraciones", ahora=vencida) is False


def test_un_token_inventado_no_desbloquea_nada(instalacion):
    assert licensing.tiene_feature("MVPM2.mentira.firma", "integraciones") is False


def test_una_feature_que_no_existe_es_no(instalacion):
    """Un typo en el nombre tiene que cerrar la puerta, no abrirla."""
    token = licensing.issue_license("professional", "c@e.com", "mp-1")
    assert licensing.tiene_feature(token, "integracionesss") is False


# ------------------------------------------------------- honestidad del plan

def test_toda_feature_declarada_existe_o_esta_admitida_como_pendiente():
    """El test que impide vender humo.

    Cada nombre de `PLANES[...]["features"]` tiene que consultarse en algún
    lado del producto, o figurar en `FEATURES_NO_IMPLEMENTADAS`. Si mañana
    alguien agrega "reportes_pdf" al plan Enterprise y lo pone en la landing,
    esto se cae hasta que exista el código o hasta que se admita, por escrito,
    que todavía no existe.
    """
    from pathlib import Path

    raiz = Path(__file__).resolve().parent.parent
    fuentes = "\n".join(
        p.read_text(encoding="utf-8")
        for carpeta, patron in [("mvpm", "*.py"), ("app", "*.py"), ("api", "*.py"),
                                ("api", "*.js")]
        for p in (raiz / carpeta).glob(patron)
        # licensing.py es donde se DECLARAN: nombrarlas ahí no es implementarlas.
        if p.name != "licensing.py"
    )

    declaradas = {f for datos in licensing.PLANES.values() for f in datos["features"]}
    eximidas = licensing.FEATURES_BASE | licensing.FEATURES_NO_IMPLEMENTADAS
    huerfanas = sorted(
        f for f in declaradas - eximidas
        if f'"{f}"' not in fuentes and f"'{f}'" not in fuentes
    )
    assert not huerfanas, (
        "features que el plan promete y ninguna línea del producto consulta:\n  "
        + "\n  ".join(huerfanas)
        + "\n\nO se implementan, o se admiten en FEATURES_NO_IMPLEMENTADAS, o "
          "—si están en todos los planes— en FEATURES_BASE.")


def test_el_nucleo_esta_en_todos_los_planes():
    """`FEATURES_BASE` se exime del test de arriba porque no existe un plan sin
    ella. Si alguna dejara de estar en algún plan, esa exención sería mentira y
    la feature pasaría a necesitar un control real."""
    for plan, datos in licensing.PLANES.items():
        faltan = sorted(licensing.FEATURES_BASE - set(datos["features"]))
        assert not faltan, (
            f"el plan {plan} no incluye {faltan}, que están declaradas como "
            "núcleo común: o vuelven al plan, o salen de FEATURES_BASE y "
            "necesitan su propio control")


def test_lo_admitido_como_pendiente_no_se_promete_en_la_landing():
    """Lo declarado y no construido puede vivir en el código como intención.
    Lo que no puede es aparecer en la página donde alguien decide pagar."""
    from pathlib import Path

    raiz = Path(__file__).resolve().parent.parent
    landing = raiz / "landing"
    if not landing.exists():
        pytest.skip("landing/ no viaja en el paquete: es del repositorio")

    textos = {p: p.read_text(encoding="utf-8").lower()
              for p in landing.rglob("*.html")}
    # Se buscan las etiquetas comerciales, no el identificador interno: nadie
    # escribe "white_label" en una landing, escribe "marca blanca".
    etiquetas = {"sso": ["single sign-on", "single sign on"],
                 "auditoria": ["log de auditoría", "trazabilidad de auditoría"],
                 "white_label": ["marca blanca", "white label", "white-label"]}
    promesas = [
        (p.name, feature, e)
        for feature in licensing.FEATURES_NO_IMPLEMENTADAS
        for e in etiquetas.get(feature, [])
        for p, texto in textos.items() if e in texto
    ]
    assert not promesas, f"la landing promete funciones que no existen: {promesas}"


# ------------------------------------- el gate de la API, probado de verdad

def test_un_plan_pago_sin_integraciones_no_abre_la_api_de_bi(instalacion, monkeypatch):
    """El control de comportamiento, no de texto.

    El test de honestidad de arriba sólo busca el NOMBRE de la feature en el
    código: borrar el `if` de `api/main.py` lo dejaba pasar, porque el string
    seguía apareciendo en otro archivo. Lo probé mutando: pasaba. Esto ejercita
    la ruta real — un cliente con licencia vigente cuyo plan no incluye
    conectores tiene que recibir 402 de la API que consumen Power BI y Tableau.

    Hoy ningún plan a la venta excluye integraciones, así que se construye el
    caso quitándosela a Professional: lo que se fija es que el control exista,
    no la política comercial de hoy.
    """
    from fastapi.testclient import TestClient

    from api import main

    token = licensing.issue_license("professional", "c@e.com", "mp-1")
    licensing.guardar_token(token)
    # Con integraciones, entra.
    assert TestClient(main.app).get("/api/proyectos").status_code == 200

    sin_conectores = dict(licensing.PLANES["professional"])
    sin_conectores["features"] = [f for f in sin_conectores["features"]
                                  if f != "integraciones"]
    monkeypatch.setitem(licensing.PLANES, "professional", sin_conectores)

    r = TestClient(main.app).get("/api/proyectos")
    assert r.status_code == 402, r.text
    assert "integraciones" in r.text.lower()


def test_el_dueno_entra_aunque_su_plan_no_liste_la_feature(instalacion, monkeypatch):
    """El dueño no tiene licencia ni plan: entra por otra puerta. Si el gate
    nuevo lo dejara afuera de su propia herramienta, sería una regresión."""
    from fastapi.testclient import TestClient

    from api import main

    monkeypatch.setattr(main.owner, "es_owner", lambda: True)
    assert TestClient(main.app).get("/api/proyectos").status_code == 200
