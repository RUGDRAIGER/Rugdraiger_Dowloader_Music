"""Utilidades para URLs de YouTube / YouTube Music."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

PLAYLIST_ID_RE = re.compile(r"list=([a-zA-Z0-9_-]+)")
PLAYLIST_PATH_RE = re.compile(r"/playlist\b", re.I)


def is_playlist_url(url: str) -> bool:
    """True si la URL apunta a una playlist o mezcla watch + list=."""
    if not url.strip():
        return False
    parsed = urlparse(url.strip())
    query = parse_qs(parsed.query)
    if query.get("list"):
        return True
    return bool(PLAYLIST_PATH_RE.search(parsed.path or ""))


def playlist_id_from_url(url: str) -> str | None:
    match = PLAYLIST_ID_RE.search(url)
    return match.group(1) if match else None
