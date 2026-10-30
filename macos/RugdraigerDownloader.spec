# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

ROOT = Path(SPECPATH).parent
datas = [(str(ROOT / "assets"), "assets")]
datas += collect_data_files("customtkinter")

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Rugdraiger Downloader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    argv_emulation=False,
    target_arch="arm64",
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Rugdraiger Downloader",
)

app = BUNDLE(
    coll,
    name="Rugdraiger Downloader.app",
    icon=str(ROOT / "assets" / "app-icon.png"),
    bundle_identifier="com.rugdraiger.downloader.music",
    info_plist={
        "CFBundleDisplayName": "Rugdraiger Downloader",
        "CFBundleShortVersionString": "2.0.0",
        "LSApplicationCategoryType": "public.app-category.music",
        "NSHighResolutionCapable": True,
    },
)
