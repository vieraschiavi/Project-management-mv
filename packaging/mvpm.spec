# © 2026 Martín Viera. Todos los derechos reservados.
# -*- mode: python ; coding: utf-8 -*-
# Spec de PyInstaller — compila en un runner Windows (ver
# .github/workflows/build_windows.yml). No se puede compilar el .exe final
# desde Linux/Mac, pero el spec sí se versiona y valida acá.
#
# ## Por qué onedir y no onefile
#
# Con onefile el .exe lleva todo comprimido adentro y en CADA arranque lo
# descomprime a %TEMP%\_MEIxxxxxx. Eso produjo este error real en la máquina
# de un usuario:
#
#   Failed to extract mvpm\policies.cp311-win_amd64.pyd:
#   decompression resulted in return code -1!
#
# El bootloader no pudo inflar el archivo embebido. Con upx=False y
# `*.exe binary` en .gitattributes, las dos causas típicas —UPX corrompiendo
# los .pyd, git convirtiendo finales de línea— ya estaban descartadas; lo que
# queda es el propio paso de extracción: %TEMP% sin espacio, un antivirus
# tocando los archivos mientras salen, o una copia truncada del .exe.
#
# Y hay algo peor que el error: %TEMP% vive en C:. O sea que con onefile el
# programa escribe ~300-400 MB en C: cada vez que abre, aunque el usuario lo
# haya instalado en D: para no tocar C:. "No usar el disco C" era imposible
# por construcción.
#
# onedir no descomprime nada en runtime: los archivos quedan en la carpeta de
# instalación, en el disco que el usuario eligió. Desaparece la clase entera
# de error y el arranque es bastante más rápido. El usuario sigue recibiendo
# UN instalador y UN acceso directo — el Inno Setup empaqueta la carpeta.
#
# Streamlit es difícil de empaquetar: en runtime busca sus metadatos
# (importlib.metadata) y sus archivos estáticos (el front-end compilado). Sin
# collect_all + copy_metadata, el .exe arranca pero `streamlit run` falla. Por
# eso se recolecta todo el paquete y sus metadatos, más los de sus deps que
# también consultan su versión en runtime.

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata

block_cipher = None
ROOT = Path(SPECPATH).resolve().parent
ICON = str(ROOT / 'packaging' / 'assets' / 'icon.ico')

# mvpm/ llega a este punto ya compilado a .pyd (ver el paso "Compilar mvpm/
# a binario nativo (Cython)" en build_windows.yml / build_electron.yml,
# corrido ANTES de este spec) — el .py original se borra ahí mismo. Este
# datas= copia el contenido del directorio tal cual esté en ese momento, sea
# .py (build local sin ese paso) o .pyd (build real de CI), sin distinguir.
datas = [
    (str(ROOT / 'app'), 'app'),
    (str(ROOT / 'mvpm'), 'mvpm'),
]
binaries = []
hiddenimports = [
    'streamlit', 'streamlit.web.cli',
    'streamlit.runtime.scriptrunner.magic_funcs',
    'pandas', 'openpyxl',
]

# Recolecta el paquete completo de Streamlit (front-end estático incluido) y
# el de las deps que Streamlit inspecciona por metadatos en tiempo de ejecución.
for _pkg in ('streamlit', 'altair', 'pyarrow', 'pydeck'):
    _d, _b, _h = collect_all(_pkg)
    datas += _d
    binaries += _b
    hiddenimports += _h

# Metadatos que Streamlit y sus deps leen en runtime (importlib.metadata).
for _pkg in ('streamlit', 'click', 'rich', 'pandas', 'numpy', 'altair', 'pyarrow'):
    try:
        datas += copy_metadata(_pkg)
    except Exception:
        pass

a = Analysis(
    ['mvpm_launcher.py'],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# `exclude_binaries=True` es lo que separa onedir de onefile: el EXE queda
# como lanzador chico y las dependencias las junta COLLECT en la carpeta de
# al lado, en vez de ir embebidas y descomprimirse a %TEMP% en cada arranque.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MVProjectManagement',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON,
)

# Deja `dist/MVProjectManagement/` con el .exe y todo lo que necesita. Es esa
# carpeta —no un único archivo— la que empaqueta packaging/instalador.iss.
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='MVProjectManagement',
)
