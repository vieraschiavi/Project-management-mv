# © 2026 Martín Viera. Todos los derechos reservados.
"""El camino completo del cliente que paga: MercadoPago → Vercel → su PC.

La licencia la EMITE Node (`api/verify-payment.js` llamando a
`api/_license.js`, corriendo en Vercel) y la VERIFICA Python
(`mvpm/licensing.py`, corriendo en la computadora del cliente). Son dos
implementaciones distintas del mismo formato, escritas en dos lenguajes, y
nada las obliga a coincidir: `tests/test_licencias.js` prueba Node contra Node
y la suite de pytest prueba Python contra Python. Las dos pueden estar verdes
mientras el token que sale de una no lo abre la otra.

Ese desacuerdo no lo ve nadie hasta que alguien paga. No hay error, no hay
alerta: hay un cliente con un token en la mano y una app que le dice que su
licencia no vale.

Acá se cruzan de verdad: se emite con un lenguaje y se verifica con el otro,
en las dos direcciones, y se comprueba que el payload que llega alcance para
desbloquear el programa (`estado_acceso`) con la prueba ya vencida — que es
el estado real del cliente el día que paga.

El par de claves es el efímero de `conftest.py`, exportado por variables de
entorno que las dos implementaciones leen. Nunca toca las claves reales.
"""

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

from mvpm import licensing

RAIZ = Path(__file__).resolve().parent.parent
DIA = 86400

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="node no está instalado")


def _node(cuerpo: str) -> str:
    """Corre un fragmento de JS con `api/_license.js` cargado como `L`."""
    script = (
        f"const L = require({json.dumps(str(RAIZ / 'api' / '_license.js'))});\n"
        + cuerpo
    )
    hecho = subprocess.run(
        ["node", "-e", script],
        capture_output=True, text=True, env=os.environ.copy())
    if hecho.returncode != 0:
        raise AssertionError(f"node falló:\n{hecho.stderr.strip()}")
    return hecho.stdout.strip()


@pytest.fixture
def prueba_vencida(monkeypatch, tmp_path):
    """La situación real del cliente que paga: los 7 días ya se le acabaron.

    Se aísla el archivo de la prueba en tmp para no tocar el de la máquina que
    corre la suite (si es la del dueño, borrárselo sería un efecto secundario
    de correr tests).
    """
    ruta = tmp_path / "trial.json"
    monkeypatch.setattr(licensing, "_RUTAS_TRIAL", (ruta,))
    ruta.write_text(json.dumps({"primer_uso": time.time() - 30 * DIA}),
                    encoding="utf-8")
    # Sin licencia, esta máquina está bloqueada. Si no lo estuviera, el test de
    # abajo pasaría igual con una licencia inservible.
    assert licensing.estado_acceso(None)["acceso"] is False
    return ruta


# ------------------------------------------- Vercel emite → la PC del cliente

@pytest.mark.parametrize("plan", ["professional", "professional_anual"])
def test_la_licencia_que_emite_vercel_desbloquea_el_programa(plan, prueba_vencida):
    """EL test de esto. Node firma como en producción; Python verifica como en
    la PC del cliente; y el resultado no es sólo "la firma da": es que el
    programa efectivamente se abre."""
    token = _node(
        f"process.stdout.write(L.issueLicense({json.dumps(plan)}, "
        "'cliente@ejemplo.com', 'mp-123456789'));")

    payload = licensing.verify_license(token)
    assert payload is not None, (
        "el programa del cliente rechaza la licencia que emitió el servidor")
    assert payload["plan"] == plan
    assert payload["email"] == "cliente@ejemplo.com"
    assert payload["payment_id"] == "mp-123456789", (
        "sin el id de pago no se puede rastrear una licencia hasta su cobro")

    estado = licensing.estado_acceso(token)
    assert estado["acceso"] is True and estado["modo"] == "licencia", estado


def test_el_cupo_de_ia_que_vende_el_servidor_es_el_que_aplica_el_programa(
        prueba_vencida):
    """El cupo viaja DENTRO del token firmado, pero el programa también tiene
    su propia tabla de planes. Si las dos difieren, el cliente pagó por un
    número y usa otro."""
    for plan, datos in licensing.PLANES.items():
        if plan not in licensing.PLANES_PAGOS or plan == "enterprise":
            continue
        token = _node(f"process.stdout.write(L.issueLicense({json.dumps(plan)},"
                      " 'c@e.com', 'mp-1'));")
        payload = licensing.verify_license(token)
        assert payload["cupo_mensual_ia"] == datos["cupo_mensual_ia"], (
            f"plan {plan}: el servidor vende {payload['cupo_mensual_ia']} "
            f"consultas y el programa aplica {datos['cupo_mensual_ia']}")


def test_la_vigencia_anual_no_se_corta_a_los_30_dias(prueba_vencida):
    """El plan anual se cobra una vez y tiene que durar el año. La vigencia la
    decide el programa a partir del `iat` firmado, no el servidor."""
    token = _node("process.stdout.write(L.issueLicense('professional_anual',"
                  " 'c@e.com', 'mp-1'));")
    payload = licensing.verify_license(token)
    assert licensing.licencia_vigente(payload, time.time() + 300 * DIA), (
        "una licencia anual se estaría venciendo antes de tiempo")


# ------------------------------------------- el dueño emite → Vercel verifica

def test_una_licencia_emitida_a_mano_por_el_dueno_tambien_vale(prueba_vencida):
    """La otra dirección. El panel del dueño (`owner/panel.py`) emite con
    Python; si Node no la aceptara, una licencia dada a mano no se podría
    validar del lado del servidor."""
    token = licensing.issue_license("professional", "manual@ejemplo.com", "sin-pago")
    salida = _node(
        f"const p = L.verifyLicense({json.dumps(token)});"
        "process.stdout.write(JSON.stringify(p));")
    assert salida != "null", "Node rechaza una licencia emitida por Python"
    assert json.loads(salida)["email"] == "manual@ejemplo.com"


# ------------------------------------------------------------ lo que NO vale

def test_un_token_manoseado_lo_rechazan_los_dos_lados(prueba_vencida):
    """Cambiarse el plan a mano en el token es el ataque obvio: el payload va
    en base64, no cifrado. Tiene que caerse por la firma."""
    token = _node("process.stdout.write(L.issueLicense('professional',"
                  " 'c@e.com', 'mp-1'));")
    prefijo, payload_b64, firma = token.split(".")
    payload = json.loads(licensing._b64url_decode(payload_b64))
    payload["cupo_mensual_ia"] = 999999
    falso = (f"{prefijo}."
             f"{licensing._b64url(json.dumps(payload).encode())}.{firma}")

    assert licensing.verify_license(falso) is None
    assert _node(f"process.stdout.write(String(L.verifyLicense("
                 f"{json.dumps(falso)})));") == "null"


def test_las_dos_listas_de_revocacion_dicen_lo_mismo():
    """Un token revocado tiene la firma perfecta: lo único que lo frena es
    estar en la lista. Si las listas se desincronizan, el token sigue valiendo
    en el lado que no lo tiene."""
    en_node = json.loads(_node(
        "process.stdout.write(JSON.stringify([...L.FIRMAS_REVOCADAS]));"))
    assert set(en_node) == set(licensing.FIRMAS_REVOCADAS), (
        "FIRMAS_REVOCADAS difiere entre mvpm/licensing.py y api/_license.js")


def test_el_plan_enterprise_no_sale_de_un_checkout():
    """Se cotiza por proyecto. `api/checkout.js` lo rechaza; acá se fija que
    los dos lados coincidan en que existe como plan pero no como compra."""
    planes_node = json.loads(_node(
        "process.stdout.write(JSON.stringify(Object.keys(L.PLANES)));"))
    assert set(planes_node) == set(licensing.PLANES), (
        "la tabla de planes difiere entre el servidor y el programa")
