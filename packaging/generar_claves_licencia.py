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


def publica_de(privada_b64url: str) -> str:
    """La clave pública que corresponde a una privada dada."""
    faltan = "=" * (-len(privada_b64url) % 4)
    cruda = base64.urlsafe_b64decode(privada_b64url + faltan)
    if len(cruda) != 32:
        raise ValueError(f"la clave privada mide {len(cruda)} bytes, se esperaban 32")
    privada = Ed25519PrivateKey.from_private_bytes(cruda)
    return _b64url(privada.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ))


def verificar() -> int:
    """¿La clave privada de ESTA máquina sirve para emitir licencias que el
    programa acepte?

    Es la pregunta que decide si un cliente que paga puede usar el producto, y
    la única que no se puede responder desde el servidor: Vercel firma con la
    privada que tenga cargada y nunca la compara con la pública que viaja
    embebida en los instaladores ya repartidos.
    """
    sys.path.insert(0, str(RAIZ))
    from mvpm import licensing, owner

    embebida = licensing.CLAVE_PUBLICA_EMBEBIDA
    print()
    print(f"  Clave pública embebida en el programa:\n    {embebida}")

    privada = owner.clave_privada_local()
    if not privada:
        print()
        print("  NO se encontró ninguna clave privada en esta máquina.")
        print("    Se buscó en la variable MVPM_LICENSE_PRIVATE_KEY y en")
        print(f"    {owner.ruta_clave_local()}")
        print()
        print("  Si la tenés guardada en tu gestor de contraseñas, exportala:")
        print("    export MVPM_LICENSE_PRIVATE_KEY=<la-clave>   # PowerShell: $env:...")
        print("  y volvé a correr esto. Si la perdiste, hay que rotar el par:")
        print("    python packaging/generar_claves_licencia.py --escribir")
        print("  ...y reconstruir y repartir los instaladores, porque los que ya")
        print("  entregaste verifican contra la pública vieja.")
        return 1

    try:
        derivada = publica_de(privada)
    except ValueError as e:
        print(f"\n  La clave encontrada no sirve: {e}")
        return 1

    print(f"  Pública que corresponde a tu clave privada:\n    {derivada}")
    print()
    if derivada == embebida:
        print("  COINCIDEN. Esta clave privada emite licencias que el programa")
        print("  acepta. Cargala en Vercel tal cual:")
        print()
        print("    Nombre : MVPM_LICENSE_PRIVATE_KEY")
        print("    Scope  : Production")
        print(f"    Valor  : {privada}")
        print()
        print("  Después redeployá y comprobá:")
        print("    curl https://<tu-dominio>/api/estado-licencias")
        return 0

    print("  NO COINCIDEN. Esta privada es de otro par: las licencias que")
    print("  emita no las abre ninguna copia instalada del programa.")
    print()
    print("  Opciones:")
    print("   1. Buscar la privada correcta (gestor de contraseñas, otra máquina).")
    print("   2. Rotar el par y reconstruir los instaladores:")
    print("        python packaging/generar_claves_licencia.py --escribir")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--escribir", action="store_true",
        help="pega la clave pública en mvpm/licensing.py (si no, sólo la imprime)",
    )
    parser.add_argument(
        "--verificar", action="store_true",
        help="NO genera nada: dice si la clave privada de esta máquina "
             "corresponde a la pública embebida en el programa",
    )
    args = parser.parse_args()

    if args.verificar:
        return verificar()

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
