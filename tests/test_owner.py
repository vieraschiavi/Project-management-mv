"""Edición Owner (mvpm/owner.py): el dueño usa su producto sin candado.

Dos cosas que fijar, y la segunda importa más que la primera:

1. Que el modo owner funcione **en toda forma de arrancar** el programa. Antes
   la decisión vivía en `packaging/mvpm_launcher.py`, o sea sólo en el `.exe`:
   el mismo dueño abriendo su programa con `./run.sh app` o con el `.bat`
   portable caía igual en "la prueba de 7 días venció".

2. Que NADA de esto viaje en lo que recibe un cliente. Si el marcador se colara
   en el instalador o en el ZIP portable, el candado de licencia dejaría de
   existir para todo el mundo y el producto sería gratis sin querer.
"""

import ast
import os
from pathlib import Path

import pytest

from mvpm import licensing, owner

RAIZ = Path(__file__).resolve().parent.parent


def _par_de_claves() -> tuple[str, str]:
    """Un par Ed25519 nuevo, en el mismo base64url que usa licensing.py.
    Cada test firma con el suyo: nunca se toca el par real de producción."""
    import sys as _sys

    _sys.path.insert(0, str(RAIZ / "packaging"))
    from generar_claves_licencia import generar

    return generar()


@pytest.fixture
def sin_marcadores(monkeypatch, tmp_path):
    """Aísla la detección: marcadores en tmp y sin la env var.

    Es imprescindible que no toque los archivos reales — si el dueño corre la
    suite en su propia máquina, un test no puede borrarle el marcador.
    """
    monkeypatch.delenv("MVPM_OWNER_BYPASS", raising=False)
    rutas = (tmp_path / "datos" / owner.MARCADOR, tmp_path / "programa" / owner.MARCADOR)
    monkeypatch.setattr(owner, "RUTAS_MARCADOR", rutas)
    return rutas


# --------------------------------------------------------------- detección

def test_una_instalacion_limpia_no_es_owner(sin_marcadores):
    """El caso del cliente: sin marcadores ni env var, pasa por el candado."""
    assert owner.es_owner() is False
    assert owner.motivo() is None


def test_la_env_var_de_bypass_ya_no_activa_nada(sin_marcadores, monkeypatch):
    """Regresión de seguridad. `MVPM_OWNER_BYPASS=1` desbloqueaba el producto
    entero por el solo hecho de existir la variable, y estaba documentada en
    `mvpm/owner.py` — un archivo que viaja en el ZIP portable que baja
    cualquiera. Era un bypass del candado a un `export` de distancia."""
    for valor in ["1", "0", "", "true", "si"]:
        monkeypatch.setenv("MVPM_OWNER_BYPASS", valor)
        assert owner.es_owner() is False, (
            f"MVPM_OWNER_BYPASS={valor!r} no puede desbloquear nada")


@pytest.mark.parametrize("indice", [0, 1])
def test_cualquiera_de_los_marcadores_activa_el_modo_owner(sin_marcadores, indice):
    """Uno vive en los datos del usuario (lo escribe `./run.sh owner`) y el
    otro junto al programa (lo empaqueta el .exe de la Owner Edition)."""
    ruta = sin_marcadores[indice]
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(licensing.issue_license("enterprise", "dueno@ejemplo.com"),
                    encoding="utf-8")
    assert owner.es_owner() is True
    assert str(ruta) in owner.motivo()


@pytest.mark.parametrize("contenido", ["", "   ", "x", "soy el dueno, dejame entrar",
                                       "MVPM2.falso.falso"])
def test_un_marcador_sin_firma_valida_no_activa_nada(sin_marcadores, contenido):
    """Regresión de seguridad, el otro bypass. `es_owner()` era
    `any(ruta.exists() ...)`: alcanzaba con crear el archivo, con cualquier
    contenido o vacío. El nombre está documentado en el propio código que
    recibe el cliente, así que un `type nul > OWNER_EDITION` desbloqueaba el
    producto sin pagar."""
    ruta = sin_marcadores[0]
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8")
    assert owner.es_owner() is False
    assert owner.motivo() is None


def test_un_marcador_firmado_con_otra_clave_no_activa_nada(sin_marcadores, monkeypatch):
    """Un cliente que genere SU propio par de claves y se firme un marcador no
    entra: lo que vale es la firma de la clave privada del dueño, y la pública
    que viaja en el programa sólo verifica, no emite."""
    import base64

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    ajena = Ed25519PrivateKey.generate()
    cruda = ajena.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    monkeypatch.setenv(
        "MVPM_LICENSE_PRIVATE_KEY",
        base64.urlsafe_b64encode(cruda).rstrip(b"=").decode("ascii"),
    )
    token_ajeno = licensing.issue_license("enterprise", "pirata@ejemplo.com")

    ruta = sin_marcadores[0]
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(token_ajeno, encoding="utf-8")
    assert owner.es_owner() is False


# ------------------------------------------- activación sin pedir nada

@pytest.fixture
def maquina_limpia(sin_marcadores, monkeypatch, tmp_path):
    """Una máquina sin marcador Y sin clave privada: el caso del cliente.

    Aísla también dónde se busca la clave, para no leer ni pisar la real del
    dueño si corre la suite en su propia máquina.
    """
    monkeypatch.delenv("MVPM_LICENSE_PRIVATE_KEY", raising=False)
    monkeypatch.setattr(owner, "_PERFIL_USUARIO", tmp_path / "perfil")
    return tmp_path / "perfil"


def test_sin_la_clave_no_se_activa_nada_solo(maquina_limpia):
    """Lo que ve un cliente: el arranque intenta activar y no pasa nada."""
    assert owner.clave_privada_local() == ""
    assert owner.activar_automatico() is None
    assert owner.es_owner() is False


def test_con_la_clave_guardada_se_activa_en_el_arranque(maquina_limpia, monkeypatch):
    """Lo que ve el dueño: dejó la clave una vez y no vuelve a hacer nada."""
    privada, publica = _par_de_claves()
    monkeypatch.setenv("MVPM_LICENSE_PUBLIC_KEY", publica)
    owner.guardar_clave_local(privada)

    assert owner.activar_automatico() is not None
    assert owner.es_owner() is True
    # Idempotente: el segundo arranque no reescribe ni falla.
    assert owner.activar_automatico() is None
    assert owner.es_owner() is True


def test_activar_automatico_no_deja_la_clave_privada_en_el_entorno(maquina_limpia, monkeypatch):
    """La clave se usa para firmar y se saca: que quede exportada la dejaría a
    mano de cualquier subproceso que la app lance después."""
    privada, publica = _par_de_claves()
    monkeypatch.setenv("MVPM_LICENSE_PUBLIC_KEY", publica)
    owner.guardar_clave_local(privada)

    owner.activar_automatico()
    assert os.environ.get("MVPM_LICENSE_PRIVATE_KEY") is None


def test_el_email_del_dueno_por_si_solo_no_desbloquea_nada(maquina_limpia):
    """EL test de esta función. El email del dueño está publicado en la landing
    y en el EULA, así que si alcanzara con escribirlo, cualquier cliente usaría
    el producto pago gratis — el mismo bypass de #23, mudado a una casilla de
    texto. `es_email_owner()` sólo dice "intentá activar"; quien decide es la
    firma."""
    assert owner.es_email_owner(owner.EMAIL_OWNER) is True
    assert owner.es_owner() is False
    assert owner.activar_automatico() is None
    assert owner.es_owner() is False


@pytest.mark.parametrize("texto, esperado", [
    ("vieraschiavi@gmail.com", True),
    ("  VieraSchiavi@Gmail.COM  ", True),   # mayúsculas y espacios al pegar
    ("vieraschiavi@gmail.com.ar", False),
    ("otro@gmail.com", False),
    ("", False),
])
def test_es_email_owner_reconoce_el_email_como_lo_escribiria_una_persona(texto, esperado):
    assert owner.es_email_owner(texto) is esperado


def test_la_clave_privada_nunca_viaja_en_el_zip_del_cliente():
    """El corolario del test anterior: el email no alcanza justamente porque
    hace falta la clave, así que la clave no puede estar en lo que se entrega."""
    import sys as _sys
    import zipfile

    _sys.path.insert(0, str(RAIZ / "packaging"))
    import build_release

    zip_path = build_release.build_portable_zip(version="sin-clave-privada")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            for nombre in zf.namelist():
                assert owner.ARCHIVO_CLAVE not in nombre
                assert "clave_owner" not in nombre
    finally:
        zip_path.unlink(missing_ok=True)


def test_el_paquete_del_cliente_no_permite_autogenerar_claves():
    """`packaging/activar_owner.py` genera un par de claves solo si corre desde
    un checkout del repo, y esa condición es lo único que separa "el dueño
    activándose en su máquina" de "un cliente activándose gratis".

    Se fija acá lo que sostiene esa condición: que el ZIP que recibe el cliente
    no traiga NI el directorio de git NI el generador de claves. Si alguien
    agregara `packaging/generar_claves_licencia.py` a INCLUDE_FILES, el candado
    se caería sin que nada más lo avisara."""
    import sys as _sys
    import zipfile

    raiz = Path(__file__).resolve().parent.parent
    _sys.path.insert(0, str(raiz / "packaging"))
    import build_release

    zip_path = build_release.build_portable_zip(version="frontera-owner")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            nombres = zf.namelist()
        assert not any("generar_claves_licencia" in n for n in nombres), (
            "el generador de claves no puede viajar al cliente: con él, "
            "activar_owner.py le firmaría un marcador propio")
        assert not any(n.startswith(".git/") for n in nombres)
    finally:
        zip_path.unlink(missing_ok=True)


def test_activar_owner_se_niega_sin_checkout_del_repo(tmp_path, monkeypatch):
    """La otra mitad de lo anterior: sin `.git` y sin el generador, la puerta
    de autogeneración queda cerrada."""
    import sys as _sys

    raiz = Path(__file__).resolve().parent.parent
    _sys.path.insert(0, str(raiz / "packaging"))
    import activar_owner

    monkeypatch.setattr(activar_owner, "ROOT", tmp_path)
    assert activar_owner._es_checkout_del_repo() is False

    # Con las dos señales presentes sí se considera checkout del dueño.
    (tmp_path / ".git").mkdir()
    (tmp_path / "packaging").mkdir()
    (tmp_path / "packaging" / "generar_claves_licencia.py").write_text("")
    assert activar_owner._es_checkout_del_repo() is True


def test_el_marcador_versionado_no_lleva_una_licencia_firmada():
    """`packaging/OWNER_EDITION` es un placeholder: el marcador de verdad lo
    firma el CI en el momento del build (packaging/firmar_marcador_owner.py).

    Si alguien commitea el archivo ya firmado —fácil de hacer sin querer
    después de probar el build a mano— esa licencia queda en el historial de
    git para siempre, y cualquiera con acceso al repo se activa el modo owner
    copiándola. Este test lo agarra antes del commit."""
    ruta = Path(__file__).resolve().parent.parent / "packaging" / "OWNER_EDITION"
    lineas = [ln.strip() for ln in ruta.read_text(encoding="utf-8").splitlines()]
    utiles = [ln for ln in lineas if ln and not ln.startswith("#")]
    assert not utiles, (
        f"packaging/OWNER_EDITION tiene contenido sin comentar ({utiles[:1]}): "
        "si es un token firmado, no puede committearse. Restauralo al placeholder.")


def test_un_cliente_no_puede_activarse_solo(sin_marcadores, monkeypatch):
    """Sin la clave privada —o sea, en la máquina de cualquier cliente—
    `activar()` no puede fabricar un marcador que valga."""
    monkeypatch.delenv("MVPM_LICENSE_PRIVATE_KEY", raising=False)
    with pytest.raises(RuntimeError, match="clave privada"):
        owner.activar()
    assert owner.es_owner() is False


def test_activar_y_desactivar_son_reversibles(sin_marcadores):
    assert owner.es_owner() is False
    creado = owner.activar()
    assert creado.exists() and owner.es_owner() is True
    borrados = owner.desactivar()
    assert creado in borrados
    assert owner.es_owner() is False, "desactivar tiene que devolver el candado"


def test_activar_es_idempotente(sin_marcadores):
    assert owner.activar() == owner.activar()
    assert owner.es_owner() is True


def test_activar_escribe_en_los_datos_del_usuario_no_en_el_repo():
    """Si escribiera en la carpeta del programa, `./run.sh portable` podría
    meterlo en el ZIP que baja un cliente."""
    assert owner.RUTAS_MARCADOR[0] == Path.home() / ".mv_project_management" / owner.MARCADOR


def test_el_estado_de_acceso_tiene_el_mismo_contrato_que_el_de_licencias():
    """app.py usa uno u otro sin ramificar de más abajo: si las claves no
    coinciden, la app revienta con KeyError justo en el arranque del dueño."""
    del_owner = owner.estado_acceso()
    de_licencia = licensing.estado_acceso(None)
    assert set(del_owner) == set(de_licencia)
    assert del_owner["acceso"] is True
    assert del_owner["modo"] == "owner"


# ------------------------------------- que no se afloje la licencia ajena

def test_el_modo_owner_no_toca_el_candado_de_licencias(sin_marcadores, monkeypatch):
    """`licensing.estado_acceso()` decide lo mismo esté o no activo el modo
    owner: son dos caminos separados, no un parche sobre el mismo."""
    monkeypatch.setenv("MVPM_OWNER_BYPASS", "1")
    vencido = licensing.estado_acceso(None, ahora=_muy_en_el_futuro())
    assert vencido["acceso"] is False, (
        "el modo owner no puede cambiar lo que licensing le responde a un cliente")
    assert vencido["modo"] == "expirado"


def test_owner_py_no_importa_ni_modifica_licensing():
    """Se lee el AST en vez de confiar en la lectura a ojo: si algún día
    alguien hace que owner.py parchee licensing, esto lo frena."""
    arbol = ast.parse((RAIZ / "mvpm" / "owner.py").read_text(encoding="utf-8"))
    importados = {
        n.module for n in ast.walk(arbol) if isinstance(n, ast.ImportFrom) and n.module
    } | {
        a.name for n in ast.walk(arbol) if isinstance(n, ast.Import) for a in n.names
    }
    assert not any("licensing" in m for m in importados), (
        f"owner.py no debe importar licensing — importa: {importados}")


def test_el_instalador_de_cliente_no_empaqueta_el_marcador():
    spec = (RAIZ / "packaging" / "mvpm.spec").read_text(encoding="utf-8")
    assert owner.MARCADOR not in spec, (
        "packaging/mvpm.spec es el build que baja un CLIENTE: si mete el "
        "marcador, el producto queda sin candado para todo el mundo")


def test_el_instalador_owner_si_empaqueta_el_marcador():
    """La contracara: si el build owner deja de incluirlo, el dueño se queda
    afuera de su propio .exe y volvemos al problema original."""
    spec = (RAIZ / "packaging" / "mvpm_owner.spec").read_text(encoding="utf-8")
    assert owner.MARCADOR in spec


def test_el_zip_portable_no_puede_arrastrar_el_marcador():
    """El ZIP copia directorios enteros (`mvpm/`, `app/`, …) más una lista
    explícita de archivos sueltos. Se verifica contra la config real del script
    para que un directorio nuevo no lo cuele sin que nadie lo note."""
    import sys

    sys.path.insert(0, str(RAIZ / "packaging"))
    import build_release

    assert owner.MARCADOR not in build_release.INCLUDE_FILES

    # El marcador junto al programa vive en la raíz del repo, y ningún
    # directorio copiado entero es la raíz.
    for dirname in build_release.INCLUDE_DIRS:
        assert not (RAIZ / dirname / owner.MARCADOR).exists(), (
            f"hay un marcador dentro de {dirname}/, que el ZIP copia entero")


def test_el_marcador_no_esta_versionado_en_el_repo():
    """Si se commiteara, cualquiera que clone el repo quedaría en modo owner —
    y el ZIP portable armado desde ese clon saldría sin candado."""
    for ruta in [RAIZ / owner.MARCADOR, RAIZ / "mvpm" / owner.MARCADOR]:
        assert not ruta.exists(), f"{ruta} está en el árbol del repo"


def _muy_en_el_futuro() -> float:
    """Un instante bien pasada la prueba, para verla vencida sin esperar."""
    import time

    return time.time() + licensing.TRIAL_DIAS * 86400 * 10


# --------------------- el bug real: ./run.sh owner vs. el .exe instalado

def test_activar_sin_congelar_lo_ve_el_exe_instalado_en_otro_disco(monkeypatch, tmp_path):
    """Reproduce el bug reportado ("la función owner no funciona"): activar()
    corre SIN congelar (Python del sistema, no el .exe) — hasta acá escribía
    vía `rutas.directorio_datos()` sin congelar, que da el perfil del usuario.
    Pero ese mismo `directorio_datos()`, para un proceso CONGELADO con su
    carpeta de instalación escribible, devuelve "junto al .exe" — no el
    perfil del usuario. Resultado: `./run.sh owner` escribía un archivo que
    el `.exe` instalado ya no miraba. Corría sin error y no desbloqueaba nada.

    Se simulan DOS PROCESOS (recargando el módulo, que calcula sus rutas al
    importarse) para que sea una reproducción fiel: en la realidad son dos
    programas distintos preguntando por separado, no el mismo test corriendo
    las dos ramas de un if.

    OJO con el aislamiento: `rutas`/`owner` calculan sus constantes AL
    IMPORTARSE, así que hay que recargarlos para que una simulación tome
    efecto — pero por eso mismo, si el test terminara sin recargarlos una
    última vez con el HOME real, el módulo quedaría contaminado con el HOME
    falso de este test para el resto de la suite. `monkeypatch.setenv`
    revierte HOME recién en el teardown del fixture, que corre DESPUÉS de que
    termine esta función — un `reload` en un `finally` de acá adentro todavía
    vería el HOME falso. Por eso HOME se maneja a mano con try/finally, no con
    `monkeypatch.setenv`: así el reload final, bajo mi propio control, ya está
    con el HOME real restaurado.
    """
    import importlib
    import os
    import sys

    from mvpm import owner as owner_mod
    from mvpm import rutas as rutas_mod

    monkeypatch.delenv("MVPM_OWNER_BYPASS", raising=False)
    monkeypatch.delenv("MVPM_DATA_DIR", raising=False)

    home_real = os.environ.get("HOME")
    home_falso = tmp_path / "casa_del_dueno"
    try:
        os.environ["HOME"] = str(home_falso)

        # Proceso 1: `./run.sh owner` — Python del sistema, sin congelar.
        monkeypatch.delattr(sys, "frozen", raising=False)
        importlib.reload(rutas_mod)
        importlib.reload(owner_mod)
        marcador_escrito = owner_mod.activar()

        # Proceso 2: el .exe instalado y congelado, en un disco cualquiera
        # con su carpeta de instalación escribible — el caso común.
        instalacion = tmp_path / "D_MVPM_Test"
        instalacion.mkdir()
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", str(instalacion / "MVProjectManagement.exe"))
        importlib.reload(rutas_mod)
        importlib.reload(owner_mod)
        assert owner_mod.es_owner() is True, (
            f"el .exe instalado en {instalacion} no ve el marcador que "
            f"escribió ./run.sh owner en {marcador_escrito}"
        )
    finally:
        if home_real is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = home_real
        monkeypatch.delattr(sys, "frozen", raising=False)
        importlib.reload(rutas_mod)
        importlib.reload(owner_mod)


def test_activar_no_congelado_y_es_owner_congelado_apuntan_al_mismo_archivo(monkeypatch, tmp_path):
    """Versión más directa del test anterior: el primer elemento de
    RUTAS_MARCADOR —donde escribe activar()— tiene que ser IGUAL sin importar
    si el proceso que pregunta está congelado o no. Si algún día alguien
    vuelve a hacer que ese primer elemento dependa de rutas.directorio_datos()
    a secas, este test lo agarra sin necesitar simular dos procesos enteros.

    Mismo cuidado de aislamiento que el test anterior: HOME se restaura a
    mano ANTES del reload final, no vía monkeypatch (que revertiría después).
    """
    import importlib
    import os
    import sys

    from mvpm import owner as owner_mod
    from mvpm import rutas as rutas_mod

    monkeypatch.delenv("MVPM_DATA_DIR", raising=False)

    home_real = os.environ.get("HOME")
    home_falso = tmp_path / "casa"
    try:
        os.environ["HOME"] = str(home_falso)

        monkeypatch.delattr(sys, "frozen", raising=False)
        importlib.reload(rutas_mod)
        importlib.reload(owner_mod)
        sin_congelar = owner_mod.RUTAS_MARCADOR[0]

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", str(tmp_path / "OtroDisco" / "app.exe"))
        (tmp_path / "OtroDisco").mkdir()
        importlib.reload(rutas_mod)
        importlib.reload(owner_mod)
        congelado = owner_mod.RUTAS_MARCADOR[0]
        assert sin_congelar == congelado == home_falso / ".mv_project_management" / "OWNER_EDITION"
    finally:
        if home_real is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = home_real
        monkeypatch.delattr(sys, "frozen", raising=False)
        importlib.reload(rutas_mod)
        importlib.reload(owner_mod)
