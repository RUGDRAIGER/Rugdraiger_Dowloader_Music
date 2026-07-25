"""Configuración persistente de la aplicación."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.paths import app_root, bin_dir, config_dir
from app.core.validators import normalize_playlist_items

ROOT = app_root()
CONFIG_DIR = config_dir()
CONFIG_FILE = CONFIG_DIR / "settings.json"
BIN_DIR = bin_dir()
DOWNLOADS_DEFAULT = Path.home() / "Music" / "Rugdraiger Downloads"


@dataclass
class AppSettings:
    output_dir: str = str(DOWNLOADS_DEFAULT)
    audio_format: str = "m4a"  # m4a | opus | mp3 | best
    embed_thumbnail: bool = True
    embed_metadata: bool = True
    use_cookies: bool = False
    browser: str = "firefox"  # firefox recomendado para cookies YT Music
    cookies_file: str = ""  # alternativa: cookies.txt exportadas (Netscape)
    playlist_items: str = ""  # vacío = todo; ej. "1-10"
    filename_template: str = "%(artist)s - %(title)s"

    @classmethod
    def load(cls) -> AppSettings:
        if not CONFIG_FILE.exists():
            return cls()
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            settings = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            settings.playlist_items = normalize_playlist_items(settings.playlist_items)
            return settings
        except (json.JSONDecodeError, TypeError):
            return cls()

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        data["playlist_items"] = normalize_playlist_items(self.playlist_items)
        CONFIG_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def ensure_dirs() -> None:
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    Path(AppSettings.load().output_dir).mkdir(parents=True, exist_ok=True)
