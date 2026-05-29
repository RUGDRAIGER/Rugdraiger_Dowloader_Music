"""Motor de descarga basado en yt-dlp para YouTube Music."""

from __future__ import annotations

import re
import subprocess
import sys
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

from app.config import AppSettings
from app.core.dependencies import (
    ensure_ytdlp,
    ffmpeg_available,
    ffmpeg_location_args,
    find_ytdlp,
    js_runtime_args,
)

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
    ERROR_RE = re.compile(r"^ERROR: (.+)$")

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
                self._process.terminate()
                self._state = DownloadState.CANCELLED

    def _build_command(self, job: DownloadJob, ytdlp: Path) -> tuple[list[str], list[str]]:
        s = job.settings
        out = Path(s.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        notes: list[str] = []
        has_ffmpeg = ffmpeg_available()

        cmd: list[str] = [
            str(ytdlp),
            "--no-playlist-reverse",
            "--ignore-errors",
            "--progress",
            "--newline",
            "-o", str(out / f"{s.filename_template}.%(ext)s"),
        ]
        cmd.extend(js_runtime_args())
        cmd.extend(ffmpeg_location_args())

        if s.playlist_items.strip():
            cmd.extend(["--playlist-items", s.playlist_items.strip()])

        fmt = s.audio_format.lower()
        embed_thumb = s.embed_thumbnail and has_ffmpeg
        embed_meta = s.embed_metadata and has_ffmpeg

        if not has_ffmpeg:
            notes.append(
                "ffmpeg no detectado: descarga sin carátula/metadatos/remux. "
                "Instala con: winget install Gyan.FFmpeg"
            )

        if has_ffmpeg:
            if fmt == "m4a":
                cmd.extend([
                    "-f", "ba[acodec^=mp4a.40.2]/ba[acodec^=mp4a.40.]/ba/b",
                    "--remux-video", "m4a",
                ])
            elif fmt == "opus":
                cmd.extend([
                    "-f", "ba[acodec=opus]/ba/b",
                    "--remux-video", "opus",
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

        if embed_thumb or embed_meta:
            cmd.extend(["--add-metadata", "--convert-thumbnails", "jpg"])

        if s.use_cookies:
            cmd.extend(["--cookies-from-browser", s.browser])

        extractor_args = "youtube:player_client=android,web,default"
        if s.use_cookies:
            extractor_args = "youtube:player_client=web_music,android,default;formats=missing_pot"
        cmd.extend(["--extractor-args", extractor_args])

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

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
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

                dest = self.DESTINATION_RE.search(line)
                if dest:
                    last_file = dest.group(1)
                merger = self.MERGER_RE.search(line)
                if merger:
                    last_file = merger.group(1)
                extract = self.EXTRACT_AUDIO_RE.search(line)
                if extract:
                    last_file = extract.group(1)

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

            if code == 0 or last_file:
                self._state = DownloadState.SUCCESS
                msg = f"Completado. Archivo: {last_file}" if last_file else "Descarga completada."
                if notes:
                    msg += "\n\n" + "\n".join(notes)
                if on_status:
                    on_status("Completado", 100.0)
                return True, msg

            self._state = DownloadState.ERROR
            if last_errors:
                detail = last_errors[-1]
                if "ffmpeg" in detail.lower():
                    detail += "\n\nInstala ffmpeg: winget install Gyan.FFmpeg"
                return False, detail
            return False, f"yt-dlp terminó con código {code}. Revisa el log."

        except Exception as exc:
            self._state = DownloadState.ERROR
            return False, str(exc)

    def list_formats(self, url: str, settings: AppSettings) -> tuple[bool, str]:
        """Lista formatos disponibles (útil para diagnosticar calidad)."""
        ytdlp = find_ytdlp() or ensure_ytdlp()
        cmd = [str(ytdlp), "--list-formats", url]
        cmd.extend(js_runtime_args())
        cmd.extend(ffmpeg_location_args())
        if settings.use_cookies:
            cmd.extend([
                "--cookies-from-browser", settings.browser,
                "--extractor-args", "youtube:player_client=web_music,android,default;formats=missing_pot",
            ])
        else:
            cmd.extend(["--extractor-args", "youtube:player_client=android,web,default"])
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            out = (result.stdout or "") + (result.stderr or "")
            return result.returncode == 0, out
        except Exception as exc:
            return False, str(exc)
