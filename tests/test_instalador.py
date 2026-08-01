"""Consistencia de los instaladores de Windows (packaging/*.iss).

Inno Setup sólo compila en Windows, así que la compilación real la hace CI
(`.github/workflows/build_windows*.yml`). Lo que se puede verificar acá —y es
donde estaban los errores que llegaban al usuario— es que el script sea
coherente consigo mismo y con los archivos del repo: que el `.exe`, el icono y
el EULA que referencia existan, que las `Tasks` usadas estén declaradas, que
los mensajes personalizados estén en los dos idiomas, y que las dos ediciones
(cliente y owner) no se pisen si están instaladas en la misma PC.
"""

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
PACKAGING = RAIZ / "packaging"
ISS = sorted(PACKAGING.glob("instalador*.iss"))


def _texto(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _seccion(texto: str, nombre: str) -> str:
    """Devuelve el cuerpo de una sección `[Nombre]` del .iss."""
    m = re.search(rf"^\[{nombre}\]\s*$(.*?)(?=^\[|\Z)", texto,
                  re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


def _directiva(texto: str, clave: str) -> str | None:
    m = re.search(rf"^{re.escape(clave)}=(.*)$", texto, re.MULTILINE)
    return m.group(1).strip() if m else None


def _define(texto: str, nombre: str) -> str | None:
    """`#define Nombre "valor"` — va con espacio, no con `=` como el resto."""
    m = re.search(rf'^#define\s+{re.escape(nombre)}\s+"([^"]*)"', texto, re.MULTILINE)
    return m.group(1) if m else None


def test_hay_instaladores_para_verificar():
    assert ISS, "no se encontró ningún packaging/instalador*.iss"


@pytest.mark.parametrize("iss", ISS, ids=lambda p: p.name)
def test_estan_las_secciones_obligatorias(iss):
    texto = _texto(iss)
    for seccion in ["Setup", "Languages", "Files", "Icons", "Tasks", "Run"]:
        assert f"[{seccion}]" in texto, f"falta la sección [{seccion}]"


# ------------------------------------------- lo que el .iss dice que existe

@pytest.mark.parametrize("iss", ISS, ids=lambda p: p.name)
def test_el_icono_del_instalador_existe(iss):
    """Las rutas del .iss son relativas al propio .iss. Si el icono no está,
    Inno falla la compilación entera en CI."""
    ruta = _directiva(_texto(iss), "SetupIconFile")
    assert ruta, "sin SetupIconFile: el instalador saldría con el icono genérico"
    assert (PACKAGING / ruta.replace("\\", "/")).exists(), (
        f"{iss.name} apunta a un icono que no existe: {ruta}")


@pytest.mark.parametrize("iss", ISS, ids=lambda p: p.name)
def test_el_eula_existe_y_es_obligatorio(iss):
    ruta = _directiva(_texto(iss), "LicenseFile")
    assert ruta, "sin LicenseFile no hay pantalla de aceptación del EULA"
    assert (PACKAGING / ruta.replace("\\", "/")).exists()


@pytest.mark.parametrize("iss", ISS, ids=lambda p: p.name)
def test_el_exe_que_empaqueta_es_el_que_compila_pyinstaller(iss):
    """Si el nombre del .exe del .iss y el del .spec se desalinean, el build
    de CI termina 'bien' pero el instalador queda sin el programa adentro."""
    texto = _texto(iss)
    origen = re.search(r'^Source:\s*"([^"]+)"', _seccion(texto, "Files"), re.MULTILINE)
    assert origen, "la sección [Files] no declara ningún Source"

    nombre_exe = _define(texto, "MyAppExeName")
    assert nombre_exe, "no se declara #define MyAppExeName"
    assert origen.group(1).endswith("{#MyAppExeName}"), (
        "el Source no usa MyAppExeName: los dos nombres pueden desalinearse")

    specs = list(PACKAGING.glob("*.spec"))
    declarados = {m for s in specs
                  for m in re.findall(r"name=['\"]([^'\"]+)['\"]", _texto(s))}
    assert nombre_exe.removesuffix(".exe") in declarados, (
        f"{iss.name} empaqueta '{nombre_exe}', que ningún .spec produce: {declarados}")


# --------------------------------------------------- iconos que pidió el dueño

@pytest.mark.parametrize("iss", ISS, ids=lambda p: p.name)
def test_crea_icono_en_el_menu_inicio(iss):
    iconos = _seccion(_texto(iss), "Icons")
    assert "{group}\\" in iconos, "no crea entrada en el menú Inicio de Windows"


@pytest.mark.parametrize("iss", ISS, ids=lambda p: p.name)
def test_crea_icono_en_el_escritorio_y_viene_marcado(iss):
    """Venía con `Flags: unchecked`, o sea desmarcado: el usuario instalaba y
    no le aparecía nada en el escritorio."""
    texto = _texto(iss)
    iconos = _seccion(texto, "Icons")
    assert "{autodesktop}" in iconos, "no crea acceso directo en el escritorio"

    tarea_desktop = [linea for linea in _seccion(texto, "Tasks").splitlines()
                     if "desktopicon" in linea]
    assert tarea_desktop, "el icono de escritorio referencia una Task inexistente"
    assert "unchecked" not in tarea_desktop[0], (
        "el icono de escritorio viene desmarcado: hay que marcarlo por defecto")


@pytest.mark.parametrize("iss", ISS, ids=lambda p: p.name)
def test_toda_task_usada_esta_declarada(iss):
    """Una `Tasks:` mal escrita en [Icons] hace fallar la compilación."""
    texto = _texto(iss)
    declaradas = set(re.findall(r'^Name:\s*"([^"]+)"', _seccion(texto, "Tasks"),
                                re.MULTILINE))
    usadas = set(re.findall(r"Tasks:\s*([A-Za-z0-9_]+)", _seccion(texto, "Icons")))
    assert usadas <= declaradas, f"tasks usadas y no declaradas: {usadas - declaradas}"


# ------------------------------------- elegir carpeta y disco sin errores

@pytest.mark.parametrize("iss", ISS, ids=lambda p: p.name)
def test_siempre_deja_elegir_la_carpeta(iss):
    assert _directiva(_texto(iss), "DisableDirPage") == "no", (
        "sin la página de destino el usuario no puede elegir carpeta ni disco")


@pytest.mark.parametrize("iss", ISS, ids=lambda p: p.name)
def test_se_puede_instalar_sin_ser_administrador(iss):
    """En notebooks de empresa el usuario no es admin local. Sin esto, elegir
    Archivos de programa terminaba en un error de permisos sin explicación."""
    texto = _texto(iss)
    assert _directiva(texto, "PrivilegesRequired") == "lowest"
    assert _directiva(texto, "PrivilegesRequiredOverridesAllowed") == "dialog"
    assert "{autopf}" in (_directiva(texto, "DefaultDirName") or ""), (
        "DefaultDirName tiene que usar {autopf} para resolver según ese diálogo")


@pytest.mark.parametrize("iss", ISS, ids=lambda p: p.name)
def test_valida_la_carpeta_elegida_antes_de_copiar(iss):
    """El asistente avanzaba con una unidad inexistente, sin espacio o sin
    permiso de escritura, y recién fallaba al copiar con un error genérico de
    Windows. Ahora se comprueba en la misma pantalla donde se elige."""
    texto = _texto(iss)
    codigo = _seccion(texto, "Code")
    assert codigo.strip(), "no hay sección [Code] con la validación"
    assert "NextButtonClick" in codigo, "la validación no se engancha al botón Siguiente"
    assert "wpSelectDir" in codigo, "no valida en la página de elegir carpeta"
    for funcion in ["UnidadDisponible", "EspacioLibreMB", "SePuedeEscribir"]:
        assert funcion in codigo, f"falta la comprobación {funcion}"


@pytest.mark.parametrize("iss", ISS, ids=lambda p: p.name)
def test_los_mensajes_de_error_estan_en_los_dos_idiomas(iss):
    """[Languages] declara spanish e english: un CustomMessage que falte en uno
    sale vacío en pantalla para ese idioma."""
    texto = _texto(iss)
    mensajes = _seccion(texto, "CustomMessages")
    claves = {m.split(".", 1)[1] for m in re.findall(r"^(\w+\.\w+)=", mensajes,
                                                     re.MULTILINE)}
    assert claves, "no hay mensajes personalizados"
    for clave in claves:
        for idioma in ["spanish", "english"]:
            assert f"{idioma}.{clave}=" in mensajes, f"falta {idioma}.{clave}"


@pytest.mark.parametrize("iss", ISS, ids=lambda p: p.name)
def test_todo_custom_message_usado_esta_definido(iss):
    texto = _texto(iss)
    definidos = {m.split(".", 1)[1] for m in re.findall(r"^(\w+\.\w+)=",
                                                        _seccion(texto, "CustomMessages"),
                                                        re.MULTILINE)}
    usados = set(re.findall(r"CustomMessage\('(\w+)'\)", _seccion(texto, "Code")))
    assert usados <= definidos, f"mensajes usados y no definidos: {usados - definidos}"


# ------------------------------- que las dos ediciones no se pisen entre sí

def test_cliente_y_owner_no_se_pisan_en_la_misma_pc():
    """Tienen que poder convivir instalados: el dueño usa la edición owner y
    prueba con la de cliente. Con el mismo AppId, instalar una desinstala la
    otra; con la misma carpeta o el mismo .exe, se sobrescriben."""
    if len(ISS) < 2:
        pytest.skip("hay un solo instalador")
    valores = {}
    for iss in ISS:
        texto = _texto(iss)
        valores[iss.name] = (
            _directiva(texto, "AppId"),
            _directiva(texto, "DefaultDirName"),
            _define(texto, "MyAppExeName"),
        )
    for i, campo in enumerate(["AppId", "DefaultDirName", "MyAppExeName"]):
        vistos = [v[i] for v in valores.values()]
        assert len(set(vistos)) == len(vistos), (
            f"{campo} repetido entre ediciones: {vistos}")
