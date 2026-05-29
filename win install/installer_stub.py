"""
Instalador Rugdraiger Downloader Music (stub empaquetado con PyInstaller).
Extrae el payload embebido y crea accesos directos en Windows.
"""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import tempfile
import tkinter as tk
import zipfile
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

APP_NAME = "Rugdraiger Downloader Music"
APP_EXE = "Rugdraiger_Dowloader_Music.exe"
PAYLOAD_NAME = "payload.zip"
DEFAULT_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Rugdraiger Downloader Music"

CSIDL_PROGRAMS = 0x0002
CSIDL_DESKTOPDIRECTORY = 0x0010


def resource_path(name: str) -> Path:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).resolve().parent
    return base / name


def get_shell_folder(csid: int) -> Path | None:
    buf = ctypes.create_unicode_buffer(260)
    hr = ctypes.windll.shell32.SHGetFolderPathW(None, csid, None, 0, buf)
    if hr == 0 and buf.value:
        return Path(buf.value)
    return None


def get_start_menu_dir() -> Path:
    folder = get_shell_folder(CSIDL_PROGRAMS)
    if folder:
        return folder
    return Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs"


def get_desktop_dir() -> Path:
    folder = get_shell_folder(CSIDL_DESKTOPDIRECTORY)
    if folder and folder.exists():
        return folder

    userprofile = Path(os.environ.get("USERPROFILE", Path.home()))
    for candidate in (
        userprofile / "Desktop",
        userprofile / "OneDrive" / "Desktop",
        userprofile / "OneDrive - Personal" / "Desktop",
    ):
        if candidate.exists():
            return candidate

    fallback = userprofile / "Desktop"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def _vbs_quote(value: str) -> str:
    return value.replace('"', '""')


def create_shortcut(target: Path, shortcut_path: Path, description: str) -> None:
    """Crea un .lnk usando WScript.Shell (sin PowerShell)."""
    target = target.resolve()
    shortcut_path = shortcut_path.resolve()
    shortcut_path.parent.mkdir(parents=True, exist_ok=True)

    vbs = f'''Set WshShell = CreateObject("WScript.Shell")
Set shortcut = WshShell.CreateShortcut("{_vbs_quote(str(shortcut_path))}")
shortcut.TargetPath = "{_vbs_quote(str(target))}"
shortcut.WorkingDirectory = "{_vbs_quote(str(target.parent))}"
shortcut.Description = "{_vbs_quote(description)}"
shortcut.Save
'''

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".vbs",
        delete=False,
        encoding="utf-8",
    ) as handle:
        handle.write(vbs)
        vbs_path = handle.name

    try:
        result = subprocess.run(
            ["wscript.exe", "//Nologo", vbs_path],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        if result.returncode != 0 or not shortcut_path.exists():
            detail = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(
                f"No se pudo crear el acceso directo: {shortcut_path.name}"
                + (f" ({detail})" if detail else "")
            )
    finally:
        Path(vbs_path).unlink(missing_ok=True)


def extract_payload(dest: Path, progress: ttk.Progressbar | None = None) -> None:
    payload = resource_path(PAYLOAD_NAME)
    if not payload.exists():
        raise FileNotFoundError(f"No se encontro {PAYLOAD_NAME} embebido.")

    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(payload, "r") as zf:
        members = zf.namelist()
        total = len(members) or 1
        for i, member in enumerate(members, start=1):
            zf.extract(member, dest)
            if progress is not None:
                progress["value"] = (i / total) * 100
                progress.update_idletasks()


def find_app_exe(dest: Path) -> Path:
    app_exe = dest / APP_EXE
    if app_exe.exists():
        return app_exe
    candidates = list(dest.rglob(APP_EXE))
    if not candidates:
        raise FileNotFoundError(f"No se encontro {APP_EXE} tras extraer.")
    return candidates[0]


def run_install(dest: Path, desktop: bool) -> list[str]:
    app_exe = find_app_exe(dest)
    warnings: list[str] = []

    start_menu = get_start_menu_dir()
    start_menu.mkdir(parents=True, exist_ok=True)
    create_shortcut(app_exe, start_menu / f"{APP_NAME}.lnk", APP_NAME)

    if desktop:
        desktop_dir = get_desktop_dir()
        try:
            create_shortcut(app_exe, desktop_dir / f"{APP_NAME}.lnk", APP_NAME)
        except RuntimeError as exc:
            warnings.append(str(exc))

    desktop_lnk = get_desktop_dir() / f"{APP_NAME}.lnk"
    start_menu_lnk = get_start_menu_dir() / f"{APP_NAME}.lnk"
    uninstall_bat = dest / "uninstall.bat"
    uninstall_bat.write_text(
        f"""@echo off
chcp 65001 >nul
echo Desinstalando {APP_NAME}...
del /q "{start_menu_lnk}" 2>nul
del /q "{desktop_lnk}" 2>nul
rmdir /s /q "{dest.resolve()}"
echo Listo.
pause
""",
        encoding="utf-8",
    )
    return warnings


class InstallerUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"Instalar {APP_NAME}")
        self.geometry("520x320")
        self.configure(bg="#131313")
        self.resizable(False, False)
        self._apply_icon()

        frame = tk.Frame(self, bg="#131313", highlightbackground="#FF0000", highlightthickness=3)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        tk.Label(
            frame,
            text=APP_NAME,
            font=("Segoe UI", 18, "bold"),
            fg="#ffffff",
            bg="#131313",
        ).pack(anchor="w", padx=16, pady=(16, 4))

        tk.Label(
            frame,
            text="Instalador para Windows",
            font=("Segoe UI", 11),
            fg="#ffb4a8",
            bg="#131313",
        ).pack(anchor="w", padx=16)

        path_row = tk.Frame(frame, bg="#131313")
        path_row.pack(fill="x", padx=16, pady=(20, 8))

        self.dest_var = tk.StringVar(value=str(DEFAULT_DIR))
        tk.Entry(
            path_row,
            textvariable=self.dest_var,
            width=48,
            bg="#2a2a2a",
            fg="#e2e2e2",
            insertbackground="#fff",
        ).pack(side="left", fill="x", expand=True)
        tk.Button(
            path_row,
            text="...",
            command=self._browse,
            bg="#FF0000",
            fg="#000",
            width=3,
        ).pack(side="left", padx=(8, 0))

        self.desktop_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            frame,
            text="Crear acceso directo en el escritorio",
            variable=self.desktop_var,
            fg="#e2e2e2",
            bg="#131313",
            selectcolor="#2a2a2a",
            activebackground="#131313",
        ).pack(anchor="w", padx=16)

        self.progress = ttk.Progressbar(frame, mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=16, pady=(16, 8))

        tk.Button(
            frame,
            text="INSTALAR",
            font=("Segoe UI", 12, "bold"),
            bg="#FF0000",
            fg="#000000",
            activebackground="#c00100",
            command=self._install,
            height=2,
        ).pack(fill="x", padx=16, pady=(8, 16))

    def _apply_icon(self) -> None:
        for name in ("app-icon.ico", "app-icon.png"):
            icon = resource_path(name)
            if not icon.exists():
                continue
            try:
                if icon.suffix.lower() == ".ico":
                    self.iconbitmap(str(icon))
                    return
                img = Image.open(icon).convert("RGBA")
                img = img.resize((64, 64), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.iconphoto(True, photo)
                self._icon_photo = photo
                return
            except tk.TclError:
                continue

    def _browse(self) -> None:
        path = filedialog.askdirectory(initialdir=self.dest_var.get())
        if path:
            self.dest_var.set(path)

    def _install(self) -> None:
        dest = Path(self.dest_var.get())
        try:
            if dest.exists() and any(dest.iterdir()):
                if not messagebox.askyesno(
                    "Carpeta existente",
                    f"{dest} ya tiene archivos. ¿Continuar?",
                ):
                    return
            extract_payload(dest, self.progress)
            warnings = run_install(dest, self.desktop_var.get())
            msg = f"{APP_NAME} instalado en:\n{dest}"
            if warnings:
                msg += "\n\nAvisos:\n" + "\n".join(warnings)
            messagebox.showinfo("Instalacion completa", msg)
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))


def main() -> None:
    app = InstallerUI()
    app.mainloop()


if __name__ == "__main__":
    main()
