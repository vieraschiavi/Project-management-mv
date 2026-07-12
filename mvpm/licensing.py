"""Licencias y plan de créditos de IA — mismo patrón que `backend_venta/licencias.py`
de MV Kobra AI: el core del producto (catálogo, salud, dependencias, backlog,
políticas) no requiere licencia y no tiene cupo. Lo que se mide y factura es
el uso del **copiloto con IA** (consultas que enriquece Claude), porque es lo
único con costo variable real — el motor de reglas es gratis siempre.

Token propio, sin dependencias externas (HMAC-SHA256, formato
`MVPM1.<payload_b64url>.<firma_b64url>`), para no atar el proyecto a una
librería JWT y poder reimplementar el mismo esquema en las funciones
serverless de Node (`api/_license.js`) con el mismo secreto compartido.
"""

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

_STORE_DIR = Path.home() / ".mv_project_management"
_SECRET_FILE = _STORE_DIR / "license_secret.txt"
_USAGE_FILE = _STORE_DIR / "uso_copiloto.json"

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
        "precio_usd": 9,  # por usuario/mes
        "cupo_mensual_ia": 1000,
        "vigencia_dias": 30,
        "features": ["catalogo", "salud", "dependencias", "backlog", "copiloto_reglas",
                     "copiloto_ia", "reportes_automaticos", "integraciones"],
    },
    "enterprise": {
        "nombre": "Enterprise",
        "precio_usd": None,  # a medida, desde US$1.500/mes
        "cupo_mensual_ia": None,  # ilimitado
        "vigencia_dias": 30,
        "features": ["catalogo", "salud", "dependencias", "backlog", "copiloto_reglas",
                     "copiloto_ia", "reportes_automaticos", "integraciones",
                     "sso", "auditoria", "white_label"],
    },
}


def _secret() -> bytes:
    """Resuelve el secreto de firma: env var > archivo local generado una vez.
    Mismo criterio de prioridad que `kobra/config.py`."""
    import os
    env = os.environ.get("MVPM_LICENSE_SECRET")
    if env:
        return env.encode("utf-8")
    if _SECRET_FILE.exists():
        return _SECRET_FILE.read_text().strip().encode("utf-8")
    import secrets
    token = secrets.token_hex(32)
    _STORE_DIR.mkdir(parents=True, exist_ok=True)
    _SECRET_FILE.write_text(token)
    return token.encode("utf-8")


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def issue_license(plan: str, email: str, payment_id: str | None = None) -> str:
    """Emite un token de licencia firmado. `payment_id` viene de MercadoPago
    cuando la emisión sigue a un pago verificado; None para el plan demo."""
    if plan not in PLANES:
        raise ValueError(f"Plan desconocido: {plan}")
    payload = {
        "plan": plan,
        "email": email,
        "payment_id": payment_id,
        "iat": int(time.time()),
        "cupo_mensual_ia": PLANES[plan]["cupo_mensual_ia"],
    }
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = hmac.new(_secret(), payload_b64.encode("ascii"), hashlib.sha256).digest()
    return f"MVPM1.{payload_b64}.{_b64url(sig)}"


def verify_license(token: str) -> dict | None:
    """Verifica firma y estructura. Devuelve el payload si es válido, None si no."""
    try:
        prefix, payload_b64, sig_b64 = token.split(".")
        if prefix != "MVPM1":
            return None
        expected = hmac.new(_secret(), payload_b64.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64url_decode(sig_b64)):
            return None
        return json.loads(_b64url_decode(payload_b64))
    except (ValueError, KeyError, json.JSONDecodeError):
        return None


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
    plan = payload["plan"] if payload else "demo"
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
