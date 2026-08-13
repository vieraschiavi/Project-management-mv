# © 2026 Martín Viera. Todos los derechos reservados.
"""Seguridad de la API REST de BI (api/main.py).

La API sirve el portafolio completo del cliente. Antes escuchaba en 0.0.0.0
con CORS "*" y sin ninguna autorización, así que cualquiera en la misma red
podía leer proyectos, presupuestos y equipo. Estos tests fijan el
comportamiento nuevo para que no se vuelva a abrir sin querer.
"""

import importlib

import pytest
from fastapi.testclient import TestClient

from mvpm import licensing


def _cliente(monkeypatch, tmp_path, api_key: str | None = None):
    """Recarga api.main con las env vars dadas (se leen al importar).

    `MVPM_DATA_DIR` aísla la base y el id de máquina en una carpeta nueva por
    test. Eso NO alcanza para el reloj de la prueba de 7 días: `_RUTAS_TRIAL`
    en licensing.py incluye dos rutas fijas a `Path.home()` además de la que
    sigue a `MVPM_DATA_DIR`, y `_leer_trial()` toma la MÁS VIEJA entre las que
    pueda leer — así que sin parchear `_RUTAS_TRIAL` directamente, un test acá
    seguiría leyendo el marcador real de la máquina que corre la suite. Mismo
    parche que ya usa `_patch_store` en test_core.py.
    """
    monkeypatch.setenv("MVPM_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(licensing, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(licensing, "_USAGE_FILE", tmp_path / "uso.json")
    monkeypatch.setattr(licensing, "_TRIAL_FILE", tmp_path / "trial.json")
    monkeypatch.setattr(licensing, "_RUTAS_TRIAL", (tmp_path / "trial.json",))
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


def test_endpoints_publicos_no_exponen_datos_del_cliente(monkeypatch, tmp_path):
    """/, /health y /licencias/planes quedan abiertos a propósito: no dicen
    nada del portafolio de nadie."""
    _, client = _cliente(monkeypatch, tmp_path)
    assert client.get("/health").status_code == 200
    assert client.get("/").status_code == 200
    r = client.get("/licencias/planes")
    assert r.status_code == 200
    assert "professional" in r.json()


@pytest.mark.parametrize("ruta", ENDPOINTS_CON_DATOS)
def test_desde_la_misma_maquina_no_pide_credenciales(monkeypatch, tmp_path, ruta):
    """El caso normal —Power BI y el dashboard en la misma PC, prueba de 7
    días vigente— no se rompe.

    Se afirma que el pedido NO lo frena la autorización (401/402/403), no que
    devuelva 200: si la base está vacía o el nombre de tabla no existe, la
    respuesta legítima puede ser 404, y eso no dice nada sobre el gate. Atar
    este test al contenido de la base lo hacía fallar según qué datos hubiera
    quedado de otros tests.
    """
    _, client = _cliente(monkeypatch, tmp_path)
    assert client.get(ruta).status_code not in (401, 402, 403)


def test_prueba_vencida_bloquea_los_endpoints_de_datos(monkeypatch, tmp_path):
    """Antes, esta API servía el portafolio completo para siempre aunque la
    prueba de 7 días del dashboard ya hubiera vencido: `requiere_acceso` nunca
    consultaba `licensing.estado_acceso`. El candado real está en el reloj de
    archivo (`primer_uso`), no en un mock: se hace vencer la prueba de verdad,
    escribiendo el marcador con una fecha de hace 30 días.
    """
    import json
    import time

    main, client = _cliente(monkeypatch, tmp_path)

    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "trial.json").write_text(
        json.dumps({"primer_uso": time.time() - 30 * 86400}))

    r = client.get("/api/proyectos")
    assert r.status_code == 402
    assert "venci" in r.json()["detail"].lower()


def test_prueba_vencida_no_bloquea_los_endpoints_publicos(monkeypatch, tmp_path):
    """El candado es de datos, no del programa entero: /health y
    /licencias/planes siguen respondiendo aunque la prueba haya vencido —
    son los que necesita ver alguien decidiendo si comprar."""
    import json
    import time

    _, client = _cliente(monkeypatch, tmp_path)

    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "trial.json").write_text(
        json.dumps({"primer_uso": time.time() - 30 * 86400}))

    assert client.get("/health").status_code == 200
    assert client.get("/licencias/planes").status_code == 200


def test_el_dueno_no_se_bloquea_aunque_la_prueba_este_vencida(monkeypatch, tmp_path):
    """`owner.es_owner()` va ANTES del chequeo de prueba/licencia — la
    instalación del dueño no tiene reloj de 7 días."""
    import json
    import time

    main, client = _cliente(monkeypatch, tmp_path)

    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "trial.json").write_text(
        json.dumps({"primer_uso": time.time() - 30 * 86400}))

    monkeypatch.setattr(main.owner, "es_owner", lambda: True)
    assert client.get("/api/proyectos").status_code not in (401, 402, 403)


def test_desde_otra_maquina_sin_api_key_configurada_se_niega(monkeypatch, tmp_path):
    """Sin MVPM_API_KEY, un pedido remoto no recibe datos: corta con 403.

    Se ejerce la dependencia directamente porque TestClient siempre se
    presenta como "testclient" (loopback) y no permite simular otra IP de
    origen; lo que importa verificar es la decisión de autorización.
    """
    from types import SimpleNamespace

    from fastapi import HTTPException
    main, _ = _cliente(monkeypatch, tmp_path)

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


def test_con_api_key_configurada_exige_el_header(monkeypatch, tmp_path):
    from types import SimpleNamespace

    from fastapi import HTTPException
    main, _ = _cliente(monkeypatch, tmp_path, api_key="clave-secreta-de-prueba")

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


def test_cors_no_es_comodin(monkeypatch, tmp_path):
    """allow_origins="*" dejaba que cualquier web abierta en el navegador del
    cliente leyera su portafolio. Ahora la lista es acotada."""
    main, _ = _cliente(monkeypatch, tmp_path)
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
