"""Licencias y plan de créditos de IA — mismo patrón que `backend_venta/licencias.py`
de MV Kobra AI: el core del producto (catálogo, salud, dependencias, backlog,
políticas) no requiere licencia y no tiene cupo. Lo que se mide y factura es
el uso del **copiloto con IA** (consultas que enriquece Claude), porque es lo
único con costo variable real — el motor de reglas es gratis siempre.

Token propio (formato `MVPM2.<payload_b64url>.<firma_b64url>`), sin atar el
proyecto a una librería JWT, reimplementado con el mismo esquema en las
funciones serverless de Node (`api/_license.js`).

## Por qué la firma es asimétrica (Ed25519) y no un secreto compartido

El servidor de pagos firma con la clave PRIVADA, que nunca sale de Vercel; el
programa del cliente lleva sólo la clave PÚBLICA, que sirve para verificar y
**no** para emitir.

Antes esto era HMAC-SHA256 con un "secreto compartido" que, si no llegaba por
variable de entorno, el propio cliente se autogeneraba al azar en su disco. Eso
rompía el candado en las dos direcciones a la vez:

* **El que no pagaba entraba.** Dos líneas con el módulo que viene en la caja
  —`issue_license("enterprise", ...)`— firmaban con el secreto local y
  `verify_license()` las validaba contra ese mismo secreto local.
* **El que pagaba no entraba.** El token legítimo emitido por el servidor venía
  firmado con el secreto de Vercel, que no coincidía con el del cliente, así
  que `verify_license()` devolvía None y la persona que acababa de pagar seguía
  viendo "la prueba venció".

Con firma asimétrica las dos se caen solas: sin la clave privada no se puede
producir una firma que la pública acepte, y la pública que viaja en cada copia
del programa no sirve para emitir nada.
"""

import base64
import binascii
import json
import os
import secrets
import time
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from mvpm import rutas

_STORE_DIR = rutas.directorio_datos()
_USAGE_FILE = _STORE_DIR / "uso_copiloto.json"
_TRIAL_FILE = _STORE_DIR / "trial.json"

#: Dónde se guarda la marca de "primer uso". Se escribe en TODAS y se lee la
#: MÁS VIEJA de las que existan, así borrar una sola no devuelve la prueba a
#: cero — que era lo que pasaba: `rm trial.json` daba 7 días nuevos, infinitas
#: veces. Sin duplicados y en orden (dict.fromkeys): cuando el proceso no está
#: congelado, _STORE_DIR ya es el perfil del usuario.
#:
#: Honestidad sobre el alcance: esto sube el listón de "borrar un archivo
#: obvio" a "encontrar y borrar todos", no lo vuelve imposible. Una prueba
#: offline en una máquina ajena siempre se puede resetear con suficiente
#: empeño; lo que no puede pasar es que sea trivial.
_RUTAS_TRIAL = tuple(dict.fromkeys([
    _TRIAL_FILE,
    Path.home() / rutas.NOMBRE_CARPETA / "trial.json",
    Path.home() / ".mvpm_estado",
]))

# Prueba completa: el programa se descarga 100% desbloqueado y funciona sin
# recortes durante estos días desde el primer uso. Al vencer, se bloquea el
# acceso hasta cargar una licencia paga vigente — pero los datos ya cargados
# NUNCA se borran: al pagar, la persona sigue con todo lo que hizo.
TRIAL_DIAS = 7
DIA_SEGUNDOS = 86400
PLANES_PAGOS = ("professional", "professional_anual", "enterprise")

PLANES = {
    "demo": {
        "nombre": "Demo de evaluación",
        "precio_usd": 0,
        "cupo_mensual_ia": 20,
        "vigencia_dias": None,  # sin vencimiento, pero no apto para producción
        "features": ["catalogo", "salud", "dependencias", "backlog", "copiloto_reglas"],
    },
    "professional": {
        "nombre": "Professional",
        "precio_usd": 9,  # por usuario/mes (suscripción mensual automática)
        "cupo_mensual_ia": 1000,
        # 365 días, no 30: el cobro es recurrente en MercadoPago, pero la
        # licencia se emite una sola vez. Con 30 días el cliente que YA pagó
        # quedaba bloqueado al día 31 esperando un token nuevo. La vigencia
        # larga desacopla "cobrar todos los meses" de "no dejar afuera a quien
        # pagó". Si alguien cancela, se deja de cobrar y no se renueva al año.
        "vigencia_dias": 365,
        "features": ["catalogo", "salud", "dependencias", "backlog", "copiloto_reglas",
                     "copiloto_ia", "reportes_automaticos", "integraciones"],
    },
    "professional_anual": {
        "nombre": "Professional (12 meses)",
        "precio_usd": 90,  # 12 meses al precio de 10
        "cupo_mensual_ia": 1000,
        "vigencia_dias": 365,
        "features": ["catalogo", "salud", "dependencias", "backlog", "copiloto_reglas",
                     "copiloto_ia", "reportes_automaticos", "integraciones"],
    },
    "enterprise": {
        "nombre": "Enterprise",
        "precio_usd": None,  # implementación a medida, cotizada por proyecto
        "cupo_mensual_ia": None,  # ilimitado
        "vigencia_dias": 365,
        "features": ["catalogo", "salud", "dependencias", "backlog", "copiloto_reglas",
                     "copiloto_ia", "reportes_automaticos", "integraciones",
                     "sso", "auditoria", "white_label"],
    },
}


#: Clave PÚBLICA de firma de licencias, en base64url de los 32 bytes crudos.
#: Es la que viaja en cada copia del programa. Se puede pisar con la variable
#: de entorno MVPM_LICENSE_PUBLIC_KEY (rotación de claves, o tests).
#:
#: Vacía = todavía no se generó el par de claves de producción. Mientras esté
#: así, `verify_license()` rechaza TODO token: preferimos que no entre nadie
#: con licencia a que entre cualquiera. Se genera una sola vez con
#: `python packaging/generar_claves_licencia.py`.
CLAVE_PUBLICA_EMBEBIDA = "Ba7bsdl1pysbGEuG6wa3fne1PfdsTbkIpo8DD7cIgMg"


#: Tokens que se emitieron de verdad —firma válida, clave correcta— pero que
#: dejaron de valer. Se listan por su FIRMA (la tercera parte del token), que
#: es lo único que identifica un token sin ambigüedad y que nadie puede cambiar
#: sin invalidarlo: Ed25519 es determinista (RFC 8032), así que un mismo payload
#: firmado con una misma clave da siempre exactamente estos bytes.
#:
#: Por qué una lista y no rotar el par de claves, que sería lo obvio: rotar
#: mata TODAS las licencias a la vez —incluidas las que alguien pagó— y obliga
#: a actualizar el secreto de Vercel y a custodiar una clave privada nueva.
#: Revocar por firma es quirúrgico: cae el token que se filtró y nada más.
#:
#: --- por qué hay una acá ---
#:
#: `packaging/OWNER_EDITION` estuvo versionado en un repositorio PÚBLICO con un
#: token `enterprise` firmado adentro. Se diseñó pensando que el repo era
#: privado y no lo era. Cualquiera que pasara por el repo podía:
#:   * pegar esa línea en el campo de licencia y tener el producto pago gratis
#:     (`estado_acceso()` devolvía modo "licencia", plan enterprise), o
#:   * copiarla a ~/.mv_project_management/OWNER_EDITION y quedar en modo dueño.
#: Sacar el archivo del repo no alcanza: el historial de git queda, y quien ya
#: lo bajó tiene el token para siempre. Lo único que lo mata es que el programa
#: deje de aceptarlo, que es esto.
FIRMAS_REVOCADAS = frozenset({
    # packaging/OWNER_EDITION — enterprise, vieraschiavi@gmail.com, iat 1786131101.
    "7toxxzkepMP3F1giHxrDlwsiHuSGItLuG56s3aRGOhhjoXElTc9zWP8WexWa8leXFbeYf4zG3m8C57GWlR_YDw",
})


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _clave_publica() -> Ed25519PublicKey | None:
    """La clave con la que el programa VERIFICA licencias. None si todavía no
    hay par de claves configurado."""
    crudo = os.environ.get("MVPM_LICENSE_PUBLIC_KEY", "").strip() or CLAVE_PUBLICA_EMBEBIDA
    if not crudo:
        return None
    try:
        return Ed25519PublicKey.from_public_bytes(_b64url_decode(crudo))
    except (ValueError, TypeError, binascii.Error):
        return None


def _clave_privada() -> Ed25519PrivateKey | None:
    """La clave con la que se EMITEN licencias. Vive sólo en el servidor de
    pagos (variable de entorno en Vercel) y en la máquina del dueño para el
    panel de licencias. Nunca viaja en lo que recibe un cliente."""
    crudo = os.environ.get("MVPM_LICENSE_PRIVATE_KEY", "").strip()
    if not crudo:
        return None
    try:
        return Ed25519PrivateKey.from_private_bytes(_b64url_decode(crudo))
    except (ValueError, TypeError, binascii.Error):
        return None


def issue_license(plan: str, email: str, payment_id: str | None = None,
                  extra: dict | None = None) -> str:
    """Emite un token de licencia firmado. `payment_id` viene de MercadoPago
    cuando la emisión sigue a un pago verificado; None para el plan demo.

    `extra` agrega campos al payload antes de firmar. Lo usa el marcador del
    dueño para atar el token a su máquina (`{"maquina": ...}`); las licencias
    que se venden no lo usan, porque el cliente tiene que poder mover la suya
    a otra computadora.

    Requiere la clave PRIVADA. En la máquina de un cliente no está, así que
    esto no es una forma de fabricarse una licencia: es exactamente el punto
    del esquema asimétrico.
    """
    if plan not in PLANES:
        raise ValueError(f"Plan desconocido: {plan}")
    clave = _clave_privada()
    if clave is None:
        raise RuntimeError(
            "No hay clave privada de licencias (MVPM_LICENSE_PRIVATE_KEY). "
            "Sólo el servidor de pagos y el panel del dueño pueden emitir licencias."
        )
    payload = {
        "plan": plan,
        "email": email,
        "payment_id": payment_id,
        "iat": int(time.time()),
        "cupo_mensual_ia": PLANES[plan]["cupo_mensual_ia"],
    }
    if extra:
        payload.update(extra)
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = clave.sign(payload_b64.encode("ascii"))
    return f"MVPM2.{payload_b64}.{_b64url(sig)}"


def verify_license(token: str) -> dict | None:
    """Verifica firma y estructura. Devuelve el payload si es válido, None si no.

    Sólo acepta `MVPM2` (Ed25519). Los `MVPM1` viejos (HMAC con secreto que el
    propio cliente se autogeneraba) se rechazan a propósito: aceptarlos sería
    dejar abierta la puerta que este cambio vino a cerrar.

    Un token de FIRMAS_REVOCADAS se rechaza aunque la firma sea perfecta: son
    tokens que se emitieron bien y después se filtraron.
    """
    clave = _clave_publica()
    if clave is None or not token:
        return None
    try:
        prefix, payload_b64, sig_b64 = token.split(".")
        if prefix != "MVPM2":
            return None
        if sig_b64 in FIRMAS_REVOCADAS:
            return None
        clave.verify(_b64url_decode(sig_b64), payload_b64.encode("ascii"))
        return json.loads(_b64url_decode(payload_b64))
    except (ValueError, KeyError, TypeError, binascii.Error,
            json.JSONDecodeError, InvalidSignature):
        return None


# ------------------------------------------------- tokens atados a una máquina

#: Identificador aleatorio de ESTA máquina. No dice nada de la computadora (no
#: es el MAC ni el hostname ni el usuario): es un número al azar que se escribe
#: una vez y no cambia más.
#:
#: Se eligió así a propósito por encima de una huella de hardware. Lo que hace
#: falta es que dos máquinas distintas den valores distintos —y eso lo garantiza
#: el azar—, no identificar el equipo. Una huella de hardware, en cambio, se
#: rompe sola el día que cambia la placa de red o se renombra la máquina, y
#: dejaría al dueño afuera de su propio programa sin ninguna razón visible.
ARCHIVO_MAQUINA = "maquina_id"
_RUTA_MAQUINA = Path.home() / rutas.NOMBRE_CARPETA / ARCHIVO_MAQUINA


def huella_maquina() -> str:
    """El id de esta máquina, creándolo la primera vez. "" si no se puede
    escribir (disco de sólo lectura), y en ese caso ningún token atado vale:
    se falla cerrado, que es lo mismo que ya pasa si no se puede activar."""
    try:
        actual = _RUTA_MAQUINA.read_text(encoding="utf-8").strip()
        if actual:
            return actual
    except OSError:
        pass
    nueva = secrets.token_hex(16)
    try:
        _RUTA_MAQUINA.parent.mkdir(parents=True, exist_ok=True)
        _RUTA_MAQUINA.write_text(nueva, encoding="utf-8")
    except OSError:
        return ""
    return nueva


def atada_a_esta_maquina(payload: dict | None) -> bool:
    """¿Este token se puede usar acá?

    Un token SIN campo `maquina` no está atado a ninguna y vale en todas: es el
    caso de las licencias que se venden, que la persona tiene que poder mover a
    otra computadora. Uno CON el campo vale sólo donde se emitió.

    Lo usan el marcador del dueño (`mvpm/owner.py`) y `licencia_vigente()`, para
    que atar signifique lo mismo en los dos lados: si el marcador del dueño se
    filtrara, no alcanzaría ni para desbloquear otra máquina ni para pegarlo
    como licencia en el campo de texto de la app.
    """
    if not payload:
        return False
    atada = payload.get("maquina")
    if not atada:
        return True
    huella = huella_maquina()
    return bool(huella) and atada == huella


def _load_usage() -> dict:
    if not _USAGE_FILE.exists():
        return {}
    try:
        return json.loads(_USAGE_FILE.read_text())
    except json.JSONDecodeError:
        return {}


def _save_usage(data: dict) -> None:
    _STORE_DIR.mkdir(parents=True, exist_ok=True)
    _USAGE_FILE.write_text(json.dumps(data, indent=2))


def _current_period() -> str:
    return time.strftime("%Y-%m")


def consultas_usadas(email: str) -> int:
    usage = _load_usage()
    return usage.get(email, {}).get(_current_period(), 0)


def puede_usar_ia(token: str | None) -> tuple[bool, str]:
    """Chequea si el titular del token todavía tiene cupo de IA este mes.
    Sin token válido, se trata como plan demo (cupo bajo, siempre disponible
    para evaluar). Nunca bloquea el motor de reglas — solo la capa de IA."""
    payload = verify_license(token) if token else None
    plan = plan_para_cupo(token)
    email = payload["email"] if payload else "demo@local"
    cupo = PLANES[plan]["cupo_mensual_ia"]
    if cupo is None:  # enterprise: ilimitado
        return True, "ilimitado"
    usadas = consultas_usadas(email)
    if usadas >= cupo:
        return False, f"Cupo mensual de IA agotado ({usadas}/{cupo}). El motor de reglas sigue funcionando sin límite."
    return True, f"{usadas}/{cupo} consultas de IA usadas este mes"


def registrar_uso_ia(email: str = "demo@local") -> None:
    usage = _load_usage()
    period = _current_period()
    usage.setdefault(email, {})
    usage[email][period] = usage[email].get(period, 0) + 1
    _save_usage(usage)


# --------------------------------------------------------------- prueba 7 días

def _leer_trial() -> dict:
    """La marca MÁS VIEJA de todas las copias que existan. Borrar una sola no
    reinicia la prueba: mientras quede otra, esa es la que manda."""
    mas_vieja = None
    for ruta in _RUTAS_TRIAL:
        try:
            data = json.loads(ruta.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        try:
            ts = float(data["primer_uso"])
        except (KeyError, TypeError, ValueError):
            continue
        if mas_vieja is None or ts < mas_vieja:
            mas_vieja = ts
    return {} if mas_vieja is None else {"primer_uso": mas_vieja}


def primer_uso(ahora: float | None = None) -> float:
    """Devuelve el timestamp del primer uso, creándolo la primera vez. La marca
    se guarda en disco y no se pisa: define desde cuándo corre la prueba.

    Se reescribe en todas las rutas en cada llamada (no sólo al crearla) para
    que restaurar una copia borrada sea automático: si quedó una sola, la
    próxima apertura del programa vuelve a dejar las demás en su lugar.
    """
    data = _leer_trial()
    ts = float(data["primer_uso"]) if "primer_uso" in data else float(
        ahora if ahora is not None else time.time())
    contenido = json.dumps({"primer_uso": ts}, indent=2)
    for ruta in _RUTAS_TRIAL:
        try:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(contenido)
        except OSError:
            continue  # una ruta sin permiso no puede tumbar el arranque
    return ts


def licencia_vigente(payload: dict | None, ahora: float | None = None) -> bool:
    """Una licencia paga vale mientras no venza su `vigencia_dias` desde `iat`.
    Enterprise/Professional tienen 30 días (se renuevan con cada pago mensual)."""
    if not payload:
        return False
    plan = payload.get("plan")
    if plan not in PLANES_PAGOS:
        return False
    if not atada_a_esta_maquina(payload):
        return False
    vigencia = PLANES.get(plan, {}).get("vigencia_dias")
    if vigencia is None:  # paga sin vencimiento explícito
        return True
    iat = float(payload.get("iat", 0))
    ahora = float(ahora if ahora is not None else time.time())
    return (ahora - iat) <= vigencia * DIA_SEGUNDOS


def estado_acceso(token: str | None, ahora: float | None = None) -> dict:
    """Candado maestro del programa. Devuelve si se puede usar la app completa:

    - Con licencia paga vigente  → acceso total, modo 'licencia'.
    - Dentro de los 7 días        → acceso total, modo 'trial'.
    - Prueba vencida y sin pago    → bloqueado, modo 'expirado'.

    Bloquear NUNCA borra datos: al cargar una licencia válida, la persona sigue
    con todo lo que hizo. El motor de reglas y la app entera se habilitan igual
    durante la prueba; sólo al vencer se corta hasta pagar.
    """
    ahora = float(ahora if ahora is not None else time.time())
    payload = verify_license(token) if token else None

    if licencia_vigente(payload, ahora):
        return {
            "acceso": True, "modo": "licencia", "plan": payload["plan"],
            "dias_restantes": None,
            "mensaje": f"Licencia {PLANES[payload['plan']]['nombre']} activa.",
        }

    inicio = primer_uso(ahora)
    transcurridos = (ahora - inicio) / DIA_SEGUNDOS
    restantes = TRIAL_DIAS - transcurridos
    if restantes > 0:
        dias = max(1, int(restantes + 0.999))  # redondeo hacia arriba, mínimo 1
        return {
            "acceso": True, "modo": "trial", "plan": "trial",
            "dias_restantes": dias,
            "mensaje": f"Prueba completa: te quedan {dias} día(s) con todo desbloqueado.",
        }

    return {
        "acceso": False, "modo": "expirado", "plan": None, "dias_restantes": 0,
        "mensaje": "La prueba de 7 días venció. Tus datos están guardados: "
                   "activá una licencia Professional para seguir usándolos.",
    }


def plan_para_cupo(token: str | None, ahora: float | None = None) -> str:
    """Plan efectivo para el cupo de IA. Durante la prueba se trata como
    Professional (la prueba es completa); con licencia paga, su propio plan."""
    payload = verify_license(token) if token else None
    if licencia_vigente(payload, ahora):
        return payload["plan"]
    est = estado_acceso(token, ahora)
    return "professional" if est["modo"] == "trial" else "demo"
