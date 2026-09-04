# © 2026 Martín Viera. Todos los derechos reservados.
"""Marca ESTE build como Owner Edition, poniendo `ES_OWNER_BUILD` en True.

Lo corre `.github/workflows/build_electron.yml` —sólo el job de la edición
del dueño— justo ANTES de compilar
`mvpm/` con Cython, para que la constante quede adentro del `.pyd` y no como un
`.py` legible al lado del ejecutable. Sólo toca el workspace efímero del runner:
lo versionado sigue en False, y hay un test que lo fija.

## Por qué esto reemplazó al marcador firmado

El build del dueño empaquetaba `packaging/OWNER_EDITION`: un archivo con una
licencia `enterprise` firmada. Se sacó porque ese archivo se podía copiar a
cualquier otra instalación, y porque además servía pegado en el campo de
licencia de la app. Una constante compilada no se puede copiar ni pegar: sólo
desbloquea el binario en el que se compiló.

Y a diferencia de la firma, esto NO necesita ningún secreto configurado: no hay
nada que firmar. El build del dueño dejó de depender de
`MVPM_LICENSE_PRIVATE_KEY`.

Uso:
    python packaging/marcar_build_owner.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVO = ROOT / "mvpm" / "edicion.py"

#: La línea tal cual está en el repositorio, y en la que tiene que quedar.
ORIGEN = "ES_OWNER_BUILD = False"
DESTINO = "ES_OWNER_BUILD = True"


def main() -> int:
    texto = ARCHIVO.read_text(encoding="utf-8")

    nuevo, reemplazos = re.subn(
        rf"^{re.escape(ORIGEN)}$", DESTINO, texto, count=1, flags=re.MULTILINE)
    if reemplazos != 1:
        # Sin esto el build seguiría, compilaría bien y saldría un .exe que dice
        # "Owner Edition" y se comporta como el de un cliente: prueba de 7 días
        # incluida. Es el modo de fallar que más caro sale, porque no se nota
        # hasta que el dueño instala y se encuentra con el candado.
        print(
            f"ERROR: no encontré exactamente `{ORIGEN}` en {ARCHIVO.relative_to(ROOT)}.\n"
            "Sin ese reemplazo el .exe saldría con el candado de cliente puesto,\n"
            "así que se corta acá en vez de entregar eso.",
            file=sys.stderr,
        )
        return 1

    ARCHIVO.write_text(nuevo, encoding="utf-8")

    # Se relee del disco: es la única forma de saber que lo que va a compilar
    # Cython dentro de un minuto dice lo que creemos que dice.
    if DESTINO not in ARCHIVO.read_text(encoding="utf-8"):
        print("ERROR: el archivo no quedó marcado después de escribirlo.", file=sys.stderr)
        return 1

    print(f"{ARCHIVO.relative_to(ROOT)}: {DESTINO} — este build es la Owner Edition.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
