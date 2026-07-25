"""Validación y normalización de opciones de descarga."""

from __future__ import annotations

import re

PLAYLIST_ITEMS_RE = re.compile(r"^[0-9,\-\s]+$")


def normalize_playlist_items(value: str) -> str:
    """
    Normaliza el campo «ítems playlist» para yt-dlp.

    Acepta entradas humanas como «1 - 5» y las convierte a «1-5».
    Vacío = descargar toda la playlist.
    """
    raw = value.strip()
    if not raw:
        return ""

    compact = re.sub(r"\s+", "", raw)
    compact = compact.replace("–", "-").replace("—", "-")
    return compact


def validate_playlist_items(value: str) -> tuple[bool, str]:
    """Devuelve (válido, mensaje de error)."""
    normalized = normalize_playlist_items(value)
    if not normalized:
        return True, ""

    if not PLAYLIST_ITEMS_RE.match(normalized):
        return False, (
            "Formato inválido en «Ítems playlist».\n\n"
            "Ejemplos válidos:\n"
            "  (vacío) = todas las canciones\n"
            "  1-5\n"
            "  1,3,7"
        )

    for part in normalized.split(","):
        part = part.strip()
        if not part:
            return False, "Hay comas sueltas en «Ítems playlist»."
        if part.startswith("-") or part.endswith("-") or "--" in part:
            return False, f"Rango inválido: {part}. Usa formato 1-5 sin espacios."

    return True, ""
