"""Edición Owner: la instalación del dueño del producto, sin candado de licencia.

El dueño usa su propio programa todos los días —para su portafolio real, para
demos, para probar antes de publicar— y no tiene sentido que la prueba de 7 días
lo deje afuera de su propia herramienta.

Hasta ahora esto vivía sólo en `packaging/mvpm_launcher.py`, o sea que
funcionaba únicamente si se arrancaba por el `.exe` de la Owner Edition. Quien
abría el mismo programa con `./run.sh app`, con el `.bat` portable o con
`streamlit run` directo caía igual en la pantalla de "la prueba venció". Por eso
la decisión se centraliza acá: todas las formas de arrancar preguntan lo mismo.

## Cómo se activa

Cualquiera de estas tres, en orden de cómo se usan en la práctica:

1. **Marcador en los datos del usuario** (`~/.mv_project_management/OWNER_EDITION`).
   Es el que activa `./run.sh owner`: se escribe una vez y vale para siempre en
   esa máquina, sin importar con qué comando se abra el programa.
2. **Marcador junto al programa** (`<raíz>/OWNER_EDITION`). Es el que empaqueta
   `packaging/mvpm_owner.spec` al lado del `.exe` de la Owner Edition.
3. **Variable de entorno** `MVPM_OWNER_BYPASS=1`, para un arranque puntual sin
   dejar nada escrito.

## Por qué esto no afloja la licencia de nadie más

Ninguno de los tres viaja en lo que recibe un cliente, y hay tests que lo fijan
(`tests/test_owner.py`): ni el instalador de cliente (`packaging/mvpm.spec`) ni
el ZIP portable (`packaging/build_release.py`) incluyen el marcador, y este
módulo no toca `licensing.py` — el candado de 7 días y la verificación de firma
de los tokens quedan exactamente igual. Una instalación de cliente no tiene
forma de activarse sola: alguien tiene que crear el archivo a mano en su propia
máquina, que es lo mismo que decir que tiene que editar el código.
"""

from __future__ import annotations

import os
from pathlib import Path

MARCADOR = "OWNER_EDITION"

_DATOS_USUARIO = Path.home() / ".mv_project_management"
_RAIZ_PROGRAMA = Path(__file__).resolve().parent.parent

#: Dónde se busca el marcador, en orden. `activar()` escribe en el primero.
RUTAS_MARCADOR = (
    _DATOS_USUARIO / MARCADOR,
    _RAIZ_PROGRAMA / MARCADOR,
)

_TEXTO_MARCADOR = (
    "Este archivo marca esta instalación como la del DUEÑO del producto:\n"
    "el programa corre sin el candado de la prueba de 7 días.\n"
    "\n"
    "No cambia nada del esquema de licencias — sólo esta instalación.\n"
    "Borralo para volver al comportamiento normal (prueba + licencia).\n"
    "Nunca se incluye en lo que se le entrega a un cliente.\n"
)


def es_owner() -> bool:
    """¿Esta instalación es la del dueño del producto?"""
    if os.environ.get("MVPM_OWNER_BYPASS") == "1":
        return True
    return any(ruta.exists() for ruta in RUTAS_MARCADOR)


def motivo() -> str | None:
    """De dónde salió el modo owner. Sirve para mostrarlo y para diagnosticar
    por qué una instalación quedó (o no quedó) desbloqueada."""
    if os.environ.get("MVPM_OWNER_BYPASS") == "1":
        return "variable de entorno MVPM_OWNER_BYPASS=1"
    for ruta in RUTAS_MARCADOR:
        if ruta.exists():
            return f"marcador {ruta}"
    return None


def activar() -> Path:
    """Marca esta máquina como la del dueño. Idempotente.

    Escribe en los datos del usuario y no junto al programa: así sobrevive a
    reinstalar o mover la carpeta, y no hay riesgo de que se cuele en un ZIP
    armado desde el repo.
    """
    ruta = RUTAS_MARCADOR[0]
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(_TEXTO_MARCADOR, encoding="utf-8")
    return ruta


def desactivar() -> list[Path]:
    """Vuelve al comportamiento de cliente (prueba + licencia). Devuelve los
    marcadores que borró — sirve para verificar el estado real de la máquina
    cuando se quiere probar el candado como lo ve un cliente."""
    borrados = []
    for ruta in RUTAS_MARCADOR:
        if ruta.exists():
            ruta.unlink()
            borrados.append(ruta)
    return borrados


def estado_acceso() -> dict:
    """Mismo contrato que `licensing.estado_acceso()`, para que la app pueda
    usar uno u otro sin ramificar la lógica de más abajo."""
    return {
        "acceso": True,
        "modo": "owner",
        "plan": None,
        "dias_restantes": None,
        "mensaje": "Modo owner — sin restricciones de licencia.",
    }
