"""Firma el marcador de la Owner Edition antes de compilar el `.exe`.

Lo corre el CI (`.github/workflows/build_windows_owner.yml`) justo antes de
PyInstaller. Escribe `packaging/OWNER_EDITION` con un token firmado por la
clave privada del dueño, que `packaging/mvpm_owner.spec` empaqueta dentro del
ejecutable y `mvpm/owner.py` verifica al arrancar.

Por qué acá y no un archivo committeado: el marcador contiene una licencia
firmada. Committearlo lo dejaría en el historial de git para siempre, así que
se genera en el momento del build a partir del secreto de GitHub y no toca el
repo. El `packaging/OWNER_EDITION` que sí está versionado es un placeholder sin
firma válida: si alguien compila sin el secreto, el `.exe` que sale NO es una
Owner Edition, que es el modo seguro de fallar.

Uso:
    MVPM_LICENSE_PRIVATE_KEY=<clave> python packaging/firmar_marcador_owner.py
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DESTINO = ROOT / "packaging" / "OWNER_EDITION"


def main() -> int:
    if not os.environ.get("MVPM_LICENSE_PRIVATE_KEY", "").strip():
        print(
            "ERROR: falta MVPM_LICENSE_PRIVATE_KEY.\n"
            "\n"
            "El marcador de la Owner Edition es un token FIRMADO: sin la clave\n"
            "privada del dueño no se puede generar uno que el programa acepte.\n"
            "Compilar igual produciría un .exe que dice 'Owner Edition' pero se\n"
            "comporta como el de un cliente (prueba de 7 días), así que se corta\n"
            "acá en vez de entregar eso.\n"
            "\n"
            "En CI: cargá el secreto MVPM_LICENSE_PRIVATE_KEY en\n"
            "Settings -> Secrets and variables -> Actions.\n"
            "Si todavía no generaste el par de claves:\n"
            "    python packaging/generar_claves_licencia.py --escribir",
            file=sys.stderr,
        )
        return 1

    from mvpm import licensing, owner

    token = licensing.issue_license("enterprise", owner.EMAIL_OWNER)
    DESTINO.write_text(owner._TEXTO_MARCADOR.format(token=token), encoding="utf-8")

    # Se verifica lo que se acaba de escribir: si el token no valida contra la
    # clave pública embebida, el .exe tampoco lo va a aceptar, y es mucho mejor
    # enterarse acá que después de instalar.
    if licensing.verify_license(token) is None:
        print(
            "ERROR: el token que se acaba de firmar NO valida contra la clave\n"
            "pública embebida en mvpm/licensing.py (CLAVE_PUBLICA_EMBEBIDA).\n"
            "Son de pares distintos: revisá que el secreto del CI y la pública\n"
            "committeada salgan de la misma corrida de\n"
            "packaging/generar_claves_licencia.py.",
            file=sys.stderr,
        )
        return 1

    print(f"Marcador de Owner Edition firmado en {DESTINO.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
