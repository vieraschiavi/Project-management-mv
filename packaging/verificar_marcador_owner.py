"""¿El marcador versionado sirve para compilar la Owner Edition?

Sale 0 si `packaging/OWNER_EDITION` tiene un token que valida contra la clave
pública embebida, y 1 si no (placeholder, token roto, o firmado con un par de
claves distinto al que trae esta versión del programa).

Lo usa `.github/workflows/build_windows_owner.yml` para decidir si hace falta
firmar. Con el marcador ya versionado —que es el caso normal en este repo
privado— el build no necesita ningún secreto configurado; el paso de firma
queda sólo como salida para cuando se rotan las claves.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

MARCADOR = ROOT / "packaging" / "OWNER_EDITION"


def marcador_es_valido() -> bool:
    from mvpm import licensing, owner

    token = owner._token_del_marcador(MARCADOR)
    if not token:
        return False
    payload = licensing.verify_license(token)
    return bool(payload) and payload.get("plan") in licensing.PLANES_PAGOS


def main() -> int:
    if marcador_es_valido():
        print("packaging/OWNER_EDITION ya tiene una licencia válida: no hace "
              "falta firmar nada.")
        return 0
    print("packaging/OWNER_EDITION no sirve como está (placeholder, token roto "
          "o de otro par de claves): hay que firmarlo.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
