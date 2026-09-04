# © 2026 Martín Viera. Todos los derechos reservados.
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
import re
from pathlib import Path

import pytest

from mvpm import licensing, owner

RAIZ = Path(__file__).resolve().parent.parent

#: El único build de instaladores. Arma las dos ediciones —cliente y dueño—
#: como jobs de una matriz, así que preguntar "¿el build del dueño publica en
#: Vercel Blob?" es leer los pasos que corren para ESA edición, no el archivo
#: entero: buscar la palabra en todo el archivo diría que sí, porque el paso
#: del cliente está ahí al lado.
BUILD = "build_electron.yml"
_EDICIONES = ("cliente", "owner")


def _pasos_de_la_edicion(edicion: str) -> str:
    """Las líneas del workflow que SÍ ejecuta esa edición, sin comentarios.

    Se descartan los pasos condicionados a otra edición (`if: matrix.edicion ==
    '...'`) y los comentarios, que hablan de Vercel Blob justamente para
    explicar por qué el dueño NO va ahí — buscar la palabra suelta daría un
    falso positivo eterno.

    Sin parsear YAML a propósito: pyyaml no está en requirements.txt.
    """
    texto = (RAIZ / ".github" / "workflows" / BUILD).read_text(encoding="utf-8")
    otras = [e for e in _EDICIONES if e != edicion]
    sin_comentarios = [ln for ln in texto.splitlines()
                       if not ln.lstrip().startswith("#")]

    bloques, actual = [], []
    for linea in sin_comentarios:
        if linea.startswith("      - "):
            if actual:
                bloques.append(actual)
            actual = [linea]
        elif actual:
            actual.append(linea)
    if actual:
        bloques.append(actual)

    propios = []
    for bloque in bloques:
        cond = next((ln for ln in bloque if ln.strip().startswith("if:")), "")
        if any(f"'{o}'" in cond for o in otras):
            continue
        propios.extend(bloque)
    return "\n".join(propios)


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
    # El id de máquina también va a tmp: por el mismo motivo que los marcadores,
    # y además porque varios tests simulan "otra computadora" cambiándolo.
    monkeypatch.setattr(licensing, "_RUTA_MAQUINA", tmp_path / "maquina_id")
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
    """Uno vive en los datos del usuario (lo escribe `./run.sh owner`) y el otro
    junto al programa, si se activó ahí. El token va atado a esta máquina, que
    es como los emite `owner.activar()`."""
    ruta = sin_marcadores[indice]
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        licensing.issue_license("enterprise", "dueno@ejemplo.com",
                                extra={"maquina": licensing.huella_maquina()}),
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


# ------------------------------------- el marcador está atado a una máquina

def _otra_computadora(monkeypatch, tmp_path):
    """Simula que el mismo archivo de marcador aparece en OTRA máquina: cambia
    de dónde sale el id, que es lo único que distingue una computadora de otra."""
    monkeypatch.setattr(licensing, "_RUTA_MAQUINA", tmp_path / "otra" / "maquina_id")


def test_el_marcador_no_sirve_en_otra_computadora(maquina_limpia, monkeypatch, tmp_path):
    """EL test de esta historia, del lado del código.

    El marcador del dueño estuvo versionado en un repo público y desbloqueaba
    cualquier máquina donde se lo copiara. Ahora se emite atado a la máquina que
    lo creó: el mismo archivo, con la misma firma impecable, no vale en otra.
    """
    privada, publica = _par_de_claves()
    monkeypatch.setenv("MVPM_LICENSE_PUBLIC_KEY", publica)
    owner.guardar_clave_local(privada)

    assert owner.activar_automatico() is not None
    assert owner.es_owner() is True
    robado = owner.RUTAS_MARCADOR[0].read_text(encoding="utf-8")

    # Mismo archivo, otra computadora. La firma sigue siendo válida.
    _otra_computadora(monkeypatch, tmp_path)
    token = owner._token_del_marcador(owner.RUTAS_MARCADOR[0])
    assert licensing.verify_license(token) is not None, "la firma tendría que seguir siendo buena"
    assert owner.es_owner() is False, "un marcador copiado desbloqueó otra máquina"
    assert robado  # el contenido no cambió: lo que cambió es dónde se lo lee


def test_el_marcador_robado_tampoco_sirve_pegado_como_licencia(
        maquina_limpia, monkeypatch, tmp_path):
    """La segunda puerta, que es la que casi se pasa por alto: el token del
    marcador es una licencia `enterprise` válida. De nada serviría bloquear el
    modo dueño si el mismo texto, pegado en el campo de licencia de la app,
    diera el producto pago igual."""
    privada, publica = _par_de_claves()
    monkeypatch.setenv("MVPM_LICENSE_PUBLIC_KEY", publica)
    owner.guardar_clave_local(privada)
    owner.activar_automatico()
    token = owner._token_del_marcador(owner.RUTAS_MARCADOR[0])

    assert licensing.estado_acceso(token)["modo"] == "licencia"  # en SU máquina, sí
    _otra_computadora(monkeypatch, tmp_path)
    assert licensing.estado_acceso(token)["modo"] != "licencia"


def test_un_marcador_sin_atar_se_rechaza(maquina_limpia, monkeypatch):
    """Los marcadores viejos —incluido el que quedó publicado— no llevan el
    campo `maquina`. Se rechazan de plano, que es lo que mata de una a todas las
    copias que ya estén dando vueltas."""
    privada, publica = _par_de_claves()
    monkeypatch.setenv("MVPM_LICENSE_PUBLIC_KEY", publica)
    monkeypatch.setenv("MVPM_LICENSE_PRIVATE_KEY", privada)

    viejo = licensing.issue_license("enterprise", owner.EMAIL_OWNER)  # sin extra
    assert licensing.verify_license(viejo) is not None
    ruta = owner.RUTAS_MARCADOR[0]
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(owner._TEXTO_MARCADOR.format(token=viejo), encoding="utf-8")

    assert owner.es_owner() is False


def test_la_licencia_que_se_vende_no_se_ata_a_ninguna_maquina(
        maquina_limpia, monkeypatch, tmp_path):
    """El contrapeso, y es tan importante como lo anterior: al cliente que paga
    NO se le ata la licencia. Tiene que poder cambiar de computadora, reinstalar
    Windows o trabajar en dos máquinas sin quedarse afuera de lo que compró.
    Sólo se ata el marcador del dueño."""
    privada, publica = _par_de_claves()
    monkeypatch.setenv("MVPM_LICENSE_PUBLIC_KEY", publica)
    monkeypatch.setenv("MVPM_LICENSE_PRIVATE_KEY", privada)

    comprada = licensing.issue_license("professional", "cliente@empresa.com",
                                       payment_id="mp-123")
    assert licensing.estado_acceso(comprada)["modo"] == "licencia"
    _otra_computadora(monkeypatch, tmp_path)
    assert licensing.estado_acceso(comprada)["modo"] == "licencia"


def test_el_id_de_maquina_no_cambia_entre_arranques(maquina_limpia):
    """Si cambiara, el dueño perdería el modo owner cada vez que abre el
    programa. Por eso es un número al azar guardado en disco y no una huella de
    hardware, que se rompe sola al cambiar la placa de red o el nombre del equipo."""
    primero = licensing.huella_maquina()
    assert primero
    assert licensing.huella_maquina() == primero
    assert licensing._RUTA_MAQUINA.read_text(encoding="utf-8").strip() == primero


def test_dos_maquinas_distintas_dan_ids_distintos(maquina_limpia, monkeypatch, tmp_path):
    """Lo único que este id tiene que garantizar. No identifica la computadora
    —no es el MAC ni el hostname—: sólo tiene que no repetirse."""
    una = licensing.huella_maquina()
    _otra_computadora(monkeypatch, tmp_path)
    assert licensing.huella_maquina() != una


def test_sin_poder_escribir_el_id_no_se_activa_nada(maquina_limpia, monkeypatch):
    """Se falla cerrado. Si no se puede identificar la máquina, un marcador
    valdría en todas — que es el agujero que esto vino a tapar."""
    monkeypatch.setattr(licensing, "huella_maquina", lambda: "")
    privada, publica = _par_de_claves()
    monkeypatch.setenv("MVPM_LICENSE_PUBLIC_KEY", publica)
    monkeypatch.setenv("MVPM_LICENSE_PRIVATE_KEY", privada)

    with pytest.raises(RuntimeError, match="atar"):
        owner.activar()
    assert owner.es_owner() is False


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
    ejecutable = _pasos_de_la_edicion("owner").lower()

    assert "publish_blob" not in ejecutable
    assert "blob_read_write_token" not in ejecutable
    assert "@vercel/blob" not in ejecutable


def test_la_carpeta_instalador_no_viaja_en_el_paquete_del_cliente():
    """INSTALADOR/OWNER/ tiene el .exe que desbloquea el producto entero. Si
    `INSTALADOR` entrara en INCLUDE_DIRS, ese ejecutable saldría adentro del ZIP
    que se publica en la landing — o sea, regalado."""
    import sys as _sys

    _sys.path.insert(0, str(RAIZ / "packaging"))
    import build_release

    assert "INSTALADOR" not in build_release.INCLUDE_DIRS
    assert not any("INSTALADOR" in f for f in build_release.INCLUDE_FILES)


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
    workflow = (RAIZ / ".github" / "workflows" / BUILD).read_text(encoding="utf-8")
    assert "prerelease: ${{ matrix.edicion == 'owner' }}" in workflow, (
        "el Release del dueño dejó de marcarse como prerelease: pasa a ser el "
        "'Latest' que ve cualquiera con acceso al repositorio")


def test_ningun_build_mete_un_marcador_adentro_del_exe():
    """El `.exe` de la Owner Edition llevaba adentro un marcador firmado, y se
    publica como Release de un repo público: era una licencia enterprise para
    quien lo bajara. Además ya no podría funcionar —el marcador va atado a una
    máquina y el CI no sabe cuál es la del dueño—, así que reponerlo daría un
    .exe que dice "Owner Edition" y se comporta como el de cliente."""
    spec = (RAIZ / "packaging" / "mvpm.spec").read_text(encoding="utf-8")
    lineas_datas = [ln for ln in spec.splitlines()
                    if owner.MARCADOR in ln and not ln.lstrip().startswith("#")]
    assert not lineas_datas, f"mvpm.spec vuelve a empaquetar el marcador: {lineas_datas}"

    assert "MVPM_LICENSE_PRIVATE_KEY" not in _pasos_de_la_edicion("owner"), (
        "el build owner volvió a recibir la clave privada: no tiene nada que firmar")


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


#: Archivos que por su tamaño o su tipo no pueden contener un token pegado a
#: mano y que costaría minutos escanear en cada corrida.
_NO_ESCANEAR = {".exe", ".zip", ".png", ".jpg", ".jpeg", ".ico", ".mp4", ".pdf",
                ".woff", ".woff2", ".ttf"}

#: Un token es MVPM2.<payload>.<firma>, todo en base64url.
_PATRON_TOKEN = re.compile(r"MVPM2\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")


def _archivos_con_licencia_valida(archivos: list[Path]) -> list[Path]:
    """Cuáles de estos archivos contienen algo que `verify_license()` acepta."""
    culpables = []
    for ruta in archivos:
        if ruta.suffix.lower() in _NO_ESCANEAR or not ruta.is_file():
            continue
        try:
            texto = ruta.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(licensing.verify_license(c) is not None
               for c in _PATRON_TOKEN.findall(texto)):
            culpables.append(ruta)
    return culpables


def test_el_escaner_de_licencias_encuentra_una_de_verdad(tmp_path, monkeypatch):
    """Que el escáner de abajo sirva para algo.

    Sin esto sería un test que recorre 300 archivos, no encuentra nada y da
    verde — y daría exactamente lo mismo si el patrón estuviera mal escrito o si
    `verify_license()` devolviera None siempre. Se planta una licencia firmada
    de verdad (con un par efímero) y se exige que la encuentre.
    """
    privada, publica = _par_de_claves()
    monkeypatch.setenv("MVPM_LICENSE_PUBLIC_KEY", publica)
    monkeypatch.setenv("MVPM_LICENSE_PRIVATE_KEY", privada)
    token = licensing.issue_license("enterprise", "dueno@ejemplo.com")

    plantado = tmp_path / "cualquier_nombre.txt"
    plantado.write_text(f"# nota suelta\n{token}\n# fin\n", encoding="utf-8")
    limpio = tmp_path / "limpio.txt"
    limpio.write_text("MVPM2.esto-no.es-un-token\n", encoding="utf-8")

    assert _archivos_con_licencia_valida([plantado, limpio]) == [plantado]


def test_ningun_archivo_versionado_es_una_licencia_valida(monkeypatch):
    """EL test de esta historia. Ningún archivo del repo puede contener algo que
    `verify_license()` acepte.

    Acá vivía el test contrario. Decía, textual, que tener una licencia firmada
    versionada "es sostenible sólo porque el repo es privado". El repo es
    PÚBLICO, y lo fue todo el tiempo. Así que `packaging/OWNER_EDITION` —un
    token `enterprise` a nombre del dueño— estuvo descargable por cualquiera,
    sirviendo para las dos cosas a la vez: pegado en el campo de licencia daba
    `estado_acceso() -> modo "licencia"`, y copiado al perfil del usuario daba
    modo dueño.

    Por eso este test no comprueba una premisa (¿el repo es privado?) sino un
    hecho verificable acá adentro: que no haya un token válido en ningún lado.
    Un test que se apoya en una condición que no puede medir no protege nada —
    lo demostró el que reemplazó.

    Se escanea el contenido, no los nombres: el archivo podría llamarse
    cualquier cosa.
    """
    import subprocess

    # conftest.py inyecta un par de claves efímero por corrida y ése le gana a
    # la embebida. Acá interesa la EMBEBIDA: es la que trae la copia instalada,
    # y por lo tanto la única contra la que un token filtrado valdría de verdad.
    monkeypatch.delenv("MVPM_LICENSE_PUBLIC_KEY", raising=False)

    if not (RAIZ / ".git").exists():
        pytest.skip("no es un checkout del repo: no hay archivos versionados que revisar")

    salida = subprocess.run(
        ["git", "ls-files", "-z"], cwd=RAIZ, capture_output=True, text=True, check=True)
    archivos = [RAIZ / n for n in salida.stdout.split("\0") if n]
    assert archivos, "git ls-files no devolvió nada: el test no estaría revisando nada"

    culpables = [r.relative_to(RAIZ) for r in _archivos_con_licencia_valida(archivos)]
    assert not culpables, (
        f"Hay una licencia FIRMADA Y VÁLIDA versionada en: {culpables}.\n"
        "Este repositorio es público: eso es regalar el producto pago. Sacá el "
        "archivo, agregá su firma a licensing.FIRMAS_REVOCADAS (borrarlo no "
        "alcanza: queda en el historial y quien ya lo bajó lo tiene para "
        "siempre) y revisá qué lo generó.")


def test_el_token_que_se_filtro_ya_no_vale(monkeypatch):
    """El token que estuvo en `packaging/OWNER_EDITION`, contra la clave pública
    embebida. Sacarlo del repo no lo mata —el historial de git queda, y quien lo
    bajó lo tiene—; lo único que lo mata es que el programa lo rechace."""
    from mvpm import licensing

    monkeypatch.delenv("MVPM_LICENSE_PUBLIC_KEY", raising=False)

    filtrado = (
        "MVPM2.eyJwbGFuIjoiZW50ZXJwcmlzZSIsImVtYWlsIjoidmllcmFzY2hpYXZpQGdtYWlsLmNvbSIsInBheW1"
        "lbnRfaWQiOm51bGwsImlhdCI6MTc4NjEzMTEwMSwiY3Vwb19tZW5zdWFsX2lhIjpudWxsfQ.7toxxzkepMP3F"
        "1giHxrDlwsiHuSGItLuG56s3aRGOhhjoXElTc9zWP8WexWa8leXFbeYf4zG3m8C57GWlR_YDw")

    assert licensing.verify_license(filtrado) is None, "el token filtrado sigue validando"
    # Las dos puertas que abría, cerradas por separado.
    assert licensing.estado_acceso(filtrado)["modo"] != "licencia"
    assert filtrado.split(".")[2] in licensing.FIRMAS_REVOCADAS


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


def test_el_zip_del_dueno_tampoco_lleva_el_marcador():
    """Este ZIP está commiteado en un repo público, así que vale lo mismo que
    para el del cliente: adentro no puede haber nada firmado.

    Antes este test exigía lo CONTRARIO —que el marcador estuviera en la raíz
    del ZIP— porque el paquete venía ya activado. Eso es exactamente lo que
    hacía que bajarlo le diera el producto pago a cualquiera.

    Lo que hace distinto a este paquete ahora son herramientas, no credenciales:
    se comprueba en `test_el_zip_del_dueno_lleva_con_que_activar`.
    """
    import zipfile

    ruta = RAIZ / "owner" / "MV_Project_Management_OWNER.zip"
    if not ruta.exists():
        pytest.skip("owner/ no viaja en el paquete: es del repositorio")
    with zipfile.ZipFile(ruta) as zf:
        nombres = zf.namelist()
        assert owner.MARCADOR not in nombres
        assert not any(n.endswith("/" + owner.MARCADOR) for n in nombres)


def test_el_zip_del_dueno_lleva_con_que_activar():
    """Sin esto sería idéntico al del cliente y el dueño no tendría con qué
    activar su máquina — que es el único paso que hoy separa una cosa de la
    otra. Ninguno de estos archivos sirve sin la clave privada."""
    import sys as _sys
    import zipfile

    _sys.path.insert(0, str(RAIZ / "packaging"))
    import build_release

    ruta = RAIZ / "owner" / "MV_Project_Management_OWNER.zip"
    if not ruta.exists():
        pytest.skip("owner/ no viaja en el paquete: es del repositorio")
    with zipfile.ZipFile(ruta) as zf:
        nombres = set(zf.namelist())
    for extra in build_release.EXTRAS_OWNER:
        assert extra in nombres, f"el paquete del dueño salió sin {extra}"


def test_el_zip_del_dueno_esta_actualizado():
    """El paquete del dueño es un archivo commiteado: nada lo reconstruye solo
    cuando cambia el código. Es exactamente el problema que ya pasó con el ZIP
    público de la landing, que quedó congelado meses sin que nada lo avisara —
    con la diferencia de que acá el perjudicado es el dueño, que abriría una
    build vieja creyendo que tiene la última.

    Se compara contra lo que saldría del código actual, salvo los extras del
    dueño (que es lo único que este paquete agrega). Si falla:
    `python packaging/build_release.py --owner`.
    """
    import sys as _sys
    import zipfile

    _sys.path.insert(0, str(RAIZ / "packaging"))
    import build_release

    publico = RAIZ / "owner" / "MV_Project_Management_OWNER.zip"
    if not publico.exists():
        # En una copia extraída no hay `owner/`: este chequeo es del repo.
        pytest.skip("owner/ no viaja en el paquete: es del repositorio")

    fresco = build_release.build_portable_zip(version="freshness-owner")
    try:
        with zipfile.ZipFile(publico) as zf_pub, zipfile.ZipFile(fresco) as zf_new:
            # Los extras son lo único que este paquete suma; el resto tiene que
            # ser idéntico al portable armado con el código de hoy.
            nombres_pub = set(zf_pub.namelist()) - set(build_release.EXTRAS_OWNER)
            nombres_new = set(zf_new.namelist())
            faltan = sorted(nombres_new - nombres_pub)
            sobran = sorted(nombres_pub - nombres_new)
            assert not faltan and not sobran, (
                "owner/MV_Project_Management_OWNER.zip desactualizado — "
                f"faltan: {faltan[:10]}, sobran: {sobran[:10]}. Regenerar con "
                "`python packaging/build_release.py --owner`.")
            # mvpm/edicion.py difiere A PROPÓSITO: es la línea que marca este
            # paquete como el del dueño. Que sea distinta la fijan
            # test_el_zip_del_dueno_sale_desbloqueado y
            # test_el_zip_del_cliente_sale_con_el_candado_puesto.
            distintos = [n for n in nombres_new - {"mvpm/edicion.py"}
                         if zf_pub.read(n) != zf_new.read(n)]
            assert not distintos, (
                "owner/MV_Project_Management_OWNER.zip tiene contenido viejo en: "
                f"{distintos[:10]}. Regenerar con "
                "`python packaging/build_release.py --owner`.")
    finally:
        fresco.unlink(missing_ok=True)


def test_el_zip_del_dueno_no_se_publica_en_la_web():
    """La carpeta que se publica en la web es landing/, y ahí no puede
    aparecer: el paquete del dueño no es un producto que se venda."""
    if not (RAIZ / "landing").exists():
        pytest.skip("landing/ no viaja en el paquete: es del repositorio")
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


# ------------------------------------ la Owner Edition compilada (sin clave)

def test_el_repositorio_nunca_esta_marcado_como_owner():
    """EL test de este mecanismo, y el único que de verdad importa.

    `ES_OWNER_BUILD` se pone en True durante el build del dueño. Si esa línea se
    commitea en True —por un merge mal resuelto, por probar algo y olvidarse—,
    TODA copia del programa queda sin candado: el instalador de cliente, el ZIP
    de la landing y el repositorio. El producto pasa a ser gratis para todo el
    mundo y nada lo avisa, porque compila y funciona perfecto.

    Se lee el ARCHIVO, no el módulo importado: un test que mirara
    `edicion.ES_OWNER_BUILD` podría estar viendo un valor que otro test
    monkeypatcheó.
    """
    texto = (RAIZ / "mvpm" / "edicion.py").read_text(encoding="utf-8")
    assert "ES_OWNER_BUILD = False" in texto
    assert "ES_OWNER_BUILD = True" not in texto, (
        "mvpm/edicion.py quedó commiteado como Owner Edition: el programa sale "
        "sin candado para todo el mundo. Lo pone en True el build "
        "(packaging/marcar_build_owner.py), nunca el repositorio.")


def test_un_build_marcado_abre_sin_pedir_nada(sin_marcadores, monkeypatch):
    """Lo que el dueño pidió: instalar el .exe y que abra, sin clave, sin token
    y sin archivo al lado. Sin marcador de ningún tipo en la máquina."""
    from mvpm import edicion

    monkeypatch.setattr(edicion, "ES_OWNER_BUILD", True)
    assert owner.es_owner() is True
    assert owner.estado_acceso()["acceso"] is True
    assert "Owner Edition" in owner.motivo()


def test_sin_marcar_el_mismo_codigo_tiene_el_candado_puesto(sin_marcadores, monkeypatch):
    """La otra mitad: es la MISMA base de código. Lo único que separa al binario
    del dueño del de un cliente es esa constante."""
    from mvpm import edicion

    monkeypatch.setattr(edicion, "ES_OWNER_BUILD", False)
    assert owner.es_owner() is False
    assert owner.motivo() is None


def test_marcar_el_build_falla_si_no_encuentra_la_linea(tmp_path, monkeypatch):
    """Si el reemplazo no se hace y el build sigue, sale un .exe que dice "Owner
    Edition" y se comporta como el de un cliente, con prueba de 7 días. Es el
    modo de fallar más caro, porque no se nota hasta que el dueño instala."""
    import sys as _sys

    _sys.path.insert(0, str(RAIZ / "packaging"))
    import marcar_build_owner

    roto = tmp_path / "edicion.py"
    roto.write_text("ES_OWNER_BUILD=False  # sin espacios\n", encoding="utf-8")
    monkeypatch.setattr(marcar_build_owner, "ARCHIVO", roto)
    monkeypatch.setattr(marcar_build_owner, "ROOT", tmp_path)

    assert marcar_build_owner.main() == 1


def test_marcar_el_build_deja_la_constante_en_true(tmp_path, monkeypatch):
    import sys as _sys

    _sys.path.insert(0, str(RAIZ / "packaging"))
    import marcar_build_owner

    copia = tmp_path / "edicion.py"
    copia.write_text((RAIZ / "mvpm" / "edicion.py").read_text(encoding="utf-8"),
                     encoding="utf-8")
    monkeypatch.setattr(marcar_build_owner, "ARCHIVO", copia)
    monkeypatch.setattr(marcar_build_owner, "ROOT", tmp_path)

    assert marcar_build_owner.main() == 0
    assert "ES_OWNER_BUILD = True" in copia.read_text(encoding="utf-8")


def test_solo_el_build_del_dueno_marca_la_edicion():
    """Si el build de CLIENTE llamara a este script, el instalador que se publica
    en la web saldría desbloqueado."""
    assert "marcar_build_owner.py" in _pasos_de_la_edicion("owner"), (
        "la edición del dueño dejó de marcarse: saldría con el candado de cliente")
    assert "marcar_build_owner.py" not in _pasos_de_la_edicion("cliente"), (
        "el instalador que se publica en la web saldría DESBLOQUEADO")


def test_el_zip_del_cliente_sale_con_el_candado_puesto():
    """El ZIP que se publica en la landing. Los dos paquetes se arman con la
    misma función y difieren en esta línea: si el reemplazo se filtrara al
    portable, el producto sería gratis para cualquiera que lo baje."""
    import sys as _sys
    import zipfile

    _sys.path.insert(0, str(RAIZ / "packaging"))
    import build_release

    zip_path = build_release.build_portable_zip(version="candado")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            contenido = zf.read("mvpm/edicion.py").decode("utf-8")
        assert "ES_OWNER_BUILD = False" in contenido
        assert "ES_OWNER_BUILD = True" not in contenido
    finally:
        zip_path.unlink(missing_ok=True)


def test_el_zip_del_dueno_sale_desbloqueado():
    """Y el del dueño, al revés: se descomprime y abre, sin pegar nada."""
    import zipfile

    ruta = RAIZ / "owner" / "MV_Project_Management_OWNER.zip"
    if not ruta.exists():
        pytest.skip("owner/ no viaja en el paquete: es del repositorio")
    with zipfile.ZipFile(ruta) as zf:
        assert "ES_OWNER_BUILD = True" in zf.read("mvpm/edicion.py").decode("utf-8")


def test_marcar_el_zip_del_dueno_no_toca_el_arbol_de_trabajo(tmp_path):
    """El accidente que hay que hacer imposible: que armar el paquete del dueño
    deje `mvpm/edicion.py` en True en el repositorio. Commitear eso deja sin
    candado a todas las copias, incluida la del cliente.

    Va a `tmp_path` y no al destino real: la primera versión de este test
    llamaba a `build_owner_zip()` a secas, y como esa función escribe en un
    archivo VERSIONADO, cada corrida de la suite dejaba el repositorio sucio con
    un ZIP que sólo difería en los timestamps internos. El ruido en
    `git status` era lo de menos — lo feo era terminar commiteando un paquete
    armado desde un árbol a medio editar.
    """
    import sys as _sys

    _sys.path.insert(0, str(RAIZ / "packaging"))
    import build_release

    archivo = RAIZ / "mvpm" / "edicion.py"
    antes = archivo.read_text(encoding="utf-8")
    salida = build_release.build_owner_zip(version="no-toca-nada",
                                           destino=tmp_path / "owner.zip")
    assert salida == tmp_path / "owner.zip"
    assert archivo.read_text(encoding="utf-8") == antes
    assert "ES_OWNER_BUILD = False" in archivo.read_text(encoding="utf-8")


def _foto_del_arbol() -> dict[str, tuple[int, int]] | None:
    """(mtime, tamaño) de cada archivo versionado. None fuera de un checkout.

    Se mira el ARCHIVO y no `git status --porcelain`, que fue el primer intento y
    no servía: git reporta la misma línea ` M archivo.zip` lo haya modificado un
    test o lo hubiera dejado así el desarrollador antes de correr la suite. O
    sea que sobre un archivo YA sucio —el caso más probable, porque los ZIP se
    regeneran a mano— el test no veía nada nuevo y daba verde.

    mtime alcanza y es barato: no hay que leer contenido, así que el .exe de 98
    MB de INSTALADOR/ no cuesta nada. Un test que reescriba un archivo con el
    mismo contenido igual lo mueve, y también queremos enterarnos de eso.
    """
    import subprocess

    if not (RAIZ / ".git").exists():
        return None
    salida = subprocess.run(["git", "ls-files", "-z"], cwd=RAIZ,
                            capture_output=True, text=True, check=True)
    foto = {}
    for nombre in salida.stdout.split("\0"):
        if not nombre:
            continue
        try:
            st = (RAIZ / nombre).stat()
        except OSError:
            continue
        foto[nombre] = (st.st_mtime_ns, st.st_size)
    return foto


#: Foto del árbol ANTES de que corra un solo test. Se toma al importar el
#: módulo, y pytest importa todo durante la colección, o sea antes de ejecutar
#: nada.
#:
#: Comparar contra esta foto y no contra "el árbol tiene que estar limpio" es lo
#: que hace al test de abajo utilizable: quien corre la suite casi siempre tiene
#: trabajo sin commitear, y un test que se pone rojo por eso se aprende a
#: ignorar — que es lo mismo que no tenerlo.
_ARBOL_AL_EMPEZAR = _foto_del_arbol()


def test_la_suite_no_ensucia_el_repositorio():
    """Ningún test puede dejar cambios en archivos versionados.

    Los artefactos commiteados —los dos ZIP— se regeneran a propósito cuando
    cambia el código, no como efecto colateral de correr `pytest`. Ya pasó: un
    test de este mismo archivo llamaba a `build_owner_zip()` sin destino, y esa
    función escribe en `owner/MV_Project_Management_OWNER.zip`. Cada corrida
    dejaba un diff de timestamps que nadie había hecho, y lo feo no era el ruido
    en `git status` sino terminar commiteando un paquete armado desde un árbol a
    medio editar.

    Va último en el archivo para ver lo que dejaron los demás. `git status` mira
    el árbol entero, así que con la suite completa también agarra a los tests de
    los otros archivos.
    """
    ahora = _foto_del_arbol()
    if ahora is None or _ARBOL_AL_EMPEZAR is None:
        pytest.skip("no es un checkout del repo")

    tocados = sorted(n for n, v in ahora.items()
                     if n in _ARBOL_AL_EMPEZAR and v != _ARBOL_AL_EMPEZAR[n])
    assert not tocados, (
        "la suite modificó archivos versionados:\n  " + "\n  ".join(tocados) +
        "\nUn test que escribe en un archivo del repo tiene que escribir en "
        "tmp_path (ver build_owner_zip(destino=...)).")


# --------------------------------------- el instalador del paquete del dueño

def _instalador_owner() -> str:
    return (RAIZ / "INSTALAR_OWNER.bat").read_text(encoding="ascii")


def test_el_instalador_owner_no_desbloquea_una_copia_ajena():
    """Lo que este instalador NO es, y es lo que lo separa de un crack.

    Instala ESTE paquete, que ya viene con ES_OWNER_BUILD = True desde que se
    armó el ZIP. No toca ninguna otra instalación ni convierte una copia de
    cliente en la del dueño: una herramienta que hiciera eso funcionaría igual
    en la máquina de cualquier cliente, y ahí el candado deja de existir para
    todos. Sería el cuarto intento del mismo agujero, después de
    MVPM_OWNER_BYPASS, del marcador vacío y del marcador filtrado.
    """
    bat = _instalador_owner()
    # Copia desde donde está parado hacia el destino, y nada más.
    assert "robocopy" in bat
    for prohibido in ("edicion.json", "> mvpm\\edicion.py", "OWNER_EDITION"):
        assert prohibido not in bat, (
            f"INSTALAR_OWNER.bat escribe {prohibido}: eso desbloquearía copias ajenas")


def test_el_instalador_owner_se_niega_a_instalar_el_paquete_de_cliente():
    """Sin este corte, correrlo sobre el ZIP equivocado deja un programa que se
    llama "Owner" y se comporta como el de un cliente: prueba de 7 días
    incluida, icono en el escritorio y el instalador diciendo que todo salió
    bien. Es el modo de fallar que más tarda en notarse."""
    bat = _instalador_owner()
    assert 'findstr /C:"ES_OWNER_BUILD = True"' in bat
    # La cadena que busca tiene que ser EXACTAMENTE la que escribe el build; si
    # una de las dos cambia sola, el instalador rechaza el paquete correcto.
    import sys as _sys

    _sys.path.insert(0, str(RAIZ / "packaging"))
    import build_release

    assert 'ES_OWNER_BUILD = True' in (
        (RAIZ / "mvpm" / "edicion.py").read_text(encoding="utf-8").replace(
            "ES_OWNER_BUILD = False", "ES_OWNER_BUILD = True"))
    assert build_release.EXTRAS_OWNER  # el paquete del dueño existe como concepto


def test_el_instalador_owner_verifica_antes_de_dejar_el_icono():
    """Comprueba `owner.es_owner()` sobre la copia YA instalada antes de crear
    accesos directos. Un icono que abre un programa con candado es peor que no
    tener icono: parece que funcionó."""
    bat = _instalador_owner()
    assert "owner.es_owner()" in bat
    assert bat.index("owner.es_owner()") < bat.index("Creando accesos directos")


def test_el_instalador_owner_deja_desinstalador_y_no_borra_los_datos():
    """El desinstalador borra el programa, nunca la carpeta de datos: ahí está
    el portafolio del usuario."""
    bat = _instalador_owner()
    assert "DESINSTALAR.bat" in bat
    assert "rmdir /s /q" in bat
    assert ".mv_project_management" in bat, (
        "el desinstalador no aclara dónde quedan los datos")


def test_el_instalador_owner_no_viaja_en_el_paquete_del_cliente():
    """Si se colara en el ZIP de la landing, cualquiera que lo corriera...
    se encontraría con el corte del test de arriba. Igual no tiene nada que
    hacer ahí: es del paquete del dueño."""
    import sys as _sys
    import zipfile

    _sys.path.insert(0, str(RAIZ / "packaging"))
    import build_release

    zip_path = build_release.build_portable_zip(version="sin-instalador-owner")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            assert "INSTALAR_OWNER.bat" not in zf.namelist()
    finally:
        zip_path.unlink(missing_ok=True)
