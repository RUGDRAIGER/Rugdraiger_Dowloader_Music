# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — Rugdraiger Downloader Music."""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
root = Path(SPECPATH).parent
app_name = "Rugdraiger_Dowloader_Music"

datas = collect_data_files("customtkinter")
assets_dir = root / "assets"
if assets_dir.exists():
    for asset in assets_dir.iterdir():
        if asset.is_file():
            datas.append((str(asset), "assets"))
binaries = []
if (root / "bin" / "yt-dlp.exe").exists():
    binaries.append((str(root / "bin" / "yt-dlp.exe"), "bin"))

hiddenimports = collect_submodules("customtkinter") + ["PIL", "PIL._tkinter_finder"]

a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)],
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
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(Path(SPECPATH) / "assets" / "app-icon.ico") if (Path(SPECPATH) / "assets" / "app-icon.ico").exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)
