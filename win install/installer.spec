# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec para el instalador Rugdraiger_Dowloader_Music.exe"""

from pathlib import Path

block_cipher = None
win_install = Path(SPECPATH)
payload = win_install / "payload.zip"

datas = []
if payload.exists():
    datas.append((str(payload), "."))
for asset in (win_install / "assets").glob("*"):
    if asset.is_file():
        datas.append((str(asset), "assets"))

a = Analysis(
    [str(win_install / "installer_stub.py")],
    pathex=[str(win_install)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="Rugdraiger_Dowloader_Music",
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
    icon=str(win_install / "assets" / "app-icon.ico") if (win_install / "assets" / "app-icon.ico").exists() else None,
)
