#!/bin/zsh
set -euo pipefail

ROOT_DIR="${0:A:h}"
cd "$ROOT_DIR"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

if [[ ! -x .venv/bin/python ]]; then
  "$ROOT_DIR/setup_macos.command"
fi

exec .venv/bin/python main.py
