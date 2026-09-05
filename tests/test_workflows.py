# © 2026 Martín Viera. Todos los derechos reservados.
"""Los workflows de CI, tratados como código que puede romperse en silencio.

Un workflow mal escrito no falla: simplemente no corre, o corre y no hace lo que
se esperaba. No hay pila de errores ni test en rojo — sólo un instalador que
quedó viejo o un PR que nunca se mergea. Por eso los invariantes que sostienen
la automatización se fijan acá.

No se parsea YAML a propósito: pyyaml no está en requirements.txt y no vale una
dependencia nueva para leer cinco archivos.
"""

from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
WORKFLOWS = RAIZ / ".github" / "workflows"

#: Lo que termina adentro del .exe, según `datas` en packaging/mvpm.spec:
#: app/ y mvpm/, más el launcher de packaging/.
#:
#: api/ NO está a propósito, y es el error que este test agarró: viaja en el
#: ZIP portable pero no en el instalador, así que un cambio ahí no tiene por
#: qué gastar minutos de runner de Windows. La frescura del ZIP la cubren los
#: tests de tests/test_owner.py y tests/test_core.py, que es donde importa.
RUTAS_DE_PRODUCTO = ("mvpm/", "app/", "packaging/", "requirements.txt")

#: Este archivo viaja en el ZIP portable (INCLUDE_DIRS incluye `tests/`), pero
#: `.github/workflows/` NO viaja: sólo existe en el repositorio. Sin este skip, el
#: usuario que abre el programa ve 12 tests fallando por archivos que su copia no tiene — el `.bat` corre la suite al
#: arrancar, así que es lo primero que aparece en pantalla.
if not WORKFLOWS.exists():
    pytest.skip(".github/workflows/ no viaja en el paquete: es del repositorio", allow_module_level=True)


def _texto(nombre: str) -> str:
    return (WORKFLOWS / nombre).read_text(encoding="utf-8")


def _sin_comentarios(nombre: str) -> str:
    """El workflow sin sus comentarios: los comentarios explican decisiones y
    nombran cosas que el archivo justamente NO hace, así que buscar texto suelto
    da falsos positivos."""
    return "\n".join(ln for ln in _texto(nombre).splitlines()
                     if not ln.lstrip().startswith("#"))


#: El único build de instaladores, y las dos ediciones que produce.
BUILD = "build_electron.yml"
EDICIONES = ("cliente", "owner")


def _pasos(nombre: str) -> list[tuple[str, str]]:
    """Los `steps:` del workflow como (condición, texto), sin comentarios.

    Existe porque las dos ediciones dejaron de ser dos archivos y pasaron a ser
    dos jobs de una matriz: preguntar "¿el build del dueño publica en Vercel
    Blob?" ya no es leer un archivo entero, es leer los pasos que corren para
    ESA edición. Buscar la palabra en el archivo completo daría que sí, porque
    el paso del cliente está en el mismo archivo.

    Sin parsear YAML a propósito: pyyaml no está en requirements.txt y no vale
    una dependencia nueva para leer cinco archivos.
    """
    texto = _sin_comentarios(nombre)
    cuerpo = texto[texto.index("\n    steps:"):]
    bloques, actual = [], []
    for linea in cuerpo.splitlines():
        if linea.startswith("      - "):
            if actual:
                bloques.append("\n".join(actual))
            actual = [linea]
        elif actual:
            actual.append(linea)
    if actual:
        bloques.append("\n".join(actual))

    salida = []
    for bloque in bloques:
        cond = ""
        for linea in bloque.splitlines():
            if linea.strip().startswith("if:"):
                cond = linea.split("if:", 1)[1].strip()
                break
        salida.append((cond, bloque))
    return salida


def _pasos_de(edicion: str) -> str:
    """Sólo lo que ESA edición ejecuta: los pasos sin condición (corren en las
    dos) más los condicionados a esta edición."""
    otras = [e for e in EDICIONES if e != edicion]
    partes = []
    for cond, bloque in _pasos(BUILD):
        if any(f"'{o}'" in cond for o in otras):
            continue
        partes.append(bloque)
    return "\n".join(partes)


# ------------------------------------------------ el merge automático

def test_el_automerge_solo_actua_con_los_tests_en_verde():
    """Lo único que separa "se mergea solo" de "se mergea cualquier cosa"."""
    wf = _sin_comentarios("automerge.yml")
    assert "workflows: [\"Tests\"]" in wf
    assert "github.event.workflow_run.conclusion == 'success'" in wf


def test_el_automerge_no_toca_los_borradores():
    """Un PR en borrador es trabajo a medio terminar: que se mergee solo sería
    exactamente lo contrario de lo que significa marcarlo como borrador."""
    script = _texto("automerge.yml")
    assert "!pr.draft" in script


def test_el_automerge_no_mergea_con_conflictos_ni_commits_nuevos():
    """Dos carreras reales: que la base haya avanzado y el merge tenga
    conflictos, y que hayan entrado commits DESPUÉS de los tests que dieron
    verde — en ese caso el verde no dice nada del código que se mergearía."""
    script = _texto("automerge.yml")
    assert "actual.mergeable === false" in script
    assert "actual.head.sha !== sha" in script


def test_el_automerge_borra_la_rama():
    script = _texto("automerge.yml")
    assert "deleteRef" in script
    assert "heads/${actual.head.ref}" in script


def test_el_automerge_dispara_los_builds_a_mano():
    """EL punto del workflow, y lo que más fácil se rompe al editarlo.

    Un push hecho con GITHUB_TOKEN no dispara workflows (protección de GitHub
    contra bucles). O sea que al mergear con el token, los builds de instalador
    —que escuchan push a main— nunca se enterarían, y los instaladores
    quedarían congelados justamente por haber automatizado el merge.

    createWorkflowDispatch sí funciona con el token: es una llamada de API, no
    un push. Si alguien saca estas líneas, el merge sigue andando y los
    instaladores dejan de actualizarse sin que nada lo diga."""
    script = _texto("automerge.yml")
    assert "createWorkflowDispatch" in script
    assert BUILD in script


def test_el_automerge_dispara_electron_aunque_el_pr_solo_toque_desktop():
    """El build empaqueta desktop/ (el propio Electron) además de
    RUTAS_DE_PRODUCTO. Un PR que sólo toca desktop/ tiene que dispararlo
    igual: si automerge lo gatillara sólo con `tocaElProducto`, ese cambio se
    mergearía sin reconstruir el instalador que justamente modificó."""
    script = _texto("automerge.yml")
    assert "startsWith('desktop/')" in script
    assert "tocaElEscritorio ? ['build_electron.yml'] : []" in script, (
        "automerge dejó de disparar el build por un cambio de desktop/")


def test_el_automerge_tiene_los_permisos_que_necesita():
    """Sin `actions: write` el dispatch de los builds falla con 403, y como está
    envuelto en try/catch fallaría en silencio."""
    wf = _sin_comentarios("automerge.yml")
    for permiso in ("contents: write", "pull-requests: write", "actions: write"):
        assert permiso in wf


# --------------------------------- que los builds se disparen cuando toca

def test_los_instaladores_se_reconstruyen_al_cambiar_el_producto():
    """Los instaladores se reconstruyen con push a main.

    El del dueño no lo hacía: sólo corría a mano o con un tag, así que se podía
    bajar de Actions una build de semanas atrás, sin los arreglos que ya estaban
    en main. El de Electron tenía el mismo problema —sólo tag o a mano— y en
    toda una serie de cambios al producto no se disparó ni una vez: el
    instalador de escritorio nunca se llegó a construir.
    """
    wf = _sin_comentarios(BUILD)
    assert "branches:" in wf and "- main" in wf
    assert "paths:" in wf


def test_el_unico_build_produce_LAS_DOS_ediciones():
    """Antes había tres builds para dos ediciones: cliente y dueño con
    PyInstaller + Inno, y una tercera copia del cliente con Electron. O sea que
    el instalador de cliente se compilaba dos veces con dos tecnologías, y el
    .exe del dueño que se usa de verdad es el de Electron — el de Inno no
    producía nada que alguien usara.

    Quedó un solo build con las dos ediciones en una matriz. Este test es lo
    que impide que vuelvan a separarse sin que nadie lo note."""
    wf = _sin_comentarios(BUILD)
    assert "matrix:" in wf, "el build dejó de armar las dos ediciones en una matriz"
    for edicion in EDICIONES:
        assert f"edicion: {edicion}" in wf, f"la matriz ya no arma la edición {edicion!r}"

    viejos = ["build_windows.yml", "build_windows_owner.yml"]
    presentes = [v for v in viejos if (WORKFLOWS / v).exists()]
    assert not presentes, (
        f"volvieron los builds de Inno: {presentes}. Son la tercera y cuarta "
        "forma de compilar dos instaladores.")


def test_el_instalador_de_escritorio_se_compila_en_el_pr_que_lo_toca():
    """Un cambio al instalador de escritorio se compila ANTES de mergear.

    Es el único de los tres que se puede romper de formas que ningún test de
    Python ve: una opción mal escrita en la config de NSIS, o el
    package-lock.json desincronizado —que hace abortar a `npm ci`—. Sin
    disparador de PR, eso entraba a main con todos los checks en verde y se
    descubría del otro lado.

    El filtro es sólo desktop/ y no las rutas de producto: el runner de Windows
    se cobra al doble y un PR que toca mvpm/ ya queda cubierto por el build que
    corre al mergear.
    """
    wf = _sin_comentarios("build_electron.yml")
    assert "pull_request:" in wf, (
        "build_electron.yml no compila en los PR: un cambio al instalador "
        "recién se prueba después de mergearlo")

    disparador = wf.split("pull_request:", 1)[1].split("workflow_dispatch", 1)[0]
    assert '"desktop/**"' in disparador
    # Las rutas de producto NO: encarecerían casi todos los PR del repo.
    for ruta in ("mvpm/**", "app/**", "requirements.txt"):
        assert f'"{ruta}"' not in disparador, (
            f"{ruta} en el disparador de PR hace correr un runner de Windows "
            f"en casi todos los PR")


def test_electron_tambien_se_reconstruye_al_cambiar_el_propio_electron():
    """A diferencia de los otros dos, este instalador empaqueta desktop/ (el
    código de Electron en sí) además de RUTAS_DE_PRODUCTO — un cambio ahí
    tiene que reconstruirlo aunque no toque mvpm/app/packaging."""
    wf = _sin_comentarios("build_electron.yml")
    assert '"desktop/**"' in wf


def test_los_paths_de_los_builds_cubren_todo_el_producto():
    """El riesgo real de estas listas es la deriva: se agrega un módulo nuevo
    bajo api/ y el instalador deja de reconstruirse cuando cambia, sin que nada
    lo avise. Se comparan contra la misma lista que usa automerge.yml para
    decidir si dispara los builds — si las dos no dicen lo mismo, una de las
    dos está mal."""
    wf = _sin_comentarios(BUILD)
    for ruta in RUTAS_DE_PRODUCTO:
        esperado = f'"{ruta}**"' if ruta.endswith("/") else f'"{ruta}"'
        assert esperado in wf, (
            f"{BUILD} no se reconstruye cuando cambia {ruta} — falta {esperado} "
            "en paths:")


def test_automerge_y_los_builds_coinciden_en_que_es_el_producto():
    """La otra mitad del test anterior, del lado de automerge.yml."""
    script = _texto("automerge.yml")
    for ruta in RUTAS_DE_PRODUCTO:
        assert f"'{ruta}'" in script, (
            f"automerge.yml no considera {ruta} parte del producto, así que un "
            "cambio ahí se mergearía sin reconstruir los instaladores")


# ---------------------------------------------- lo que no puede cambiar

def test_el_build_del_dueno_sigue_sin_publicarse_en_ningun_canal_publico():
    """El canal del dueño es el canal del dueño: no se linkea desde la landing
    ni se sube a Vercel Blob, y su Release nunca queda como "Latest".

    Ojo con por qué esto ya NO es lo que protege el producto. Lo era cuando el
    .exe llevaba un marcador firmado adentro, y ese razonamiento resultó falso:
    el repositorio era público, así que ese canal "privado" no lo era. Hoy el
    .exe del dueño no lleva nada que desbloquee nada (es una constante
    compilada, ver packaging/marcar_build_owner.py)
    y esto queda como higiene, no como candado."""
    owner = _pasos_de("owner").lower()
    assert "publish_blob" not in owner
    assert "blob_read_write_token" not in owner
    assert "@vercel/blob" not in owner
    # El Release del dueño va como prerelease para que nunca quede marcado
    # "Latest" en la portada del repositorio.
    assert "prerelease: ${{ matrix.edicion == 'owner' }}" in _sin_comentarios(BUILD)


# --------------------------- los binarios NO viven en el árbol de git

#: La ÚNICA ruta de este repositorio donde se acepta un binario versionado.
#:
#: Es una excepción pedida y decidida por el dueño: quiere bajar la Owner
#: Edition completa de un clic, sin depender del artefacto de Actions ni de un
#: tag. Se acota a esta carpeta —y no se borran los tests— para que todo lo
#: demás siga protegido: el instalador de CLIENTE nunca puede volver al árbol.
#:
#: Lo que cuesta, escrito acá a propósito porque es donde se va a leer:
#: este repositorio es PÚBLICO (verificado contra la API de GitHub), y este
#: .exe se compila con ES_OWNER_BUILD = True, así que abre el producto
#: completo sin prueba, sin token y sin clave, en cualquier máquina. Mientras
#: el repo sea público, cualquiera se lo baja. Pasar el repo a privado
#: (Settings → General → Change repository visibility) elimina ese costo y
#: deja esta excepción sin contraindicación.
CARPETA_OWNER_VERSIONADA = "INSTALADOR_OWNER/"


def test_ningun_ejecutable_esta_versionado():
    """Ningún `.exe` puede estar seguido por git, salvo el de la Owner Edition.

    Estuvieron: los dos instaladores, 71 MB cada uno, recommiteados en cada
    build. Veintisiete veces. `.git` llegó a **1,9 GB** para un proyecto cuyo
    código fuente pesa unos pocos MB — cada clon se bajaba eso entero y cada
    push arrastraba el objeto nuevo, así que los pushes tardaban minutos y se
    cortaban solos.

    Y costaba algo peor que tiempo. `api/download-installer.js` entrega el
    instalador SÓLO a quien presenta una licencia MVPM2 válida. Con el .exe de
    CLIENTE en el árbol de un repositorio público, cualquiera se lo bajaba sin
    licencia y sin dejar rastro: el candado puesto, y la puerta de al lado
    abierta de par en par. Eso sigue prohibido y es lo que este test cuida.

    Lo único admitido es `INSTALADOR_OWNER/` (ver CARPETA_OWNER_VERSIONADA):
    UN archivo, que se reemplaza en vez de acumularse, así el repositorio no
    vuelve a crecer sin techo.
    """
    import subprocess

    seguidos = subprocess.run(
        ["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True).stdout.split()
    exes = [f for f in seguidos
            if f.lower().endswith((".exe", ".msi", ".dmg"))
            and not f.startswith(CARPETA_OWNER_VERSIONADA)]
    assert not exes, (
        "ejecutables versionados fuera de " + CARPETA_OWNER_VERSIONADA + ": "
        + ", ".join(exes)
        + "\n\nVan a Vercel Blob (cliente, con licencia) o al artefacto de "
          "Actions (dueño, con login). Nunca al árbol.")


def test_el_instalador_de_cliente_nunca_esta_versionado():
    """El complemento del de arriba: la excepción es SÓLO para el del dueño.

    Sin esto, `INSTALADOR_OWNER/` sería un agujero por el que también podría
    colarse el instalador de cliente — y ése sí rompe el cobro, porque
    `api/download-installer.js` existe justamente para entregarlo únicamente a
    quien presenta una licencia válida.
    """
    import subprocess

    seguidos = subprocess.run(
        ["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True).stdout.split()
    en_owner = [f for f in seguidos if f.startswith(CARPETA_OWNER_VERSIONADA)]
    binarios = [f for f in en_owner if f.lower().endswith((".exe", ".msi", ".dmg"))]
    assert len(binarios) <= 1, (
        "en " + CARPETA_OWNER_VERSIONADA + " tiene que haber UN solo binario "
        "(se reemplaza, no se acumula): " + ", ".join(binarios))
    for f in binarios:
        nombre = f.rsplit("/", 1)[-1].lower()
        assert "owner" in nombre, (
            f"{f} no se llama como el instalador del dueño. Esta carpeta es "
            "sólo para la Owner Edition — el instalador de CLIENTE nunca se "
            "versiona: se entrega por Vercel Blob contra licencia válida.")


def test_ningun_archivo_versionado_es_enorme():
    """El complemento del de arriba, por tamaño y no por extensión.

    Renombrar el instalador a `.dat` esquivaría el test anterior y volvería a
    inflar el repositorio igual. Lo que importa no es la extensión: es que un
    binario grande, recommiteado build tras build, hace que el repositorio
    crezca sin techo.

    El límite duro de GitHub por archivo son 100 MiB; 25 MB deja lugar de sobra
    para el video de la landing (3 MB) y corta cualquier instalador.

    `INSTALADOR_OWNER/` queda exento por decisión del dueño, pero con techo
    propio: 60 MB, bien por debajo del límite de GitHub. Un instalador que
    crezca más que eso es una señal de que algo se empaquetó de más.
    """
    import subprocess

    LIMITE_MB = 25
    LIMITE_OWNER_MB = 60
    seguidos = subprocess.run(
        ["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True).stdout.split()
    gordos = []
    for nombre in seguidos:
        ruta = RAIZ / nombre
        if not ruta.is_file():
            continue
        mb = ruta.stat().st_size / 1024 / 1024
        techo = (LIMITE_OWNER_MB if nombre.startswith(CARPETA_OWNER_VERSIONADA)
                 else LIMITE_MB)
        if mb > techo:
            gordos.append(f"{nombre} ({mb:.0f} MB, techo {techo} MB)")
    assert not gordos, "archivos versionados por encima de su techo: " + ", ".join(gordos)


@pytest.mark.parametrize("workflow", [BUILD])
def test_ningun_build_commitea_su_resultado(workflow):
    """La otra mitad: que los workflows no vuelvan a meter el .exe en el árbol.

    Sin esto, el test de arriba pasa hoy y se cae dentro de un mes, con el
    repositorio ya inflado de nuevo y sin que nadie sepa cuándo empezó.
    """
    wf = _sin_comentarios(workflow)
    for prohibido in ("git commit", "git push", "publicar_en_carpeta_instalador"):
        assert prohibido not in wf, (
            f"{workflow} vuelve a commitear el instalador ({prohibido!r})")


@pytest.mark.parametrize("workflow", [BUILD])
def test_cada_build_deja_su_instalador_en_algun_lado(workflow):
    """No commitear no puede significar que el .exe se pierda: el build tarda
    minutos y el resultado tiene que quedar en un canal que alguien pueda usar.

    El artefacto de Actions es ese canal, y exige estar logueado con acceso al
    repositorio — que es exactamente la propiedad que faltaba cuando el .exe
    colgaba del árbol de un repo público.
    """
    wf = _sin_comentarios(workflow)
    assert "actions/upload-artifact" in wf, (
        f"{workflow} ya no publica el instalador en ningún lado: compila y tira "
        "el resultado")
    assert "retention-days" in wf, (
        "sin retención explícita el artefacto se borra a los 90 días por "
        "defecto y nadie se entera")
    # Y las DOS ediciones lo suben: el paso no puede quedar condicionado a una.
    for edicion in EDICIONES:
        assert "actions/upload-artifact" in _pasos_de(edicion), (
            f"la edición {edicion!r} compila y no deja el instalador en ningún lado")


def test_solo_el_del_cliente_va_al_canal_publico():
    """El del cliente va a Vercel Blob, que es lo que `download-installer`
    entrega contra una licencia. El del dueño no va a ningún canal servido por
    la web."""
    assert "publish_blob" in _pasos_de("cliente")
    assert "publish_blob" not in _pasos_de("owner").lower()


def test_el_instalador_del_dueno_y_el_del_cliente_no_se_pisan():
    """Van a artefactos con nombres distintos. Si compartieran nombre, el
    segundo build pisaría al primero y quedaría un solo instalador — con el
    riesgo de que el que sobreviva sea el del dueño."""
    import re as _re

    wf = _sin_comentarios(BUILD)
    nombres = _re.findall(r"^\s+artefacto:\s*(\S+)$", wf, _re.MULTILINE)
    assert len(nombres) == len(EDICIONES), (
        f"se esperaba un artefacto por edición, hay {nombres}")
    assert len(set(nombres)) == len(EDICIONES), (
        f"las ediciones comparten nombre de artefacto: {nombres}")
    # Y el paso lo toma de la matriz, no lo escribe fijo: si estuviera fijo, la
    # segunda edición pisaría el artefacto de la primera igual.
    assert "name: ${{ matrix.artefacto }}" in wf


def test_el_build_ensucia_archivos_versionados():
    """Los pasos de compilación tocan archivos que git sigue —
    `strip_py_sources.py` borra los `mvpm/*.py` ya compilados a `.pyd`.

    Mientras el build commiteaba su resultado, eso importaba muchísimo: `git
    pull --rebase` se niega a correr con el árbol sucio y los dos builds
    murieron por eso después de compilar entero. Ahora que no commitea nada, el
    árbol sucio es inofensivo — pero el test queda porque el día que alguien
    quiera volver a escribir en el repo desde un build, esto es lo que le va a
    recordar por qué no era gratis.
    """
    import subprocess

    strip = (RAIZ / "packaging" / "strip_py_sources.py").read_text(encoding="utf-8")
    assert ".unlink()" in strip and 'MVPM_DIR.glob("*.py")' in strip

    seguidos = subprocess.run(
        ["git", "ls-files", "mvpm/"], cwd=RAIZ, capture_output=True, text=True,
    ).stdout.split()
    assert len([f for f in seguidos if f.endswith(".py")]) > 1


# ------------------------------------------- lo que cuesta correr el CI

def test_la_suite_no_corre_dos_veces_sobre_el_mismo_commit():
    """`push:` a secas junto con `pull_request:` disparaba la suite DOS veces
    sobre el MISMO sha: dos corridas idénticas, mismo resultado, las dos
    cobrando.

    No se notaba porque el repositorio era público, y GitHub no cobra minutos de
    Actions en repos públicos. Al pasarlo a privado esos minutos empezaron a
    descontar de la cuota de la cuenta.

    La cobertura no cambia: `pull_request` cubre cualquier rama que vaya a
    mergearse y `push` a main cubre lo que entra directo.
    """
    wf = _sin_comentarios("tests.yml")
    assert "pull_request:" in wf
    push = wf[wf.index("push:"):wf.index("pull_request:")]
    assert "branches:" in push and "- main" in push, (
        "tests.yml volvió a correr en push de cualquier rama: con pull_request "
        "también activo, cada commit paga la suite dos veces")


@pytest.mark.parametrize("workflow", ["tests.yml", BUILD])
def test_un_push_nuevo_cancela_la_corrida_que_quedo_vieja(workflow):
    """Tres pushes seguidos pagaban tres corridas completas y se quedaban con la
    última: las dos primeras se descartan igual, pero se cobran. Pesa el doble en
    los builds de Windows, que se facturan a 2x y tardan unos cinco minutos."""
    wf = _sin_comentarios(workflow)
    assert "concurrency:" in wf, f"{workflow} no cancela las corridas superadas"
    assert "cancel-in-progress: true" in wf


def test_una_edicion_que_falla_no_deja_a_la_otra_sin_instalador():
    """Antes las dos ediciones eran dos workflows, y el riesgo era que
    compartieran grupo de concurrencia: uno cancelaba al otro y ese instalador
    no se reconstruía nunca. Ahora son dos jobs de una matriz en la MISMA
    corrida, así que un solo grupo es correcto —cancelar la corrida vieja
    cancela las dos y la nueva rebuildea las dos— y el riesgo se mudó de
    lugar: `fail-fast` por defecto es `true`, o sea que si la edición del
    dueño falla, GitHub cancela la del cliente aunque estuviera por terminar
    bien, y ese día no hay instalador para vender."""
    wf = _sin_comentarios(BUILD)
    assert "concurrency:" in wf and "group:" in wf
    assert "fail-fast: false" in wf, (
        "sin `fail-fast: false`, que falle una edición deja a la otra sin "
        "instalador aunque su compilación estuviera bien")


def test_run_sh_ci_corre_las_mismas_compuertas_que_el_workflow():
    """`./run.sh ci` tiene que ser el espejo local de tests.yml.

    Correr sólo `./run.sh test` deja pasar dos cosas que en el PR salen en
    rojo: ruff (la suite puede estar verde y el linter voltear el build igual)
    y los tests de pago, que son de Node y pytest no los ve. Si CI agrega un
    paso y el comando local no, el espejo deja de serlo en silencio — que es
    justo cuando alguien pushea confiado.
    """
    wf = _sin_comentarios("tests.yml")
    run_sh = (RAIZ / "run.sh").read_text(encoding="utf-8")
    ci = run_sh.split("  ci)", 1)[1].split(";;", 1)[0]

    assert "ruff check ." in wf and "ruff check ." in ci
    assert "pytest tests/" in wf and "pytest tests/" in ci

    # Cada .js que CI corre por nombre tiene que estar en el comando local.
    for linea in wf.splitlines():
        limpia = linea.strip()
        if limpia.startswith("node tests/"):
            archivo = limpia.split()[1]
            assert archivo in ci, f"{archivo} lo corre CI pero no `./run.sh ci`"


def test_todo_suite_de_node_esta_enganchado_a_ci():
    """La dirección que faltaba del espejo de arriba.

    Ese test compara CI contra `./run.sh ci`, así que un archivo que no esté
    en NINGUNO de los dos pasa desapercibido: existe, nadie lo corre, y como
    un test que no corre no falla, parece cobertura cuando no lo es. Pasó con
    `tests/test_rotar_claves.js`, que cubre la ruta por donde viaja la clave
    privada de licencias.

    pytest levanta solo cualquier `tests/test_*.py` nuevo; los de Node hay que
    nombrarlos uno por uno en los dos lugares. Este test es lo que hace que
    olvidarse duela ahora y no el día que importa.
    """
    wf = _sin_comentarios("tests.yml")
    ci = (RAIZ / "run.sh").read_text(encoding="utf-8").split("  ci)", 1)[1].split(";;", 1)[0]

    for archivo in sorted(p.name for p in (RAIZ / "tests").glob("test_*.js")):
        ruta = f"tests/{archivo}"
        assert ruta in wf, f"{ruta} existe y tests.yml no lo corre"
        assert ruta in ci, f"{ruta} existe y `./run.sh ci` no lo corre"
