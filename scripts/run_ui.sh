#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
else
  echo "run-ui: need .venv/bin/python or python3 on PATH" >&2
  exit 1
fi

STRUCTURE="${1:-residence}"
STAGE="${2:-1}"

exec "$PYTHON" -m ui --structure "$STRUCTURE" --stage "$STAGE"
