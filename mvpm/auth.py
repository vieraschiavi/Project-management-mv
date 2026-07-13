"""Autenticación con usuario y contraseña sobre la base local (`mvpm/db.py`).

Sin dependencias nuevas: hash de contraseña con PBKDF2-HMAC-SHA256 (stdlib
`hashlib`), 200.000 iteraciones, salt aleatorio de 16 bytes por usuario —
mismo nivel que recomienda OWASP para PBKDF2 en 2026. Nunca se guarda la
contraseña en texto plano, ni siquiera para las cuentas de ejemplo.
"""

import hashlib
import re
import secrets

from . import db

_ITERATIONS = 200_000
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), _ITERATIONS)
    return digest.hex(), salt


def _validar_password(password: str) -> str | None:
    if len(password) < 8:
        return "La contraseña debe tener al menos 8 caracteres."
    return None


def registrar(email: str, nombre: str, password: str, rol: str | None = None) -> dict:
    """Crea un usuario nuevo. El primer usuario de la instalación siempre es
    admin, sin importar qué rol se pida — nadie más puede auto-asignarse admin."""
    email = email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise ValueError("Email inválido.")
    if not nombre.strip():
        raise ValueError("El nombre es obligatorio.")
    error_password = _validar_password(password)
    if error_password:
        raise ValueError(error_password)
    if db.obtener_usuario_por_email(email):
        raise ValueError("Ya existe una cuenta con ese email.")

    es_primer_usuario = db.contar_usuarios() == 0
    rol_final = "admin" if es_primer_usuario else "miembro"

    password_hash, salt = _hash_password(password)
    user_id = db.crear_usuario(email, nombre.strip(), password_hash, salt, rol_final)
    return {"id": user_id, "email": email, "nombre": nombre.strip(), "rol": rol_final}


def iniciar_sesion(email: str, password: str) -> dict | None:
    """Devuelve el usuario si las credenciales son correctas, None si no.
    Cuentas de ejemplo (sembradas por `db.cargar_datos_de_ejemplo`, sin
    password_hash) nunca pueden iniciar sesión — evita que un hash vacío
    verifique como válido con cualquier contraseña."""
    user = db.obtener_usuario_por_email(email)
    if not user or not user["password_hash"]:
        return None
    digest, _ = _hash_password(password, user["password_salt"])
    if not secrets.compare_digest(digest, user["password_hash"]):
        return None
    return user
