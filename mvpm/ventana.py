"""Abre el dashboard como una ventana de programa, no como una pestaña.

El problema que resuelve: el `.exe` instalado hacía `webbrowser.open(url)`. Eso
abre una pestaña más en el navegador que el usuario ya tenía abierto, con barra
de direcciones, pestañas, favoritos y la sesión de todo lo demás. El resultado
es que un programa que la persona instaló, con su icono en el escritorio y en el
menú de inicio, se ve como "una página web de Streamlit" en vez de como Excel o
cualquier otro programa de escritorio: no tiene su propia entrada en la barra de
tareas, se pierde entre veinte pestañas, y si el usuario cierra el navegador se
lleva la aplicación puesta.

## Cómo se abre entonces

Los navegadores basados en Chromium tienen **modo aplicación** (`--app=URL`):
una ventana sola, sin barra de direcciones ni pestañas, con su propio icono en
la barra de tareas y su propio Alt+Tab. Es lo que usan las PWA instaladas. Para
el usuario es indistinguible de un programa nativo, y no cuesta ni una
dependencia nueva ni los ~150 MB que agregaría empaquetar Electron.

En Windows siempre hay uno: Edge viene con el sistema desde Windows 10. Se
prueba Edge primero y Chrome después; en Linux y macOS, los nombres habituales.

## Por qué un perfil propio

`--user-data-dir` apunta a una carpeta nuestra dentro de los datos del
programa. Sin eso, Chromium reutiliza el proceso del navegador que el usuario ya
tiene abierto y la "ventana de aplicación" termina siendo otra ventana de esa
misma sesión: hereda extensiones, comparte cookies con todo lo que la persona
tenga abierto y vuelve a colgarse de su icono en la barra de tareas. Con perfil
propio es un proceso aparte, con su icono aparte, y la sesión del dashboard no
se mezcla con la navegación personal de nadie.

## Si no hay ningún Chromium

Se cae a `webbrowser.open()`, que es lo que había antes: una pestaña común. Es
peor estéticamente pero funciona, y es preferible a no abrir nada.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

#: Ejecutables de Chromium que soportan `--app=`, en orden de preferencia.
#: En Windows Edge está garantizado desde Windows 10, así que va primero.
_CANDIDATOS_WINDOWS = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
)

#: En Linux/macOS se buscan por nombre en el PATH.
_CANDIDATOS_PATH = (
    "microsoft-edge", "microsoft-edge-stable",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
    "brave-browser",
)

_CANDIDATO_MACOS = (
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)

TAMANO_VENTANA = (1360, 900)


def _perfil() -> Path:
    """Carpeta de perfil propia para la ventana. Ver el docstring del módulo:
    sin esto la ventana se cuelga de la sesión de navegador del usuario."""
    from mvpm import rutas

    ruta = rutas.directorio_datos() / "ventana"
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def buscar_navegador() -> str | None:
    """El primer Chromium disponible que sepa abrir en modo aplicación."""
    if sys.platform == "win32":
        candidatos = _CANDIDATOS_WINDOWS
    elif sys.platform == "darwin":
        candidatos = _CANDIDATO_MACOS
    else:
        candidatos = ()

    for ruta in candidatos:
        if Path(ruta).exists():
            return ruta

    for nombre in _CANDIDATOS_PATH:
        encontrado = shutil.which(nombre)
        if encontrado:
            return encontrado
    return None


def comando(url: str, navegador: str) -> list[str]:
    """El comando exacto que abre `url` como ventana de aplicación.

    Está separado de `abrir()` para poder verificarlo en un test sin lanzar un
    navegador de verdad.
    """
    ancho, alto = TAMANO_VENTANA
    return [
        navegador,
        f"--app={url}",
        f"--user-data-dir={_perfil()}",
        f"--window-size={ancho},{alto}",
        # Sin esto Chromium ofrece traducir la página, guardar contraseñas y
        # mostrar el globo de "restaurar pestañas" tras un cierre forzado —
        # tres cosas que delatan que abajo hay un navegador.
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=Translate,TranslateUI",
    ]


def abrir(url: str) -> bool:
    """Abre el dashboard en una ventana propia. True si lo logró como ventana
    de aplicación, False si tuvo que caer a la pestaña común del navegador."""
    navegador = buscar_navegador()
    if navegador:
        try:
            subprocess.Popen(
                comando(url, navegador),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                # Que el navegador no muera cuando termine el proceso que lo
                # lanzó, ni herede la consola del launcher.
                start_new_session=(sys.platform != "win32"),
            )
            return True
        except OSError:
            # Ejecutable presente pero no lanzable (permisos, ruta rota): se
            # sigue al fallback en vez de dejar al usuario sin ventana.
            pass

    webbrowser.open(url)
    return False


def esta_deshabilitada() -> bool:
    """Permite volver a la pestaña común con MVPM_SIN_VENTANA=1. Es la salida
    de emergencia si el modo aplicación diera problemas en alguna máquina."""
    return os.environ.get("MVPM_SIN_VENTANA", "").strip() not in ("", "0")


def esperar_y_abrir(url: str, timeout_s: float = 25.0) -> bool:
    """Espera a que el servidor acepte conexiones y recién ahí abre la ventana.

    Sin la espera, la ventana arranca contra un puerto que todavía no escucha y
    el usuario ve el error de "no se puede acceder a este sitio" del navegador
    en lugar del programa — que es exactamente lo que no queremos que vea.
    """
    import socket
    import time

    puerto = int(url.rsplit(":", 1)[1])
    limite = time.monotonic() + timeout_s
    while time.monotonic() < limite:
        try:
            with socket.create_connection(("127.0.0.1", puerto), timeout=0.5):
                break
        except OSError:
            time.sleep(0.3)

    if esta_deshabilitada():
        webbrowser.open(url)
        return False
    return abrir(url)


if __name__ == "__main__":
    # Lo usa MV_ProjectManagement.bat, que arranca esto en segundo plano
    # mientras Streamlit levanta en primer plano:
    #     python -m mvpm.ventana http://localhost:8731
    esperar_y_abrir(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8731")
