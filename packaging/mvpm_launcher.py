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
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

# La elección del puerto vive en mvpm/puertos.py, que consultan las cuatro
# formas de abrir el programa. Acá había una copia propia que buscaba con
# connect_ex(): eso da falsos negativos —un puerto reservado por otra app que
# todavía no acepta conexiones parecía libre— y Streamlit moría después con
# "Address already in use". Se importa adentro de main() porque recién ahí
# está sys.path armado para el .exe congelado.


def _esperar_y_abrir(url: str, timeout_s: int = 25) -> None:
    inicio = time.time()
    while time.time() - inicio < timeout_s:
        try:
            with socket.create_connection(("127.0.0.1", int(url.rsplit(":", 1)[1])), timeout=0.5):
                webbrowser.open(url)
                return
        except OSError:
            time.sleep(0.3)


def main() -> None:
    if getattr(sys, "frozen", False):
        base_dir = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base_dir = Path(__file__).resolve().parent.parent

    sys.path.insert(0, str(base_dir))

    # El build "Owner Edition" (packaging/mvpm_owner.spec, nunca el que baja un
    # cliente) empaqueta este marcador junto al .exe. Cuando el programa corre
    # congelado, sys._MEIPASS no es la raíz que ve mvpm/owner.py, así que la
    # env var es la forma de pasarle el dato — owner.es_owner() la reconoce.
    # La decisión en sí vive en mvpm/owner.py: acá no se duplica la regla, sólo
    # se cubre el caso del .exe. El candado de 7 días queda intacto para
    # cualquier build sin el marcador (todo lo que se distribuye a clientes).
    if (base_dir / "OWNER_EDITION").exists():
        os.environ.setdefault("MVPM_OWNER_BYPASS", "1")

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
