# © 2026 Martín Viera. Todos los derechos reservados.
"""Respaldo y restauración: que la copia tenga TODO y que restaurar no destruya.

El portafolio entero de un cliente vive en un archivo SQLite dentro de su VM.
Hasta ahora el producto no ofrecía ni sacar una copia ni volver de ella, y lo
único parecido —`mvpm/exporters.py`— exporta las tablas derivadas: sirve para
mirar en Excel, no para restaurar.

Los dos fallos que esta suite fija son los que no se notan hasta el peor día:

**Una copia que abre bien y está incompleta.** La base corre en WAL, así que
las transacciones recientes viven en `datos.db-wal` hasta el checkpoint.
Copiar sólo `datos.db` con la aplicación abierta da un archivo que abre sin
error, pasa el chequeo de integridad y no tiene lo último que se guardó. Está
medido abajo, con la copia casera al lado del respaldo de verdad, porque la
diferencia entre los dos es justamente lo que nadie ve hasta que restaura.

**Una restauración que pisa la base con cualquier cosa.** Restaurar es la
única operación del producto que destruye datos. Un archivo corrupto, uno
truncado a medio bajar o uno de otro programa no puede llegar a tocar nada.
"""

import sqlite3

import pytest

from mvpm import db, respaldo


@pytest.fixture(autouse=True)
def base_aislada(tmp_path, monkeypatch):
    """Base propia por test, con la convención del resto de la suite
    (`monkeypatch` sobre las rutas y NO un reload del módulo, que deja a
    `mvpm.db` apuntando a un temporal para todo lo que corra después)."""
    monkeypatch.setattr(db, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(db, "_DB_FILE", tmp_path / "datos.db")
    db.init_db()


def _con_datos() -> int:
    empresa = db.obtener_o_crear_empresa("Conaprole")
    db.guardar_version(empresa, "gobernanza", "politica", "DATO-VIEJO", "vigente")
    return empresa


def _contenidos(ruta) -> list[str]:
    conn = sqlite3.connect(ruta)
    try:
        return [f[0] for f in conn.execute("SELECT contenido FROM versiones")]
    finally:
        conn.close()


# ------------------------------------------- el respaldo se lleva TODO el dato

def test_el_respaldo_incluye_lo_que_todavia_esta_en_el_wal(tmp_path):
    """EL test de este módulo.

    Con la aplicación abierta, copiar el `.db` a mano pierde lo último que se
    guardó, en silencio. Acá se hacen las dos copias sobre la MISMA base y en
    el mismo instante: la casera y la de verdad. Si alguna vez el respaldo
    volviera a hacerse con un `copyfile`, este test lo dice.
    """
    empresa = _con_datos()

    # Una conexión viva = la aplicación corriendo mientras alguien respalda.
    viva = sqlite3.connect(db._DB_FILE)
    viva.execute("PRAGMA journal_mode = WAL")
    viva.execute("SELECT 1").fetchone()
    try:
        db.guardar_version(empresa, "gobernanza", "politica",
                           "DATO-NUEVO-CRITICO", "vigente")

        import shutil
        casera = tmp_path / "casera.db"
        shutil.copyfile(db._DB_FILE, casera)

        bueno = respaldo.crear(tmp_path / "bueno.db")
    finally:
        viva.close()

    assert "DATO-NUEVO-CRITICO" in _contenidos(bueno), (
        "el respaldo perdió lo último que se guardó: se está copiando el "
        "archivo en vez de usar la API de respaldo de SQLite")
    assert "DATO-NUEVO-CRITICO" not in _contenidos(casera), (
        "la copia casera dejó de perder datos: si SQLite cambió de "
        "comportamiento, revisá si este respaldo sigue haciendo falta tal cual")


def test_el_respaldo_es_UN_solo_archivo(tmp_path):
    """Un respaldo que necesita tres archivos al lado es un respaldo que
    alguien va a mandar por mail incompleto."""
    _con_datos()
    destino = respaldo.crear(tmp_path / "copia.db")
    sueltos = sorted(p.name for p in destino.parent.glob("copia.db-*"))
    assert not sueltos, f"el respaldo dejó archivos sueltos al lado: {sueltos}"
    assert destino.exists()


def test_el_respaldo_se_lleva_las_tablas_que_exportar_deja_afuera():
    """`exporters.py` exporta proyectos y tareas. Un respaldo sin usuarios ni
    el historial de `versiones` no permite volver al estado anterior — y ese
    historial es, por diseño del producto, lo que nunca se pisa."""
    empresa = _con_datos()
    db.guardar_version(empresa, "gobernanza", "politica", "CORREGIDO", "vigente")
    datos = respaldo.a_bytes()
    revision = respaldo.verificar(datos)
    assert revision["valido"]
    assert revision["conteos"]["versiones"] == 2, (
        "el respaldo no trae el historial completo de versiones")
    assert "usuarios" in revision["conteos"]


# ------------------------------------------------- verificar antes de destruir

def test_rechaza_un_archivo_que_no_es_una_base():
    revision = respaldo.verificar(b"%PDF-1.4 esto es un PDF")
    assert not revision["valido"]
    assert "SQLite" in revision["motivo"]


def test_rechaza_una_base_de_otro_programa(tmp_path):
    ajena = tmp_path / "ajena.db"
    conn = sqlite3.connect(ajena)
    conn.execute("CREATE TABLE cosas (a TEXT)")
    conn.commit()
    conn.close()
    revision = respaldo.verificar(ajena)
    assert not revision["valido"]
    assert "este programa" in revision["motivo"]


def test_rechaza_un_archivo_truncado(tmp_path):
    """El caso real: una descarga cortada por la mitad. El archivo existe,
    parece una base y no lo es."""
    _con_datos()
    entero = respaldo.crear(tmp_path / "entero.db").read_bytes()
    cortado = tmp_path / "cortado.db"
    cortado.write_bytes(entero[:len(entero) // 3])
    assert not respaldo.verificar(cortado)["valido"]


def test_un_archivo_invalido_no_llega_a_tocar_la_base():
    """Lo que de verdad importa de verificar: que el rechazo ocurra ANTES de
    pisar nada. Si la base quedara a medio reemplazar, el cliente perdería el
    portafolio por intentar restaurarlo."""
    empresa = _con_datos()
    with pytest.raises(ValueError):
        respaldo.restaurar(b"no soy una base")
    vigente = db.obtener_version_actual(empresa, "gobernanza", "politica")
    assert vigente["contenido"] == "DATO-VIEJO"


# --------------------------------------------------------- la vuelta completa

def test_respaldar_seguir_trabajando_y_volver_al_respaldo():
    empresa = _con_datos()
    copia = respaldo.a_bytes()

    db.guardar_version(empresa, "gobernanza", "politica", "POSTERIOR", "vigente")
    assert db.obtener_version_actual(
        empresa, "gobernanza", "politica")["contenido"] == "POSTERIOR"

    respaldo.restaurar(copia)
    vigente = db.obtener_version_actual(empresa, "gobernanza", "politica")
    assert vigente["contenido"] == "DATO-VIEJO", (
        "restaurar no dejó la base como estaba en el respaldo")


def test_restaurar_guarda_la_base_anterior_por_las_dudas():
    """Equivocarse de archivo tiene que ser reversible, no terminal: es la
    diferencia entre un susto y perder el portafolio de un cliente."""
    empresa = _con_datos()
    copia = respaldo.a_bytes()
    db.guardar_version(empresa, "gobernanza", "politica", "POSTERIOR", "vigente")

    resultado = respaldo.restaurar(copia)
    previa = resultado["copia_previa"]
    assert previa, "no se guardó copia de la base que se pisó"
    assert "POSTERIOR" in _contenidos(previa), (
        "la copia de seguridad no tiene lo que había antes de restaurar: "
        "no sirve para deshacer")


def test_el_nombre_sugerido_lleva_fecha_para_que_dos_no_se_pisen():
    from datetime import datetime, timezone
    uno = respaldo.nombre_sugerido(datetime(2026, 3, 4, 9, 5, tzinfo=timezone.utc))
    assert uno == "mvpm_respaldo_2026-03-04_0905.db"


# ------------------------------------------------------------- en la pantalla

def test_la_pantalla_de_respaldo_abre_y_ofrece_la_descarga(tmp_path, monkeypatch):
    """Cruza el motor con la interfaz: sin esto, todo lo de arriba puede estar
    verde con la pantalla rota o desconectada.

    Vale la pena en esta sección más que en otras porque el respaldo se arma
    AL apretar el botón (`respaldo.a_bytes()` se evalúa al dibujar): si esa
    llamada explotara, la pantalla entera quedaría inservible justo para el
    admin que viene a sacar una copia antes de una migración.
    """
    import pathlib

    from streamlit.testing.v1 import AppTest

    # Base aislada. No alcanza con la variable de entorno: `mvpm/db.py`
    # resuelve su ruta una sola vez, al importarse, y acá ya está importado.
    monkeypatch.setenv("MVPM_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(db, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(db, "_DB_FILE", tmp_path / "datos.db")

    raiz = pathlib.Path(__file__).resolve().parent.parent
    at = AppTest.from_file(str(raiz / "app" / "app.py"), default_timeout=120)
    at.run()

    # Primera cuenta del servidor: es admin, que es quien ve esta sección.
    at.text_input[0].set_value("Tester")
    at.text_input[1].set_value("tester@ejemplo.com")
    at.text_input[2].set_value("Turbina-9-Verde")
    [b for b in at.button if "administrador" in b.label][0].click().run()
    assert not at.exception

    at.radio[0].set_value("Respaldo y restauración").run()
    assert not at.exception, f"la pantalla de respaldo explotó: {at.exception}"

    etiquetas = [b.label for b in at.download_button]
    assert any("Descargar respaldo" in e for e in etiquetas), (
        f"no está el botón de descarga; los que hay: {etiquetas}")
