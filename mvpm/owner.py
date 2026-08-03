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

El marcador es un **archivo que contiene un token de licencia firmado** con la
clave privada Ed25519 del dueño (`mvpm/licensing.py`). No alcanza con que el
archivo exista: se verifica la firma en cada arranque.

1. **Marcador en el perfil del usuario** (`~/.mv_project_management/OWNER_EDITION`,
   SIEMPRE ahí, sin importar disco de instalación ni si el proceso que pregunta
   está congelado). Es el que escriben `./run.sh owner` y
   `MV_ProjectManagement_OWNER.bat` —que necesitan `MVPM_LICENSE_PRIVATE_KEY`
   para poder firmarlo—, y el único que se puede activar sin tocar la carpeta
   de instalación: se escribe una vez y vale para siempre en esa máquina.
2. **Marcador junto al programa** (`<raíz o carpeta de datos del proceso que
   pregunta>/OWNER_EDITION`). Es el que empaqueta `packaging/mvpm_owner.spec`
   al lado del `.exe` de la Owner Edition, ya firmado desde el build.

## Por qué no alcanza con que el archivo exista

Antes `es_owner()` era `any(ruta.exists() ...)` y además había una variable de
entorno `MVPM_OWNER_BYPASS=1`. Las dos eran bypasses triviales del candado que
viajaban documentadas en el propio código que recibe el cliente: un
`type nul > OWNER_EDITION` (o exportar la variable) desbloqueaba el producto
entero, sin pagar y sin tocar una línea de código. El docstring de antes decía
que crear ese archivo "es lo mismo que decir que tiene que editar el código";
no lo era, y por eso ahora el contenido tiene que estar firmado.

## El bug que esto corrige

`./run.sh owner` y el `.bat` corren SIN congelar (Python del sistema, no el
`.exe`), así que hasta acá escribían el marcador vía `rutas.directorio_datos()`
sin congelar — que siempre da el perfil del usuario. Pero desde que ese mismo
`directorio_datos()` empezó a devolver "junto al .exe" para un proceso
CONGELADO con la carpeta de instalación escribible (para respetar el disco
elegido en el instalador), el `.exe` instalado dejó de preguntar en el perfil
del usuario — pasó a preguntar junto a sí mismo. Activar con `./run.sh owner`
escribía en un archivo que el `.exe` instalado ya no miraba: la función corría
sin ningún error, pero no desbloqueaba nada.

Por eso acá se pregunta SIEMPRE en el perfil del usuario (fijo, sin pasar por
`directorio_datos()`) además del directorio de datos del proceso actual — así
`./run.sh owner`/el `.bat` y el `.exe` instalado terminan mirando el mismo
archivo pase lo que pase con el disco elegido.

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

from mvpm import licensing, rutas

MARCADOR = "OWNER_EDITION"

#: Con qué email se emite el token del marcador. Sólo es una etiqueta para
#: saber de quién es la instalación al diagnosticar; no habilita nada por sí.
EMAIL_OWNER = "owner@mv-project-management"

# Fijo, SIN pasar por rutas.directorio_datos(): ese valor depende de si el
# proceso que pregunta está congelado y de si su propia carpeta de instalación
# es escribible, así que un `./run.sh owner` (sin congelar) y el `.exe`
# instalado (congelado) podían terminar de acuerdo en un directorio distinto
# cada uno — el bug real de esta sección. El perfil del usuario es el único
# punto que da la misma respuesta sin importar quién pregunta.
_PERFIL_USUARIO = Path.home() / rutas.NOMBRE_CARPETA
# Además de dónde este PROCESO en particular guarda sus datos (coincide con lo
# de arriba si no está congelado, o si la instalación no es escribible; puede
# ser otro si el .exe congelado escribe junto a sí mismo).
_DATOS_DEL_PROCESO = rutas.directorio_datos()
_RAIZ_PROGRAMA = Path(__file__).resolve().parent.parent

#: Dónde se busca el marcador, en orden. `activar()` escribe en el primero.
#: Sin duplicados (dict.fromkeys conserva el orden) — cuando el proceso no
#: está congelado, _DATOS_DEL_PROCESO y _PERFIL_USUARIO son la misma ruta.
#: Ruta extra que puede indicar el launcher del `.exe` Owner Edition
#: (packaging/mvpm_launcher.py): cuando corre congelado, la carpeta que ve
#: _RAIZ_PROGRAMA es la temporal de PyInstaller, no la del .exe. Va ÚLTIMA para
#: no desplazar el perfil del usuario como destino de `activar()`. Apuntar esta
#: variable a un archivo cualquiera no desbloquea nada: igual se verifica la
#: firma.
_MARCADOR_INDICADO = os.environ.get("MVPM_OWNER_MARCADOR", "").strip()

RUTAS_MARCADOR = tuple(dict.fromkeys(
    [
        _PERFIL_USUARIO / MARCADOR,
        _DATOS_DEL_PROCESO / MARCADOR,
        _RAIZ_PROGRAMA / MARCADOR,
    ]
    + ([Path(_MARCADOR_INDICADO)] if _MARCADOR_INDICADO else [])
))

_TEXTO_MARCADOR = (
    "{token}\n"
    "\n"
    "# Este archivo marca esta instalación como la del DUEÑO del producto:\n"
    "# el programa corre sin el candado de la prueba de 7 días.\n"
    "#\n"
    "# La primera línea es un token firmado con la clave privada del dueño.\n"
    "# Sin esa firma el archivo no sirve: copiarlo, vaciarlo o escribir\n"
    "# cualquier cosa acá no desbloquea nada.\n"
    "#\n"
    "# Borralo para volver al comportamiento normal (prueba + licencia).\n"
    "# Nunca se incluye en lo que se le entrega a un cliente.\n"
)


def _token_del_marcador(ruta: Path) -> str | None:
    """El token guardado en un marcador: la primera línea que no sea comentario
    ni esté vacía. El resto del archivo es texto explicativo para quien lo abra."""
    try:
        contenido = ruta.read_text(encoding="utf-8")
    except OSError:
        return None
    for linea in contenido.splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#"):
            return linea
    return None


def _marcador_valido() -> tuple[Path, dict] | None:
    """El primer marcador cuyo contenido tenga una firma válida del dueño.

    Un archivo vacío, con texto cualquiera o firmado con otra clave no sirve:
    la verificación es criptográfica, no de existencia.
    """
    for ruta in RUTAS_MARCADOR:
        token = _token_del_marcador(ruta)
        if not token:
            continue
        payload = licensing.verify_license(token)
        if payload and payload.get("plan") in licensing.PLANES_PAGOS:
            return ruta, payload
    return None


def es_owner() -> bool:
    """¿Esta instalación es la del dueño del producto?"""
    return _marcador_valido() is not None


def motivo() -> str | None:
    """De dónde salió el modo owner. Sirve para mostrarlo y para diagnosticar
    por qué una instalación quedó (o no quedó) desbloqueada."""
    encontrado = _marcador_valido()
    if encontrado is None:
        return None
    ruta, payload = encontrado
    return f"marcador firmado {ruta} ({payload.get('email', 'sin email')})"


def activar(email: str = EMAIL_OWNER) -> Path:
    """Marca esta máquina como la del dueño. Idempotente.

    Necesita la clave privada de licencias (`MVPM_LICENSE_PRIVATE_KEY`): el
    marcador es un token firmado, así que sólo el dueño —que es quien tiene esa
    clave— puede crear uno que `es_owner()` acepte. Un cliente no puede
    activarse solo ni copiando el archivo de otra máquina a mano.

    Escribe en los datos del usuario y no junto al programa: así sobrevive a
    reinstalar o mover la carpeta, y no hay riesgo de que se cuele en un ZIP
    armado desde el repo.
    """
    token = licensing.issue_license("enterprise", email)
    ruta = RUTAS_MARCADOR[0]
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(_TEXTO_MARCADOR.format(token=token), encoding="utf-8")
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
