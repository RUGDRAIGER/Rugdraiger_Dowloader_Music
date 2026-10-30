"""Ayuda y utilidades para cookies de navegador con yt-dlp."""

from __future__ import annotations

import sys

CHROMIUM_BROWSERS = frozenset(
    {"chrome", "chromium", "edge", "brave", "opera", "vivaldi", "whale"}
)

def _chrome_cookie_error_help() -> str:
    if sys.platform == "darwin":
        platform_hint = (
            "En macOS, permite el acceso al Llavero cuando el sistema lo solicite. "
            "Si Chrome mantiene bloqueada su base de cookies, ciérralo por completo con ⌘Q."
        )
    else:
        platform_hint = (
            "Chrome/Edge pueden bloquear su base de cookies mientras siguen abiertos. "
            "Ciérralos por completo, incluida la bandeja del sistema."
        )
    return (
        "No se pudieron leer las cookies del navegador.\n\n"
        f"{platform_hint}\n\n"
        "Alternativas:\n"
        "1. Usa Firefox con tu sesión de YouTube Music iniciada.\n"
        "2. Exporta un cookies.txt en formato Netscape y selecciónalo en la app.\n"
        "3. Comprueba que el perfil elegido contiene la sesión correcta."
    )


def is_chromium_browser(browser: str) -> bool:
    name = browser.lower().split(":")[0].split("+")[0]
    return name in CHROMIUM_BROWSERS


def cookie_error_message(raw: str) -> str:
    lower = raw.lower()
    if "could not copy chrome cookie" in lower or "cookie database" in lower:
        return _chrome_cookie_error_help()
    if "cookies-from-browser" in lower and "permission" in lower:
        return _chrome_cookie_error_help()
    if "keyring" in lower or "keychain" in lower:
        return _chrome_cookie_error_help()
    return raw
