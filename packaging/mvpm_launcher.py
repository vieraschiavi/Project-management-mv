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

PUERTOS_PREFERIDOS = [8731, 8742, 8753, 8764]


def _puerto_libre() -> int:
    for puerto in PUERTOS_PREFERIDOS:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", puerto)) != 0:
                return puerto
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


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

    # Electron elige el puerto y lo pasa por env var, para poder apuntar su
    # ventana ahí sin tener que adivinarlo ni parsear stdout.
    puerto = int(os.environ.get("MVPM_PORT") or _puerto_libre())
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
