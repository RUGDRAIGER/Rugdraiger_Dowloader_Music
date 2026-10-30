"""Motor de descarga basado en yt-dlp para YouTube Music."""

from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
import threading
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from app.config import AppSettings
from app.core.cookie_help import cookie_error_message
from app.core.dependencies import (
    ensure_ytdlp,
    ffmpeg_available,
    ffmpeg_location_args,
    find_ytdlp,
    js_runtime_args,
)
from app.core.url_utils import is_playlist_url
from app.core.validators import normalize_playlist_items

ProgressCallback = Callable[[str], None]
StatusCallback = Callable[[str, float | None], None]


class DownloadState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class DownloadJob:
    url: str
    settings: AppSettings


class YtDlpDownloader:
    """
    Descarga audio de YouTube Music usando yt-dlp.

    Estrategia de calidad (sin re-codificar innecesariamente):
    - m4a/opus/best: -f ba + remux si hace falta (requiere ffmpeg)
    - mp3: conversión explícita con -x (requiere ffmpeg)
    - Sin ffmpeg: descarga audio nativo sin postproceso
    - Premium: cookies del navegador + formats=missing_pot
    """

    PROGRESS_RE = re.compile(
        r"\[download\]\s+(?:(\d+(?:\.\d+)?%)|\s*(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?))"
    )
    DESTINATION_RE = re.compile(r"\[download\] Destination: (.+)")
    MERGER_RE = re.compile(r"\[Merger\] Merging formats into \"(.+)\"")
    EXTRACT_AUDIO_RE = re.compile(r"\[ExtractAudio\] Destination: (.+)")
    FINAL_FILE_RE = re.compile(r"^__RUGDRAIGER_FILE__:(.+)$")
    ERROR_RE = re.compile(r"^ERROR: (.+)$")
    PLAYLIST_COUNT_RE = re.compile(r"Downloading (\d+) items of playlist")
    PLAYLIST_ITEM_RE = re.compile(r"\[download\] Downloading item (\d+) of (\d+)")

    def __init__(self) -> None:
        self._process: subprocess.Popen | None = None
        self._state = DownloadState.IDLE
        self._lock = threading.Lock()

    @property
    def state(self) -> DownloadState:
        return self._state

    def cancel(self) -> None:
        with self._lock:
            if self._process and self._process.poll() is None:
                self._state = DownloadState.CANCELLED
                if sys.platform == "win32":
                    self._process.terminate()
                else:
                    try:
                        os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
                    except (ProcessLookupError, PermissionError):
                        self._process.terminate()

    def _build_command(self, job: DownloadJob, ytdlp: Path) -> tuple[list[str], list[str]]:
        s = job.settings
        out = Path(s.output_dir).expanduser()
        out.mkdir(parents=True, exist_ok=True)
        notes: list[str] = []
        has_ffmpeg = ffmpeg_available()
        playlist_items = normalize_playlist_items(s.playlist_items)
        if playlist_items != s.playlist_items.strip() and s.playlist_items.strip():
            notes.append(
                f"Items playlist corregidos: '{s.playlist_items.strip()}' -> '{playlist_items}'"
            )
        playlist_mode = is_playlist_url(job.url) or bool(playlist_items)

        if playlist_mode:
            filename = f"%(playlist_index)02d - {s.filename_template}.%(ext)s"
        else:
            filename = f"{s.filename_template}.%(ext)s"

        cmd: list[str] = [
            str(ytdlp),
            "--no-update",
            "--no-playlist-reverse",
            "--ignore-errors",
            "--progress",
            "--newline",
            "--no-colors",
            "--trim-filenames", "180",
            "--print", "after_move:__RUGDRAIGER_FILE__:%(filepath)s",
            "-o", str(out / filename),
        ]
        cmd.extend(js_runtime_args())
        cmd.extend(ffmpeg_location_args())

        if is_playlist_url(job.url):
            cmd.append("--yes-playlist")
            if playlist_items:
                notes.append(f"Playlist: descargando ítems {playlist_items}.")
            else:
                notes.append("Playlist detectada: se descargarán TODAS las canciones.")
        elif playlist_items:
            notes.append(f"Descarga parcial de lista: ítems {playlist_items}.")

        if playlist_items:
            cmd.extend(["--playlist-items", playlist_items])

        fmt = s.audio_format.lower()
        embed_thumb = s.embed_thumbnail and has_ffmpeg
        embed_meta = s.embed_metadata and has_ffmpeg

        if not has_ffmpeg:
            install_hint = "brew install ffmpeg" if sys.platform == "darwin" else "instala ffmpeg"
            notes.append(
                "ffmpeg no detectado: descarga sin carátula/metadatos/remux. "
                f"Solución: {install_hint}."
            )

        if has_ffmpeg:
            if fmt == "m4a":
                cmd.extend([
                    "-f", "ba[ext=m4a]/ba[acodec^=mp4a.40.]/ba/b",
                    "-x", "--audio-format", "m4a", "--audio-quality", "0",
                ])
            elif fmt == "opus":
                cmd.extend([
                    "-f", "ba[acodec=opus]/ba/b",
                    "-x", "--audio-format", "opus", "--audio-quality", "0",
                ])
            elif fmt == "mp3":
                cmd.extend([
                    "-f", "ba/b",
                    "-x",
                    "--audio-format", "mp3",
                    "--audio-quality", "0",
                ])
            else:
                cmd.extend(["-f", "ba/b"])
        else:
            if fmt == "m4a":
                cmd.extend(["-f", "ba[ext=m4a]/ba/b"])
            elif fmt == "opus":
                cmd.extend(["-f", "ba[acodec=opus]/ba/b"])
            else:
                cmd.extend(["-f", "ba/b"])
            if fmt == "mp3":
                notes.append("MP3 requiere ffmpeg. Se descargará el mejor audio nativo disponible.")

        if embed_thumb:
            cmd.append("--embed-thumbnail")
        elif s.embed_thumbnail and not has_ffmpeg:
            notes.append("Carátula omitida (instala ffmpeg para activarla).")

        if embed_meta:
            cmd.extend(["--embed-metadata", "--parse-metadata", "%(artist)s:%(meta_artist)s"])
        elif s.embed_metadata and not has_ffmpeg:
            notes.append("Metadatos embebidos omitidos (instala ffmpeg para activarlos).")

        if embed_thumb:
            cmd.extend(["--convert-thumbnails", "jpg"])

        if s.use_cookies:
            cookies_path = Path(s.cookies_file.strip()) if s.cookies_file.strip() else None
            if cookies_path and cookies_path.is_file():
                cmd.extend(["--cookies", str(cookies_path)])
                notes.append(f"Usando archivo cookies: {cookies_path.name}")
            else:
                cmd.extend(["--cookies-from-browser", s.browser])

        if s.use_cookies:
            cmd.extend([
                "--extractor-args",
                "youtube:player_client=web_music,default;formats=missing_pot",
            ])

        cmd.append(job.url)
        return cmd, notes

    def download(
        self,
        job: DownloadJob,
        on_log: ProgressCallback | None = None,
        on_status: StatusCallback | None = None,
    ) -> tuple[bool, str]:
        ytdlp = find_ytdlp() or ensure_ytdlp(on_log)
        cmd, notes = self._build_command(job, ytdlp)

        for note in notes:
            if on_log:
                on_log(f"[aviso] {note}")

        if on_log:
            on_log(f"Comando: {' '.join(cmd[:10])}…")

        self._state = DownloadState.RUNNING
        last_file = ""
        last_errors: list[str] = []
        downloaded_files: list[str] = []
        playlist_total: int | None = None
        playlist_current: int | None = None

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                start_new_session=sys.platform != "win32",
            )

            assert self._process.stdout is not None
            for line in self._process.stdout:
                line = line.rstrip()
                if not line:
                    continue

                if on_log:
                    on_log(line)

                err = self.ERROR_RE.match(line)
                if err:
                    last_errors.append(err.group(1))

                final_file = self.FINAL_FILE_RE.match(line)
                if final_file:
                    last_file = final_file.group(1)
                    if last_file not in downloaded_files:
                        downloaded_files.append(last_file)

                dest = self.DESTINATION_RE.search(line)
                if dest:
                    last_file = dest.group(1)
                merger = self.MERGER_RE.search(line)
                if merger:
                    last_file = merger.group(1)
                extract = self.EXTRACT_AUDIO_RE.search(line)
                if extract:
                    last_file = extract.group(1)

                pl_count = self.PLAYLIST_COUNT_RE.search(line)
                if pl_count:
                    playlist_total = int(pl_count.group(1))

                pl_item = self.PLAYLIST_ITEM_RE.search(line)
                if pl_item:
                    playlist_current = int(pl_item.group(1))
                    playlist_total = int(pl_item.group(2))
                    if on_status:
                        pct = (playlist_current / playlist_total) * 100 if playlist_total else None
                        on_status(
                            f"Playlist: canción {playlist_current} de {playlist_total}",
                            pct,
                        )

                pct_match = self.PROGRESS_RE.search(line)
                if pct_match and on_status:
                    pct_str = pct_match.group(1)
                    if pct_str:
                        try:
                            pct = float(pct_str.rstrip("%"))
                            on_status("Descargando…", pct)
                        except ValueError:
                            pass

            code = self._process.wait()
            self._process = None

            if self._state == DownloadState.CANCELLED:
                return False, "Descarga cancelada."

            if code == 0:
                self._state = DownloadState.SUCCESS
                count = len(downloaded_files)
                if count > 1:
                    msg = f"Playlist completada: {count} canciones descargadas."
                    msg += f"\nÚltima: {Path(last_file).name}"
                elif last_file:
                    msg = f"Completado. Archivo: {last_file}"
                else:
                    msg = "Descarga completada."
                if notes:
                    msg += "\n\n" + "\n".join(notes)
                if on_status:
                    on_status("Completado", 100.0)
                return True, msg

            self._state = DownloadState.ERROR
            if downloaded_files:
                return False, (
                    f"Descarga incompleta: se guardaron {len(downloaded_files)} archivo(s), "
                    "pero yt-dlp informó un error. Revisa el log."
                )
            if last_errors:
                detail = cookie_error_message(last_errors[-1])
                if "ffmpeg" in detail.lower():
                    detail += "\n\nComprueba FFmpeg en la sección de dependencias."
                return False, detail
            if code == 2:
                return False, (
                    "Error de parámetros en yt-dlp (código 2). "
                    "Revisa «Ítems playlist» (usa 1-5 sin espacios, o vacío para todas) "
                    "y el enlace pegado."
                )
            return False, f"yt-dlp terminó con código {code}. Revisa el log."

        except Exception as exc:  # noqa: BLE001 - frontera de proceso externo
            self._state = DownloadState.ERROR
            return False, str(exc)

    def list_formats(self, url: str, settings: AppSettings) -> tuple[bool, str]:
        """Lista formatos disponibles (útil para diagnosticar calidad)."""
        ytdlp = find_ytdlp() or ensure_ytdlp()
        cmd = [str(ytdlp), "--no-colors", "--list-formats", url]
        cmd.extend(js_runtime_args())
        cmd.extend(ffmpeg_location_args())
        if settings.use_cookies:
            cookies_path = (
                Path(settings.cookies_file.strip())
                if settings.cookies_file.strip()
                else None
            )
            if cookies_path and cookies_path.is_file():
                cmd.extend(["--cookies", str(cookies_path)])
            else:
                cmd.extend(["--cookies-from-browser", settings.browser])
            cmd.extend([
                "--extractor-args",
                "youtube:player_client=web_music,default;formats=missing_pot",
            ])
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                check=False,
            )
            out = (result.stdout or "") + (result.stderr or "")
            return result.returncode == 0, out
        except Exception as exc:  # noqa: BLE001 - error amigable para la interfaz
            return False, str(exc)
