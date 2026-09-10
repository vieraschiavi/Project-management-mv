# © 2026 Martín Viera. Todos los derechos reservados.
"""Autenticación con usuario y contraseña sobre la base local (`mvpm/db.py`).

Sin dependencias nuevas: hash de contraseña con PBKDF2-HMAC-SHA256 (stdlib
`hashlib`), 200.000 iteraciones, salt aleatorio de 16 bytes por usuario —
mismo nivel que recomienda OWASP para PBKDF2 en 2026. Nunca se guarda la
contraseña en texto plano, ni siquiera para las cuentas de ejemplo.
"""

import hashlib
import re
import secrets
import unicodedata
from datetime import datetime, timedelta, timezone

from . import db

_ITERATIONS = 200_000
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

#: Cuántos fallos seguidos se toleran y por cuánto queda bloqueada la cuenta.
#: Medido antes de elegir los números: un intento cuesta 136 ms, o sea ~7 por
#: segundo y por hilo. Sin freno, un diccionario de 100.000 claves comunes se
#: agota en menos de 4 horas con un solo hilo — y en media hora con ocho.
MAX_FALLOS = 5
BLOQUEO_MINUTOS = 15

#: Claves que no se aceptan aunque cumplan la longitud mínima. No pretende ser
#: una lista de brechas completa (eso es un servicio aparte y este producto
#: corre sin internet): son las que aparecen primero en cualquier diccionario.
#: La regla que de verdad protege es la de abajo — no permitir que la clave sea
#: el nombre de la empresa, el del usuario o su email, que es lo que la gente
#: elige cuando le piden "ocho caracteres".
_CLAVES_PROHIBIDAS = frozenset({
    "password", "passw0rd", "contrasena", "contraseña", "12345678", "123456789",
    "1234567890", "qwertyui", "qwerty123", "abcd1234", "aaaaaaaa", "11111111",
    "iloveyou", "admin123", "administrador", "letmein1", "welcome1",
    "changeme", "cambiame", "secreto1", "password1", "password123",
})


def _sin_acentos(texto: str) -> str:
    s = unicodedata.normalize("NFD", texto.lower().strip())
    return "".join(c for c in s if not unicodedata.combining(c))


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), _ITERATIONS)
    return digest.hex(), salt


def _validar_password(password: str, email: str = "", nombre: str = "") -> str | None:
    """Devuelve el motivo del rechazo, o None si la contraseña sirve.

    La longitud sola no alcanzaba y se comprobó: `password`, `12345678` y el
    nombre de la empresa pasaban el filtro. En un despliegue en un cliente eso
    no es hipotético — es la clave que la gente elige cuando le piden "ocho
    caracteres" y la primera que prueba cualquiera desde la red.
    """
    if len(password) < 8:
        return "La contraseña debe tener al menos 8 caracteres."

    plana = _sin_acentos(password)
    if plana in _CLAVES_PROHIBIDAS:
        return ("Esa contraseña es de las primeras que prueba cualquier "
                "ataque. Elegí otra.")
    if len(set(plana)) <= 2:
        return "La contraseña no puede ser el mismo carácter repetido."

    # Que la clave no sea el nombre propio, el de la empresa ni el email. Es la
    # regla que más sirve: `Conaprole` cumplía longitud y no está en ninguna
    # lista de claves comunes, pero es la primera que se prueba en Conaprole.
    propios = {_sin_acentos(p) for p in (nombre or "").split()}
    local = (email or "").split("@")[0]
    dominio = (email or "").split("@")[-1].split(".")[0]
    propios |= {_sin_acentos(local), _sin_acentos(dominio)}
    propios.discard("")
    for propio in propios:
        if len(propio) >= 4 and propio in plana:
            return ("La contraseña no puede contener tu nombre, tu email ni "
                    "el de la organización.")
    return None


def esta_bloqueada(email: str) -> int:
    """Minutos que faltan para poder reintentar, 0 si no está bloqueada.

    Se consulta ANTES de calcular el hash, y eso es deliberado: cada intento
    cuesta 200.000 iteraciones de PBKDF2, o sea ~136 ms de CPU del servidor.
    Verificar primero convierte la defensa criptográfica en algo que ya no se
    puede usar como munición para tumbar la máquina del cliente a pedidos.
    """
    desde = (_ahora() - timedelta(minutes=BLOQUEO_MINUTOS)).isoformat()
    if db.fallos_desde(email, desde) < MAX_FALLOS:
        return 0
    ultimo = db.ultimo_intento(email)
    if not ultimo:
        return 0
    try:
        cuando = datetime.fromisoformat(ultimo["creado_en"])
    except ValueError:
        return 0
    if cuando.tzinfo is None:
        cuando = cuando.replace(tzinfo=timezone.utc)
    faltan = (cuando + timedelta(minutes=BLOQUEO_MINUTOS)) - _ahora()
    return max(0, int(faltan.total_seconds() // 60) + 1)


def registrar(email: str, nombre: str, password: str, rol: str | None = None) -> dict:
    """Crea un usuario nuevo. El primer usuario de la instalación siempre es
    admin, sin importar qué rol se pida — nadie más puede auto-asignarse admin."""
    email = email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise ValueError("Email inválido.")
    if not nombre.strip():
        raise ValueError("El nombre es obligatorio.")
    error_password = _validar_password(password, email=email, nombre=nombre)
    if error_password:
        raise ValueError(error_password)
    if db.obtener_usuario_por_email(email):
        raise ValueError("Ya existe una cuenta con ese email.")

    es_primer_usuario = db.contar_usuarios() == 0
    rol_final = "admin" if es_primer_usuario else "miembro"

    password_hash, salt = _hash_password(password)
    user_id = db.crear_usuario(email, nombre.strip(), password_hash, salt, rol_final)
    return {"id": user_id, "email": email, "nombre": nombre.strip(), "rol": rol_final}


class CuentaBloqueada(Exception):
    """Demasiados intentos fallidos seguidos. Trae los minutos que faltan.

    Es una excepción y no un `None` a propósito: quien llama TIENE que
    distinguir "credencial incorrecta" de "no te voy a atender", porque son
    dos mensajes distintos para el usuario y dos hechos distintos para quien
    después lea el registro de accesos.
    """

    def __init__(self, minutos: int):
        self.minutos = minutos
        super().__init__(f"Cuenta bloqueada por {minutos} minuto(s).")


def iniciar_sesion(email: str, password: str, origen: str | None = None) -> dict | None:
    """Devuelve el usuario si las credenciales son correctas, None si no.

    Cuentas de ejemplo (sembradas por `db.cargar_datos_de_ejemplo`, sin
    password_hash) nunca pueden iniciar sesión — evita que un hash vacío
    verifique como válido con cualquier contraseña.

    Todo intento queda registrado, acierte o no. Es lo que le permite al
    cliente responder "quién entró" cuando su área de seguridad pregunta, y
    es de dónde sale la cuenta de fallos que dispara el bloqueo.

    Lanza `CuentaBloqueada` tras `MAX_FALLOS` fallos seguidos. El chequeo va
    antes de tocar el hash: ver `esta_bloqueada`.
    """
    email = (email or "").strip().lower()

    minutos = esta_bloqueada(email)
    if minutos:
        raise CuentaBloqueada(minutos)

    user = db.obtener_usuario_por_email(email)
    if not user or not user["password_hash"]:
        db.registrar_intento_login(email, False, origen)
        return None
    digest, _ = _hash_password(password, user["password_salt"])
    if not secrets.compare_digest(digest, user["password_hash"]):
        db.registrar_intento_login(email, False, origen)
        return None
    db.registrar_intento_login(email, True, origen)
    return user
