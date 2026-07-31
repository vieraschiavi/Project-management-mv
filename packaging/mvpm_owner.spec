# -*- mode: python ; coding: utf-8 -*-
# Spec de PyInstaller para el build "Owner Edition" — mismo motor que
# packaging/mvpm.spec (el que baja un cliente), con una sola diferencia:
# empaqueta packaging/OWNER_EDITION junto al .exe, que mvpm_launcher.py usa
# como marcador para activar MVPM_OWNER_BYPASS automáticamente (sin licencia,
# sin cupo de IA). Este build NUNCA se publica en la landing ni en Vercel
# Blob — sólo se sube como artefacto/Release de GitHub, visible únicamente
# para quien tiene acceso al repo privado. Ver .github/workflows/build_windows_owner.yml.
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
    (str(ROOT / 'packaging' / 'OWNER_EDITION'), '.'),
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
