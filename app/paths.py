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


def data_dir() -> Path:
    """Directorio escribible y persistente siguiendo las convenciones del SO."""
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "RugdraigerDownloader"


def config_dir() -> Path:
    if is_frozen():
        return data_dir() / "config"
    return app_root() / "config"


def bin_dir() -> Path:
    """Binarios actualizables; fuera del bundle cuando la app está empaquetada."""
    if is_frozen():
        return data_dir() / "bin"
    return app_root() / "bin"


def bundled_bin_dir() -> Path:
    """Binarios de solo lectura incluidos por PyInstaller, si existen."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", app_root())) / "bin"
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
    names = (
        ("app-icon.png", "logo.png", "app-icon.ico")
        if sys.platform == "darwin"
        else ("app-icon.ico", "app-icon.png", "logo.png")
    )
    for name in names:
        path = folder / name
        if path.exists():
            return path
    return None
