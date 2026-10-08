#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  printf 'Virtual environment not found. Running setup...\n'
  "$ROOT_DIR/scripts/setup.sh"
fi

cd "$ROOT_DIR"
exec "$PYTHON" app.py