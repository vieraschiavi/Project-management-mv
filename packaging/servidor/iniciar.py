#!/usr/bin/env python3
# © 2026 Martín Viera. Todos los derechos reservados.
"""Arranca MV Project Management sin instalar nada. Sin .exe y sin .bat.

## Para qué existe

Una laptop corporativa que bloquea instaladores. El caso concreto: una
consultora entra a un proyecto de un cliente, la política de la laptop no deja
correr `.exe` ni `.bat`, y —lo más importante— el dato del cliente no puede
quedar en el disco de la consultora.

Este archivo es la única puerta de entrada del paquete servidor:

    python3 iniciar.py            # modo servidor: entra el equipo por la red
    python3 iniciar.py --local    # sólo esta máquina, nadie más

No instala nada en el sistema, no pide permisos de administrador y no toca el
registro de Windows. Si faltan dependencias arma un entorno virtual DENTRO de
esta misma carpeta y se relanza solo; borrar la carpeta lo deshace todo.

## Dónde queda el dato, que es el punto

En `datos/`, al lado de este archivo, salvo que se indique otra cosa con
`--datos` o `MVPM_DATA_DIR`. Es una ruta que se puede mirar, auditar y borrar:
ante un área de seguridad, "el dato está en este directorio de este servidor"
se demuestra abriendo la carpeta, y "no está en mi laptop" se demuestra porque
la laptop sólo abrió un navegador.

Por eso el default es una carpeta local del paquete y no el perfil del usuario:
el perfil del usuario en una VM compartida es de quien haya iniciado sesión, y
el argumento deja de ser verificable de un vistazo.

## Lo que este archivo NO puede resolver

Si la laptop no deja ejecutar Python y además no hay servidor ni VM del
cliente, no hay paquete que alcance: el programa tiene que correr en algún
lado. Eso se resuelve con una máquina del cliente (o VDI/Citrix), no con otro
formato de instalador. Está escrito en LEEME.md.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent

#: Las dos direcciones y qué significa cada una. `0.0.0.0` es el punto del modo
#: servidor —que la red llegue— y por eso se elige a propósito, nunca por
#: omisión: ese fue el agujero que tenía la instalación "normal".
HOST_SERVIDOR = "0.0.0.0"  # noqa: S104 — deliberado; ver el docstring
HOST_LOCAL = "127.0.0.1"

PUERTO_POR_DEFECTO = 8501


def _python_del_entorno() -> Path | None:
    """El intérprete del venv de esta carpeta, si ya existe."""
    for rel in ("Scripts/python.exe", "bin/python3", "bin/python"):
        cand = AQUI / ".venv" / rel
        if cand.exists():
            return cand
    return None


def _tiene_dependencias(python: Path | None = None) -> bool:
    """¿Se puede importar streamlit con ESE intérprete?

    Se pregunta con un subproceso y no con un `import` propio porque el
    intérprete que importa es el que va a correr la app, que no siempre es
    éste: cuando hay venv, éste sólo relanza.
    """
    if python is None:
        try:
            import streamlit  # noqa: F401
        except ImportError:
            return False
        return True
    return subprocess.run([str(python), "-c", "import streamlit"],
                          capture_output=True).returncode == 0


def _preparar_entorno() -> Path:
    """Crea el venv local e instala requirements. Devuelve su intérprete."""
    venv = AQUI / ".venv"
    if _python_del_entorno() is None:
        print("Preparando el entorno por única vez (no se instala nada en el "
              "sistema; queda todo en .venv/ dentro de esta carpeta)...")
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    python = _python_del_entorno()
    if python is None:
        raise SystemExit(
            "No se pudo crear el entorno virtual. En Debian/Ubuntu suele "
            "faltar el paquete python3-venv.")
    if not _tiene_dependencias(python):
        print("Instalando dependencias en el entorno local...")
        # `--no-cache-dir` no es una optimización: sin él pip deja cientos de
        # megas de wheels en el perfil del usuario de la máquina del cliente,
        # o sea FUERA de esta carpeta. Rompe la promesa de "borrar la carpeta
        # lo deshace todo" y, en una máquina corporativa con cuota de disco en
        # el perfil, puede directamente fallar. Se paga con que reinstalar
        # vuelva a descargar, que pasa una vez.
        subprocess.run([str(python), "-m", "pip", "install", "--quiet",
                        "--no-cache-dir", "--upgrade", "pip"], check=True)
        subprocess.run([str(python), "-m", "pip", "install", "--quiet",
                        "--no-cache-dir",
                        "-r", str(AQUI / "requirements.txt")], check=True)
    return python


def _resolver_datos(elegido: str | None) -> Path:
    """Dónde se guarda. El orden lo fija quién es más explícito."""
    if elegido:
        destino = Path(elegido).expanduser().resolve()
    elif os.environ.get("MVPM_DATA_DIR"):
        destino = Path(os.environ["MVPM_DATA_DIR"]).expanduser().resolve()
    else:
        destino = AQUI / "datos"
    destino.mkdir(parents=True, exist_ok=True)
    return destino


def _avisar(modo: str, host: str, puerto: int, datos: Path) -> None:
    """Decir qué implica ANTES de abrir el puerto, no después."""
    print()
    print("=" * 66)
    print(f"  MV Project Management — modo {modo.upper()}")
    print("=" * 66)
    print(f"  Escucha en   : {host}:{puerto}")
    if host == HOST_SERVIDOR:
        print("                 (accesible desde la red: el login de la app")
        print("                  es la única puerta)")
    else:
        print("                 (sólo esta máquina; nadie más entra)")
    print(f"  Dato guardado: {datos}")
    print("                 Todo el dato del cliente vive ahí y sólo ahí.")
    print("  Además       : el programa deja en el perfil del usuario dos")
    print("                 archivos propios (fecha de primer uso y un hash")
    print("                 de la máquina). No contienen dato del cliente.")
    print("  Telemetría   : apagada.")
    print("=" * 66)
    print()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Arranca MV Project Management sin instalar nada.")
    p.add_argument("--local", action="store_true",
                   help="Escuchar sólo en 127.0.0.1 en vez de en la red.")
    p.add_argument("--puerto", type=int, default=None,
                   help=f"Puerto (default {PUERTO_POR_DEFECTO}, o $PORT).")
    p.add_argument("--datos", default=None,
                   help="Carpeta donde guardar. Default: ./datos")
    args = p.parse_args(argv)

    modo = "local" if args.local else "servidor"
    host = HOST_LOCAL if args.local else HOST_SERVIDOR
    puerto = args.puerto or int(os.environ.get("PORT", PUERTO_POR_DEFECTO))
    datos = _resolver_datos(args.datos)

    entorno = dict(os.environ)
    entorno["MVPM_DATA_DIR"] = str(datos)
    entorno["MVPM_MODO_INSTALACION"] = modo

    python = sys.executable if _tiene_dependencias() else str(_preparar_entorno())

    _avisar(modo, host, puerto, datos)
    return subprocess.run(
        [str(python), "-m", "streamlit", "run", str(AQUI / "app" / "app.py"),
         "--server.port", str(puerto), "--server.address", host,
         "--server.headless", "true",
         # Streamlit manda estadísticas de uso a su servidor por DEFECTO. En
         # una instalación dentro del cliente eso es una conexión saliente que
         # nadie pidió y que rompe la frase "no sale nada de acá" — la que
         # justamente sostiene todo el argumento ante seguridad. Se apaga.
         "--browser.gatherUsageStats", "false"],
        env=entorno, cwd=str(AQUI)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
