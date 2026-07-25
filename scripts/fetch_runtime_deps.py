"""
Descarga ffmpeg y Node.js portables a bin/ para incluirlos en la app.

Ejecutado por setup.bat y build-installer.ps1 — el usuario final no necesita winget.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN_DIR = ROOT / "bin"

FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
NODE_INDEX_URL = "https://nodejs.org/dist/index.json"

MIN_SIZES = {
    "ffmpeg.exe": 50_000_000,
    "ffprobe.exe": 50_000_000,
    "node.exe": 20_000_000,
}


def log(msg: str) -> None:
    print(msg, flush=True)


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "Rugdraiger-Downloader/1.0"})
    with urllib.request.urlopen(req, timeout=300) as response:
        dest.write_bytes(response.read())


def latest_node_lts_win_x64() -> tuple[str, str]:
    with urllib.request.urlopen(
        urllib.request.Request(NODE_INDEX_URL, headers={"User-Agent": "Rugdraiger-Downloader/1.0"}),
        timeout=60,
    ) as response:
        releases = json.loads(response.read().decode("utf-8"))
    for entry in releases:
        if entry.get("lts"):
            version = entry["version"]
            filename = f"node-{version}-win-x64.zip"
            url = f"https://nodejs.org/dist/{version}/{filename}"
            return url, filename
    raise RuntimeError("No se encontro una version LTS de Node.js.")


def extract_member(zf: zipfile.ZipFile, name_part: str, dest: Path) -> None:
    needle = name_part.replace("\\", "/").lstrip("/")
    member = next(
        (name for name in zf.namelist() if name.replace("\\", "/").endswith(needle)),
        None,
    )
    if not member:
        raise FileNotFoundError(f"No se encontro {name_part} en el archivo zip.")
    with zf.open(member) as src, dest.open("wb") as out:
        shutil.copyfileobj(src, out)


def needs(name: str) -> bool:
    path = BIN_DIR / name
    return not path.exists() or path.stat().st_size < MIN_SIZES.get(name, 1000)


def ensure_ffmpeg() -> None:
    if not (needs("ffmpeg.exe") or needs("ffprobe.exe")):
        log("[ok] ffmpeg y ffprobe ya estan en bin/")
        return

    log("[1/2] Descargando ffmpeg (Gyan builds)...")
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "ffmpeg.zip"
        download(FFMPEG_URL, zip_path)
        with zipfile.ZipFile(zip_path) as zf:
            extract_member(zf, "bin/ffmpeg.exe", BIN_DIR / "ffmpeg.exe")
            extract_member(zf, "bin/ffprobe.exe", BIN_DIR / "ffprobe.exe")
    log("     ffmpeg instalado en bin/")


def ensure_node() -> None:
    if not needs("node.exe"):
        log("[ok] node.exe ya esta en bin/")
        return

    log("[2/2] Descargando Node.js LTS (win-x64)...")
    url, _ = latest_node_lts_win_x64()
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "node.zip"
        download(url, zip_path)
        with zipfile.ZipFile(zip_path) as zf:
            extract_member(zf, "node.exe", BIN_DIR / "node.exe")
    log("     node.exe instalado en bin/")


def main() -> int:
    log("")
    log("  RUGDRAIGER — Dependencias empaquetadas (ffmpeg + Node.js)")
    log("")
    try:
        ensure_ffmpeg()
        ensure_node()
    except Exception as exc:
        log(f"[ERROR] {exc}")
        return 1

    log("")
    log("  Listo. ffmpeg, ffprobe y node.exe estan en bin/")
    log("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
