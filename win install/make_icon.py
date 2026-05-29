"""Genera app-icon.ico desde PNG para el instalador Windows."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

assets = Path(__file__).resolve().parent / "assets"
png = assets / "app-icon.png"
ico = assets / "app-icon.ico"

if not png.exists():
    print(f"Falta {png}")
    sys.exit(1)

img = Image.open(png).convert("RGBA")
img.save(
    ico,
    format="ICO",
    sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
print(f"Icono creado: {ico}")
