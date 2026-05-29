"""Prueba local de creacion de accesos directos del instalador."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from installer_stub import APP_NAME, create_shortcut, get_desktop_dir, get_start_menu_dir


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fake_exe = Path(tmp) / "Rugdraiger_Dowloader_Music.exe"
        fake_exe.write_text("test", encoding="utf-8")

        start_lnk = get_start_menu_dir() / f"{APP_NAME}.lnk"
        desk_lnk = get_desktop_dir() / f"{APP_NAME}_TEST.lnk"

        create_shortcut(fake_exe, start_lnk, APP_NAME)
        create_shortcut(fake_exe, desk_lnk, APP_NAME)

        assert start_lnk.exists(), f"Falta acceso en menu inicio: {start_lnk}"
        assert desk_lnk.exists(), f"Falta acceso en escritorio: {desk_lnk}"

        start_lnk.unlink(missing_ok=True)
        desk_lnk.unlink(missing_ok=True)

    print("OK: accesos directos creados y eliminados correctamente.")
    print(f"Escritorio detectado: {get_desktop_dir()}")


if __name__ == "__main__":
    main()
