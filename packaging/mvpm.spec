# -*- mode: python ; coding: utf-8 -*-
# Spec de PyInstaller — compila en un runner Windows (ver
# .github/workflows/build_windows.yml). No se puede compilar el .exe final
# desde Linux/Mac, pero el spec sí se versiona y valida acá.

import sys
from pathlib import Path

block_cipher = None
ROOT = Path(SPECPATH).resolve().parent

a = Analysis(
    ['mvpm_launcher.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'app'), 'app'),
        (str(ROOT / 'mvpm'), 'mvpm'),
    ],
    hiddenimports=['streamlit', 'streamlit.web.cli', 'pandas', 'openpyxl'],
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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
