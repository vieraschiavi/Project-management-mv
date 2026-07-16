# -*- mode: python ; coding: utf-8 -*-
# Spec de PyInstaller — compila en un runner Windows (ver
# .github/workflows/build_windows.yml). No se puede compilar el .exe final
# desde Linux/Mac, pero el spec sí se versiona y valida acá.
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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MVProjectManagement',
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
