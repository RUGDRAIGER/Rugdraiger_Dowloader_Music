"""Gestión multiplataforma de yt-dlp, ffmpeg y el runtime JavaScript."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from collections.abc import Callable
from pathlib import Path

from app.config import BIN_DIR
from app.paths import bundled_bin_dir

ProgressCallback = Callable[[str], None]


def _ytdlp_release() -> tuple[str, str]:
    if sys.platform == "win32":
        return "yt-dlp.exe", "yt-dlp.exe"
    if sys.platform == "darwin":
        return "yt-dlp", "yt-dlp_macos"
    machine = platform.machine().lower()
    asset = "yt-dlp_linux_aarch64" if machine in {"arm64", "aarch64"} else "yt-dlp_linux"
    return "yt-dlp", asset


YTDLP_NAME, YTDLP_ASSET = _ytdlp_release()
YTDLP_RELEASE_URL = f"https://github.com/yt-dlp/yt-dlp/releases/latest/download/{YTDLP_ASSET}"
YTDLP_PATH = BIN_DIR / YTDLP_NAME


def _run(cmd: list[str], timeout: int = 15) -> tuple[int, str]:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            check=False,
        )
        output = (result.stdout or "") + (result.stderr or "")
        return result.returncode, output.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        return 1, str(exc)


def _tool_candidates(name: str) -> list[Path]:
    executable = f"{name}.exe" if sys.platform == "win32" else name
    candidates = [BIN_DIR / executable, bundled_bin_dir() / executable]
    found = shutil.which(executable)
    if found:
        candidates.append(Path(found))
    if sys.platform == "darwin":
        candidates.extend(
            [Path("/opt/homebrew/bin") / executable, Path("/usr/local/bin") / executable]
        )
    return candidates


def _first_executable(name: str) -> Path | None:
    for candidate in _tool_candidates(name):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def find_ytdlp() -> Path | None:
    return _first_executable("yt-dlp")


def download_ytdlp(on_progress: ProgressCallback | None = None) -> Path:
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    if on_progress:
        on_progress(f"Descargando {YTDLP_ASSET} desde GitHub…")
    request = urllib.request.Request(
        YTDLP_RELEASE_URL,
        headers={"User-Agent": "Rugdraiger-Downloader/2.0"},
    )
    temporary = YTDLP_PATH.with_suffix(YTDLP_PATH.suffix + ".download")
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            temporary.write_bytes(response.read())
        if sys.platform != "win32":
            temporary.chmod(0o755)
        temporary.replace(YTDLP_PATH)
    finally:
        temporary.unlink(missing_ok=True)
    if on_progress:
        on_progress(f"yt-dlp instalado en {YTDLP_PATH}")
    return YTDLP_PATH


def ensure_ytdlp(on_progress: ProgressCallback | None = None) -> Path:
    return find_ytdlp() or download_ytdlp(on_progress)


def find_ffmpeg() -> str | None:
    path = _first_executable("ffmpeg")
    return str(path) if path else None


def find_ffprobe() -> str | None:
    path = _first_executable("ffprobe")
    return str(path) if path else None


def ffmpeg_available() -> bool:
    return bool(find_ffmpeg() and find_ffprobe())


def ffmpeg_location_args() -> list[str]:
    ffmpeg = find_ffmpeg()
    return ["--ffmpeg-location", str(Path(ffmpeg).parent)] if ffmpeg else []


def find_js_runtime() -> tuple[str, Path] | None:
    for runtime in ("deno", "node", "quickjs", "bun"):
        path = _first_executable(runtime)
        if path:
            return runtime, path
    return None


def js_runtime_args() -> list[str]:
    runtime = find_js_runtime()
    if not runtime:
        return []
    name, path = runtime
    return ["--js-runtimes", f"{name}:{path}"]


def check_ffmpeg() -> tuple[bool, str]:
    ffmpeg = find_ffmpeg()
    ffprobe = find_ffprobe()
    if ffmpeg and ffprobe:
        code, output = _run([ffmpeg, "-version"])
        version = output.splitlines()[0] if output else "versión desconocida"
        return code == 0, version
    missing = [name for name, value in (("ffmpeg", ffmpeg), ("ffprobe", ffprobe)) if not value]
    install = "brew install ffmpeg" if sys.platform == "darwin" else "instala ffmpeg en el PATH"
    return False, f"Faltan: {', '.join(missing)}. Ejecuta: {install}."


def check_js_runtime() -> tuple[bool, str]:
    runtime = find_js_runtime()
    if not runtime:
        install = "brew install deno" if sys.platform == "darwin" else "instala Deno o Node.js"
        return False, f"No se detectó un runtime JavaScript. Ejecuta: {install}."
    name, path = runtime
    code, output = _run([str(path), "--version"])
    version = output.splitlines()[0] if output else "versión desconocida"
    return code == 0, f"{name}: {version}"


def get_ytdlp_version(path: Path) -> str:
    code, output = _run([str(path), "--version"])
    return output.splitlines()[0] if code == 0 and output else "desconocida"


def update_ytdlp(on_progress: ProgressCallback | None = None) -> tuple[bool, str]:
    ytdlp = ensure_ytdlp(on_progress)
    if on_progress:
        on_progress("Actualizando yt-dlp…")
    code, output = _run([str(ytdlp), "-U"], timeout=120)
    if code == 0:
        return True, output or "yt-dlp actualizado."
    if ytdlp.resolve() != YTDLP_PATH.resolve():
        return False, "yt-dlp lo gestiona el sistema. Actualízalo con Homebrew o pip."
    return False, output or "No se pudo actualizar yt-dlp."


def dependency_report() -> dict[str, str]:
    ytdlp = find_ytdlp()
    ffmpeg_ok, ffmpeg_message = check_ffmpeg()
    js_ok, js_message = check_js_runtime()
    return {
        "yt-dlp": get_ytdlp_version(ytdlp) if ytdlp else "No instalado",
        "ffmpeg": ffmpeg_message if ffmpeg_ok else f"⚠ {ffmpeg_message}",
        "js": js_message if js_ok else f"⚠ {js_message}",
    }
