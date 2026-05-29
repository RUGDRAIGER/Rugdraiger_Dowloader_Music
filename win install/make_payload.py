"""Empaqueta la carpeta build en payload.zip para el instalador."""

from __future__ import annotations

import zipfile
from pathlib import Path

win_install = Path(__file__).resolve().parent
source = win_install / "build" / "Rugdraiger_Dowloader_Music"
payload = win_install / "payload.zip"

if not source.exists():
    raise SystemExit(f"Falta carpeta compilada: {source}")

if payload.exists():
    payload.unlink()

with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as zf:
    for path in source.rglob("*"):
        if path.is_file():
            arcname = path.relative_to(source)
            zf.write(path, arcname)

size_mb = payload.stat().st_size / 1048576
print(f"Payload creado: {payload} ({size_mb:.1f} MB)")
