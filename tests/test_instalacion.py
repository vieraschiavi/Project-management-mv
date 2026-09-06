# © 2026 Martín Viera. Todos los derechos reservados.
"""Los dos modos de instalación: normal (una PC) y servidor/VM del cliente.

El caso real: una consultora trabaja para un cliente, y la máquina donde se
instala no siempre pertenece a quien es dueño del dato. Confundir los modos
cuesta caro en las dos direcciones — publicar el tablero sin querer, o no
poder abrirlo cuando el cliente exige que su dato no salga de su VM.

Lo que se fija acá, en orden de qué tan caro sale si falla:

 1. **Que la instalación normal NO escuche en la red.** Streamlit, sin
    `--server.address`, escucha en TODAS las interfaces: el default publicaba
    el tablero en la red de la oficina con el login de la app como única
    puerta. Se verifica en las TRES formas de abrir el producto (run.sh, el
    .exe y el .bat portable), porque cerrar una y olvidar otra deja el agujero
    igual y encima da la sensación de haberlo tapado.
 2. **Que abrir a la red sea siempre explícito.** Un typo en la variable no
    puede terminar exponiendo nada: cualquier valor que no sea exactamente
    `servidor` cae en `local`.
 3. **Que el producto funcione IGUAL en los dos modos.** Era el pedido
    textual. Si el modo cambiara un número, dejaría de ser un modo de
    instalación y pasaría a ser otro producto.
"""

import re
from pathlib import Path

import pytest

from mvpm import instalacion

RAIZ = Path(__file__).resolve().parent.parent


# --------------------------------------------- elegir el modo es explícito

def test_sin_variable_la_instalacion_es_local():
    assert instalacion.modo_actual({}) == instalacion.LOCAL


@pytest.mark.parametrize("valor", [
    "Servidorr", "server", "", "   ", "1", "true", "vm", "si", "servidor,local",
])
def test_cualquier_cosa_que_no_sea_servidor_cae_en_local(valor):
    """Ante la duda, la opción cerrada. Un typo en la variable no puede
    terminar publicando el tablero del cliente en su red."""
    modo = instalacion.modo_actual({instalacion.VAR_MODO: valor})
    assert modo == instalacion.LOCAL, (
        f"{valor!r} abrió el modo servidor sin que nadie lo eligiera")


@pytest.mark.parametrize("valor", ["servidor", "SERVIDOR", "Servidor", " servidor "])
def test_servidor_tolera_mayusculas_y_espacios(valor):
    """Mayúsculas y espacios de más son errores de tipeo honestos, no un valor
    distinto: quien escribe `Servidor ` quiere el modo servidor. Lo que NO se
    tolera es una palabra parecida — eso lo cubre el test de arriba."""
    assert instalacion.modo_actual({instalacion.VAR_MODO: valor}) == instalacion.SERVIDOR


def test_cada_modo_escucha_donde_corresponde():
    assert instalacion.host_para(instalacion.LOCAL) == "127.0.0.1"
    assert instalacion.host_para(instalacion.SERVIDOR) == "0.0.0.0"


# ------------------------------- las TRES formas de abrir cierran la puerta

def test_run_sh_app_escucha_solo_en_esta_pc():
    """`./run.sh app` es la instalación normal."""
    run = (RAIZ / "run.sh").read_text(encoding="utf-8")
    rama = run.split("  app)", 1)[1].split(";;", 1)[0]
    assert "--server.address 127.0.0.1" in rama, (
        "./run.sh app volvió a escuchar en toda la red: sin --server.address, "
        "Streamlit se publica en todas las interfaces")


def test_run_sh_servidor_existe_y_avisa_antes_de_abrir():
    run = (RAIZ / "run.sh").read_text(encoding="utf-8")
    assert "  servidor)" in run, "no existe el modo servidor"
    rama = run.split("  servidor)", 1)[1].split(";;", 1)[0]
    assert "--server.address 0.0.0.0" in rama, "el modo servidor no abre a la red"
    assert "MVPM_MODO_INSTALACION=servidor" in rama, (
        "el modo servidor no se declara, así que mvpm.instalacion no lo detecta")
    assert "mvpm.instalacion" in rama, (
        "el modo servidor abre a la red sin imprimir qué implica")


def test_el_exe_de_escritorio_escucha_solo_en_esa_pc():
    launcher = (RAIZ / "packaging" / "mvpm_launcher.py").read_text(encoding="utf-8")
    assert '"--server.address"' in launcher, (
        "el .exe volvió a publicar el tablero en la red de la oficina")
    assert "instalacion.HOST_LOCAL" in launcher, (
        "el .exe fija la dirección a mano en vez de tomarla del módulo: dos "
        "fuentes para el mismo dato terminan divergiendo")


def test_el_bat_portable_escucha_solo_en_esa_pc():
    bat = (RAIZ / "MV_ProjectManagement.bat").read_text(
        encoding="utf-8", errors="replace")
    linea = [ln for ln in bat.splitlines()
             if "streamlit run" in ln and not ln.strip().upper().startswith("REM")]
    assert linea, "no se encontró el arranque de Streamlit en el .bat"
    assert all("--server.address 127.0.0.1" in ln for ln in linea), (
        "el .bat portable volvió a escuchar en toda la red")


def test_ninguna_forma_de_abrir_quedo_sin_cerrar():
    """El test que ata los tres de arriba. Cerrar dos de tres deja el agujero
    igual, y encima da la sensación de haberlo tapado."""
    fuentes = {
        "run.sh (app)": (RAIZ / "run.sh").read_text(encoding="utf-8")
                        .split("  app)", 1)[1].split(";;", 1)[0],
        ".exe": (RAIZ / "packaging" / "mvpm_launcher.py").read_text(encoding="utf-8"),
        ".bat portable": (RAIZ / "MV_ProjectManagement.bat").read_text(
            encoding="utf-8", errors="replace"),
    }
    sin_cerrar = [n for n, t in fuentes.items()
                  if "127.0.0.1" not in t and "HOST_LOCAL" not in t]
    assert not sin_cerrar, f"formas de abrir que siguen expuestas: {sin_cerrar}"


# ------------------------------------------------------ el chequeo avisa

def test_el_modo_servidor_recuerda_que_el_login_es_la_unica_puerta():
    r = instalacion.revisar({instalacion.VAR_MODO: "servidor"})
    assert r["expuesto_en_red"] is True
    assert any("login" in a.lower() for a in r["avisos"]), (
        "el modo servidor abre a la red sin recordar de qué depende la puerta")


def test_avisa_si_la_api_esta_abierta_sin_clave():
    r = instalacion.revisar({instalacion.VAR_MODO: "servidor",
                             "MVPM_API_HOST": "0.0.0.0"})
    assert any("MVPM_API_KEY" in a for a in r["avisos"])
    # Con la clave puesta, ese aviso puntual desaparece.
    r2 = instalacion.revisar({instalacion.VAR_MODO: "servidor",
                              "MVPM_API_HOST": "0.0.0.0",
                              "MVPM_API_KEY": "una-clave"})
    assert not any("MVPM_API_KEY" in a for a in r2["avisos"])


def test_avisa_la_combinacion_incoherente():
    """Instalación normal con la API abierta a la red: o es un descuido, o el
    modo que corresponde es servidor. Las dos cosas hay que decirlas."""
    r = instalacion.revisar({"MVPM_API_HOST": "0.0.0.0"})
    assert r["modo"] == instalacion.LOCAL
    assert any("servidor" in a for a in r["avisos"])


def test_el_informe_no_filtra_el_valor_de_ninguna_variable():
    """Mismo criterio que mvpm/configuracion.py: se dice si está, nunca cuánto
    vale. Este informe se pega en un chat pidiendo ayuda."""
    salida = instalacion.como_texto({
        instalacion.VAR_MODO: "servidor",
        "MVPM_API_HOST": "0.0.0.0",
        "MVPM_API_KEY": "CLAVE-SECRETA-QUE-NO-DEBE-APARECER",
    })
    assert "CLAVE-SECRETA-QUE-NO-DEBE-APARECER" not in salida


def test_doctor_informa_el_modo():
    run = (RAIZ / "run.sh").read_text(encoding="utf-8")
    rama = run.split("  doctor)", 1)[1].split(";;", 1)[0]
    assert "mvpm.instalacion" in rama, (
        "`./run.sh doctor` no dice en qué modo está la instalación")


# ------------------------------------------- los dos modos son trilingües

def test_los_dos_modos_estan_en_los_tres_idiomas():
    for lang in instalacion.LANGS:
        modos = instalacion.catalogo(lang)
        assert len(modos) == 2
        for m in modos:
            for campo in ("nombre", "para_que", "datos", "quien_entra", "exige"):
                assert m[campo].strip(), f"[{lang}] {m['clave']}.{campo} vacío"


@pytest.mark.parametrize("lang", ["en", "pt"])
def test_ninguna_descripcion_quedo_sin_traducir(lang):
    iguales = [
        f"{es['clave']}.{campo}"
        for es, otro in zip(instalacion.catalogo("es"), instalacion.catalogo(lang))
        for campo in ("nombre", "para_que", "datos", "quien_entra", "exige")
        if es[campo] == otro[campo]
    ]
    assert not iguales, f"sin traducir al {lang}: {iguales}"


# ------------------------------------------ "y que funcione igual" (el pedido)

def test_el_motor_da_LO_MISMO_en_los_dos_modos(monkeypatch):
    """El pedido textual era «bien discriminadas las formas de instalar y
    funcione igual». El modo decide dónde escucha el servidor y nada más: si
    llegara a cambiar un número del portafolio, dejaría de ser un modo de
    instalación y pasaría a ser otro producto."""
    from mvpm import catalog, demo_data, dependencies, health, policies, prioritizer

    p, t, e = demo_data.projects(), demo_data.tasks(), demo_data.team()

    def foto() -> dict:
        return {
            "kpis": catalog.kpis(p),
            "indice": health.overall_index(p, t, e),
            "estados": health.project_health(p, t, e)["estado"].value_counts().to_dict(),
            "bloqueos": len(dependencies.bloqueos_activos(t)),
            "huerfanas": len(dependencies.orphan_dependencies(t)),
            "backlog": len(prioritizer.prioritized_backlog(p, t)),
            "politicas": sorted(policies.evaluate(p, t, e)["clave"]),
        }

    monkeypatch.delenv(instalacion.VAR_MODO, raising=False)
    assert instalacion.modo_actual() == instalacion.LOCAL
    en_local = foto()

    monkeypatch.setenv(instalacion.VAR_MODO, "servidor")
    assert instalacion.modo_actual() == instalacion.SERVIDOR
    en_servidor = foto()

    assert en_local == en_servidor, (
        "el modo de instalación cambió los números del motor: tiene que decidir "
        "dónde escucha el servidor y nada más")


def test_el_modo_no_toca_donde_vive_el_dato():
    """En los dos modos la base vive en la máquina donde corre el programa —
    que es exactamente el argumento ante el área de seguridad del cliente: en
    modo servidor el dato se queda en SU VM y no viaja a la laptop de quien lo
    instaló."""
    fuente = (RAIZ / "mvpm" / "db.py").read_text(encoding="utf-8")
    assert instalacion.VAR_MODO not in fuente, (
        "mvpm/db.py mira el modo de instalación: la ubicación del dato dejó de "
        "ser 'la máquina donde corre' y pasó a depender de una variable")


def test_la_documentacion_explica_los_dos_modos():
    """Un modo que no está escrito no existe: nadie va a adivinar que hay que
    exportar una variable para instalar en la VM del cliente."""
    textos = []
    for archivo in ("README.md", "owner/PUESTA_EN_PRODUCCION.md"):
        ruta = RAIZ / archivo
        if ruta.exists():
            textos.append(ruta.read_text(encoding="utf-8"))
    completo = "\n".join(textos)
    assert "run.sh servidor" in completo, (
        "la documentación no menciona cómo instalar en la VM del cliente")
    assert re.search(r"MVPM_MODO_INSTALACION", completo), (
        "la documentación no nombra la variable que elige el modo")
