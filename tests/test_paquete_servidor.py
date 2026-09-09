# © 2026 Martín Viera. Todos los derechos reservados.
"""El paquete servidor: el que se lleva a la VM del cliente.

Existe para un caso muy concreto —una consultora entra a un proyecto de un
cliente, la laptop corporativa no deja correr instaladores, y el dato del
cliente no puede quedar en el disco de la consultora— y cada cosa que se fija
acá es una forma conocida de que ese caso deje de cumplirse en silencio:

 1. **Que no se cuele un `.bat` ni un `.exe`.** Es la única razón por la que
    este formato existe además del portable. Agregar un archivo a
    `INCLUDE_FILES` alcanza para romperlo, y el paquete seguiría armándose sin
    ningún error: se descubriría recién en la laptop del cliente.
 2. **Que venga desbloqueado.** Es una decisión explícita del dueño: no pide
    licencia. Si un cambio en el builder dejara `ES_OWNER_BUILD = False`, el
    paquete pediría licencia justo en la máquina del cliente, donde no hay con
    qué activarla.
 3. **Que el árbol de trabajo NO quede marcado.** El reverso del punto
    anterior y mucho peor: si `mvpm/edicion.py` quedara en True en el
    repositorio, TODAS las copias —incluida la que baja un cliente— quedarían
    sin candado.
 4. **Que la telemetría de Streamlit esté apagada.** Streamlit manda
    estadísticas de uso a su servidor por defecto. En una instalación adentro
    del cliente eso es una conexión saliente que nadie pidió, y desmiente la
    frase con la que se defiende el despliegue ante seguridad.
 5. **Que el dato del cliente no salga de su carpeta.** Verificado escribiendo
    un dato y buscándolo después, no leyendo el código.
"""

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent

# `packaging/` va al path y el módulo se importa suelto, que es la convención
# del repo (ver tests/test_owner.py). No se puede hacer
# `from packaging.build_release import ...`: `packaging` es además un paquete
# de PyPI instalado como dependencia transitiva, y gana el suyo.
sys.path.insert(0, str(RAIZ / "packaging"))

from build_release import (  # noqa: E402
    EXTENSIONES_PROHIBIDAS,
    EXTRAS_SERVIDOR,
    build_owner_servidor,
)

SERVIDOR_DIR = RAIZ / "packaging" / "servidor"


@pytest.fixture(scope="module")
def paquete(tmp_path_factory) -> Path:
    """El .zip real, armado en un destino temporal.

    Con destino explícito a propósito: sin él escribiría en `dist/`, y un test
    que ensucia el árbol en cada corrida termina haciendo que alguien commitee
    un paquete armado desde un checkout a medio editar.
    """
    destino = tmp_path_factory.mktemp("paquete") / "servidor.zip"
    return build_owner_servidor(destino=destino)


@pytest.fixture(scope="module")
def extraido(paquete: Path, tmp_path_factory) -> Path:
    carpeta = tmp_path_factory.mktemp("extraido")
    with zipfile.ZipFile(paquete) as zf:
        zf.extractall(carpeta)
    return carpeta


# ------------------------------------------------- sin lanzadores de Windows

def test_no_viaja_ningun_lanzador_de_windows(paquete: Path):
    """Un `.bat` o un `.exe` es exactamente lo que bloquea la política de la
    laptop. Si viajan, este paquete no se distingue del portable y no resuelve
    nada."""
    with zipfile.ZipFile(paquete) as zf:
        prohibidos = [n for n in zf.namelist()
                      if n.lower().endswith(EXTENSIONES_PROHIBIDAS)]
    assert not prohibidos, (
        f"el paquete servidor trae lanzadores que la laptop del cliente no "
        f"puede ejecutar: {prohibidos}")


def test_trae_todo_lo_necesario_para_arrancar_sin_instalador(paquete: Path):
    with zipfile.ZipFile(paquete) as zf:
        dentro = set(zf.namelist())
    for interno in EXTRAS_SERVIDOR.values():
        assert interno in dentro, f"falta {interno} en el paquete servidor"
    # Sin el motor y la app no hay nada que arrancar.
    assert "app/app.py" in dentro
    assert "mvpm/edicion.py" in dentro
    assert "requirements.txt" in dentro


# ------------------------------------------------------- el candado, los dos

def test_el_paquete_abre_sin_pedir_licencia(paquete: Path):
    """Decisión explícita del dueño: este paquete no pide licencia. Si esto se
    rompe, lo descubre en la VM del cliente, que es el peor momento."""
    with zipfile.ZipFile(paquete) as zf:
        edicion = zf.read("mvpm/edicion.py").decode("utf-8")
    assert "ES_OWNER_BUILD = True" in edicion, (
        "el paquete servidor saldría pidiendo licencia en la máquina del "
        "cliente, donde no hay con qué activarla")


def test_el_repositorio_sigue_con_el_candado_puesto():
    """El reverso, y mucho más grave: marcar el ÁRBOL deja sin candado a todas
    las copias, incluida la que se descarga un cliente."""
    edicion = (RAIZ / "mvpm" / "edicion.py").read_text(encoding="utf-8")
    assert "ES_OWNER_BUILD = False" in edicion, (
        "mvpm/edicion.py quedó marcado como Owner en el árbol de trabajo: "
        "commitear eso deja el producto sin candado para cualquiera")


# ------------------------------------------------------ nada sale a internet

@pytest.mark.parametrize("archivo", ["iniciar.py", "Dockerfile"])
def test_la_telemetria_de_streamlit_esta_apagada(archivo: str):
    """Streamlit manda estadísticas de uso a su servidor POR DEFECTO. Adentro
    del cliente eso es una conexión saliente que nadie pidió, y desmiente la
    frase con la que se defiende el despliegue. Las dos formas de arrancar
    tienen que apagarla: apagarla en una sola da una falsa sensación."""
    texto = (SERVIDOR_DIR / archivo).read_text(encoding="utf-8")
    assert "gatherUsageStats" in texto and "false" in texto, (
        f"{archivo} arranca Streamlit sin apagar la telemetría")


def test_el_contenedor_no_corre_como_root():
    dockerfile = (SERVIDOR_DIR / "Dockerfile").read_text(encoding="utf-8")
    assert "USER mvpm" in dockerfile, "el contenedor correría como root"


def test_el_contenedor_guarda_el_dato_en_un_volumen_y_no_en_la_imagen():
    """Si el dato viviera adentro de la imagen, se perdería al actualizar y
    viajaría en cualquier copia de la imagen — las dos cosas malas juntas."""
    compose = (SERVIDOR_DIR / "docker-compose.yml").read_text(encoding="utf-8")
    assert ":/datos" in compose, "el compose no monta un volumen para el dato"
    dockerfile = (SERVIDOR_DIR / "Dockerfile").read_text(encoding="utf-8")
    assert "MVPM_DATA_DIR=/datos" in dockerfile


# ----------------------------------------- el dato del cliente no se escapa

def test_el_dato_del_cliente_queda_solo_en_su_carpeta(extraido: Path, tmp_path):
    """La promesa entera del paquete, verificada escribiendo un dato y
    buscándolo después en el disco — no leyendo el código.

    El HOME se apunta a un directorio temporal para que "no está en el perfil
    del usuario" sea una afirmación comprobable y no una suposición sobre la
    máquina donde corren los tests.
    """
    datos = tmp_path / "datos"
    home = tmp_path / "home"
    home.mkdir()
    secreto = "SECRETO-DEL-CLIENTE-b7f3a1"

    guion = (
        "import sys; sys.path.insert(0, '.')\n"
        "from mvpm import db\n"
        "db.init_db()\n"
        "eid = db.obtener_o_crear_empresa('Cliente')\n"
        f"db.guardar_version(eid, 'gobernanza', 'politica', {secreto!r}, 'vigente')\n"
    )
    entorno = {"HOME": str(home), "MVPM_DATA_DIR": str(datos),
               "PATH": "/usr/bin:/bin", "USERPROFILE": str(home)}
    r = subprocess.run([sys.executable, "-c", guion], cwd=extraido,
                       env=entorno, capture_output=True, text=True)
    assert r.returncode == 0, f"no se pudo escribir el dato: {r.stderr}"

    def contiene_el_secreto(carpeta: Path) -> list[str]:
        hallados = []
        for p in carpeta.rglob("*"):
            if not p.is_file():
                continue
            try:
                if secreto.encode() in p.read_bytes():
                    hallados.append(str(p.relative_to(carpeta)))
            except OSError:
                continue
        return hallados

    assert contiene_el_secreto(datos), (
        "el dato no quedó en la carpeta de datos: MVPM_DATA_DIR no se está "
        "respetando y la promesa del paquete no se cumple")
    fugas = contiene_el_secreto(home)
    assert not fugas, (
        f"el dato del cliente apareció en el perfil del usuario: {fugas}. "
        "Es exactamente lo que este paquete existe para evitar.")
