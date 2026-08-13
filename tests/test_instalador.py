# © 2026 Martín Viera. Todos los derechos reservados.
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


def _bloque(texto: str, constructor: str) -> str:
    """El cuerpo de una llamada `CONSTRUCTOR(...)` de un .spec, hasta el
    paréntesis de cierre a principio de renglón."""
    m = re.search(rf"\b{constructor}\((.*?)^\)", texto, re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


def _nombre_de(texto: str, constructor: str) -> str | None:
    m = re.search(r"name=['\"]([^'\"]+)['\"]", _bloque(texto, constructor))
    return m.group(1) if m else None


@pytest.mark.parametrize("spec", sorted(PACKAGING.glob("*.spec")), ids=lambda p: p.name)
def test_los_spec_compilan_en_onedir_y_no_en_onefile(spec):
    """EL bug que rompió la instalación en la máquina de un usuario:

        Failed to extract mvpm\\policies.cp311-win_amd64.pyd:
        decompression resulted in return code -1!

    En onefile el .exe lleva todo comprimido adentro y lo descomprime a
    %TEMP%\\_MEIxxxxxx en CADA arranque; ahí es donde fallaba. Y como %TEMP%
    vive en C:, el programa escribía ~350 MB en C: aunque estuviera instalado
    en otro disco — o sea que "no usar el disco C" era imposible por
    construcción, no una preferencia.

    onedir no descomprime nada: los archivos quedan en la carpeta de
    instalación, en el disco que el usuario eligió.
    """
    texto = _texto(spec)
    assert "exclude_binaries=True" in texto, (
        f"{spec.name} volvió a onefile: sin exclude_binaries las dependencias "
        "van embebidas y se descomprimen a %TEMP% en cada arranque")
    assert _bloque(texto, "COLLECT"), (
        f"{spec.name} no tiene COLLECT: sin él PyInstaller no arma la carpeta")
    assert "runtime_tmpdir" not in texto, (
        f"{spec.name} declara runtime_tmpdir, que sólo existe en onefile — "
        "en onedir no hay directorio temporal porque no hay extracción")


@pytest.mark.parametrize("iss", ISS, ids=lambda p: p.name)
def test_lo_que_empaqueta_el_iss_es_lo_que_produce_pyinstaller(iss):
    """Si los nombres del .iss y del .spec se desalinean, el build de CI
    termina 'bien' pero el instalador queda sin el programa adentro.

    Son DOS nombres desde que se pasó a onedir: la carpeta que arma COLLECT
    (lo que se empaqueta) y el .exe que arma EXE adentro de ella (lo que se
    lanza y al que apuntan los accesos directos)."""
    texto = _texto(iss)
    origen = re.search(r'^Source:\s*"([^"]+)"', _seccion(texto, "Files"), re.MULTILINE)
    assert origen, "la sección [Files] no declara ningún Source"

    nombre_dir = _define(texto, "MyAppDirName")
    nombre_exe = _define(texto, "MyAppExeName")
    assert nombre_dir, "no se declara #define MyAppDirName"
    assert nombre_exe, "no se declara #define MyAppExeName"
    assert origen.group(1).endswith("{#MyAppDirName}\\*"), (
        "el Source no usa MyAppDirName: los nombres pueden desalinearse, y sin "
        f"el \\* se empaquetaría la carpeta como archivo. Source: {origen.group(1)}")

    flags = re.search(r"^Source:.*Flags:\s*(.+)$", _seccion(texto, "Files"),
                      re.MULTILINE)
    assert flags and "recursesubdirs" in flags.group(1), (
        "sin recursesubdirs el instalador copia sólo el primer nivel de la "
        "carpeta y el programa queda sin sus dependencias")

    specs = list(PACKAGING.glob("*.spec"))
    carpetas = {_nombre_de(_texto(s), "COLLECT") for s in specs}
    ejecutables = {_nombre_de(_texto(s), "EXE") for s in specs}
    assert nombre_dir in carpetas, (
        f"{iss.name} empaqueta la carpeta '{nombre_dir}', que ningún COLLECT "
        f"produce: {carpetas}")
    assert nombre_exe.removesuffix(".exe") in ejecutables, (
        f"{iss.name} lanza '{nombre_exe}', que ningún EXE produce: {ejecutables}")


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


# ------------------------------- el Pascal de [Code], que sólo compila Inno

#: Funciones de la API de Inno Setup 6 que usa la validación. Se listan a
#: propósito: un typo en cualquiera de estas (`GetSpaceOnDisk` en vez de
#: `GetSpaceOnDisk64`, por ejemplo) rompe la compilación entera en CI, y desde
#: Linux no hay compilador para descubrirlo.
API_INNO = {
    "AddBackslash", "CustomMessage", "Copy", "DeleteFile", "DirExists",
    "ExtractFileDir", "ExtractFileDrive", "FmtMessage", "ForceDirectories",
    "GetSpaceOnDisk64", "IntToStr", "MsgBox", "RemoveBackslashUnlessRoot",
    "RemoveDir", "SaveStringToFile",
}


@pytest.mark.parametrize("iss", ISS, ids=lambda p: p.name)
def test_el_pascal_tiene_los_begin_end_balanceados(iss):
    """Un `end` de más o de menos es el error de compilación más común y el
    más difícil de ver leyendo."""
    codigo = _seccion(_texto(iss), "Code")
    sin_comentarios = re.sub(r"\{[^}]*\}", "", codigo, flags=re.DOTALL)
    palabras = re.findall(r"\b(begin|end)\b", sin_comentarios, re.IGNORECASE)
    saldo = 0
    for palabra in palabras:
        saldo += 1 if palabra.lower() == "begin" else -1
        assert saldo >= 0, "aparece un 'end' antes de su 'begin'"
    assert saldo == 0, f"quedan {saldo} 'begin' sin cerrar"


@pytest.mark.parametrize("iss", ISS, ids=lambda p: p.name)
def test_toda_funcion_llamada_existe(iss):
    """Cada llamada tiene que resolver: o es una función definida en el mismo
    archivo, o es de la API de Inno. Si aparece una que no está en ninguna de
    las dos listas, o es un typo o hay que agregarla a API_INNO a conciencia."""
    codigo = _seccion(_texto(iss), "Code")
    sin_comentarios = re.sub(r"\{[^}]*\}", "", codigo, flags=re.DOTALL)

    definidas = set(re.findall(r"^\s*(?:function|procedure)\s+(\w+)",
                               sin_comentarios, re.MULTILINE | re.IGNORECASE))
    llamadas = set(re.findall(r"\b([A-Za-z_]\w*)\s*\(", sin_comentarios))

    # Palabras del lenguaje que también van seguidas de paréntesis.
    lenguaje = {"if", "while", "for", "and", "or", "not", "div", "mod",
                "function", "procedure", "then", "do", "begin", "case"}
    desconocidas = {f for f in llamadas
                    if f not in definidas
                    and f not in API_INNO
                    and f.lower() not in lenguaje}
    assert not desconocidas, (
        f"funciones que no se definen acá ni están declaradas como API de Inno: "
        f"{sorted(desconocidas)}")


@pytest.mark.parametrize("iss", ISS, ids=lambda p: p.name)
def test_la_validacion_no_deja_carpetas_vacias_tiradas(iss):
    """`SePuedeEscribir` crea la carpeta para probar si escribe. Si el usuario
    después cancela, no puede quedar una carpeta vacía en su disco."""
    codigo = _seccion(_texto(iss), "Code")
    assert "RemoveDir" in codigo, (
        "se crea la carpeta para probar pero no se borra si no se instala")


# ------------------------------- el bug real que rompió el build de CI

@pytest.mark.parametrize("iss", ISS, ids=lambda p: p.name)
def test_ninguna_linea_del_code_empieza_con_corchete(iss):
    """EL BUG REAL, encontrado por el build de Windows (que sí compila con
    Inno de verdad) después de que los 32 tests estáticos anteriores pasaran
    igual: un literal de array de Pascal como

        MsgBox(FmtMessage(msg,
                          [Detalle1, Detalle2]), ...)

    con el '[' como primer carácter no-blanco de un renglón, hace que el
    PREPROCESADOR de Inno —que lee línea por línea buscando encabezados de
    sección— lo confunda con un "[NombreDeSección]". Resultado real de CI:
    'Error on line N: Invalid section tag. Compile aborted.'

    Nada de la sintaxis de Pascal en sí estaba mal: por eso ni el chequeo de
    begin/end ni el de funciones conocidas lo agarraban. Hacía falta simular
    la regla exacta del parser de Inno, no la del lenguaje Pascal.
    """
    codigo = _seccion(_texto(iss), "Code")
    for numero, linea in enumerate(codigo.splitlines(), start=1):
        recortada = linea.strip()
        if recortada.startswith("["):
            pytest.fail(
                f"{iss.name}: línea {numero} del bloque [Code] empieza con "
                f"'[' — Inno la va a leer como un encabezado de sección, no "
                f"como código: {linea!r}. Armá el array en una variable "
                f"aparte en vez de como literal al principio de renglón.")
