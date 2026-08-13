# © 2026 Martín Viera. Todos los derechos reservados.
"""Genera el par de claves Ed25519 con el que se firman las licencias.

Se corre UNA sola vez, en la máquina del dueño del producto:

    python packaging/generar_claves_licencia.py --escribir

Qué hace con cada mitad del par:

* **Clave privada** — la que EMITE licencias. Se imprime en pantalla y no se
  guarda en ningún archivo del repo a propósito. Va en dos lugares, los dos
  como secreto, nunca en el código:
  1. Vercel → tu proyecto → Settings → Environment Variables →
     `MVPM_LICENSE_PRIVATE_KEY` (la usa `api/verify-payment.js` para emitir
     el token cuando MercadoPago confirma un pago).
  2. Tu propia máquina, como variable de entorno, si querés emitir licencias
     a mano desde el panel del dueño (`owner/panel.py`) o activar tu modo
     owner con `./run.sh owner`.
* **Clave pública** — la que VERIFICA licencias. Viaja en cada copia del
  programa (con `--escribir` se pega sola en `mvpm/licensing.py`). No es un
  secreto: sirve para comprobar una firma y no para producirla, que es
  justamente por qué el esquema es asimétrico.

Si perdés la clave privada, las licencias ya emitidas siguen funcionando pero
no podés emitir nuevas: hay que generar un par nuevo, publicar una versión con
la pública nueva y reemitir. Guardala en tu gestor de contraseñas.
"""

import argparse
import base64
import re
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO_LICENSING = RAIZ / "mvpm" / "licensing.py"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def generar() -> tuple[str, str]:
    """Devuelve (privada_b64url, publica_b64url) de un par Ed25519 nuevo."""
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
    return _b64url(cruda_privada), _b64url(cruda_publica)


def escribir_clave_publica(publica: str) -> None:
    """Pega la clave pública en CLAVE_PUBLICA_EMBEBIDA de mvpm/licensing.py."""
    texto = ARCHIVO_LICENSING.read_text(encoding="utf-8")
    nuevo, reemplazos = re.subn(
        r'^CLAVE_PUBLICA_EMBEBIDA = ".*"$',
        f'CLAVE_PUBLICA_EMBEBIDA = "{publica}"',
        texto,
        count=1,
        flags=re.MULTILINE,
    )
    if reemplazos != 1:
        raise SystemExit(
            f"No encontré la línea CLAVE_PUBLICA_EMBEBIDA en {ARCHIVO_LICENSING}. "
            "Pegala a mano."
        )
    ARCHIVO_LICENSING.write_text(nuevo, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--escribir", action="store_true",
        help="pega la clave pública en mvpm/licensing.py (si no, sólo la imprime)",
    )
    args = parser.parse_args()

    privada, publica = generar()
    if args.escribir:
        escribir_clave_publica(publica)

    print()
    print("=" * 72)
    print("  CLAVE PRIVADA — SECRETA. No la commitees ni la pegues en un chat.")
    print("=" * 72)
    print(f"MVPM_LICENSE_PRIVATE_KEY={privada}")
    print()
    print("  Cargala en Vercel (Settings -> Environment Variables) para que el")
    print("  checkout pueda emitir licencias, y en tu máquina si vas a emitirlas")
    print("  a mano desde owner/panel.py.")
    print()
    print("=" * 72)
    print("  CLAVE PÚBLICA — viaja en el programa. No es secreta.")
    print("=" * 72)
    print(f"MVPM_LICENSE_PUBLIC_KEY={publica}")
    print()
    if args.escribir:
        print(f"  Ya quedó escrita en {ARCHIVO_LICENSING.relative_to(RAIZ)}.")
        print("  Commiteá ese cambio y publicá una versión nueva.")
    else:
        print("  Volvé a correr con --escribir para pegarla sola en")
        print(f"  {ARCHIVO_LICENSING.relative_to(RAIZ)}, o copiala a mano en")
        print("  CLAVE_PUBLICA_EMBEBIDA.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
