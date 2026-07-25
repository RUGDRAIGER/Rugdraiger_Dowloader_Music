"""Ayuda y utilidades para cookies de navegador con yt-dlp."""

from __future__ import annotations

CHROMIUM_BROWSERS = frozenset(
    {"chrome", "chromium", "edge", "brave", "opera", "vivaldi", "whale"}
)

CHROME_COOKIE_ERROR_HELP = (
    "No se pudieron leer las cookies de Chrome/Edge.\n\n"
    "En Windows, estos navegadores bloquean el acceso a cookies mientras estan abiertos.\n\n"
    "Soluciones (elige una):\n"
    "1. RECOMENDADO: usa Firefox\n"
    "   - Instala Firefox, inicia sesion en YouTube Music\n"
    "   - En la app elige navegador: firefox\n\n"
    "2. Cierra Chrome/Edge por completo y vuelve a intentar\n"
    "   (incluido icono en bandeja del sistema)\n\n"
    "3. Usa un archivo cookies.txt\n"
    "   - Extension: Get cookies.txt LOCALLY (Chrome/Firefox)\n"
    "   - En la app: boton «Archivo cookies...» y selecciona el .txt\n\n"
    "Mas info: https://github.com/yt-dlp/yt-dlp/issues/7271"
)


def is_chromium_browser(browser: str) -> bool:
    name = browser.lower().split(":")[0].split("+")[0]
    return name in CHROMIUM_BROWSERS


def cookie_error_message(raw: str) -> str:
    lower = raw.lower()
    if "could not copy chrome cookie" in lower or "cookie database" in lower:
        return CHROME_COOKIE_ERROR_HELP
    if "cookies-from-browser" in lower and "permission" in lower:
        return CHROME_COOKIE_ERROR_HELP
    return raw
