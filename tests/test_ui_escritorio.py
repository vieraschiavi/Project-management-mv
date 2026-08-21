# © 2026 Martín Viera. Todos los derechos reservados.
"""La interfaz React de escritorio, contra el motor que consume.

La versión `.exe` dejó de usar Streamlit: React consume `api/main.py` y dibuja
el portafolio con componentes propios. El motor es el mismo, pero ahora hay una
capa más escrita en OTRO lenguaje, y con eso aparece una clase de bug que antes
no existía — que las dos se separen.

No es hipotético: escribí `color()` en `App.jsx` con umbrales 70/40 antes de
mirar `mvpm/health.py`, donde son 55 y 75. La interfaz habría pintado de verde
proyectos que el motor considera en observación, sin que nada fallara. Estos
tests existen para que esa clase de error salga acá y no en la pantalla de un
cliente.
"""

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
UI = RAIZ / "desktop" / "ui" / "src"

if not UI.exists():
    pytest.skip("desktop/ no viaja en el paquete: es del repositorio",
                allow_module_level=True)

APP = (UI / "App.jsx").read_text(encoding="utf-8")
I18N = (UI / "i18n.js").read_text(encoding="utf-8")
API_JS = (UI / "api.js").read_text(encoding="utf-8")


# ------------------------------------------- que la UI no invente umbrales

def test_los_umbrales_del_semaforo_son_los_del_motor():
    """`mvpm/health.py` decide: < 55 riesgo, < 75 observación, resto saludable.
    Si la interfaz usa otros, pinta de un color lo que el motor llama de otro
    — y las dos pantallas del mismo producto dicen cosas distintas."""
    motor = (RAIZ / "mvpm" / "health.py").read_text(encoding="utf-8")
    linea = next(ln for ln in motor.splitlines() if 'estado = "riesgo"' in ln)
    numeros = [int(n) for n in re.findall(r"indice < (\d+)", linea)]
    assert len(numeros) == 2, f"no pude leer los umbrales del motor: {linea!r}"
    riesgo, observacion = numeros

    ui = {n: int(v) for n, v in re.findall(r"const (UMBRAL_\w+) = (\d+);", APP)}
    assert ui.get("UMBRAL_RIESGO") == riesgo, (
        f"la interfaz usa {ui.get('UMBRAL_RIESGO')} y el motor {riesgo}")
    assert ui.get("UMBRAL_OBSERVACION") == observacion, (
        f"la interfaz usa {ui.get('UMBRAL_OBSERVACION')} y el motor {observacion}")


def test_los_estados_que_pinta_la_ui_son_los_que_emite_el_motor():
    """`COLOR_ESTADO` mapea el `estado` de cada fila a un color. Si el motor
    emitiera un estado que la interfaz no conoce, esa fila quedaría gris sin
    ningún aviso — parecería un dato faltante y sería un mapeo incompleto."""
    from mvpm import db, exporters

    db.init_db()
    del exporters  # sólo se necesitaba para forzar el import del motor

    motor = (RAIZ / "mvpm" / "health.py").read_text(encoding="utf-8")
    linea = next(ln for ln in motor.splitlines() if 'estado = "riesgo"' in ln)
    del_motor = set(re.findall(r'"(\w+)"', linea))

    bloque = APP[APP.index("const COLOR_ESTADO"):]
    bloque = bloque[:bloque.index("}")]
    de_la_ui = set(re.findall(r"(\w+):\s*'", bloque))

    faltan = sorted(del_motor - de_la_ui)
    assert not faltan, f"la interfaz no sabe pintar estos estados del motor: {faltan}"


def test_las_dimensiones_de_salud_son_las_del_motor():
    """El panorama promedia por dimensión. Una dimensión de más da una barra
    siempre en cero; una de menos la esconde, y el usuario ve un promedio de
    cinco cosas creyendo que son seis."""
    from mvpm import health

    bloque = APP[APP.index("const DIMENSIONES"):]
    bloque = bloque[:bloque.index("]")]
    de_la_ui = re.findall(r"'(\w+)'", bloque)
    assert de_la_ui == list(health.DIMENSIONS), (
        f"interfaz {de_la_ui} vs motor {list(health.DIMENSIONS)}")


def test_el_estado_de_tarea_que_filtra_la_ui_existe_en_el_motor():
    """El panorama cuenta tareas abiertas comparando contra 'done'. Escribí
    'hecho' en el primer intento: el contador habría mostrado SIEMPRE el total
    de tareas, y nadie lo hubiera notado sin contar a mano."""
    from mvpm import demo_data

    estados = set(demo_data.tasks()["estado"].unique())
    usados = set(re.findall(r"x\.estado !== '(\w+)'", APP))
    assert usados, "la interfaz no filtra por ningún estado de tarea"
    desconocidos = sorted(usados - estados)
    assert not desconocidos, (
        f"la interfaz compara contra estados que el motor no emite: "
        f"{desconocidos}. Los reales: {sorted(estados)}")


# ------------------------------------------------- que la UI pida lo que hay

def test_las_tablas_que_pide_la_ui_existen_en_la_api():
    """`portafolio()` pide seis tablas por nombre. Un nombre que la API no
    conoce devuelve 404 y deja la pantalla entera en error, no sólo esa vista."""
    from mvpm import db, exporters

    db.init_db()
    disponibles = set(exporters.portfolio_tables(db.projects(), db.tasks(), db.team()))
    pedidas = set(re.findall(r"tabla\('([\w_]+)'\)", API_JS))
    assert pedidas, "no encontré ninguna tabla pedida en api.js"
    inexistentes = sorted(pedidas - disponibles)
    assert not inexistentes, (
        f"la interfaz pide tablas que la API no sirve: {inexistentes}. "
        f"Las que hay: {sorted(disponibles)}")


def test_los_endpoints_de_licencia_que_usa_la_ui_existen():
    """La pantalla de licencia es la única salida de una instalación con la
    prueba vencida. Si una de sus rutas no existiera, el cliente que está por
    pagar quedaría sin forma de activar lo que compró."""
    from api import main

    rutas = {r.path for r in main.app.routes}
    for ruta in sorted(set(re.findall(r"pedir\('(/[\w/]+)'", API_JS))):
        assert ruta in rutas, f"la interfaz llama a {ruta} y la API no la expone"


def test_los_endpoints_de_licencia_no_estan_detras_del_candado():
    """El candado sin llave adentro: si `/licencias/acceso` exigiera licencia,
    una instalación con la prueba vencida recibiría 402 al preguntarlo, la
    interfaz no podría explicar qué pasa ni ofrecer activar, y el cliente
    quedaría en una pantalla de error sin salida — justo cuando iba a pagar."""
    from api import main

    for ruta in ("/licencias/acceso", "/licencias/activar", "/licencias/estado"):
        r = next(x for x in main.app.routes if x.path == ruta)
        nombres = [d.call.__name__ for d in r.dependant.dependencies
                   if getattr(d, "call", None)]
        assert "requiere_acceso" not in nombres, (
            f"{ruta} está detrás de requiere_acceso: sin licencia no se puede "
            "cargar la licencia")
        assert "solo_local" in nombres, (
            f"{ruta} no exige ni siquiera ser local: quedaría abierta")


# --------------------------------------------------------- paridad de idiomas

def _claves(lang: str) -> list[str]:
    bloque = I18N[I18N.index(f"const {lang} = {{"):]
    bloque = bloque[:bloque.index("\n};")]
    return re.findall(r"^\s{2}(\w+):", bloque, re.MULTILINE)


@pytest.mark.parametrize("lang", ["EN", "PT"])
def test_los_tres_idiomas_tienen_las_mismas_claves(lang):
    """La misma regla que `test_i18n_parity_all_languages` para el motor. Sin
    esto, una clave sólo en español deja texto en español dentro de la interfaz
    en inglés — y el fallback es silencioso a propósito, así que no hay ningún
    error que lo delate."""
    es, otro = set(_claves("ES")), set(_claves(lang))
    assert not (es - otro), f"faltan en {lang}: {sorted(es - otro)}"
    assert not (otro - es), f"sobran en {lang}: {sorted(otro - es)}"


@pytest.mark.parametrize("lang", ["ES", "EN", "PT"])
def test_ninguna_clave_esta_declarada_dos_veces(lang):
    claves = _claves(lang)
    repetidas = sorted({c for c in claves if claves.count(c) > 1})
    assert not repetidas, f"claves duplicadas en {lang}: {repetidas}"


def test_toda_clave_usada_en_la_interfaz_esta_traducida():
    """Una `t('nav_x')` sin entrada muestra `nav_x` crudo en pantalla."""
    usadas = set(re.findall(r"t\('([\w_]+)'", APP))
    # Las que se arman por interpolación se listan a mano: el regex no las ve.
    def _lista(nombre):
        """Los literales de una constante, cortando en su `]` — y no a N
        caracteres, que se comía la constante siguiente y daba claves como
        `nav_alcance`, que no existen ni tienen por qué existir."""
        bloque = APP[APP.index(f"const {nombre}"):]
        return re.findall(r"'(\w+)'", bloque[:bloque.index("]")])

    dinamicas = {f"dim_{d}" for d in _lista("DIMENSIONES")}
    dinamicas |= {f"nav_{v}" for v in _lista("VISTAS")}
    dinamicas |= {f"col_{c}" for c in []}
    dinamicas |= {"estado_saludable", "estado_observacion", "estado_riesgo"}
    declaradas = set(_claves("ES"))
    faltan = sorted((usadas | dinamicas) - declaradas)
    assert not faltan, f"claves usadas en App.jsx y no traducidas: {faltan}"


# -------------------------------------------------------- el bundle y su CSP

def test_el_bundle_no_baja_nada_de_internet():
    """El programa promete funcionar sin conexión y se instala en PCs
    corporativas que a veces no tienen salida. Un `<script src="https://…">`
    lo rompería justo en esas, y sólo en esas — o sea, nunca en la máquina de
    quien lo probó."""
    build = (RAIZ / "desktop" / "scripts" / "build-ui.mjs").read_text(encoding="utf-8")
    assert "bundle: true" in build, "esbuild no está empaquetando las dependencias"

    dist = RAIZ / "desktop" / "ui" / "dist" / "index.html"
    if not dist.exists():
        pytest.skip("ui/dist no está construido (npm run build-ui)")
    html = dist.read_text(encoding="utf-8")
    externos = re.findall(r'(?:src|href)="(https?://[^"]+)"', html)
    assert not externos, f"la interfaz carga recursos externos: {externos}"
    assert "default-src 'self'" in html, "falta la CSP"
    assert "unsafe-eval" not in html, "la CSP permite eval"


def test_la_api_monta_la_interfaz_en_app():
    """Sin este montaje la ventana de Electron abre en blanco con un 404, y el
    síntoma aparece recién después de instalar."""
    main_py = (RAIZ / "api" / "main.py").read_text(encoding="utf-8")
    assert 'app.mount("/app"' in main_py
    assert "MVPM_UI_DIR" in main_py, (
        "sin la variable de entorno, el .exe instalado no encuentra el bundle: "
        "electron-builder no deja la carpeta al lado de api/")


def test_electron_carga_la_barra_final():
    """`/app` sin barra devuelve un 307 y la ventana parpadea en cada arranque."""
    main_js = (RAIZ / "desktop" / "main.js").read_text(encoding="utf-8")
    assert "/app/`" in main_js, "main.js carga /app sin la barra final"


def test_la_ventana_no_le_da_acceso_al_sistema_a_la_interfaz():
    """La ventana carga HTTP local. Con `nodeIntegration`, cualquier cosa que
    se cuele en la interfaz tendría `require` y el disco entero."""
    main_js = (RAIZ / "desktop" / "main.js").read_text(encoding="utf-8")
    assert "nodeIntegration: false" in main_js
    assert "contextIsolation: true" in main_js


def test_el_bundle_no_se_commitea():
    """`ui/dist` es un artefacto de build: commitearlo lo deja envejecer
    respecto del código, que es exactamente lo que pasó con el ZIP de la
    landing durante meses."""
    gitignore = (RAIZ / ".gitignore").read_text(encoding="utf-8")
    assert any("ui/dist" in ln for ln in gitignore.splitlines()), (
        "desktop/ui/dist no está en .gitignore")


def test_la_interfaz_no_recalcula_lo_que_el_motor_ya_resolvio():
    """La regla de esta capa: mostrar, no calcular. El índice de salud, el
    valor esperado y el estado llegan resueltos. Si la interfaz los recalculara,
    habría dos motores y uno se quedaría atrás."""
    # Un `const indice = ...` NO es sospechoso por sí solo: el panorama
    # promedia el índice que ya viene calculado, y eso es mostrar, no calcular.
    # Lo que no puede pasar es que ese valor se DERIVE de las dimensiones, que
    # es la fórmula del motor. Se exige que todo cálculo de índice lea `.indice`.
    for m in re.finditer(r"const (indice|valor\w*) = ([^;]+);", APP):
        nombre, expresion = m.group(1), m.group(2)
        assert ".indice" in expresion or "valor_esperado" in expresion, (
            f"`{nombre}` se calcula sin leer el valor del motor: {expresion[:90]!r}")
        assert "dim_" not in expresion, (
            f"`{nombre}` se deriva de las dimensiones: eso es la fórmula del "
            "motor, y tenerla dos veces garantiza que se separen")

    # Y los pesos de la fórmula no pueden aparecer acá de ninguna forma.
    for prohibido in ["PESOS", "weights", "WEIGHTS"]:
        assert prohibido not in APP, (
            f"App.jsx parece traer la fórmula del motor: {prohibido!r}")
