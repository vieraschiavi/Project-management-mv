"""Punto de entrada del programa empaquetado (instalador .exe o portable).

Mismo patrón que `kobra_launcher.py` de MV Kobra AI: busca un puerto libre,
arranca Streamlit embebido, y recién abre el navegador cuando el server ya
respondió — para no mostrarle al usuario una pestaña en blanco mientras
carga.

Cuando corre embebido dentro del wrapper de Electron (`desktop/`), la
variable de entorno MVPM_ELECTRON=1 evita abrir además una pestaña del
navegador del sistema — Electron ya muestra su propia ventana nativa
apuntando al mismo puerto.
"""

import os
import sys
import threading
from pathlib import Path

# La elección del puerto vive en mvpm/puertos.py, que consultan las cuatro
# formas de abrir el programa. Acá había una copia propia que buscaba con
# connect_ex(): eso da falsos negativos —un puerto reservado por otra app que
# todavía no acepta conexiones parecía libre— y Streamlit moría después con
# "Address already in use". Se importa adentro de main() porque recién ahí
# está sys.path armado para el .exe congelado.


def _esperar_y_abrir(url: str) -> None:
    """Abre el programa cuando Streamlit ya esté escuchando.

    La espera y la ventana viven en mvpm/ventana.py, que es lo que usan también
    el `.bat` portable y `run.sh`: una sola definición de "cómo se ve abrir el
    programa" para todas las formas de arrancarlo.
    """
    from mvpm import ventana

    ventana.esperar_y_abrir(url)


def main() -> None:
    if getattr(sys, "frozen", False):
        base_dir = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base_dir = Path(__file__).resolve().parent.parent

    sys.path.insert(0, str(base_dir))

    # Si el dueño activó ESTA instalación, el marcador puede haber quedado junto
    # al programa. Cuando el programa corre congelado, sys._MEIPASS no es la raíz
    # que ve mvpm/owner.py, así que se le pasa la RUTA del archivo por env var —
    # no un "está activado: sí".
    #
    # La decisión en sí vive en mvpm/owner.py, que verifica la firma del token y
    # que esté emitido para esta máquina: acá no se duplica la regla ni se puede
    # saltear. Apuntar esto a un archivo cualquiera no desbloquea nada, y un
    # marcador traído de otra computadora tampoco.
    #
    # Ningún build empaqueta ya un marcador: el .exe de la Owner Edition lo hacía
    # y era una licencia enterprise regalada a quien bajara el instalador de un
    # repo público (ver packaging/mvpm_owner.spec). Antes de eso, esto seteaba
    # MVPM_OWNER_BYPASS=1, que desbloqueaba el producto por el solo hecho de
    # existir la variable. Van dos.
    marcador_owner = base_dir / "OWNER_EDITION"
    if marcador_owner.exists():
        os.environ.setdefault("MVPM_OWNER_MARCADOR", str(marcador_owner))

    from mvpm import puertos

    # Electron elige el puerto y lo pasa por env var, para poder apuntar su
    # ventana ahí sin tener que adivinarlo ni parsear stdout. `desde_entorno`
    # lo respeta si sigue libre y, si no, elige otro en vez de morir.
    puerto = puertos.desde_entorno(os.environ.get("MVPM_PORT"))
    url = f"http://127.0.0.1:{puerto}"

    if not os.environ.get("MVPM_ELECTRON"):
        threading.Thread(target=_esperar_y_abrir, args=(url,), daemon=True).start()
    print(f"MVPM_READY_PORT:{puerto}", flush=True)

    from streamlit.web import cli as stcli

    sys.argv = [
        "streamlit", "run", str(base_dir / "app" / "app.py"),
        "--server.port", str(puerto),
        # Sin esto el .exe no abre: muere en el arranque con
        #   RuntimeError: server.port does not work when global.developmentMode is true.
        #
        # Streamlit decide si está "en modo desarrollo" mirando su PROPIA ruta
        # (config.py, _global_development_mode): da True cuando "site-packages"
        # no aparece en `__file__`. Adentro de un .exe de PyInstaller el módulo
        # vive en _MEIxxxxx\streamlit\config.py, sin site-packages a la vista,
        # así que el empaquetado arranca creyéndose un checkout de desarrollo.
        # Y en modo desarrollo _check_conflicts prohíbe fijar server.port —que
        # es justo lo que necesitamos, porque el puerto lo elige mvpm/puertos.py
        # y Electron tiene que saber a dónde apuntar la ventana.
        #
        # Corriendo desde el repo no pasa nunca: ahí Streamlit SÍ está en
        # site-packages. Por eso la suite entera y `./run.sh app` pasan en
        # verde mientras el instalador no abre — el bug sólo existe congelado.
        "--global.developmentMode", "false",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--theme.base", "dark",
        "--theme.primaryColor", "#f2b441",
        "--theme.backgroundColor", "#081527",
        "--theme.secondaryBackgroundColor", "#0c2137",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
