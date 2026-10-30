#!/bin/zsh
set -euo pipefail

ROOT_DIR="${0:A:h}"
cd "$ROOT_DIR"

if [[ "$(uname -m)" != "arm64" ]]; then
  echo "Aviso: este instalador está optimizado para Apple Silicon (M1-M4)."
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew no está instalado. Instálalo desde https://brew.sh y vuelve a ejecutar este archivo."
  exit 1
fi

missing_formulae=()
for formula in python@3.13 python-tk@3.13 ffmpeg deno; do
  if ! brew list --versions "$formula" >/dev/null 2>&1; then
    missing_formulae+=("$formula")
  fi
done

if (( ${#missing_formulae[@]} )); then
  echo "Instalando dependencias nativas: ${missing_formulae[*]}"
  brew install "${missing_formulae[@]}"
fi

PYTHON_BIN="$(brew --prefix python@3.13)/bin/python3.13"
"$PYTHON_BIN" -c 'import tkinter; print(f"Tkinter {tkinter.TkVersion}: OK")'

if [[ ! -x .venv/bin/python ]]; then
  "$PYTHON_BIN" -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install --upgrade -r requirements.txt
.venv/bin/python -c 'from app.core.dependencies import ensure_ytdlp; print(f"yt-dlp: {ensure_ytdlp()}")'
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'

echo
echo "Instalación terminada. Abre run_macos.command para iniciar Rugdraiger Downloader."
