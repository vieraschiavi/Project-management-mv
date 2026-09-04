# © 2026 Martín Viera. Todos los derechos reservados.
"""Consistencia del instalador de escritorio (Electron + NSIS).

`packaging/*.iss` —el instalador Python— tiene 19 tests que fijan que siempre
deje elegir la carpeta, que se pueda instalar sin ser administrador y que deje
desinstalador. El instalador de ESCRITORIO no tenía ninguno, y es el que el
usuario reportó: no lo dejaba elegir el disco. Un `oneClick: true` de más en
`desktop/package.json` apagaba la pantalla de destino entera sin que nada
fallara — el build seguía saliendo verde.

Lo que estos tests NO pueden verificar: cómo se ve el asistente al ejecutarlo.
Eso necesita Windows. Lo que sí verifican es que estén puestas las opciones de
las que depende ese comportamiento, que el script NSIS propio compile, y que
lo que el instalador empaqueta sea lo mismo que produce el build.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

RAIZ = Path(__file__).resolve().parent.parent
DESKTOP = RAIZ / "desktop"
PACKAGE = DESKTOP / "package.json"
NSH = DESKTOP / "installer.nsh"


@pytest.fixture(scope="module")
def paquete():
    return json.loads(PACKAGE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def nsis(paquete):
    return paquete["build"]["nsis"]


# --------------------------------------------- elegir dónde se instala

def test_no_es_instalador_de_un_solo_clic(nsis):
    """Con `oneClick: true` NSIS instala sin preguntar nada: ni carpeta, ni
    accesos directos, ni confirmación. Es el default de electron-builder."""
    assert nsis["oneClick"] is False


def test_siempre_deja_elegir_la_carpeta(nsis):
    assert nsis["allowToChangeInstallationDirectory"] is True


def test_se_puede_instalar_sin_ser_administrador(nsis):
    """`perMachine: false` instala en el perfil del usuario. En una notebook
    de empresa, donde el empleado no es admin local, es la diferencia entre
    poder instalarlo o no."""
    assert nsis["perMachine"] is False
    # ...y con allowElevation puede elegir igual instalar para toda la PC.
    assert nsis["allowElevation"] is True


# ------------------------------------------------------- desinstalador

def test_deja_desinstalador_con_nombre_propio(nsis):
    """Sin `uninstallDisplayName`, Agregar o quitar programas lo lista con el
    nombre interno del paquete."""
    assert nsis["uninstallDisplayName"] == "MV Project Management"


def test_desinstalar_no_borra_los_datos_del_cliente(nsis):
    """El portafolio vive en los datos del usuario (mvpm/rutas.py). Que
    desinstalar el programa se lleve puesta la base del cliente sería una
    pérdida de datos, no una limpieza."""
    assert nsis["deleteAppDataOnUninstall"] is False


def test_crea_accesos_directos(nsis):
    assert nsis["createDesktopShortcut"] is True
    assert nsis["createStartMenuShortcut"] is True


# ------------------------------------------------------------- íconos

@pytest.mark.parametrize("clave", [
    "installerIcon", "uninstallerIcon", "installerHeaderIcon"])
def test_los_iconos_del_instalador_existen(nsis, clave):
    """Sin ícono, el asistente sale con el de Electron por defecto y parece
    otro programa."""
    icono = (DESKTOP / nsis[clave]).resolve()
    assert icono.exists(), f"{clave} apunta a {icono}, que no existe"


def test_la_app_tiene_icono(paquete):
    icono = (DESKTOP / paquete["build"]["win"]["icon"]).resolve()
    assert icono.exists()


# ------------------------------------------- el script NSIS propio

def test_el_nsh_esta_declarado_y_existe(nsis):
    assert nsis["include"] == "installer.nsh"
    assert NSH.exists()


def test_el_nsh_compila(tmp_path):
    """Se compila de verdad con makensis, dentro de un arnés que define lo que
    aporta electron-builder alrededor. Un error de sintaxis acá no rompe los
    tests de Python pero sí el build de Windows, que tarda cinco minutos y
    cuesta el doble por correr en un runner de Windows."""
    if shutil.which("makensis") is None:
        pytest.skip("makensis no está instalado (se instala con: apt install nsis)")

    arnes = tmp_path / "arnes.nsi"
    arnes.write_text(f"""
Name "MV Project Management"
OutFile "{tmp_path / 'salida.exe'}"
InstallDir "$LOCALAPPDATA\\Programs\\MVProjectManagement"
RequestExecutionLevel user
!define INSTALL_REGISTRY_KEY "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\mvpm"
!define APP_FILENAME "MV Project Management"
!include "{NSH}"
Function .onInit
  !insertmacro preInit
FunctionEnd
Section "Principal"
  SetOutPath $INSTDIR
SectionEnd
""", encoding="utf-8")

    r = subprocess.run(["makensis", str(arnes)], capture_output=True, text=True)
    assert r.returncode == 0, f"makensis falló:\n{r.stdout}\n{r.stderr}"
    # Los warnings de NSIS son casi siempre bugs reales (una variable que no se
    # usa porque se escribió mal el nombre, por ejemplo).
    assert "warning" not in r.stdout.lower(), r.stdout


def test_el_nsh_solo_toca_la_instalacion_nueva():
    """Reinstalar tiene que quedarse donde ya estaba. Mover una instalación
    existente a otro disco y dejar la vieja tirada es el bug que ya se corrigió
    una vez en el instalador owner."""
    texto = NSH.read_text(encoding="utf-8")
    assert 'ReadRegStr $0 HKLM "${INSTALL_REGISTRY_KEY}" "InstallLocation"' in texto
    assert 'ReadRegStr $0 HKCU "${INSTALL_REGISTRY_KEY}" "InstallLocation"' in texto


def test_el_nsh_devuelve_la_pila_como_la_encontro():
    """La pila de NSIS es compartida con el resto del instalador que arma
    electron-builder. Un Push sin su Pop no falla al compilar: le devuelve
    basura al código que sigue, y eso se manifiesta como un instalador que se
    comporta raro en la PC del cliente."""
    texto = NSH.read_text(encoding="utf-8")
    cuerpo = [linea.split(";")[0].strip() for linea in texto.splitlines()]
    pushes = sum(1 for linea in cuerpo if linea.startswith("Push "))
    pops = sum(1 for linea in cuerpo if linea.startswith("Pop "))
    assert pushes == pops, f"{pushes} Push contra {pops} Pop"
    assert pushes > 0, "se esperaba que preInit preservara los registros"


def test_el_nsh_no_sugiere_unidades_removibles():
    """Sugerir instalar en un pendrive o en una unidad de red es peor que
    sugerir C:. 3 es DRIVE_FIXED."""
    texto = NSH.read_text(encoding="utf-8")
    assert "GetDriveTypeW" in texto
    assert "$2 == 3" in texto


# --------------------------------- lo que el instalador empaqueta

def test_el_motor_que_empaqueta_es_el_que_produce_pyinstaller(paquete):
    """`extraResources` copia resources/motor; el lanzador después busca el .exe
    ahí. Si los dos nombres se separan, el instalador sale sin motor y la
    ventana abre vacía.

    La búsqueda se mudó de `main.js` a `lib/server-manager.js` cuando la
    interfaz pasó a React: `main.js` no puede tener lógica testeable porque
    importa `electron`, que no se puede cargar en CI. El test mira donde la
    lógica está de verdad — pero sigue exigiendo lo mismo, que es que el nombre
    del ejecutable coincida con el que produce PyInstaller.
    """
    recursos = paquete["build"]["extraResources"]
    assert any(r["from"] == "resources/motor" and r["to"] == "motor"
               for r in recursos), recursos

    lanzador = (DESKTOP / "lib" / "server-manager.js").read_text(encoding="utf-8")
    assert "'motor'," in lanzador and "MVProjectManagement.exe" in lanzador, (
        "el lanzador no busca el .exe en resources/motor/")

    spec = (RAIZ / "packaging" / "mvpm.spec").read_text(encoding="utf-8")
    assert "MVProjectManagement" in spec


def test_el_bundle_de_react_viaja_en_el_instalador(paquete):
    """La ventana carga /app, que sirve el bundle de React desde
    `resources/ui`. Sin este `extraResources`, el instalador se arma igual y
    abre una ventana en blanco con un 404 — sólo en la PC del cliente."""
    recursos = paquete["build"]["extraResources"]
    assert any(r["from"] == "ui/dist" and r["to"] == "ui" for r in recursos), (
        f"el bundle de React no se empaqueta: {recursos}")


def test_el_bundle_se_construye_antes_de_empaquetar(paquete):
    """`ui/dist` está en .gitignore: no existe en un checkout limpio. Si
    `dist` no lo construyera primero, electron-builder empaquetaría una
    carpeta vacía y sólo avisaría."""
    dist = paquete["scripts"]["dist"]
    assert "build-ui" in dist, f"`dist` no construye la interfaz: {dist}"
    assert dist.index("verificar_motor") < dist.index("electron-builder"), (
        "la verificación del motor tiene que correr antes de empaquetar")


def test_el_modo_api_del_lanzador_existe(paquete):
    """El `.exe` empaquetado sirve React levantando la API con MVPM_MODO=api.
    Si el lanzador no conociera esa variable, el binario abriría Streamlit y la
    ventana de Electron mostraría un 404 en /app."""
    lanzador = (DESKTOP / "lib" / "server-manager.js").read_text(encoding="utf-8")
    assert "MVPM_MODO: 'api'" in lanzador

    launcher_py = (RAIZ / "packaging" / "mvpm_launcher.py").read_text(encoding="utf-8")
    assert 'MVPM_MODO' in launcher_py and "uvicorn.run" in launcher_py, (
        "packaging/mvpm_launcher.py no sabe levantar la API")


def test_el_build_aborta_si_falta_el_motor(paquete):
    """electron-builder, ante un `extraResources` inexistente, sólo avisa
    ("file source doesn't exist") y arma igual el instalador — que después
    instala bien y abre una ventana vacía en la PC del cliente. El chequeo
    previo convierte ese aviso en un build que falla."""
    assert paquete["scripts"]["dist"].startswith("node verificar_motor.js &&")
    assert (DESKTOP / "verificar_motor.js").exists()


@pytest.mark.parametrize("caso,archivos", [
    ("sin carpeta", None),
    ("carpeta vacía", []),
    ("exe truncado", [("MVProjectManagement.exe", b"")]),
])
def test_el_chequeo_del_motor_caza_cada_copia_rota(tmp_path, caso, archivos):
    if shutil.which("node") is None:
        pytest.skip("node no está instalado")

    escenario = tmp_path / "desktop"
    escenario.mkdir()
    shutil.copy(DESKTOP / "verificar_motor.js", escenario / "verificar_motor.js")
    if archivos is not None:
        motor = escenario / "resources" / "motor"
        motor.mkdir(parents=True)
        for nombre, contenido in archivos:
            (motor / nombre).write_bytes(contenido)

    r = subprocess.run(["node", str(escenario / "verificar_motor.js")],
                       capture_output=True, text=True)
    assert r.returncode == 1, f"{caso}: el build habría seguido igual"


def test_el_chequeo_del_motor_acepta_una_copia_buena(tmp_path):
    if shutil.which("node") is None:
        pytest.skip("node no está instalado")

    escenario = tmp_path / "desktop"
    escenario.mkdir()
    shutil.copy(DESKTOP / "verificar_motor.js", escenario / "verificar_motor.js")
    motor = escenario / "resources" / "motor"
    motor.mkdir(parents=True)
    (motor / "MVProjectManagement.exe").write_bytes(b"x" * 2048)

    r = subprocess.run(["node", str(escenario / "verificar_motor.js")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


# ----------------------------------------------------------- versión

def test_la_version_del_escritorio_acompana_a_la_del_producto(paquete):
    """El instalador y el motor que empaqueta tienen que decir la misma
    versión: que uno diga 0.1.0 y el otro 0.2.0 hace imposible saber qué tiene
    puesto un cliente cuando reporta un problema.

    Antes esto se comparaba contra `packaging/instalador.iss`, que era el
    tercer lugar donde vivía el número y el único que ataba los dos. Al quedar
    un solo instalador, la fuente de verdad pasa a ser `mvpm.VERSION` — el
    motor, que es lo que efectivamente corre adentro."""
    from mvpm import VERSION

    assert paquete["version"] == VERSION, (
        f"desktop/package.json dice {paquete['version']} y mvpm/__init__.py "
        f"dice {VERSION}")

    # Y que no reaparezca una copia suelta del número donde se arman los
    # paquetes: `build_release.py` tenía el suyo escrito a mano como default,
    # así que el ZIP salía v0.1.0 mientras el instalador decía 0.2.0 y nada lo
    # avisaba — el test de arriba no lo veía porque miraba otros dos archivos.
    import re

    build = (RAIZ / "packaging" / "build_release.py").read_text(encoding="utf-8")
    sueltos = re.findall(r'version: str = "(\d+\.\d+\.\d+)"', build)
    assert not sueltos, (
        f"packaging/build_release.py volvió a fijar la versión a mano: {sueltos}. "
        "Tiene que salir de mvpm.VERSION.")
    assert "from mvpm import VERSION" in build


def test_el_lockfile_no_se_desincroniza(paquete):
    """CI corre `npm ci`, que aborta si package.json y package-lock.json no
    coinciden en la versión. Cambiar una y olvidar la otra rompe el build de
    Windows entero."""
    lock = json.loads((DESKTOP / "package-lock.json").read_text(encoding="utf-8"))
    assert lock["version"] == paquete["version"]
    assert lock["packages"][""]["version"] == paquete["version"]

    # Y las DEPENDENCIAS, que es por donde se rompió de verdad.
    #
    # Este test comparaba sólo la versión del paquete. Agregué esbuild, react y
    # react-dom para la interfaz de escritorio, no regeneré el lockfile, y el
    # test pasó en verde: `npm ci` aborta con "can only install packages when
    # your package.json and package-lock.json are in sync", pero eso recién se
    # ve en el runner de Windows, cinco minutos después y en otro workflow.
    #
    # Se comprueba en los dos sentidos: una dependencia agregada sin regenerar
    # el lock, y una sacada del package.json que quedó en el lock.
    en_lock = lock["packages"][""]
    for grupo in ("dependencies", "devDependencies"):
        declaradas = set(paquete.get(grupo, {}))
        bloqueadas = set(en_lock.get(grupo, {}))
        faltan = sorted(declaradas - bloqueadas)
        sobran = sorted(bloqueadas - declaradas)
        assert not faltan, (
            f"{grupo} en package.json que no están en el lockfile: {faltan}. "
            "`npm ci` va a abortar el build de Windows. Corré `npm install` "
            "en desktop/ y commiteá el package-lock.json.")
        assert not sobran, (
            f"{grupo} en el lockfile que ya no están en package.json: {sobran}")
