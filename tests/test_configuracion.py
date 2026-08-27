# © 2026 Martín Viera. Todos los derechos reservados.
"""mvpm/configuracion.py — el inventario de variables y `./run.sh doctor`.

Lo que se fija acá, en orden de qué tan caro sale si falla:

 1. Que NUNCA se imprima el valor de un secreto. Un informe de configuración
    que muestra la clave privada es peor que no tener informe: queda en la
    terminal, en el scrollback y en el primer log que alguien pegue en un chat
    pidiendo ayuda.
 2. Que el inventario no se desincronice de `.env.example`. Si alguien agrega
    una variable en un lado y se olvida del otro, la respuesta a "¿está todo
    configurado?" vuelve a ser una opinión, que es justo lo que este módulo
    vino a arreglar.
 3. Que lo que bloquea la venta esté marcado como tal — es la diferencia entre
    "falta algo" y "cobrás y no entregás".
"""

import re
from pathlib import Path

from mvpm import configuracion

RAIZ = Path(__file__).resolve().parent.parent


def test_no_imprime_el_valor_de_ningun_secreto():
    """El test que importa. Se le pasa un entorno con valores reconocibles y se
    exige que NINGUNO aparezca en la salida."""
    veneno = {
        "MP_ACCESS_TOKEN": "APP_USR-VALOR-SECRETO-1",
        "MVPM_LICENSE_PRIVATE_KEY": "VALOR-SECRETO-2-clave-privada",
        "BLOB_READ_WRITE_TOKEN": "vercel_blob_rw_VALOR-SECRETO-3",
        "RESEND_API_KEY": "re_VALOR-SECRETO-4",
        "MVPM_OWNER_TOKEN": "VALOR-SECRETO-5",
        "ANTHROPIC_API_KEY": "sk-ant-VALOR-SECRETO-6",
    }
    salida = configuracion.como_texto(veneno)
    for nombre, valor in veneno.items():
        assert valor not in salida, f"el informe filtró el valor de {nombre}"
    # Y sin embargo tiene que decir que están configuradas.
    for nombre in veneno:
        assert nombre in salida, f"{nombre} no aparece en el informe"


def test_revisar_tampoco_devuelve_valores():
    """`revisar()` es la que consume cualquier otro código: si devolviera el
    valor, el filtrado sería cuestión de que alguien lo imprima más arriba."""
    r = configuracion.revisar({"MP_ACCESS_TOKEN": "APP_USR-SECRETO"})
    plano = repr(r)
    assert "APP_USR-SECRETO" not in plano
    fila = next(f for f in r["filas"] if f["nombre"] == "MP_ACCESS_TOKEN")
    assert fila["configurada"] is True
    assert "valor" not in fila


def test_entorno_vacio_marca_lo_que_bloquea_la_venta():
    r = configuracion.revisar({})
    assert r["puede_vender"] is False
    # Las tres sin las cuales se cobra y no se entrega.
    assert set(r["faltan_criticas"]) == {
        "MP_ACCESS_TOKEN", "MVPM_LICENSE_PRIVATE_KEY", "BLOB_READ_WRITE_TOKEN"}


def test_con_las_criticas_puestas_puede_vender():
    r = configuracion.revisar({
        "MP_ACCESS_TOKEN": "x",
        "MVPM_LICENSE_PRIVATE_KEY": "x",
        "BLOB_READ_WRITE_TOKEN": "x",
    })
    assert r["puede_vender"] is True
    assert r["faltan_criticas"] == []


def test_una_variable_en_blanco_cuenta_como_faltante():
    """`MP_ACCESS_TOKEN=` en el .env es el error más fácil de cometer: la
    variable existe, así que un chequeo por `in os.environ` la daría por
    puesta y el 503 aparecería igual, sin explicación."""
    r = configuracion.revisar({"MP_ACCESS_TOKEN": "   "})
    assert "MP_ACCESS_TOKEN" in r["faltan_criticas"]


def test_el_inventario_y_env_example_no_se_desincronizan():
    """Toda variable del inventario tiene que estar en `.env.example`, salvo
    las de GitHub Actions, que no van en un archivo .env y ahí se listan como
    comentario."""
    texto = (RAIZ / ".env.example").read_text(encoding="utf-8")
    declaradas = set(re.findall(r"^([A-Z][A-Z0-9_]*)=", texto, re.MULTILINE))
    mencionadas = set(re.findall(r"\b([A-Z][A-Z0-9_]{4,})\b", texto))

    faltan = []
    for v in configuracion.INVENTARIO:
        if v.donde == configuracion.ACTIONS:
            if v.nombre not in mencionadas:
                faltan.append(f"{v.nombre} (ni mencionada)")
        elif v.nombre not in declaradas:
            faltan.append(v.nombre)
    assert not faltan, (
        "variables del inventario que faltan en .env.example: " + ", ".join(faltan))


def test_env_example_no_trae_ningun_valor_cargado():
    """`.env.example` SÍ se versiona, así que no puede traer un valor de
    verdad. Cada línea `VAR=` tiene que estar vacía o traer un default
    inofensivo y declarado."""
    texto = (RAIZ / ".env.example").read_text(encoding="utf-8")
    DEFAULTS_OK = {"MP_CURRENCY": "UYU", "MP_TASA_UYU": "40",
                   "MVPM_API_HOST": "127.0.0.1"}
    con_valor = []
    for linea in texto.splitlines():
        m = re.match(r"^([A-Z][A-Z0-9_]*)=(.*)$", linea)
        if not m:
            continue
        nombre, valor = m.group(1), m.group(2).strip()
        if valor and DEFAULTS_OK.get(nombre) != valor:
            con_valor.append(f"{nombre}={valor}")
    assert not con_valor, (
        ".env.example trae valores cargados (se versiona, tienen que ir "
        "vacíos): " + ", ".join(con_valor))


def test_env_esta_ignorado_por_git_y_env_example_no():
    """El agujero que esto vino a tapar: `.env` no estaba en .gitignore, así
    que un .env real con la clave privada se commiteaba a un repo PÚBLICO."""
    reglas = (RAIZ / ".gitignore").read_text(encoding="utf-8").splitlines()
    reglas = [r.strip() for r in reglas if r.strip() and not r.startswith("#")]
    assert ".env" in reglas, ".env tiene que estar en .gitignore"
    assert "!.env.example" in reglas, ".env.example tiene que quedar versionable"


def test_run_sh_expone_el_comando_doctor():
    contenido = (RAIZ / "run.sh").read_text(encoding="utf-8")
    assert "doctor)" in contenido
    assert "mvpm.configuracion" in contenido
