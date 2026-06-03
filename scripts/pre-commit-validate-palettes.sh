#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
else
  echo "python not found. Run: pip install -e \".[dev]\" in the project venv." >&2
  exit 1
fi

exec "$PYTHON" -c "from registries.validate import validate_palettes; validate_palettes()"
