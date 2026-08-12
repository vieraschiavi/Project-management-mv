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

#: Lo que termina adentro del .exe, según `datas` en packaging/mvpm.spec y
#: mvpm_owner.spec: app/ y mvpm/, más el launcher de packaging/.
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
    for build in ("build_windows.yml", "build_windows_owner.yml", "build_electron.yml"):
        assert build in script


def test_el_automerge_dispara_electron_aunque_el_pr_solo_toque_desktop():
    """build_electron.yml también escucha push a main cuando cambia desktop/
    (no sólo RUTAS_DE_PRODUCTO): un PR que sólo toca desktop/ no dispararía
    ese build si automerge lo gatillara con el mismo chequeo que los otros
    dos, que ignoran desktop/ por completo."""
    script = _texto("automerge.yml")
    assert "tocaElEscritorio" in script
    assert "startsWith('desktop/')" in script
    # El build de escritorio se pide con su propio chequeo, no con
    # tocaElProducto — si comparte el mismo `if`, un PR sólo de desktop/ nunca
    # lo dispara.
    assert "if (tocaElEscritorio) workflowsADisparar.push('build_electron.yml')" in script


def test_el_automerge_tiene_los_permisos_que_necesita():
    """Sin `actions: write` el dispatch de los builds falla con 403, y como está
    envuelto en try/catch fallaría en silencio."""
    wf = _sin_comentarios("automerge.yml")
    for permiso in ("contents: write", "pull-requests: write", "actions: write"):
        assert permiso in wf


# --------------------------------- que los builds se disparen cuando toca

@pytest.mark.parametrize("workflow", ["build_windows.yml", "build_windows_owner.yml", "build_electron.yml"])
def test_los_instaladores_se_reconstruyen_al_cambiar_el_producto(workflow):
    """Los tres instaladores —cliente, dueño y Electron— se reconstruyen con
    push a main.

    El del dueño no lo hacía: sólo corría a mano o con un tag, así que se podía
    bajar de Actions una build de semanas atrás, sin los arreglos que ya estaban
    en main. El de Electron tenía el mismo problema —sólo tag o a mano— y en
    toda una serie de cambios al producto no se disparó ni una vez: el
    instalador de escritorio nunca se llegó a construir.
    """
    wf = _sin_comentarios(workflow)
    assert "branches:" in wf and "- main" in wf
    assert "paths:" in wf


def test_electron_tambien_se_reconstruye_al_cambiar_el_propio_electron():
    """A diferencia de los otros dos, este instalador empaqueta desktop/ (el
    código de Electron en sí) además de RUTAS_DE_PRODUCTO — un cambio ahí
    tiene que reconstruirlo aunque no toque mvpm/app/packaging."""
    wf = _sin_comentarios("build_electron.yml")
    assert '"desktop/**"' in wf


@pytest.mark.parametrize("workflow", ["build_windows.yml", "build_windows_owner.yml", "build_electron.yml"])
def test_los_paths_de_los_builds_cubren_todo_el_producto(workflow):
    """El riesgo real de estas listas es la deriva: se agrega un módulo nuevo
    bajo api/ y el instalador deja de reconstruirse cuando cambia, sin que nada
    lo avise. Se comparan contra la misma lista que usa automerge.yml para
    decidir si dispara los builds — si las dos no dicen lo mismo, una de las
    dos está mal."""
    wf = _sin_comentarios(workflow)
    for ruta in RUTAS_DE_PRODUCTO:
        esperado = f'"{ruta}**"' if ruta.endswith("/") else f'"{ruta}"'
        assert esperado in wf, (
            f"{workflow} no se reconstruye cuando cambia {ruta} — falta {esperado} "
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
    .exe del dueño no lleva nada que desbloquee nada (ver packaging/mvpm_owner.spec)
    y esto queda como higiene, no como candado."""
    wf = _sin_comentarios("build_windows_owner.yml")
    assert "publish_blob" not in wf.lower()
    assert "blob_read_write_token" not in wf.lower()
    assert "prerelease: true" in wf


# ------------------------------------------- la carpeta INSTALADOR/

@pytest.mark.parametrize("workflow, sub", [
    ("build_windows.yml", "CLIENTE"),
    ("build_windows_owner.yml", "OWNER"),
])
def test_cada_build_deja_su_exe_en_la_carpeta_instalador(workflow, sub):
    """El instalador se baja del repo, no de Actions. Si el paso desaparece, la
    carpeta queda con un .exe viejo y nadie se entera: el build sigue en verde
    porque compiló bien, sólo que el resultado no llegó a ningún lado."""
    wf = _sin_comentarios(workflow)
    assert "publicar_en_carpeta_instalador.ps1" in wf
    assert f"-Subcarpeta {sub}" in wf


@pytest.mark.parametrize("workflow", ["build_windows.yml", "build_windows_owner.yml"])
def test_los_builds_pueden_escribir_en_el_repo(workflow):
    """Sin `contents: write` el commit del instalador falla con 403 al final de
    un build de varios minutos."""
    assert "contents: write" in _sin_comentarios(workflow)


def test_el_instalador_del_dueno_y_el_del_cliente_no_se_pisan():
    """Van a subcarpetas distintas. Si los dos escribieran en la misma, el
    borrado previo de .exe dejaría un solo instalador y el otro desaparecería —
    y con esa mezcla el .exe del dueño podría terminar donde no va."""
    cliente = _sin_comentarios("build_windows.yml")
    owner = _sin_comentarios("build_windows_owner.yml")
    assert "-Subcarpeta CLIENTE" in cliente and "-Subcarpeta OWNER" not in cliente
    assert "-Subcarpeta OWNER" in owner and "-Subcarpeta CLIENTE" not in owner


# ------------------------------ el push de los dos builds a la misma rama

def _publicador() -> str:
    return (RAIZ / "packaging" / "publicar_en_carpeta_instalador.ps1").read_text(
        encoding="utf-8")


def test_el_push_del_instalador_reintenta():
    """Los dos builds —cliente y dueño— se disparan con el MISMO push a main,
    corren en paralelo y terminan los dos pusheando a esa misma rama. El que
    llega segundo se encuentra con que main avanzó entre su `pull --rebase` y su
    `push`, y muere con "cannot lock ref 'refs/heads/main'".

    Ya pasó una vez: el build de cliente entró y el del dueño quedó en rojo con
    el .exe compilado y tirado. Un solo `pull --rebase` no cierra el caso porque
    la ventana es justamente la que hay entre el pull y el push: lo que lo cierra
    es reintentar el par completo.
    """
    ps = _publicador()
    assert "git pull --rebase origin main" in ps
    assert "git push origin HEAD:main" in ps
    assert "maxIntentos" in ps, "el push no reintenta: la carrera entre los dos builds vuelve"
    assert "git rebase --abort" in ps, (
        "sin abortar el rebase a medio hacer, el reintento se encuentra uno en "
        "curso y falla siempre")


def test_el_publicador_limpia_el_arbol_antes_de_rebasar():
    """`git pull --rebase` se niega a correr con cambios sin commitear:

        error: cannot pull with rebase: You have unstaged changes.

    y los reintentos no limpian nada, así que los cinco fallaban idénticos y el
    .exe recién compilado se perdía. No era la carrera entre los dos builds
    —eso es lo que arregla el reintento— sino el árbol sucio.

    Quién lo ensucia, en los DOS builds: packaging/strip_py_sources.py borra los
    mvpm/*.py después de que Cython los compila, y están versionados. El del
    dueño suma mvpm/edicion.py, que marcar_build_owner.py reescribe.

    Los dos builds del merge de #39 murieron acá con el mismo error, después de
    compilar el .exe entero.
    """
    ps = _publicador()
    assert "git checkout -- ." in ps, (
        "el publicador no limpia el árbol antes del rebase: con mvpm/edicion.py "
        "modificado por marcar_build_owner.py, `git pull --rebase` falla siempre")
    assert ps.index("git checkout -- .") < ps.index("git pull --rebase origin main"), (
        "la limpieza tiene que ir ANTES del primer pull, no adentro del bucle")
    assert ps.index("git commit -m") < ps.index("git checkout -- ."), (
        "limpiar ANTES de commitear borraría el .exe que se acaba de copiar")


def test_el_build_ensucia_archivos_versionados():
    """Fija la razón de ser del test de arriba: que los pasos de compilación
    tocan archivos que git sigue. Si algún día dejaran de hacerlo, la limpieza
    pasa a sobrar y este test lo dice.

    Se comprueba contra git, no contra una lista escrita a mano: es git quien
    decide si el árbol queda sucio.
    """
    import subprocess

    # El que rompe los dos builds: borra los mvpm/*.py ya compilados a .pyd.
    strip = (RAIZ / "packaging" / "strip_py_sources.py").read_text(encoding="utf-8")
    assert ".unlink()" in strip and 'MVPM_DIR.glob("*.py")' in strip, (
        "strip_py_sources.py ya no borra los mvpm/*.py: revisar si el "
        "publicador sigue necesitando limpiar el árbol antes del rebase")

    seguidos = subprocess.run(
        ["git", "ls-files", "mvpm/"], cwd=RAIZ, capture_output=True, text=True,
    ).stdout.split()
    assert len([f for f in seguidos if f.endswith(".py")]) > 1, (
        "los mvpm/*.py dejaron de estar versionados: borrarlos ya no ensucia "
        "el árbol y la limpieza del publicador sobra")

    # El extra del build del dueño.
    marcar = (RAIZ / "packaging" / "marcar_build_owner.py").read_text(encoding="utf-8")
    assert 'ROOT / "mvpm" / "edicion.py"' in marcar
    versionado = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "mvpm/edicion.py"],
        cwd=RAIZ, capture_output=True, text=True,
    )
    assert versionado.returncode == 0


def test_el_publicador_corta_antes_del_limite_de_github():
    """GitHub rechaza todo archivo de 100 MiB o más, y no hay forma de forzarlo:
    el push muere del lado del servidor DESPUÉS de subir el archivo entero. El
    instalador de cliente ronda los 98 MiB, así que el margen es de un par de MB.
    Sin este corte, el día que se pase, el build falla con un error remoto que no
    dice cuál archivo fue, al final de quince minutos de compilación."""
    ps = _publicador()
    assert "100MB" in ps
    assert "exit 1" in ps


def test_el_publicador_no_deja_pasar_un_push_fallido_como_exito():
    """Si el bucle se queda sin intentos tiene que terminar en rojo. Salir 0 con
    el instalador sin pushear es el peor caso: el build queda en verde y la
    carpeta INSTALADOR/ se queda con el .exe viejo sin que nada lo avise."""
    ps = _publicador()
    assert "for (" in ps, "no hay bucle de reintentos que revisar"
    cola = ps[ps.rindex("for ("):]
    assert "Write-Error" in cola, "quedarse sin intentos no reporta nada"
    assert cola.rstrip().endswith("exit 1"), (
        "el script termina en verde después de agotar los reintentos: el build "
        "quedaría en verde con INSTALADOR/ sin actualizar")


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


@pytest.mark.parametrize("workflow", ["tests.yml", "build_windows.yml",
                                      "build_windows_owner.yml", "build_electron.yml"])
def test_un_push_nuevo_cancela_la_corrida_que_quedo_vieja(workflow):
    """Tres pushes seguidos pagaban tres corridas completas y se quedaban con la
    última: las dos primeras se descartan igual, pero se cobran. Pesa el doble en
    los builds de Windows, que se facturan a 2x y tardan unos cinco minutos."""
    wf = _sin_comentarios(workflow)
    assert "concurrency:" in wf, f"{workflow} no cancela las corridas superadas"
    assert "cancel-in-progress: true" in wf


def test_cada_build_de_windows_tiene_su_propio_grupo_de_concurrencia():
    """Si compartieran grupo, un build cancelaría al otro y ese instalador
    nunca se reconstruiría."""
    import re

    grupos = {}
    for workflow in ("build_windows.yml", "build_windows_owner.yml", "build_electron.yml"):
        m = re.search(r"^concurrency:\s*\n\s*group:\s*(.+)$",
                      _texto(workflow), re.MULTILINE)
        assert m, f"{workflow} no declara group:"
        grupos[workflow] = m.group(1).strip()
    assert len(set(grupos.values())) == 3, f"los builds comparten grupo: {grupos}"
