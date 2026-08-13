# © 2026 Martín Viera. Todos los derechos reservados.
"""Dónde van los datos del programa (mvpm/rutas.py).

El pedido que motiva este módulo: "la instalación debe ser 100% en el disco
que yo elija". Antes, elegir instalar en D:\\ (o cualquier disco que no sea el
del sistema) sólo movía el `.exe` — la base de datos, la licencia, las
reseñas y el marcador de modo owner seguían yendo siempre al perfil de
Windows del usuario (`~/.mv_project_management`, que resuelve al disco C).
La instalación quedaba partida entre dos discos sin que nadie lo hubiera
pedido así.

Se verifica acá: que el modo congelado (el `.exe` real) ponga los datos junto
a sí mismo — en el disco que sea —, que el modo desarrollo/portable siga
yendo al perfil de usuario como siempre, y que una carpeta de instalación no
escribible (instalación "para todos" sin ser administrador en el uso diario)
caiga al perfil de usuario en vez de romper el arranque.
"""

import sys

import pytest

from mvpm import rutas


@pytest.fixture(autouse=True)
def sin_env_var(monkeypatch):
    """Ninguno de estos tests debe depender de MVPM_DATA_DIR heredada del
    entorno donde corre la suite."""
    monkeypatch.delenv("MVPM_DATA_DIR", raising=False)


@pytest.fixture
def no_congelado(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)


@pytest.fixture
def congelado_en(monkeypatch, tmp_path):
    """Simula el `.exe` real corriendo desde `tmp_path/disco`, como si el
    usuario hubiera instalado ahí (sea C:, D:, o lo que sea)."""
    def _armar(subcarpeta: str = "disco"):
        carpeta = tmp_path / subcarpeta
        carpeta.mkdir(parents=True, exist_ok=True)
        exe = carpeta / "MVProjectManagement.exe"
        exe.write_bytes(b"")  # sólo tiene que existir para Path.resolve()
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", str(exe), raising=False)
        return carpeta
    return _armar


# --------------------------------------------------- modo desarrollo/portable

def test_sin_estar_congelado_usa_el_perfil_del_usuario(no_congelado):
    """./run.sh app, el .bat portable, y la suite de tests: comportamiento
    de siempre, sin sorpresas."""
    assert rutas.directorio_datos() == rutas._en_el_perfil_del_usuario()


def test_junto_al_ejecutable_devuelve_none_si_no_esta_congelado(no_congelado):
    assert rutas._junto_al_ejecutable() is None


# ------------------------------------------------------- el .exe instalado

def test_congelado_pone_los_datos_junto_al_exe(congelado_en):
    carpeta_instalacion = congelado_en("MiPrograma")
    resultado = rutas.directorio_datos()
    assert resultado == carpeta_instalacion / "data"


def test_congelado_respeta_el_disco_elegido_al_instalar(congelado_en, tmp_path):
    """El caso concreto del pedido: si el .exe corre desde un disco
    distinto al que tiene el perfil de usuario, los datos van a ESE disco."""
    carpeta_d = congelado_en("SimulacionDiscoD")
    resultado = rutas.directorio_datos()
    # No se puede simular una letra de unidad real en Linux, pero sí se puede
    # verificar la garantía que importa: es la MISMA raíz que la carpeta de
    # instalación, no el home del usuario (que en este test es otro tmp_path
    # o el HOME real, ninguno de los dos es carpeta_d).
    assert str(resultado).startswith(str(carpeta_d))
    assert resultado != rutas._en_el_perfil_del_usuario()


def test_congelado_no_deja_la_carpeta_data_creada_de_antemano(congelado_en):
    """directorio_datos() sólo DECIDE la ruta; la prueba de escritura que usa
    para decidir crea y borra la carpeta, así que un .exe recién instalado no
    debería aparecer con una carpeta "data" vacía antes de que el usuario
    haga algo. Quien la use en serio (db.py, licensing.py, ...) la crea."""
    congelado_en()
    resultado = rutas.directorio_datos()
    assert not resultado.exists()
    resultado.mkdir(parents=True, exist_ok=True)
    assert resultado.is_dir()


# ------------------------------------------- instalación no escribible

def test_si_no_se_puede_escribir_junto_al_exe_cae_al_perfil_de_usuario(
    congelado_en, monkeypatch
):
    """Instalación 'para todos' en Archivos de Programa: quien la hizo tenía
    privilegios de administrador, pero el uso diario corre sin ellos. Antes
    esto directamente rompía el arranque con un permiso denegado."""
    congelado_en()
    monkeypatch.setattr(rutas, "_se_puede_escribir", lambda carpeta: False)
    assert rutas.directorio_datos() == rutas._en_el_perfil_del_usuario()


@pytest.mark.skipif(
    hasattr(__import__("os"), "geteuid") and __import__("os").geteuid() == 0,
    reason="root ignora los permisos de solo lectura — no se puede probar así",
)
def test_se_puede_escribir_detecta_una_carpeta_real_sin_permiso(tmp_path):
    protegida = tmp_path / "sin_permiso"
    protegida.mkdir()
    protegida.chmod(0o444)  # sólo lectura
    try:
        assert rutas._se_puede_escribir(protegida / "data") is False
    finally:
        protegida.chmod(0o755)  # para que tmp_path se pueda limpiar solo


def test_se_puede_escribir_detecta_un_permiso_denegado_al_escribir(tmp_path, monkeypatch):
    """Independiente de si la suite corre como root (que ignora los bits de
    solo-lectura del filesystem, como en este contenedor): se fuerza el mismo
    PermissionError que Windows tira al escribir en Archivos de Programa sin
    ser administrador, y se verifica que _se_puede_escribir lo capture."""
    from pathlib import Path

    original_write_text = Path.write_text

    def _write_text_que_falla(self, *a, **kw):
        if self.name == ".prueba_escritura":
            raise PermissionError("[Errno 13] Permission denied (simulado)")
        return original_write_text(self, *a, **kw)

    monkeypatch.setattr(Path, "write_text", _write_text_que_falla)
    assert rutas._se_puede_escribir(tmp_path / "protegida") is False


def test_se_puede_escribir_no_deja_basura_si_la_carpeta_no_existia(tmp_path):
    candidata = tmp_path / "nueva"
    assert not candidata.exists()
    assert rutas._se_puede_escribir(candidata) is True
    assert not candidata.exists(), (
        "la prueba de escritura tiene que limpiar la carpeta que creó sólo para probar")


def test_se_puede_escribir_no_borra_una_carpeta_que_ya_tenia_contenido(tmp_path):
    existente = tmp_path / "ya_existe"
    existente.mkdir()
    (existente / "algo.txt").write_text("no tocar")
    assert rutas._se_puede_escribir(existente) is True
    assert existente.exists()
    assert (existente / "algo.txt").exists(), (
        "no debe borrar contenido que no creó ella")


# ---------------------------------------------------------- MVPM_DATA_DIR

def test_la_variable_de_entorno_gana_siempre(congelado_en, monkeypatch, tmp_path):
    congelado_en()
    forzada = tmp_path / "forzado-a-mano"
    monkeypatch.setenv("MVPM_DATA_DIR", str(forzada))
    assert rutas.directorio_datos() == forzada


def test_sin_congelar_tambien_respeta_la_variable(no_congelado, monkeypatch, tmp_path):
    forzada = tmp_path / "forzado"
    monkeypatch.setenv("MVPM_DATA_DIR", str(forzada))
    assert rutas.directorio_datos() == forzada


# ------------------------------------------ que los módulos reales la usen

def test_db_licensing_reviews_y_owner_usan_el_mismo_directorio(no_congelado):
    """Si cada uno calculara el suyo por separado, un .exe instalado en D:\\
    podría terminar con la base en D:\\ pero la licencia en C:\\ — y el
    programa se vería roto sin ningún error visible."""
    from mvpm import db, licensing, owner, reviews

    esperado = rutas._en_el_perfil_del_usuario()
    assert db._STORE_DIR == esperado
    assert licensing._STORE_DIR == esperado
    assert reviews._STORE_DIR == esperado
    # El marcador de modo owner es distinto a propósito (ver mvpm/owner.py):
    # SIEMPRE en el perfil del usuario, nunca junto al .exe, aunque el
    # proceso esté congelado — si no, ./run.sh owner y el .exe instalado
    # terminan de acuerdo en un archivo distinto cada uno.
    assert owner.RUTAS_MARCADOR[0] == esperado / owner.MARCADOR
