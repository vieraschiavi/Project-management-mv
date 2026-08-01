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
from pathlib import Path

import pytest

from mvpm import licensing, owner

RAIZ = Path(__file__).resolve().parent.parent


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


def test_la_env_var_activa_el_modo_owner(sin_marcadores, monkeypatch):
    monkeypatch.setenv("MVPM_OWNER_BYPASS", "1")
    assert owner.es_owner() is True
    assert "MVPM_OWNER_BYPASS" in owner.motivo()


def test_un_valor_distinto_de_1_no_activa_nada(sin_marcadores, monkeypatch):
    for valor in ["0", "", "true", "si"]:
        monkeypatch.setenv("MVPM_OWNER_BYPASS", valor)
        assert owner.es_owner() is False, f"'{valor}' no debería activar el modo owner"


@pytest.mark.parametrize("indice", [0, 1])
def test_cualquiera_de_los_marcadores_activa_el_modo_owner(sin_marcadores, indice):
    """Uno vive en los datos del usuario (lo escribe `./run.sh owner`) y el
    otro junto al programa (lo empaqueta el .exe de la Owner Edition)."""
    ruta = sin_marcadores[indice]
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("x", encoding="utf-8")
    assert owner.es_owner() is True
    assert str(ruta) in owner.motivo()


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
