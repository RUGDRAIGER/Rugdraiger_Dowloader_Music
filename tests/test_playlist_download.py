"""
Prueba de descarga de playlist — Rugdraiger Downloader Music.
Ejecutar: python tests/test_playlist_download.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import AppSettings
from app.core.downloader import DownloadJob, YtDlpDownloader
from app.core.url_utils import is_playlist_url

# Playlist pública de prueba (YouTube / YT Music compatible)
TEST_PLAYLIST = "https://www.youtube.com/playlist?list=PLFgquLnL59alCl_2TQvOiD5Vgm1hCaGSI"
TEST_ITEMS = "1-2"


def run_case(name: str, url: str, items: str) -> None:
    out_dir = ROOT / "test_playlist" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*"):
        if old.is_file():
            old.unlink()

    settings = AppSettings()
    settings.output_dir = str(out_dir)
    settings.audio_format = "m4a"
    settings.embed_thumbnail = False
    settings.embed_metadata = False
    settings.use_cookies = False
    settings.playlist_items = items

    assert is_playlist_url(url), f"URL no detectada como playlist: {url}"

    logs: list[str] = []
    ok, msg = YtDlpDownloader().download(
        DownloadJob(url=url, settings=settings),
        on_log=logs.append,
    )
    files = sorted(out_dir.glob("*"))
    print(f"\n=== {name} ===")
    print(f"OK: {ok}")
    print(f"Mensaje: {msg}")
    print(f"Archivos: {len(files)}")
    for f in files:
        print(f"  - {f.name}")

    if not ok:
        raise SystemExit(f"Fallo: {name}")
    if items == TEST_ITEMS and len(files) < 2:
        raise SystemExit(f"Se esperaban 2 archivos en {name}, hay {len(files)}")
    if items == "" and len(files) < 2:
        raise SystemExit(f"Playlist completa debería tener al menos 2 archivos en {name}")


def main() -> None:
    print("Verificando descarga de playlists…")
    run_case("yt_playlist_partial", TEST_PLAYLIST, TEST_ITEMS)
    run_case(
        "music_yt_playlist_partial",
        TEST_PLAYLIST.replace("www.youtube.com", "music.youtube.com"),
        TEST_ITEMS,
    )
    run_case(
        "watch_with_list",
        "https://music.youtube.com/watch?v=wgOxc8F_Y8o&list=PLFgquLnL59alCl_2TQvOiD5Vgm1hCaGSI",
        TEST_ITEMS,
    )
    print("\nTODAS LAS PRUEBAS DE PLAYLIST OK.")


if __name__ == "__main__":
    main()
