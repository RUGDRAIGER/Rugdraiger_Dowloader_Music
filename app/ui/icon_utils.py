"""Icono de ventana Rugdraiger."""

from __future__ import annotations

import tkinter as tk

from PIL import Image, ImageTk

from app.paths import app_icon_path


def apply_window_icon(window: tk.Misc) -> None:
    """Aplica el logo Rugdraiger a la barra de titulo y la barra de tareas."""
    icon = app_icon_path()
    if not icon:
        return

    try:
        if icon.suffix.lower() == ".ico":
            window.iconbitmap(str(icon))
            return
    except tk.TclError:
        pass

    try:
        img = Image.open(icon).convert("RGBA")
        img = img.resize((64, 64), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        window.iconphoto(True, photo)
        window._rugdraiger_icon = photo
    except OSError:
        return
