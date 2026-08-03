"""Configuración común de la suite.

Las licencias se firman con Ed25519 (`mvpm/licensing.py`): hay una clave
PRIVADA que sólo tiene el servidor de pagos y una PÚBLICA que viaja en el
programa. En producción la pública va embebida en el código y la privada vive
como variable de entorno en Vercel.

Acá se genera un par EFÍMERO por corrida y se exporta por variables de entorno,
para que la suite no dependa de las claves reales del producto (que no están en
el repo, y no deben estarlo) ni las necesite para correr en una máquina limpia.

Un test que quiera simular la máquina de un CLIENTE —que verifica licencias
pero no puede emitirlas— sólo tiene que borrar la privada:

    monkeypatch.delenv("MVPM_LICENSE_PRIVATE_KEY")
"""

import base64
import sys
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


@pytest.fixture(autouse=True, scope="session")
def _claves_de_licencia_efimeras():
    """Par Ed25519 nuevo por corrida, en las variables de entorno que lee
    mvpm/licensing.py. Session-scoped: emitir un token con una clave y
    verificarlo con otra daría falsos negativos entre tests."""
    privada = Ed25519PrivateKey.generate()
    cruda_privada = privada.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    cruda_publica = privada.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    # monkeypatch no sirve acá: su fixture es de function scope.
    parche = pytest.MonkeyPatch()
    parche.setenv("MVPM_LICENSE_PRIVATE_KEY", _b64url(cruda_privada))
    parche.setenv("MVPM_LICENSE_PUBLIC_KEY", _b64url(cruda_publica))
    yield
    parche.undo()
