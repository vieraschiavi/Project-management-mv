r"""Dónde vive el estado del programa en el disco.

Todo dato que no es del negocio en sí —licencia, marcador de modo owner, base
SQLite, reseñas— se guarda fuera del código, en una carpeta propia. Antes esa
carpeta era siempre `~/.mv_project_management` (el perfil de Windows del
usuario), sin importar en qué disco se instaló el programa: alguien que elegía
instalar en `D:\` a propósito —para no llenar `C:\`, o porque ahí tiene más
espacio— igual terminaba con todos sus datos en el perfil de Windows del
usuario, en el disco C. La
instalación quedaba partida entre dos discos sin que nadie lo hubiera pedido
así.

Ahora, cuando el programa corre como el `.exe` instalado (no en modo
desarrollo ni portable), los datos van junto al propio ejecutable: mismo disco
que el usuario eligió en el instalador, sin depender del registro de Windows
ni de una variable de entorno que necesitaría reiniciar sesión para verse.

Si esa carpeta no se puede escribir —caso real: instalación "para todos los
usuarios" en Archivos de Programa, que alguien sin privilegios de
administrador no puede modificar en el uso diario, aunque haya podido
instalarlo con un `runas` puntual— se cae al perfil del usuario, que siempre
es escribible. Mejor ahí que no arrancar.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

NOMBRE_CARPETA = ".mv_project_management"


def _en_el_perfil_del_usuario() -> Path:
    return Path.home() / NOMBRE_CARPETA


def _junto_al_ejecutable() -> Path | None:
    """Sólo aplica cuando el programa corre congelado (PyInstaller): en
    desarrollo `sys.executable` es el intérprete de Python, no el programa, y
    en general ni siquiera sería escribible."""
    if not getattr(sys, "frozen", False):
        return None
    return Path(sys.executable).resolve().parent / "data"


def _se_puede_escribir(carpeta: Path) -> bool:
    try:
        existia = carpeta.exists()
    except OSError:
        # Ni siquiera se pudo preguntar si existe — típico de una carpeta
        # padre sin permiso de lectura/ejecución (Path.exists() no traga un
        # PermissionError, sólo los errores de "no existe"). Si no se puede
        # ni mirar, seguro no se puede escribir.
        return False
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
        prueba = carpeta / ".prueba_escritura"
        prueba.write_text("x", encoding="utf-8")
        prueba.unlink()
        ok = True
    except OSError:
        ok = False
    if not existia:
        # Se creó sólo para la prueba: si el .exe recién se instaló, no
        # queremos dejar una carpeta "data" vacía junto a él antes de que el
        # programa tenga algo real que guardar ahí.
        try:
            carpeta.rmdir()
        except OSError:
            pass  # no está vacía (algo la usó mientras tanto) o ya no existe
    return ok


def directorio_datos() -> Path:
    """La carpeta donde este proceso debe guardar su estado.

    Orden de decisión:
    1. `MVPM_DATA_DIR`, si está seteada — vía de escape explícita: tests,
       instalaciones no estándar, o forzar todo a un disco puntual a mano.
    2. Junto al `.exe` instalado, si el programa corre congelado Y se puede
       escribir ahí — así el disco de los datos es el mismo que el de la
       instalación, sin configuración extra de por medio.
    3. El perfil del usuario — el comportamiento de siempre (`./run.sh app`,
       el `.bat` portable, desarrollo), y el respaldo seguro cuando la
       carpeta de instalación no es escribible.
    """
    desde_env = os.environ.get("MVPM_DATA_DIR")
    if desde_env:
        return Path(desde_env)

    candidata = _junto_al_ejecutable()
    if candidata is not None and _se_puede_escribir(candidata):
        return candidata

    return _en_el_perfil_del_usuario()
