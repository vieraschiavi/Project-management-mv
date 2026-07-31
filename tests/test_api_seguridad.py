"""Seguridad de la API REST de BI (api/main.py).

La API sirve el portafolio completo del cliente. Antes escuchaba en 0.0.0.0
con CORS "*" y sin ninguna autorización, así que cualquiera en la misma red
podía leer proyectos, presupuestos y equipo. Estos tests fijan el
comportamiento nuevo para que no se vuelva a abrir sin querer.
"""

import importlib

import pytest
from fastapi.testclient import TestClient


def _cliente(monkeypatch, api_key: str | None = None):
    """Recarga api.main con las env vars dadas (se leen al importar)."""
    if api_key is None:
        monkeypatch.delenv("MVPM_API_KEY", raising=False)
    else:
        monkeypatch.setenv("MVPM_API_KEY", api_key)
    import api.main as main
    importlib.reload(main)
    return main, TestClient(main.app)


ENDPOINTS_CON_DATOS = [
    "/api/proyectos",
    "/api/tareas",
    "/api/equipo",
    "/api/demo/pharma",
    "/api/reviews/summary",
    "/licencias/estado",
]


def test_endpoints_publicos_no_exponen_datos_del_cliente(monkeypatch):
    """/, /health y /licencias/planes quedan abiertos a propósito: no dicen
    nada del portafolio de nadie."""
    _, client = _cliente(monkeypatch)
    assert client.get("/health").status_code == 200
    assert client.get("/").status_code == 200
    r = client.get("/licencias/planes")
    assert r.status_code == 200
    assert "professional" in r.json()


@pytest.mark.parametrize("ruta", ENDPOINTS_CON_DATOS)
def test_desde_la_misma_maquina_funciona_sin_clave(monkeypatch, ruta):
    """El caso normal —Power BI y el dashboard en la misma PC— no se rompe."""
    _, client = _cliente(monkeypatch)
    assert client.get(ruta).status_code == 200


def test_desde_otra_maquina_sin_api_key_configurada_se_niega(monkeypatch):
    """Sin MVPM_API_KEY, un pedido remoto no recibe datos: corta con 403.

    Se ejerce la dependencia directamente porque TestClient siempre se
    presenta como "testclient" (loopback) y no permite simular otra IP de
    origen; lo que importa verificar es la decisión de autorización.
    """
    from types import SimpleNamespace

    from fastapi import HTTPException
    main, _ = _cliente(monkeypatch)

    remoto = SimpleNamespace(client=SimpleNamespace(host="203.0.113.9"), headers={})
    with pytest.raises(HTTPException) as exc:
        main.requiere_acceso(remoto)
    assert exc.value.status_code == 403
    assert "MVPM_API_KEY" in exc.value.detail


def test_todos_los_endpoints_de_datos_llevan_el_gate():
    """Que ninguno se agregue en el futuro sin autorización: se comprueba
    contra las rutas registradas, no contra una lista escrita a mano."""
    import api.main as main
    ABIERTAS = {"/", "/health", "/licencias/planes",
                "/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}
    sin_gate = []
    for route in main.app.routes:
        path = getattr(route, "path", None)
        if not path or path in ABIERTAS:
            continue
        deps = getattr(route, "dependencies", [])
        if not any(getattr(d, "dependency", None) is main.requiere_acceso for d in deps):
            sin_gate.append(path)
    assert not sin_gate, f"endpoints sin requiere_acceso: {sin_gate}"


def test_con_api_key_configurada_exige_el_header(monkeypatch):
    from types import SimpleNamespace

    from fastapi import HTTPException
    main, _ = _cliente(monkeypatch, api_key="clave-secreta-de-prueba")

    remoto_sin_clave = SimpleNamespace(client=SimpleNamespace(host="203.0.113.9"), headers={})
    with pytest.raises(HTTPException) as exc:
        main.requiere_acceso(remoto_sin_clave)
    assert exc.value.status_code == 401

    remoto_clave_mala = SimpleNamespace(client=SimpleNamespace(host="203.0.113.9"),
                                        headers={"x-api-key": "otra-cosa"})
    with pytest.raises(HTTPException) as exc:
        main.requiere_acceso(remoto_clave_mala)
    assert exc.value.status_code == 401

    remoto_ok = SimpleNamespace(client=SimpleNamespace(host="203.0.113.9"),
                                headers={"x-api-key": "clave-secreta-de-prueba"})
    assert main.requiere_acceso(remoto_ok) is None  # no levanta: pasa


def test_cors_no_es_comodin(monkeypatch):
    """allow_origins="*" dejaba que cualquier web abierta en el navegador del
    cliente leyera su portafolio. Ahora la lista es acotada."""
    main, _ = _cliente(monkeypatch)
    assert "*" not in main.ALLOWED_ORIGINS
    assert all(o.startswith("http://localhost") or o.startswith("http://127.0.0.1")
               for o in main.ALLOWED_ORIGINS)


def test_run_sh_no_escucha_en_todas_las_interfaces_por_defecto():
    """El default de run.sh debe ser loopback; abrirlo es una decisión
    explícita vía MVPM_API_HOST."""
    from pathlib import Path
    run_sh = Path(__file__).resolve().parent.parent / "run.sh"
    contenido = run_sh.read_text()
    assert "--host 0.0.0.0" not in contenido
    assert 'MVPM_API_HOST:-127.0.0.1' in contenido
