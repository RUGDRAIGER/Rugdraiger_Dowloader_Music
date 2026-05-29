"""Gestión de dependencias: yt-dlp, ffmpeg y runtime JS."""

from __future__ import annotations

import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Callable

from app.config import BIN_DIR

YTDLP_RELEASE_URL = (
    "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
)
YTDLP_PATH = BIN_DIR / "yt-dlp.exe"
FFMPEG_PATH = BIN_DIR / "ffmpeg.exe"
FFPROBE_PATH = BIN_DIR / "ffprobe.exe"


def _run(cmd: list[str], timeout: int = 15) -> tuple[int, str]:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        out = (result.stdout or "") + (result.stderr or "")
        return result.returncode, out.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        return 1, str(exc)


def find_ytdlp() -> Path | None:
    if YTDLP_PATH.exists():
        return YTDLP_PATH
    which = shutil.which("yt-dlp")
    if which:
        return Path(which)
    return None


def download_ytdlp(on_progress: Callable[[str], None] | None = None) -> Path:
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    if on_progress:
        on_progress("Descargando yt-dlp desde GitHub…")

    req = urllib.request.Request(
        YTDLP_RELEASE_URL,
        headers={"User-Agent": "Rugdraiger-Downloader/1.0"},
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        YTDLP_PATH.write_bytes(response.read())

    if on_progress:
        on_progress(f"yt-dlp instalado en {YTDLP_PATH}")
    return YTDLP_PATH


def ensure_ytdlp(on_progress: Callable[[str], None] | None = None) -> Path:
    existing = find_ytdlp()
    if existing:
        return existing
    return download_ytdlp(on_progress)


def find_ffmpeg() -> str | None:
    if FFMPEG_PATH.exists():
        return str(FFMPEG_PATH)
    return shutil.which("ffmpeg")


def find_ffprobe() -> str | None:
    if FFPROBE_PATH.exists():
        return str(FFPROBE_PATH)
    return shutil.which("ffprobe")


def ffmpeg_available() -> bool:
    return bool(find_ffmpeg() and find_ffprobe())


def ffmpeg_location_args() -> list[str]:
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        return []
    return ["--ffmpeg-location", str(Path(ffmpeg).parent)]


def js_runtime_args() -> list[str]:
    for runtime in ("node", "deno", "bun"):
        if shutil.which(runtime):
            return ["--js-runtimes", runtime]
    return []


def check_ffmpeg() -> tuple[bool, str]:
    ffmpeg = find_ffmpeg()
    ffprobe = find_ffprobe()
    if ffmpeg and ffprobe:
        code, out = _run([ffmpeg, "-version"])
        version_line = out.split("\n")[0] if out else "desconocida"
        return True, version_line
    missing = []
    if not ffmpeg:
        missing.append("ffmpeg")
    if not ffprobe:
        missing.append("ffprobe")
    return False, f"Faltan: {', '.join(missing)}. Instala ffmpeg y añádelo al PATH."


def check_js_runtime() -> tuple[bool, str]:
    for runtime, args in (
        ("node", ["--version"]),
        ("deno", ["--version"]),
        ("bun", ["--version"]),
    ):
        if shutil.which(runtime):
            code, out = _run([runtime, *args])
            if code == 0:
                return True, f"{runtime} {out.split(chr(10))[0]}"
    return False, (
        "No se detectó Node.js, Deno ni Bun. "
        "Instala Node.js LTS para resolver desafíos JS de YouTube."
    )


def get_ytdlp_version(path: Path) -> str:
    code, out = _run([str(path), "--version"])
    return out if code == 0 else "desconocida"


def update_ytdlp(on_progress: Callable[[str], None] | None = None) -> tuple[bool, str]:
    ytdlp = ensure_ytdlp(on_progress)
    if on_progress:
        on_progress("Actualizando yt-dlp…")
    code, out = _run([str(ytdlp), "-U"], timeout=120)
    if code == 0:
        return True, out or "yt-dlp actualizado."
    return False, out or "No se pudo actualizar yt-dlp."


def dependency_report() -> dict[str, str]:
    ytdlp = find_ytdlp()
    ffmpeg_ok, ffmpeg_msg = check_ffmpeg()
    js_ok, js_msg = check_js_runtime()
    return {
        "yt-dlp": get_ytdlp_version(ytdlp) if ytdlp else "No instalado",
        "ffmpeg": ffmpeg_msg if ffmpeg_ok else f"[!] {ffmpeg_msg}",
        "js_runtime": js_msg if js_ok else f"[!] {js_msg}",
    }
