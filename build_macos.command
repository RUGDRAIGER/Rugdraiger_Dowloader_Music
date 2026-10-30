#!/bin/zsh
set -euo pipefail

ROOT_DIR="${0:A:h}"
cd "$ROOT_DIR"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

if [[ ! -x .venv/bin/python ]]; then
  "$ROOT_DIR/setup_macos.command"
fi

.venv/bin/python -m pip install --upgrade -r requirements-dev.txt
.venv/bin/python -m PyInstaller --noconfirm --clean macos/RugdraigerDownloader.spec

APP_PATH="$ROOT_DIR/dist/Rugdraiger Downloader.app"
xattr -cr "$APP_PATH"
xattr -dr com.apple.FinderInfo "$APP_PATH" 2>/dev/null || true
xattr -dr 'com.apple.fileprovider.fpfs#P' "$APP_PATH" 2>/dev/null || true
codesign --force --deep --sign - "$APP_PATH"
codesign --verify --deep --verbose=2 "$APP_PATH"

echo
echo "Aplicación creada y firmada localmente:"
echo "$APP_PATH"
