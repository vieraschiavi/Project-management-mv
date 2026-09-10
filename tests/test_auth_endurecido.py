# © 2026 Martín Viera. Todos los derechos reservados.
"""El login como puerta de red, no como formulario de escritorio.

Estos tests nacieron de una auditoría hecha **corriendo** el programa, no
leyéndolo, después de que el modo servidor pasara a exponer el tablero en la
red del cliente. Lo que se midió antes de escribir una línea de arreglo:

  · `password`, `12345678`, `aaaaaaaa` y `Conaprole` eran contraseñas válidas;
  · 50 intentos fallidos seguidos no bloqueaban nada;
  · cada intento costaba 136 ms de CPU del servidor, o sea ~7 por segundo y por
    hilo: un diccionario de 100.000 claves comunes se agotaba en menos de 4
    horas con un hilo, y en media hora con ocho;
  · no quedaba registro de ningún acceso, ni exitoso ni fallido.

El detalle que vuelve todo esto material: en modo servidor el login es la
ÚNICA puerta, y así estaba sin traba. Cada test de acá corresponde a una de
esas mediciones, para que si alguien afloja el mecanismo la suite lo diga con
nombre propio en vez de que se descubra en la red de un cliente.
"""

from datetime import datetime, timedelta, timezone

import pytest

from mvpm import auth, db


@pytest.fixture(autouse=True)
def base_aislada(tmp_path, monkeypatch):
    """Base propia por test.

    Se apunta `_STORE_DIR`/`_DB_FILE` con monkeypatch —la convención del resto
    de la suite— y NO con un reload del módulo: recargar `mvpm.db` deja el
    módulo apuntando a un temporal para todo lo que corra después, y eso ya
    rompió otros archivos de tests una vez.
    """
    monkeypatch.setattr(db, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(db, "_DB_FILE", tmp_path / "datos.db")
    db.init_db()


# ------------------------------------------------- qué contraseñas se aceptan

@pytest.mark.parametrize("clave", ["password", "12345678", "aaaaaaaa", "Password123"])
def test_rechaza_las_claves_que_prueba_cualquier_ataque(clave):
    """Las cuatro pasaban el filtro de "ocho caracteres" y son las primeras de
    cualquier diccionario."""
    with pytest.raises(ValueError):
        auth.registrar("alguien@empresa.com.uy", "Juan Perez", clave)


def test_la_clave_no_puede_ser_el_nombre_de_la_organizacion():
    """`Conaprole` cumplía la longitud y no está en ninguna lista de claves
    comunes — pero es exactamente la primera que se prueba EN Conaprole. Es la
    regla que más protege de las que se agregaron."""
    with pytest.raises(ValueError, match="nombre"):
        auth.registrar("juan@conaprole.com.uy", "Juan Perez", "Conaprole1")


def test_la_clave_no_puede_ser_el_nombre_de_la_persona():
    with pytest.raises(ValueError, match="nombre"):
        auth.registrar("j@empresa.com.uy", "Rodriguez", "Rodriguez22")


def test_una_clave_razonable_sigue_entrando():
    """El contrapeso: endurecer de más y que nadie pueda registrarse también
    es un fallo, sólo que uno que se descubre más tarde."""
    user = auth.registrar("ana@empresa.com.uy", "Ana Lopez", "Turbina-9-Verde")
    assert user["email"] == "ana@empresa.com.uy"
    assert auth.iniciar_sesion("ana@empresa.com.uy", "Turbina-9-Verde")


# ------------------------------------------------------------- fuerza bruta

def _con_usuario() -> str:
    auth.registrar("ana@empresa.com.uy", "Ana Lopez", "Turbina-9-Verde")
    return "ana@empresa.com.uy"


def test_bloquea_despues_de_varios_fallos_seguidos():
    email = _con_usuario()
    for _ in range(auth.MAX_FALLOS):
        assert auth.iniciar_sesion(email, "incorrecta") is None
    with pytest.raises(auth.CuentaBloqueada) as bloqueo:
        auth.iniciar_sesion(email, "incorrecta")
    assert 0 < bloqueo.value.minutos <= auth.BLOQUEO_MINUTOS


def test_el_bloqueo_tambien_frena_a_quien_SI_sabe_la_clave():
    """Si el bloqueo dejara pasar la contraseña correcta, un ataque sabría que
    acertó justo cuando acierta — y el freno no serviría para nada."""
    email = _con_usuario()
    for _ in range(auth.MAX_FALLOS):
        auth.iniciar_sesion(email, "incorrecta")
    with pytest.raises(auth.CuentaBloqueada):
        auth.iniciar_sesion(email, "Turbina-9-Verde")


def test_un_login_correcto_limpia_los_fallos_anteriores():
    """Un tipeo de ayer no puede dejar a alguien a un intento del bloqueo."""
    email = _con_usuario()
    for _ in range(auth.MAX_FALLOS - 1):
        auth.iniciar_sesion(email, "incorrecta")
    assert auth.iniciar_sesion(email, "Turbina-9-Verde")
    for _ in range(auth.MAX_FALLOS - 1):
        assert auth.iniciar_sesion(email, "incorrecta") is None
    assert auth.esta_bloqueada(email) == 0


def test_el_bloqueo_se_suelta_cuando_pasa_la_ventana():
    """Bloquear para siempre convierte un ataque en una denegación de servicio
    contra el usuario legítimo: alcanzaría con fallarle el login a alguien
    cinco veces para dejarlo afuera."""
    email = _con_usuario()
    for _ in range(auth.MAX_FALLOS):
        auth.iniciar_sesion(email, "incorrecta")
    assert auth.esta_bloqueada(email) > 0

    viejo = (datetime.now(timezone.utc)
             - timedelta(minutes=auth.BLOQUEO_MINUTOS + 1)).isoformat()
    with db._connect() as conn:
        conn.execute("UPDATE intentos_login SET creado_en = ?", (viejo,))
    assert auth.esta_bloqueada(email) == 0
    assert auth.iniciar_sesion(email, "Turbina-9-Verde")


def test_bloquear_no_cuesta_CPU():
    """El motivo por el que el chequeo va ANTES del hash.

    Cada intento cuesta 200.000 iteraciones de PBKDF2 (~136 ms medidos). Si el
    bloqueo se evaluara después, un atacante seguiría gastando esa CPU del
    servidor del cliente a pedidos: la defensa criptográfica pasaría a ser la
    munición. Se compara contra el costo real de un hash en ESTA máquina, no
    contra un número fijo, porque el umbral depende del hardware.
    """
    import time
    email = _con_usuario()
    for _ in range(auth.MAX_FALLOS):
        auth.iniciar_sesion(email, "incorrecta")

    t0 = time.perf_counter()
    auth._hash_password("lo que sea", "sal")
    costo_hash = time.perf_counter() - t0

    t0 = time.perf_counter()
    for _ in range(5):
        with pytest.raises(auth.CuentaBloqueada):
            auth.iniciar_sesion(email, "incorrecta")
    costo_bloqueo = (time.perf_counter() - t0) / 5

    assert costo_bloqueo < costo_hash / 5, (
        f"un intento bloqueado cuesta {costo_bloqueo*1000:.0f} ms y un hash "
        f"{costo_hash*1000:.0f} ms: el bloqueo está evaluándose DESPUÉS del "
        "hash y sigue sirviendo para tumbar el servidor a pedidos")


# ------------------------------------------------------------ trazabilidad

def test_queda_registro_de_los_accesos_y_de_los_intentos():
    """Lo que el área de seguridad del cliente va a pedir. Antes no existía:
    ante una sospecha, la respuesta era "no sé"."""
    email = _con_usuario()
    auth.iniciar_sesion(email, "incorrecta")
    auth.iniciar_sesion(email, "Turbina-9-Verde")

    accesos = db.accesos_recientes(10)
    assert [a["exito"] for a in accesos[:2]] == [1, 0], (
        "no quedaron registrados el fallo y el acierto, en ese orden")
    assert all(a["email"] == email for a in accesos[:2])


def test_el_registro_no_guarda_la_contrasena_probada():
    """En un intento fallido esa cadena suele ser la contraseña de OTRO sistema
    del usuario. Loguearla convierte la tabla de auditoría en el peor archivo
    del servidor — es el error clásico de este tipo de registro."""
    email = _con_usuario()
    auth.iniciar_sesion(email, "MiClaveDelBanco123")
    with db._connect() as conn:
        filas = conn.execute("SELECT * FROM intentos_login").fetchall()
    for fila in filas:
        assert "MiClaveDelBanco123" not in " ".join(
            str(v) for v in tuple(fila)), "la contraseña probada quedó en el log"


# --------------------------------------------------- la base bajo varios usuarios

def test_la_base_espera_el_lock_en_vez_de_reventar():
    """Medido antes del arreglo: con el lock tomado, el guardado de otro
    usuario moría a los 5,0 s exactos con `database is locked` — el default de
    sqlite3— y nadie captura esa excepción en todo el código, así que el
    usuario veía un traceback de Python en pantalla."""
    assert db._TIMEOUT_SEGUNDOS >= 30


def test_la_pantalla_de_login_atrapa_el_bloqueo():
    """`CuentaBloqueada` es una excepción, así que si la pantalla no la
    atrapa, Streamlit dibuja el traceback COMPLETO en la pantalla de login —
    con el nombre de la excepción y las rutas del servidor, a la vista de
    quien está probando contraseñas.

    Verificado además a mano contra la app corriendo: al sexto intento la
    pantalla muestra "Demasiados intentos fallidos. Probá de nuevo en 15
    minuto(s)." y ningún rastro de Python. Este test es lo que evita que
    alguien saque ese `except` y CI siga en verde.
    """
    from pathlib import Path
    app = (Path(__file__).resolve().parent.parent / "app" / "app.py").read_text(
        encoding="utf-8")
    assert "auth.CuentaBloqueada" in app, (
        "app.py no atrapa CuentaBloqueada: el bloqueo por fuerza bruta se le "
        "muestra al usuario como un traceback de Python")
    assert "login_err_bloqueada" in app, (
        "el bloqueo se atrapa pero no se le explica nada al usuario")


def test_la_base_usa_WAL_para_que_leer_no_bloquee_escribir():
    """Es la diferencia entre "un usuario" y "un equipo mirando el tablero
    mientras alguien guarda"."""
    with db._connect() as conn:
        modo = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert modo.lower() == "wal"
