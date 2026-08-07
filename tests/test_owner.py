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


# --------------------------------- por dónde sale el instalador del dueño

def test_el_instalador_owner_no_se_publica_en_ningun_canal_publico():
    """El .exe de la Owner Edition lleva un marcador FIRMADO adentro: quien lo
    tenga tiene el producto desbloqueado, sin pagar y sin tocar nada. O sea que
    el único control que queda es por dónde se distribuye.

    El instalador de cliente sí se sube a Vercel Blob, que es una URL pública
    permanente. Si alguna vez se copiara ese paso al workflow del dueño, el
    ejecutable que desbloquea todo quedaría colgado de una URL abierta.

    Se miran las líneas que el workflow EJECUTA, descartando comentarios: los
    comentarios hablan de Vercel Blob justamente para explicar por qué no se
    usa, así que buscar la palabra suelta daría un falso positivo eterno.

    Sin parsear YAML a propósito: pyyaml no está en requirements.txt y no vale
    la pena agregar una dependencia para esto.
    """
    lineas = (RAIZ / ".github" / "workflows" / "build_windows_owner.yml").read_text(
        encoding="utf-8").splitlines()
    ejecutable = "\n".join(
        linea for linea in lineas if not linea.lstrip().startswith("#")).lower()

    assert "publish_blob" not in ejecutable
    assert "blob_read_write_token" not in ejecutable
    assert "@vercel/blob" not in ejecutable


def test_el_instalador_owner_no_se_ofrece_desde_la_landing():
    """La landing es lo que ve cualquiera. El único instalador linkeado ahí
    tiene que ser el de cliente."""
    for html in (RAIZ / "landing").rglob("*.html"):
        texto = html.read_text(encoding="utf-8", errors="ignore").lower()
        assert "owner_setup" not in texto
        assert "mvprojectmanagementowner" not in texto


def test_el_release_del_dueno_no_queda_como_ultimo_release_del_repo():
    """`prerelease: true` evita que el Release del dueño sea el que GitHub
    muestra como "Latest" — el que vería primero cualquiera con acceso."""
    workflow = (RAIZ / ".github" / "workflows" / "build_windows_owner.yml").read_text(
        encoding="utf-8")
    assert "prerelease: true" in workflow


def test_el_build_owner_corta_si_falta_la_clave_privada():
    """Sin el secreto, compilar igual daría un .exe que dice "Owner Edition" y
    se comporta como el de un cliente: prueba de 7 días incluida."""
    script = (RAIZ / "packaging" / "firmar_marcador_owner.py").read_text(encoding="utf-8")
    assert 'if not os.environ.get("MVPM_LICENSE_PRIVATE_KEY", "").strip():' in script
    assert "return 1" in script


@pytest.mark.parametrize("caso, esperado_en_el_motivo", [
    ("email", "email"),
    ("con espacios", "espacios"),
    ("cortada", "cortada"),
    ("con relleno", "de más"),
    ("caracteres raros", "caracteres que la clave no usa"),
])
def test_lo_que_no_es_la_clave_se_rechaza_antes_de_guardarlo(caso, esperado_en_el_motivo):
    """El caso real que motivó esto: el dueño pegó su EMAIL en el prompt de la
    clave. Se aceptaba, se escribía en el perfil del usuario, y recién al
    fallar la firma se borraba — así que en pantalla leía "Clave guardada"
    seguido de "esa clave no sirve", que es el orden que hace pensar que se
    rompió algo. Ahora se avisa antes de tocar el disco, y diciendo QUÉ pegó.

    Los casos con forma de clave se derivan de un par GENERADO en el momento, no
    de una constante escrita acá. La versión anterior de este test usaba la
    clave privada real de producción como dato de prueba: quedó commiteada, y
    como `tests/` viaja en el ZIP portable, terminó publicada en el paquete que
    baja cualquier cliente desde la landing. Cualquiera podía sacarla de ahí y
    emitirse licencias. Nunca una clave de verdad en un test.
    """
    import sys as _sys

    _sys.path.insert(0, str(RAIZ / "packaging"))
    import activar_owner

    privada, _ = _par_de_claves()
    pegado = {
        "email": "alguien@ejemplo.com",
        "con espacios": "mi contraseña de siempre",
        "cortada": privada[:-1],
        "con relleno": privada + "=",
        "caracteres raros": "*" * 43,
    }[caso]

    motivo = activar_owner._por_que_no_parece_una_clave(pegado)
    assert motivo is not None, f"{pegado!r} no debería pasar la revisión de forma"
    assert esperado_en_el_motivo in motivo


def test_una_clave_de_verdad_pasa_la_revision_de_forma():
    """La revisión es de forma, no de validez: no puede rechazar una clave
    legítima. Se prueba con un par recién generado, no con una constante."""
    import sys as _sys

    _sys.path.insert(0, str(RAIZ / "packaging"))
    import activar_owner

    privada, _ = _par_de_claves()
    assert activar_owner._por_que_no_parece_una_clave(privada) is None


def test_ningun_archivo_del_repo_puede_firmar_licencias():
    """Regresión de la peor falla que tuvo este repo.

    Un test usó la clave privada REAL de producción como dato de prueba. Quedó
    commiteada en tests/test_owner.py y, como `tests/` viaja en el ZIP portable,
    terminó dentro del paquete que baja cualquier cliente desde la landing:
    bastaba abrir el archivo para sacar la clave con la que se firman TODAS las
    licencias del producto y emitirse una Enterprise.

    Ninguna búsqueda de texto lo hubiera agarrado —la clave es una cadena
    cualquiera— así que este test no la busca: prueba a FIRMAR. Recorre el
    árbol, junta todo lo que tenga forma de clave Ed25519 en base64url, y falla
    si alguna de esas cadenas produce un token que la clave pública embebida
    acepta. Es la única definición que importa: si sirve para firmar, no puede
    estar acá.
    """
    import re

    from mvpm import licensing

    candidatas = set()
    for ruta in RAIZ.rglob("*"):
        partes = ruta.relative_to(RAIZ).parts
        if not ruta.is_file() or {".git", ".venv", "dist", ".pytest_cache"} & set(partes):
            continue
        if ruta.suffix.lower() in {".zip", ".png", ".jpg", ".mp4", ".ico", ".pyd", ".so"}:
            continue
        try:
            texto = ruta.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        candidatas.update(re.findall(r"\b[A-Za-z0-9_-]{43}\b", texto))

    # Se firma directo con la primitiva, sin pasar por el entorno: interesa si
    # la cadena PUEDE firmar, no si está configurada como la clave activa.
    import base64
    import binascii

    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    publica = licensing._clave_publica()
    assert publica is not None, "sin clave pública embebida este test no prueba nada"

    for candidata in sorted(candidatas):
        try:
            cruda = base64.urlsafe_b64decode(candidata + "=")
            privada = Ed25519PrivateKey.from_private_bytes(cruda)
        except (ValueError, TypeError, binascii.Error):
            continue
        firma = privada.sign(b"prueba")
        try:
            publica.verify(firma, b"prueba")
        except InvalidSignature:
            continue
        raise AssertionError(
            "Hay una cadena en el repo que firma licencias válidas contra "
            "CLAVE_PUBLICA_EMBEBIDA. Es la clave privada de producción: sacala "
            "del árbol y ROTÁ el par, porque ya quedó en el historial de git.")


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


def test_el_marcador_versionado_esta_firmado_y_sirve(monkeypatch):
    """`packaging/OWNER_EDITION` lleva una licencia firmada, a propósito.

    Antes este test exigía lo contrario —que fuera un placeholder— porque la
    licencia iba a firmarse en el CI con un secreto. La decisión cambió: el
    marcador vive versionado, y por eso el build de la Owner Edition no
    necesita ningún secreto configurado y el ZIP del dueño se puede armar en
    cualquier máquina.

    Lo que se está aceptando con eso, explícito: la licencia queda en el
    historial de git para siempre, así que **cualquiera con acceso a este repo
    tiene el producto desbloqueado**. Es sostenible sólo porque el repo es
    privado — bajar el archivo ES el control de acceso, el mismo que protege al
    .exe de la Owner Edition, que lleva ese mismo marcador adentro. Si el repo
    se hiciera público, o se sumara alguien que no es el dueño, hay que rotar
    el par de claves y republicar.

    Lo que NO cambió, y está fijado en los tests de acá abajo: nada de esto
    llega a un artefacto de cliente.
    """
    from mvpm import licensing

    # conftest.py inyecta un par de claves efímero por corrida en las variables
    # de entorno, y ésas le ganan a la embebida. Acá interesa justamente la
    # embebida: es la que va a tener la copia que se instale.
    monkeypatch.delenv("MVPM_LICENSE_PUBLIC_KEY", raising=False)

    ruta = RAIZ / "packaging" / "OWNER_EDITION"
    token = owner._token_del_marcador(ruta)
    assert token, "packaging/OWNER_EDITION quedó sin token: el build saldría con candado"
    payload = licensing.verify_license(token)
    assert payload is not None, (
        "el token de packaging/OWNER_EDITION no valida contra "
        "CLAVE_PUBLICA_EMBEBIDA: son de pares de claves distintos")
    assert payload["plan"] in licensing.PLANES_PAGOS
    assert payload["email"] == owner.EMAIL_OWNER


def test_el_zip_del_cliente_no_lleva_el_marcador_ni_por_accidente():
    """El corolario de lo anterior, y el test que sostiene todo el esquema.

    El paquete del dueño y el del cliente se arman con la MISMA función; lo
    único que los diferencia es que al del dueño se le agrega el marcador
    después. Si `packaging/OWNER_EDITION` entrara en INCLUDE_FILES, o si
    alguien copiara el marcador a la raíz del repo, el ZIP que se publica en la
    web saldría sin candado y el producto sería gratis para todos."""
    import sys as _sys
    import zipfile

    _sys.path.insert(0, str(RAIZ / "packaging"))
    import build_release

    zip_path = build_release.build_portable_zip(version="sin-marcador")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            nombres = zf.namelist()
        assert owner.MARCADOR not in nombres
        assert not any(n.endswith("/" + owner.MARCADOR) for n in nombres)
    finally:
        zip_path.unlink(missing_ok=True)


def test_el_zip_del_dueno_si_lleva_el_marcador_y_en_la_raiz():
    """En la raíz y no en packaging/: `mvpm/owner.py` busca en la raíz del
    programa, así que en cualquier otro lado el ZIP del dueño saldría con el
    candado de cliente puesto sin que nada lo avise."""
    import zipfile

    ruta = RAIZ / "owner" / "MV_Project_Management_OWNER.zip"
    assert ruta.exists(), "falta el ZIP del dueño: python packaging/build_release.py --owner"
    with zipfile.ZipFile(ruta) as zf:
        assert owner.MARCADOR in zf.namelist()


def test_el_zip_del_dueno_esta_actualizado():
    """El paquete del dueño es un archivo commiteado: nada lo reconstruye solo
    cuando cambia el código. Es exactamente el problema que ya pasó con el ZIP
    público de la landing, que quedó congelado meses sin que nada lo avisara —
    con la diferencia de que acá el perjudicado es el dueño, que abriría una
    build vieja creyendo que tiene la última.

    Se compara contra lo que saldría del código actual, salvo el marcador (que
    es lo único que el paquete del dueño agrega). Si falla:
    `python packaging/build_release.py --owner`.
    """
    import sys as _sys
    import zipfile

    _sys.path.insert(0, str(RAIZ / "packaging"))
    import build_release

    publico = RAIZ / "owner" / "MV_Project_Management_OWNER.zip"
    assert publico.exists(), "falta owner/MV_Project_Management_OWNER.zip"

    fresco = build_release.build_portable_zip(version="freshness-owner")
    try:
        with zipfile.ZipFile(publico) as zf_pub, zipfile.ZipFile(fresco) as zf_new:
            # El marcador es lo único que este paquete suma; el resto tiene que
            # ser idéntico al portable armado con el código de hoy.
            nombres_pub = set(zf_pub.namelist()) - {owner.MARCADOR}
            nombres_new = set(zf_new.namelist())
            faltan = sorted(nombres_new - nombres_pub)
            sobran = sorted(nombres_pub - nombres_new)
            assert not faltan and not sobran, (
                "owner/MV_Project_Management_OWNER.zip desactualizado — "
                f"faltan: {faltan[:10]}, sobran: {sobran[:10]}. Regenerar con "
                "`python packaging/build_release.py --owner`.")
            distintos = [n for n in nombres_new if zf_pub.read(n) != zf_new.read(n)]
            assert not distintos, (
                "owner/MV_Project_Management_OWNER.zip tiene contenido viejo en: "
                f"{distintos[:10]}. Regenerar con "
                "`python packaging/build_release.py --owner`.")
    finally:
        fresco.unlink(missing_ok=True)


def test_el_zip_del_dueno_no_se_publica_en_la_web():
    """Vive en el repo privado. La carpeta que se publica es landing/, y ahí no
    puede aparecer."""
    publicados = list((RAIZ / "landing").rglob("*.zip"))
    for zip_publico in publicados:
        assert "OWNER" not in zip_publico.name.upper(), (
            f"{zip_publico} parece el paquete del dueño y está en landing/")


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
