#!/usr/bin/env bash
# Profile pytest suite: total time + slowest tests.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/pytest" ]]; then
  PYTEST="$ROOT/.venv/bin/pytest"
elif [[ -x "$ROOT/venv/bin/pytest" ]]; then
  PYTEST="$ROOT/venv/bin/pytest"
elif command -v pytest >/dev/null 2>&1; then
  PYTEST=pytest
else
  echo "pytest not found" >&2
  exit 1
fi

ARGS=(-q)
if ((${#@})); then
  ARGS=("$@")
fi

echo "=== pytest profile ==="
echo "cwd: $ROOT"
echo "pytest: $PYTEST"
echo

START=$(date +%s.%N)
"$PYTEST" "${ARGS[@]}" --durations=25
END=$(date +%s.%N)

python3 - <<PY
import sys
start, end = float("$START"), float("$END")
print(f"\n=== wall time: {end - start:.2f}s ===")
PY
