# © 2026 Martín Viera. Todos los derechos reservados.
"""La licencia del cliente sobrevive al cierre del programa — y la ve la API.

El token vivía sólo en el campo de texto de la barra lateral, o sea en la
sesión de Streamlit. Dos consecuencias:

1. Había que volver a pegarlo en cada apertura.
2. **La API de BI devolvía 402 a un cliente con licencia paga vigente.**
   `api/main.py` corre en otro proceso y no puede ver ese campo, así que
   consultaba el candado con `token=None`: pasados los 7 días de prueba,
   quien había pagado por los conectores de Power BI y Tableau —que se
   reparten como `.pbids` en `distribucion/`— no los podía usar. Falla
   silenciosa y después de cobrar.

Acá se fija que el archivo guardado abra la API, que sólo se guarde lo que
verifica, y que guardar no sea una puerta nueva: sin licencia válida el 402
sigue igual.
"""

import json
import time

import pytest
from fastapi.testclient import TestClient

from mvpm import licensing, owner

DIA = 86400


@pytest.fixture
def cliente_sin_prueba(monkeypatch, tmp_path):
    """Una instalación de cliente con la prueba de 7 días ya vencida: el
    estado en el que está la persona el día que decide pagar."""
    monkeypatch.setattr(licensing, "_RUTA_LICENCIA", tmp_path / "licencia")
    monkeypatch.setattr(licensing, "_RUTAS_TRIAL", (tmp_path / "trial.json",))
    (tmp_path / "trial.json").write_text(
        json.dumps({"primer_uso": time.time() - 30 * DIA}), encoding="utf-8")
    # Y no es la máquina del dueño, que entra sin candado por otra puerta.
    monkeypatch.setattr(owner, "es_owner", lambda: False)
    assert licensing.estado_acceso(licensing.token_guardado())["acceso"] is False
    return tmp_path


def _licencia() -> str:
    return licensing.issue_license("professional", "cliente@ejemplo.com", "mp-1")


# ------------------------------------------------------------ guardar y leer

def test_lo_guardado_se_lee_despues(cliente_sin_prueba):
    token = _licencia()
    assert licensing.guardar_token(token) is True
    assert licensing.token_guardado() == token


def test_no_se_guarda_un_token_que_no_verifica(cliente_sin_prueba):
    """Guardar basura dejaría al programa arrancando con una licencia que no
    es, y —peor— haría creer que quedó cargada."""
    assert licensing.guardar_token("MVPM2.no.sirve") is False
    assert licensing.token_guardado() is None
    assert not (cliente_sin_prueba / "licencia").exists()


def test_un_archivo_manoseado_no_vale(cliente_sin_prueba):
    """El archivo es texto plano en la carpeta del usuario: cualquiera lo edita.
    Lo que lo sostiene no es el permiso sino la firma."""
    licensing.guardar_token(_licencia())
    guardado = (cliente_sin_prueba / "licencia").read_text()
    prefijo, payload, firma = guardado.split(".")
    payload_falso = licensing._b64url(
        json.dumps({**json.loads(licensing._b64url_decode(payload)),
                    "plan": "enterprise"}).encode())
    (cliente_sin_prueba / "licencia").write_text(f"{prefijo}.{payload_falso}.{firma}")
    assert licensing.token_guardado() is None


def test_una_licencia_de_otro_par_de_claves_no_vale(cliente_sin_prueba, monkeypatch):
    """El caso de la clave rotada: el archivo sigue ahí y ya no sirve. Tiene
    que dar None, no un token que después falle en otro lado."""
    licensing.guardar_token(_licencia())
    assert licensing.token_guardado() is not None
    monkeypatch.setenv("MVPM_LICENSE_PUBLIC_KEY",
                       licensing._b64url(bytes(range(32))))
    assert licensing.token_guardado() is None


def test_olvidar_borra_de_verdad(cliente_sin_prueba):
    licensing.guardar_token(_licencia())
    assert licensing.olvidar_token() is True
    assert licensing.token_guardado() is None
    assert licensing.olvidar_token() is False  # ya no estaba


def test_un_disco_de_solo_lectura_no_tumba_el_programa(cliente_sin_prueba,
                                                       monkeypatch):
    """No poder guardar es una molestia (hay que repegar el token la próxima),
    no un motivo para que el programa no abra."""
    def negar(*a, **k):
        raise OSError("read-only file system")

    monkeypatch.setattr(licensing.Path, "write_text", negar)
    assert licensing.guardar_token(_licencia()) is False


# ------------------------------------------------------- lo que rompía: la API

def _api():
    from api import main
    return TestClient(main.app)


def test_sin_licencia_guardada_la_api_sigue_cobrando(cliente_sin_prueba):
    """El complemento imprescindible: si esto pasara igual, el test de abajo
    no probaría nada — la API estaría abierta para cualquiera."""
    r = _api().get("/api/proyectos")
    assert r.status_code == 402


def test_con_la_licencia_guardada_la_api_responde(cliente_sin_prueba):
    """EL test de esto. El cliente pagó, pegó su token en el dashboard, y
    Power BI —otro proceso, otra conexión— tiene que poder leer el portafolio."""
    licensing.guardar_token(_licencia())
    r = _api().get("/api/proyectos")
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), (list, dict))


def test_una_licencia_vencida_no_reabre_la_api(cliente_sin_prueba, monkeypatch):
    """Guardar el token no puede volverse una licencia perpetua: la vigencia
    la sigue decidiendo el `iat` firmado."""
    licensing.guardar_token(_licencia())
    vigencia = licensing.PLANES["professional"]["vigencia_dias"]
    despues = time.time() + (vigencia + 5) * DIA  # fuera del lambda: si no, se
    monkeypatch.setattr(licensing.time, "time", lambda: despues)  # llama a sí mismo
    assert _api().get("/api/proyectos").status_code == 402
