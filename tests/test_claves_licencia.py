# © 2026 Martín Viera. Todos los derechos reservados.
"""`packaging/generar_claves_licencia.py --verificar`: ¿la clave privada que
tengo emite licencias que el programa abre?

Es la única pregunta del sistema de licencias que no se puede responder desde
el servidor. `api/_license.js` deriva la pública de la privada que tenga
cargada, así que Vercel siempre es coherente CONSIGO MISMO: si la privada no
es la del par de producción, la emisión sale 200, el token está bien firmado,
y no lo verifica ninguna instalación — porque cada copia del programa trae
embebida la OTRA pública. Eso no lo agarra un deploy verde: lo agarra el
cliente que ya pagó.

Lo que se fija acá:

* que la derivación de Python dé lo MISMO que la de Node (si divergen, el
  chequeo diría "coinciden" sobre un par que en producción no coincide);
* que `verificar()` distinga los tres casos —sin clave, clave de otro par,
  clave correcta— y devuelva 0 sólo en el último;
* que no imprima la privada cuando NO coincide (ahí el valor no sirve para
  nada y filtrarlo a una consola compartida es gratis para el atacante).
"""

import base64
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "packaging"))

from generar_claves_licencia import generar, publica_de  # noqa: E402
import generar_claves_licencia as claves  # noqa: E402


def test_publica_de_es_la_inversa_de_generar():
    """Ida y vuelta: la pública derivada de la privada es la que generó el par."""
    for _ in range(5):
        privada, publica = generar()
        assert publica_de(privada) == publica


def test_publica_de_rechaza_una_clave_del_largo_equivocado():
    """Una privada de 31 bytes no puede pasar por buena: Ed25519 los pide 32."""
    corta = base64.urlsafe_b64encode(b"\x01" * 31).rstrip(b"=").decode()
    with pytest.raises(ValueError, match="32"):
        publica_de(corta)


@pytest.mark.skipif(shutil.which("node") is None, reason="node no está instalado")
def test_python_y_node_derivan_la_misma_publica(tmp_path):
    """El acuerdo entre las dos mitades del sistema.

    Python deriva la pública con `cryptography` (bytes crudos) y Node con
    `crypto` (envoltorio DER a mano, `302e0201...` + semilla). Son dos
    implementaciones distintas del mismo cálculo; si una se corriera un byte,
    `--verificar` daría "COINCIDEN" sobre un par que en Vercel no coincide, que
    es justo el fallo que este comando existe para evitar.
    """
    privada, publica = generar()
    script = tmp_path / "derivar.js"
    script.write_text(
        "const crypto = require('crypto');\n"
        "const DER = Buffer.from('302e020100300506032b657004220420', 'hex');\n"
        "function dec(s){s=s.replace(/-/g,'+').replace(/_/g,'/');"
        "while(s.length%4)s+='=';return Buffer.from(s,'base64');}\n"
        f"const semilla = dec({json.dumps(privada)});\n"
        "const k = crypto.createPrivateKey({key: Buffer.concat([DER, semilla]),"
        " format:'der', type:'pkcs8'});\n"
        "const spki = crypto.createPublicKey(k).export({format:'der', type:'spki'});\n"
        "process.stdout.write(spki.subarray(spki.length-32).toString('base64')"
        ".replace(/\\+/g,'-').replace(/\\//g,'_').replace(/=+$/,''));\n",
        encoding="utf-8",
    )
    salida = subprocess.run(
        ["node", str(script)], capture_output=True, text=True, check=True).stdout
    assert salida == publica == publica_de(privada)


@pytest.fixture
def entorno(monkeypatch, capsys):
    """Corre `verificar()` con una pública embebida y una privada a elección,
    sin tocar ni el archivo real de licensing.py ni la clave de la máquina."""
    from mvpm import licensing, owner

    def correr(*, embebida, privada):
        monkeypatch.setattr(licensing, "CLAVE_PUBLICA_EMBEBIDA", embebida)
        monkeypatch.setattr(owner, "clave_privada_local", lambda: privada)
        codigo = claves.verificar()
        return codigo, capsys.readouterr().out

    return correr


def test_sin_clave_privada_avisa_y_falla(entorno):
    _, publica = generar()
    codigo, salida = entorno(embebida=publica, privada=None)
    assert codigo == 1
    assert "NO se encontró" in salida
    assert "MVPM_LICENSE_PRIVATE_KEY" in salida


def test_una_clave_de_otro_par_no_pasa(entorno):
    """El caso que motiva todo: una privada perfectamente válida, pero de otro
    par. Firma bien y el programa la rechaza."""
    privada_otra, _ = generar()
    _, publica_produccion = generar()
    codigo, salida = entorno(embebida=publica_produccion, privada=privada_otra)
    assert codigo == 1
    assert "NO COINCIDEN" in salida
    # Y no filtra la privada: acá no sirve para nada y la salida puede terminar
    # pegada en un chat o en un log de CI.
    assert privada_otra not in salida


def test_la_clave_correcta_pasa_y_dice_donde_cargarla(entorno):
    privada, publica = generar()
    codigo, salida = entorno(embebida=publica, privada=privada)
    assert codigo == 0
    assert "COINCIDEN" in salida and "NO COINCIDEN" not in salida
    # El valor exacto a pegar en Vercel, con nombre y scope: el paso siguiente
    # no debería requerir adivinar nada.
    assert privada in salida
    assert "MVPM_LICENSE_PRIVATE_KEY" in salida
    assert "Production" in salida


def test_una_privada_ilegible_no_revienta(entorno):
    """Si en la variable de entorno quedó pegada media clave, tiene que salir
    un mensaje, no un traceback."""
    codigo, salida = entorno(embebida=generar()[1], privada="no-es-una-clave")
    assert codigo == 1
    assert "no sirve" in salida


def test_verificar_no_genera_ni_escribe_nada(entorno, monkeypatch):
    """`--verificar` es de sólo lectura. Si algún día llamara a
    `escribir_clave_publica`, rotaría el par de producción sin querer y todos
    los instaladores repartidos dejarían de verificar."""
    def explotar(*a, **k):
        raise AssertionError("--verificar escribió en mvpm/licensing.py")

    monkeypatch.setattr(claves, "escribir_clave_publica", explotar)
    privada, publica = generar()
    antes = (RAIZ / "mvpm" / "licensing.py").read_bytes()
    entorno(embebida=publica, privada=privada)
    assert (RAIZ / "mvpm" / "licensing.py").read_bytes() == antes


def test_el_endpoint_de_estado_mira_la_misma_pareja():
    """`api/estado-licencias.js` responde la misma pregunta desde el servidor.
    Si uno de los dos comparara contra otra constante, dirían cosas distintas
    sobre el mismo despliegue."""
    estado = (RAIZ / "api" / "estado-licencias.js").read_text(encoding="utf-8")
    assert "CLAVE_PUBLICA_EMBEBIDA" in estado
    assert "require('./_license')" in estado

    from mvpm import licensing
    licencia_js = (RAIZ / "api" / "_license.js").read_text(encoding="utf-8")
    assert f"'{licensing.CLAVE_PUBLICA_EMBEBIDA}'" in licencia_js, (
        "la pública embebida en el programa (mvpm/licensing.py) y la de "
        "api/_license.js se separaron: el servidor emitiría licencias que "
        "el programa no abre")
