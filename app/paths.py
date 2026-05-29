"""Rutas de la aplicación (desarrollo y ejecutable empaquetado)."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def app_root() -> Path:
    if is_frozen():
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def config_dir() -> Path:
    if is_frozen():
        base = Path(os.environ.get("APPDATA", str(Path.home()))) / "RugdraigerDownloader"
        base.mkdir(parents=True, exist_ok=True)
        return base / "config"
    return app_root() / "config"


def bin_dir() -> Path:
    return app_root() / "bin"


def assets_dir() -> Path:
    if is_frozen():
        bundle = Path(getattr(sys, "_MEIPASS", app_root())) / "assets"
        if bundle.exists():
            return bundle
        installed = app_root() / "assets"
        if installed.exists():
            return installed
    return app_root() / "assets"


def app_icon_path() -> Path | None:
    folder = assets_dir()
    for name in ("app-icon.ico", "app-icon.png", "logo.png"):
        path = folder / name
        if path.exists():
            return path
    return None
