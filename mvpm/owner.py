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
   pregunta>/OWNER_EDITION`), para una instalación que se activó ahí.

Lo que ya NO existe es un marcador firmado en el momento del build y metido
adentro del `.exe`. Ver "Por qué el marcador está atado a la máquina".

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

## Por qué el marcador está atado a la máquina

Porque el diseño anterior se apoyaba en que el repositorio era privado, y no lo
era. `packaging/OWNER_EDITION` —un token `enterprise` firmado— quedó versionado
en un repositorio PÚBLICO, y con él cualquiera podía pegarlo en el campo de
licencia de la app y usar el producto pago gratis, o copiarlo a su perfil y
quedar en modo dueño.

De ahí salen las tres decisiones de este módulo:

* El token del marcador se emite **atado a esta máquina** (`activar()`), y
  `_marcador_valido()` lo exige. Un marcador copiado a otra computadora no
  desbloquea nada.
* Un marcador SIN ese campo se rechaza. Eso mata de una a todas las copias del
  marcador viejo que ya estén dando vueltas.
* El `.exe` de la Owner Edition dejó de llevar un marcador firmado adentro. El
  CI no puede saber la máquina del dueño, así que un marcador firmado en el
  build o no vale en ningún lado, o vale en todos — y "vale en todos" es
  exactamente el agujero que estamos tapando. La Owner Edition se activa sola
  en la máquina del dueño vía `activar_automatico()`, que usa la clave privada
  local, y esa clave nunca viaja en ningún paquete.

## Por qué esto no afloja la licencia de nadie más

El marcador no viaja en lo que recibe un cliente, y hay tests que lo fijan
(`tests/test_owner.py`): ni el instalador de cliente (`packaging/mvpm.spec`) ni
el ZIP portable (`packaging/build_release.py`) lo incluyen. El candado de 7 días
queda igual, y las licencias que se venden NO se atan a una máquina —el cliente
tiene que poder cambiar de computadora—: sólo se ata el marcador del dueño.
Una instalación de cliente no tiene forma de activarse sola.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

from mvpm import licensing, rutas

MARCADOR = "OWNER_EDITION"

#: Con qué email se emite el token del marcador, y qué email reconoce
#: `es_email_owner()` como "soy yo" en la pantalla de licencia.
#:
#: Ojo con qué significa esto: el email NO es la credencial. Escribirlo no
#: desbloquea nada por sí solo — lo único que hace es disparar el intento de
#: activación, que después necesita la clave privada de abajo. Si alcanzara
#: con el email, cualquier cliente escribiría el del dueño (está publicado en
#: la landing y en el EULA) y usaría el producto pago gratis: sería el mismo
#: bypass que ya cerramos dos veces, ahora escrito en una casilla de texto.
EMAIL_OWNER = "vieraschiavi@gmail.com"

#: Archivo donde queda la clave privada de licencias en la máquina del dueño.
#: Es LO ÚNICO que separa su instalación de la de un cliente: el marcador se
#: firma con esto, y esto nunca viaja en el ZIP ni en el instalador.
ARCHIVO_CLAVE = "clave_privada_owner"

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
    "# La primera línea es un token firmado con la clave privada del dueño y\n"
    "# emitido para ESTA maquina en particular. Sin esa firma el archivo no\n"
    "# sirve, y copiado a otra computadora tampoco: alla no desbloquea nada.\n"
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
    """El primer marcador cuyo contenido tenga una firma válida del dueño **y**
    esté emitido para esta máquina.

    Un archivo vacío, con texto cualquiera o firmado con otra clave no sirve:
    la verificación es criptográfica, no de existencia.

    Lo de la máquina se exige, no se tolera: un marcador sin el campo `maquina`
    se rechaza aunque la firma sea impecable. Ver `activar()` para por qué.
    """
    huella = licensing.huella_maquina()
    for ruta in RUTAS_MARCADOR:
        token = _token_del_marcador(ruta)
        if not token:
            continue
        payload = licensing.verify_license(token)
        if not payload or payload.get("plan") not in licensing.PLANES_PAGOS:
            continue
        if not huella or payload.get("maquina") != huella:
            continue
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
    clave— puede crear uno que `es_owner()` acepte.

    El token se emite **atado a esta máquina** (`maquina` en el payload). Esa
    es la diferencia con la versión anterior, y viene de un error concreto:
    `packaging/OWNER_EDITION` quedó versionado en un repositorio público con un
    marcador adentro, y como el token no estaba atado a nada, cualquiera que lo
    copiara tenía el producto pago —de las dos formas, como marcador y pegándolo
    como licencia—. Atado, un marcador filtrado no sirve en ninguna otra
    computadora, así que el peor caso deja de ser "se regala el producto" y pasa
    a ser "hay que activar de nuevo acá".

    Escribe en los datos del usuario y no junto al programa: así sobrevive a
    reinstalar o mover la carpeta, y no hay riesgo de que se cuele en un ZIP
    armado desde el repo.
    """
    huella = licensing.huella_maquina()
    if not huella:
        raise RuntimeError(
            "No se pudo identificar esta máquina para atar el marcador: no hay "
            f"dónde escribir {licensing._RUTA_MAQUINA}. Un marcador sin atar "
            "valdría en cualquier computadora, así que no se emite."
        )
    token = licensing.issue_license("enterprise", email, extra={"maquina": huella})
    ruta = RUTAS_MARCADOR[0]
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(_TEXTO_MARCADOR.format(token=token), encoding="utf-8")
    return ruta


def ruta_clave_local() -> Path:
    """Dónde vive la clave privada del dueño en esta máquina. Siempre en el
    perfil del usuario, por lo mismo que el marcador: no depende del disco de
    instalación ni de si el proceso está congelado, y no hay forma de que se
    cuele en un ZIP armado desde la carpeta del programa."""
    return _PERFIL_USUARIO / ARCHIVO_CLAVE


def clave_privada_local() -> str:
    """La clave privada de licencias disponible en esta máquina, o "".

    Mira la variable de entorno primero y el archivo del perfil después, que es
    el mismo orden que usa `packaging/activar_owner.py`.
    """
    desde_entorno = os.environ.get("MVPM_LICENSE_PRIVATE_KEY", "").strip()
    if desde_entorno:
        return desde_entorno
    try:
        return ruta_clave_local().read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def guardar_clave_local(clave: str) -> Path:
    """Guarda la clave privada para que no haya que volver a pegarla nunca.
    Permisos 600: sólo la cuenta del dueño puede leerla."""
    ruta = ruta_clave_local()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(clave.strip(), encoding="utf-8")
    try:
        ruta.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        # En Windows el modo POSIX no aplica igual; tampoco molesta.
        pass
    return ruta


def es_email_owner(texto: str) -> bool:
    """¿El texto que escribieron es el email del dueño?

    Por sí solo no habilita nada (ver el comentario de EMAIL_OWNER): sirve para
    saber que hay que INTENTAR activar, no para dar por activado.
    """
    return texto.strip().casefold() == EMAIL_OWNER.casefold()


def activar_automatico() -> Path | None:
    """Deja esta máquina en modo dueño si tiene con qué, sin pedir nada.

    Es lo que hace que el dueño no tenga que correr un `.bat` ni pegar un token
    en cada instalación: si la clave privada está en la máquina, el marcador se
    escribe solo en el primer arranque y ya queda para siempre.

    Devuelve la ruta del marcador si lo escribió, o None si no había nada que
    hacer — porque ya estaba activo, o porque esta máquina no tiene la clave,
    que es el caso de cualquier cliente.
    """
    if es_owner():
        return None
    clave = clave_privada_local()
    if not clave:
        return None
    anterior = os.environ.get("MVPM_LICENSE_PRIVATE_KEY")
    os.environ["MVPM_LICENSE_PRIVATE_KEY"] = clave
    try:
        return activar()
    except (RuntimeError, OSError):
        # Clave inservible o disco de sólo lectura: se sigue como cliente en
        # vez de romper el arranque de la app.
        return None
    finally:
        if anterior is None:
            os.environ.pop("MVPM_LICENSE_PRIVATE_KEY", None)
        else:
            os.environ["MVPM_LICENSE_PRIVATE_KEY"] = anterior


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
