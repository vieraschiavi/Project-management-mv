# © 2026 Martín Viera. Todos los derechos reservados.
"""Los `.bat` tienen que poder correr en Windows, que es donde se usan.

Este archivo existe por un bug que estuvo desde el primer commit y que nadie
podía ver desde Linux: los dos `.bat` se escribieron con finales de línea de
Unix (LF), y `cmd.exe` necesita CRLF.

Con LF solo, cmd tolera comandos sueltos pero **rompe los bloques `if (...)` y
`for`** — que es exactamente de lo que están hechos estos archivos: cuatro
`if errorlevel 1 (...)` y un `for /f` que resuelve el puerto. El programa "no
abría" y no había forma de darse cuenta editándolo en Linux, donde se ve igual.

Ninguna suite de tests lo agarraba porque los tests corren en Linux, donde el
`.bat` ni se ejecuta. Por eso se revisa el ARCHIVO, no su comportamiento.
"""

import zipfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
BATS = sorted(RAIZ.glob("*.bat"))


def test_hay_bats_para_revisar():
    """Si alguien los renombra o los mueve, este archivo dejaría de proteger
    nada y pasaría en verde sin revisar absolutamente nada."""
    assert BATS, "no se encontró ningún .bat en la raíz del repo"


@pytest.mark.parametrize("bat", BATS, ids=lambda p: p.name)
def test_los_bats_usan_finales_de_linea_de_windows(bat):
    """CRLF en TODAS las líneas. Una sola con LF alcanza para que cmd.exe
    malinterprete el bloque que la contiene."""
    crudo = bat.read_bytes()
    lineas = crudo.split(b"\n")
    # La última puede no tener salto; se descarta si quedó vacía.
    if lineas and lineas[-1] == b"":
        lineas = lineas[:-1]
    sin_cr = [i + 1 for i, ln in enumerate(lineas) if not ln.endswith(b"\r")]
    assert not sin_cr, (
        f"{bat.name}: {len(sin_cr)} línea(s) sin CRLF (primeras: {sin_cr[:5]}). "
        "cmd.exe rompe los bloques `if (...)` y `for` con finales de línea de "
        "Unix. Lo sostiene .gitattributes con `*.bat text eol=crlf`.")


@pytest.mark.parametrize("bat", BATS, ids=lambda p: p.name)
def test_los_bats_son_ascii_puro(bat):
    """cmd.exe lee los .bat en la codepage OEM de la máquina (850/437 en
    español), no en UTF-8. Una tilde o un guión largo salen como caracteres
    rotos en pantalla, y dentro de una cadena con comillas pueden romper el
    comando entero. Se escriben sin acentos a propósito."""
    crudo = bat.read_bytes()
    try:
        crudo.decode("ascii")
    except UnicodeDecodeError as e:
        contexto = crudo[max(0, e.start - 40):e.start + 20].decode("utf-8", "replace")
        pytest.fail(
            f"{bat.name}: hay caracteres no ASCII en el byte {e.start} "
            f"(...{contexto}...). Escribilos sin tilde: cmd.exe no los lee como UTF-8.")


@pytest.mark.parametrize("bat", BATS, ids=lambda p: p.name)
def test_los_bats_no_tienen_bom(bat):
    """Un BOM UTF-8 al principio hace que cmd.exe lea la primera línea como
    `<basura>@echo off` y falle antes de ejecutar nada."""
    assert not bat.read_bytes().startswith(b"\xef\xbb\xbf"), (
        f"{bat.name} empieza con BOM: cmd.exe no arranca")


def test_el_gitattributes_sostiene_el_crlf():
    """Sin esta regla, el próximo que edite un .bat desde Linux vuelve a
    dejarlo en LF y el bug reaparece — y de nuevo sin que nada lo avise."""
    attrs = (RAIZ / ".gitattributes").read_text(encoding="utf-8")
    assert "*.bat text eol=crlf" in attrs


def test_el_bat_que_viaja_en_el_zip_tambien_tiene_crlf():
    """El test que de verdad importa: lo que le llega al usuario.

    El ZIP se arma copiando del árbol de trabajo, así que hereda lo que haya
    ahí. Si alguien genera el paquete desde un checkout mal configurado, el
    `.bat` sale con LF y el cliente recibe un programa que no abre — aunque en
    el repo esté todo bien.
    """
    import sys as _sys

    _sys.path.insert(0, str(RAIZ / "packaging"))
    import build_release

    zip_path = build_release.build_portable_zip(version="crlf-check")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            bats = [n for n in zf.namelist() if n.lower().endswith(".bat")]
            assert bats, "el ZIP portable no lleva ningún .bat: no hay cómo abrirlo"
            for nombre in bats:
                crudo = zf.read(nombre)
                lineas = [ln for ln in crudo.split(b"\n")[:-1]]
                sin_cr = [i + 1 for i, ln in enumerate(lineas) if not ln.endswith(b"\r")]
                assert not sin_cr, (
                    f"{nombre} sale del ZIP con {len(sin_cr)} línea(s) en LF: "
                    "no va a abrir en Windows")
                crudo.decode("ascii")  # explota si hay no-ASCII
    finally:
        zip_path.unlink(missing_ok=True)
