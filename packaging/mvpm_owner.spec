# -*- mode: python ; coding: utf-8 -*-
# Spec de PyInstaller para el build "Owner Edition" — mismo motor que
# packaging/mvpm.spec (el que baja un cliente).
#
# Antes empaquetaba packaging/OWNER_EDITION junto al .exe: un marcador firmado
# que desbloqueaba el producto con sólo estar ahí. Eso se sacó. Dos razones, y
# la segunda sola ya alcanza:
#
#   1. El marcador ahora se emite atado a UNA máquina (ver mvpm/owner.py), y el
#      CI no puede saber cuál es la del dueño. Un marcador firmado en el build
#      o no valdría en ningún lado, o valdría en todos.
#   2. Este build se subía como Release de GitHub "visible sólo para quien tiene
#      acceso al repo privado". El repo es PÚBLICO. O sea que el marcador —una
#      licencia enterprise firmada— era descargable por cualquiera.
#
# Lo que hace distinto a este .exe es una CONSTANTE compilada, no un archivo:
# packaging/marcar_build_owner.py pone ES_OWNER_BUILD = True en mvpm/edicion.py
# antes de que Cython compile mvpm/ a .pyd, así que viaja como código nativo.
# No se puede copiar a otra instalación ni pegar en el campo de licencia.
# Ver .github/workflows/build_windows_owner.yml.
#
# Se mantiene deliberadamente como copia de mvpm.spec en vez de compartir
# código: son ~90 líneas de configuración declarativa de PyInstaller, y una
# indirección para no duplicarlas complicaría más de lo que ahorra.

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata

block_cipher = None
ROOT = Path(SPECPATH).resolve().parent
ICON = str(ROOT / 'packaging' / 'assets' / 'icon.ico')

# mvpm/ llega a este punto ya compilado a .pyd (ver el paso "Compilar mvpm/
# a binario nativo (Cython)" en build_windows_owner.yml, corrido ANTES de
# este spec) — el .py original se borra ahí mismo.
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

for _pkg in ('streamlit', 'altair', 'pyarrow', 'pydeck'):
    _d, _b, _h = collect_all(_pkg)
    datas += _d
    binaries += _b
    hiddenimports += _h

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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MVProjectManagementOwner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON,
)
