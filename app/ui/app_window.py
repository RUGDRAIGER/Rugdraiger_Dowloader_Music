"""Ventana principal de Rugdraiger Downloader."""

from __future__ import annotations

import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from app.config import AppSettings, ensure_dirs
from app.core.cookie_help import is_chromium_browser
from app.core.dependencies import (
    dependency_report,
    ensure_ytdlp,
    update_ytdlp,
)
from app.core.downloader import DownloadJob, DownloadState, YtDlpDownloader
from app.core.url_utils import is_supported_url
from app.core.validators import validate_playlist_items
from app.paths import app_icon_path
from app.theme import (
    APP_SUBTITLE,
    APP_TITLE,
    APP_VERSION,
    BORDER_RED,
    FONT_BODY,
    FONT_BODY_FB,
    FONT_BODY_SM,
    FONT_DISPLAY,
    FONT_DISPLAY_FB,
    FONT_HEADLINE,
    FONT_HEADLINE_FB,
    FONT_LABEL,
    FONT_MONO,
    NEON_RED,
    NEON_RED_DIM,
    PRIMARY,
    SURFACE,
    SURFACE_CONTAINER,
    SURFACE_CONTAINER_HIGH,
    SURFACE_CONTAINER_HIGHEST,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from app.ui.icon_utils import apply_window_icon


def _pick_font(primary: tuple, fallback: tuple) -> tuple:
    return primary


class RugdraigerApp(ctk.CTk):
    """Aplicación de escritorio estilo Rugdraiger Play."""

    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title(f"{APP_TITLE} v{APP_VERSION}")
        self.geometry("980x840")
        self.minsize(760, 650)
        self.configure(fg_color=SURFACE)
        apply_window_icon(self)

        ensure_dirs()
        self.settings = AppSettings.load()
        self.downloader = YtDlpDownloader()
        self._download_thread: threading.Thread | None = None

        self._build_ui()
        self._refresh_deps()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        # Marco exterior con borde rojo intenso
        self.outer = ctk.CTkFrame(
            self,
            fg_color=SURFACE,
            border_color=BORDER_RED,
            border_width=3,
            corner_radius=8,
        )
        self.outer.pack(fill="both", expand=True, padx=12, pady=12)
        self.content = ctk.CTkScrollableFrame(
            self.outer,
            fg_color="transparent",
            scrollbar_button_color=SURFACE_CONTAINER_HIGH,
            scrollbar_button_hover_color=NEON_RED_DIM,
        )
        self.content.pack(fill="both", expand=True, padx=2, pady=2)

        self._build_header()
        self._build_url_section()
        self._build_options_section()
        self._build_actions()
        self._build_progress()
        self._build_log()
        self._build_footer()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 8))

        row = ctk.CTkFrame(header, fg_color="transparent")
        row.pack(fill="x")

        icon_path = app_icon_path()
        if icon_path:
            logo = ctk.CTkImage(
                light_image=Image.open(icon_path),
                dark_image=Image.open(icon_path),
                size=(52, 52),
            )
            ctk.CTkLabel(row, text="", image=logo).pack(side="left", padx=(0, 14))
            self._header_logo = logo

        text_col = ctk.CTkFrame(row, fg_color="transparent")
        text_col.pack(side="left", fill="x", expand=True)

        title = ctk.CTkLabel(
            text_col,
            text=APP_TITLE,
            font=_pick_font(FONT_DISPLAY, FONT_DISPLAY_FB),
            text_color=TEXT_PRIMARY,
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            text_col,
            text=APP_SUBTITLE,
            font=_pick_font(FONT_BODY, FONT_BODY_FB),
            text_color=PRIMARY,
        )
        subtitle.pack(anchor="w", pady=(4, 0))

        hint = ctk.CTkLabel(
            text_col,
            text="M4A nativo (AAC 256 kbps Premium) · Opus 128 kbps gratuito · Sin conversión innecesaria",
            font=FONT_BODY_SM,
            text_color=TEXT_MUTED,
        )
        hint.pack(anchor="w", pady=(6, 0))

    def _section(self, parent, title: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            parent,
            fg_color=SURFACE_CONTAINER,
            border_color=NEON_RED_DIM,
            border_width=1,
            corner_radius=6,
        )
        frame.pack(fill="x", padx=24, pady=8)

        lbl = ctk.CTkLabel(
            frame,
            text=title.upper(),
            font=FONT_LABEL,
            text_color=NEON_RED,
        )
        lbl.pack(anchor="w", padx=16, pady=(12, 4))
        return frame

    def _build_url_section(self) -> None:
        sec = self._section(self.content, "Enlace YouTube Music")

        inner = ctk.CTkFrame(sec, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=(0, 12))

        self.url_var = tk.StringVar()
        self.url_entry = ctk.CTkEntry(
            inner,
            textvariable=self.url_var,
            placeholder_text="https://music.youtube.com/playlist?list=… o watch?v=…",
            height=42,
            font=FONT_BODY,
            fg_color=SURFACE_CONTAINER_HIGH,
            border_color=SURFACE_CONTAINER_HIGHEST,
            border_width=1,
        )
        self.url_entry.pack(fill="x", pady=(0, 8))

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x")

        self.playlist_var = tk.StringVar(value=self.settings.playlist_items)
        ctk.CTkLabel(row, text="Ítems playlist:", font=FONT_BODY_SM, text_color=TEXT_MUTED).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkEntry(
            row,
            textvariable=self.playlist_var,
            width=120,
            placeholder_text="vacío=todas | 1-5 | 1,3,7",
            fg_color=SURFACE_CONTAINER_HIGH,
            border_color=SURFACE_CONTAINER_HIGHEST,
        ).pack(side="left")

        ctk.CTkLabel(
            inner,
            text="Playlist: pega el enlace de la playlist y deja «Ítems» vacío para bajar todas las canciones.",
            font=FONT_BODY_SM,
            text_color=TEXT_MUTED,
            wraplength=820,
            justify="left",
        ).pack(anchor="w", pady=(6, 0))

    def _build_options_section(self) -> None:
        sec = self._section(self.content, "Opciones de calidad")

        grid = ctk.CTkFrame(sec, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=(0, 12))

        # Formato
        ctk.CTkLabel(grid, text="Formato:", font=FONT_BODY_SM, text_color=TEXT_SECONDARY).grid(
            row=0, column=0, sticky="w", padx=(0, 12), pady=4
        )
        self.format_var = tk.StringVar(value=self.settings.audio_format)
        fmt_menu = ctk.CTkOptionMenu(
            grid,
            variable=self.format_var,
            values=["m4a", "opus", "mp3", "best"],
            fg_color=SURFACE_CONTAINER_HIGH,
            button_color=NEON_RED_DIM,
            button_hover_color=NEON_RED,
            dropdown_fg_color=SURFACE_CONTAINER_HIGH,
            width=140,
        )
        fmt_menu.grid(row=0, column=1, sticky="w", pady=4)

        ctk.CTkLabel(
            grid,
            text="m4a = AAC sin re-codificar (recomendado Premium)",
            font=FONT_BODY_SM,
            text_color=TEXT_MUTED,
        ).grid(row=0, column=2, sticky="w", padx=(16, 0))

        # Carpeta destino
        ctk.CTkLabel(grid, text="Destino:", font=FONT_BODY_SM, text_color=TEXT_SECONDARY).grid(
            row=1, column=0, sticky="w", pady=4
        )
        self.output_var = tk.StringVar(value=self.settings.output_dir)
        out_frame = ctk.CTkFrame(grid, fg_color="transparent")
        out_frame.grid(row=1, column=1, columnspan=2, sticky="ew", pady=4)
        grid.columnconfigure(2, weight=1)

        ctk.CTkEntry(
            out_frame,
            textvariable=self.output_var,
            fg_color=SURFACE_CONTAINER_HIGH,
            border_color=SURFACE_CONTAINER_HIGHEST,
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            out_frame,
            text="Examinar",
            width=90,
            fg_color="transparent",
            border_color=NEON_RED,
            border_width=2,
            hover_color=SURFACE_CONTAINER_HIGHEST,
            text_color=TEXT_PRIMARY,
            command=self._pick_folder,
        ).pack(side="left")

        # Premium cookies
        prem_row = ctk.CTkFrame(sec, fg_color="transparent")
        prem_row.pack(fill="x", padx=16, pady=(0, 8))

        self.cookies_var = tk.BooleanVar(value=self.settings.use_cookies)
        ctk.CTkCheckBox(
            prem_row,
            text="Usar cookies del navegador (YouTube Music Premium → AAC 256 kbps)",
            variable=self.cookies_var,
            font=FONT_BODY_SM,
            text_color=TEXT_SECONDARY,
            fg_color=NEON_RED,
            hover_color=NEON_RED_DIM,
            border_color=NEON_RED_DIM,
        ).pack(side="left")

        self.browser_var = tk.StringVar(value=self.settings.browser)
        browsers = ["firefox", "chrome", "edge", "brave", "chromium", "opera", "vivaldi"]
        if sys.platform == "darwin":
            browsers.append("safari")
        ctk.CTkOptionMenu(
            prem_row,
            variable=self.browser_var,
            values=browsers,
            width=110,
            fg_color=SURFACE_CONTAINER_HIGH,
            button_color=NEON_RED_DIM,
            button_hover_color=NEON_RED,
        ).pack(side="left", padx=(12, 0))

        cookies_file_row = ctk.CTkFrame(sec, fg_color="transparent")
        cookies_file_row.pack(fill="x", padx=16, pady=(0, 4))

        ctk.CTkLabel(
            cookies_file_row,
            text="Archivo cookies (.txt):",
            font=FONT_LABEL,
            text_color=TEXT_SECONDARY,
            width=150,
            anchor="w",
        ).pack(side="left")

        self.cookies_file_var = tk.StringVar(value=self.settings.cookies_file)
        ctk.CTkEntry(
            cookies_file_row,
            textvariable=self.cookies_file_var,
            font=FONT_BODY_SM,
            fg_color=SURFACE_CONTAINER_HIGH,
            border_color=BORDER_RED,
            placeholder_text="Opcional — exporta con extensión Get cookies.txt LOCALLY",
        ).pack(side="left", fill="x", expand=True, padx=(8, 8))

        ctk.CTkButton(
            cookies_file_row,
            text="Examinar…",
            width=90,
            font=FONT_BODY_SM,
            fg_color=SURFACE_CONTAINER_HIGHEST,
            hover_color=NEON_RED_DIM,
            command=self._pick_cookies_file,
        ).pack(side="left")

        ctk.CTkLabel(
            sec,
            text=(
                "Si el navegador bloquea las cookies, ciérralo por completo. En macOS, "
                "acepta la solicitud del Llavero; Firefox o cookies.txt suelen ser más fiables."
            ),
            font=FONT_BODY_SM,
            text_color=TEXT_MUTED,
            wraplength=820,
            justify="left",
        ).pack(fill="x", padx=16, pady=(0, 8))

        # Metadatos
        meta_row = ctk.CTkFrame(sec, fg_color="transparent")
        meta_row.pack(fill="x", padx=16, pady=(0, 12))

        self.thumb_var = tk.BooleanVar(value=self.settings.embed_thumbnail)
        self.meta_var = tk.BooleanVar(value=self.settings.embed_metadata)
        ctk.CTkCheckBox(
            meta_row, text="Incrustar carátula", variable=self.thumb_var,
            font=FONT_BODY_SM, text_color=TEXT_SECONDARY,
            fg_color=NEON_RED, hover_color=NEON_RED_DIM,
        ).pack(side="left", padx=(0, 16))
        ctk.CTkCheckBox(
            meta_row, text="Incrustar metadatos", variable=self.meta_var,
            font=FONT_BODY_SM, text_color=TEXT_SECONDARY,
            fg_color=NEON_RED, hover_color=NEON_RED_DIM,
        ).pack(side="left")

    def _build_actions(self) -> None:
        row = ctk.CTkFrame(self.content, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=4)

        self.btn_download = ctk.CTkButton(
            row,
            text="⬇ DESCARGAR",
            font=_pick_font(FONT_HEADLINE, FONT_HEADLINE_FB),
            fg_color=NEON_RED,
            hover_color=NEON_RED_DIM,
            text_color="#000000",
            height=44,
            width=180,
            corner_radius=4,
            command=self._start_download,
        )
        self.btn_download.pack(side="left", padx=(0, 8))

        self.btn_cancel = ctk.CTkButton(
            row,
            text="Cancelar",
            font=FONT_BODY,
            fg_color="transparent",
            border_color=NEON_RED,
            border_width=2,
            hover_color=SURFACE_CONTAINER_HIGH,
            text_color=TEXT_PRIMARY,
            height=44,
            width=110,
            state="disabled",
            command=self._cancel_download,
        )
        self.btn_cancel.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            row,
            text="Formatos",
            font=FONT_BODY,
            fg_color="transparent",
            border_color=SURFACE_CONTAINER_HIGHEST,
            border_width=1,
            hover_color=SURFACE_CONTAINER_HIGH,
            text_color=TEXT_MUTED,
            height=44,
            width=100,
            command=self._list_formats,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            row,
            text="Abrir carpeta",
            font=FONT_BODY,
            fg_color="transparent",
            border_color=SURFACE_CONTAINER_HIGHEST,
            border_width=1,
            hover_color=SURFACE_CONTAINER_HIGH,
            text_color=TEXT_MUTED,
            height=44,
            width=110,
            command=self._open_output_folder,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            row,
            text="Actualizar yt-dlp",
            font=FONT_BODY_SM,
            fg_color=SURFACE_CONTAINER_HIGH,
            hover_color=SURFACE_CONTAINER_HIGHEST,
            text_color=TEXT_SECONDARY,
            height=44,
            width=140,
            command=self._update_ytdlp,
        ).pack(side="right")

    def _build_progress(self) -> None:
        prog_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        prog_frame.pack(fill="x", padx=24, pady=(8, 4))

        self.status_label = ctk.CTkLabel(
            prog_frame,
            text="Listo",
            font=FONT_BODY_SM,
            text_color=TEXT_MUTED,
        )
        self.status_label.pack(anchor="w")

        self.progress = ctk.CTkProgressBar(
            prog_frame,
            height=8,
            fg_color=SURFACE_CONTAINER_HIGH,
            progress_color=NEON_RED,
            corner_radius=4,
        )
        self.progress.pack(fill="x", pady=(4, 0))
        self.progress.set(0)

    def _build_log(self) -> None:
        sec = self._section(self.content, "Log")

        self.log_box = ctk.CTkTextbox(
            sec,
            height=160,
            font=FONT_MONO,
            fg_color=SURFACE_CONTAINER_HIGH,
            border_color=SURFACE_CONTAINER_HIGHEST,
            border_width=1,
            text_color=TEXT_SECONDARY,
            wrap="word",
        )
        self.log_box.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        self.log_box.configure(state="disabled")

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self.content, fg_color="transparent")
        footer.pack(fill="x", padx=24, pady=(4, 16))

        self.deps_label = ctk.CTkLabel(
            footer,
            text="Comprobando dependencias…",
            font=FONT_BODY_SM,
            text_color=TEXT_MUTED,
        )
        self.deps_label.pack(anchor="w")

    def _log(self, msg: str) -> None:
        def append() -> None:
            self.log_box.configure(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")

        self.after(0, append)

    def _set_status(self, text: str, pct: float | None = None) -> None:
        def update() -> None:
            self.status_label.configure(text=text)
            if pct is not None:
                self.progress.set(min(pct / 100.0, 1.0))

        self.after(0, update)

    def _refresh_deps(self) -> None:
        def worker() -> None:
            try:
                ensure_ytdlp(lambda m: self._log(m))
            except Exception as exc:  # noqa: BLE001 - no dejar caer el hilo de inicio
                self._log(f"Error yt-dlp: {exc}")
            report = dependency_report()
            text = " | ".join(f"{k}: {v}" for k, v in report.items())
            self.after(0, lambda: self.deps_label.configure(text=text))

        threading.Thread(target=worker, daemon=True).start()

    def _save_settings(self) -> None:
        self.settings.output_dir = self.output_var.get()
        self.settings.audio_format = self.format_var.get()
        self.settings.embed_thumbnail = self.thumb_var.get()
        self.settings.embed_metadata = self.meta_var.get()
        self.settings.use_cookies = self.cookies_var.get()
        self.settings.browser = self.browser_var.get()
        self.settings.cookies_file = self.cookies_file_var.get().strip()
        self.settings.playlist_items = self.playlist_var.get()
        self.settings.save()

    def _pick_cookies_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Seleccionar cookies.txt",
            filetypes=[("Cookies Netscape", "*.txt"), ("Todos", "*.*")],
        )
        if path:
            self.cookies_file_var.set(path)

    def _pick_folder(self) -> None:
        path = filedialog.askdirectory(initialdir=self.output_var.get())
        if path:
            self.output_var.set(path)

    def _open_output_folder(self) -> None:
        path = Path(self.output_var.get()).expanduser()
        try:
            path.mkdir(parents=True, exist_ok=True)
            if sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            elif sys.platform == "win32":
                subprocess.Popen(["explorer", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except OSError as exc:
            messagebox.showerror("No se pudo abrir la carpeta", str(exc))

    def _set_download_ui(self, running: bool) -> None:
        state_dl = "disabled" if running else "normal"
        state_cancel = "normal" if running else "disabled"
        self.btn_download.configure(state=state_dl)
        self.btn_cancel.configure(state=state_cancel)

    def _start_download(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("URL vacía", "Pega un enlace de YouTube Music.")
            return
        if not is_supported_url(url):
            messagebox.showwarning("URL inválida", "El enlace debe ser de YouTube Music o YouTube.")
            return

        ok_items, err_items = validate_playlist_items(self.playlist_var.get())
        if not ok_items:
            messagebox.showwarning("Ítems playlist inválidos", err_items)
            return

        self._save_settings()

        if self.settings.use_cookies and not self.settings.cookies_file.strip():
            browser = self.settings.browser
            if is_chromium_browser(browser):
                platform_detail = (
                    "macOS puede pedir permiso para acceder al Llavero y el navegador "
                    "debe estar cerrado con ⌘Q."
                    if sys.platform == "darwin"
                    else "El navegador debe estar cerrado por completo."
                )
                if not messagebox.askyesno(
                    "Aviso de cookies",
                    (
                        f"Has elegido «{browser}». {platform_detail}\n\n"
                        "¿Continuar igual?\n\n"
                        "Alternativa: Firefox o un archivo cookies.txt."
                    ),
                ):
                    return

        self._set_download_ui(True)
        self.progress.set(0)
        self._set_status("Iniciando…", 0)
        self._log("--- Nueva descarga ---")

        job = DownloadJob(url=url, settings=self.settings)

        def worker() -> None:
            ok, msg = self.downloader.download(
                job,
                on_log=self._log,
                on_status=self._set_status,
            )
            self.after(0, lambda: self._on_download_done(ok, msg))

        self._download_thread = threading.Thread(target=worker, daemon=True)
        self._download_thread.start()

    def _on_download_done(self, ok: bool, msg: str) -> None:
        self._set_download_ui(False)
        self._log(msg)
        if ok:
            self._set_status("Completado", 100)
            messagebox.showinfo("Descarga completa", msg)
        elif self.downloader.state != DownloadState.CANCELLED:
            self._set_status("Error", None)
            messagebox.showerror("Error", msg)

    def _cancel_download(self) -> None:
        self.downloader.cancel()
        self._log("Cancelando…")
        self._set_status("Cancelado", None)
        self._set_download_ui(False)

    def _list_formats(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("URL vacía", "Pega un enlace primero.")
            return
        self._save_settings()
        self._log("Listando formatos disponibles…")

        def worker() -> None:
            ok, out = self.downloader.list_formats(url, self.settings)
            self._log(out if ok else f"Error: {out}")

        threading.Thread(target=worker, daemon=True).start()

    def _update_ytdlp(self) -> None:
        self._log("Actualizando yt-dlp…")

        def worker() -> None:
            ok, msg = update_ytdlp(self._log)
            self._log(msg)
            self._refresh_deps()
            if ok:
                self.after(0, lambda: messagebox.showinfo("yt-dlp", msg))

        threading.Thread(target=worker, daemon=True).start()

    def _on_close(self) -> None:
        self._save_settings()
        if self.downloader.state == DownloadState.RUNNING:
            self.downloader.cancel()
        self.destroy()


def run_app() -> None:
    app = RugdraigerApp()
    app.mainloop()
