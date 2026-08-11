"""`run.sh` es el único punto de entrada documentado en Linux/Mac (CLAUDE.md y
README lo usan para instalar, correr, testear y empaquetar). Estos tests fijan
que el flujo documentado funcione en una máquina limpia.
"""

from pathlib import Path

RUN_SH = Path(__file__).resolve().parent.parent / "run.sh"


def test_run_sh_usa_el_venv_que_creo_install():
    """`install` arma `.venv` e instala ahí las dependencias, pero el `source`
    de esa rama muere junto con el proceso del script. Sin activarlo también
    para los demás comandos, el flujo que documenta CLAUDE.md —`./run.sh
    install` y después `./run.sh app`— fallaba en una máquina limpia: `app` y
    `api` buscaban `streamlit`/`uvicorn` en el PATH del sistema (donde no
    están) y `test` corría con el pytest del sistema, que no ve `cryptography`
    y moría importando `tests/conftest.py`.

    Se fija que la activación esté ANTES del `case`, que es lo que la hace
    valer para todos los comandos y no sólo para `install`.
    """
    contenido = RUN_SH.read_text()

    assert "source .venv/bin/activate" in contenido, (
        "run.sh tiene que activar el .venv que arma `install`")

    pos_activate = contenido.index("source .venv/bin/activate")
    pos_case = contenido.index('case "$cmd" in')
    assert pos_activate < pos_case, (
        "la activación del .venv quedó adentro del `case`: así sólo vale para "
        "el comando que la contiene. Tiene que estar antes, para que `app`, "
        "`api`, `test` y `portable` usen el mismo intérprete que `install`.")


def test_run_sh_no_explota_si_todavia_no_hay_venv():
    """La activación tiene que ser condicional: en un checkout recién clonado
    `.venv` no existe todavía, y `set -euo pipefail` convierte un `source` de
    un archivo inexistente en una salida con error — o sea que `./run.sh
    install`, que es justamente el comando que lo crea, no podría ni arrancar.
    """
    contenido = RUN_SH.read_text()
    assert "if [ -d .venv ]" in contenido, (
        "el `source` del .venv tiene que estar guardado por un chequeo de "
        "existencia, si no `./run.sh install` falla en un clon limpio")
