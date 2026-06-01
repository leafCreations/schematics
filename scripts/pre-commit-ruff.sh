#!/usr/bin/env bash
# Pre-commit hook: fix staged Python files with Ruff and re-stage them so the
# commit succeeds on the first attempt instead of failing after auto-fixes.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/ruff" ]]; then
  RUFF="$ROOT/.venv/bin/ruff"
elif command -v ruff >/dev/null 2>&1; then
  RUFF=ruff
else
  echo "ruff not found. Run: pip install -e \".[dev]\" in the project venv." >&2
  exit 1
fi

mapfile -t STAGED_PY < <(git diff --cached --name-only --diff-filter=ACM -- '*.py' '*.pyi')

if ((${#STAGED_PY[@]} == 0)); then
  exit 0
fi

"$RUFF" check --fix "${STAGED_PY[@]}"
"$RUFF" format "${STAGED_PY[@]}"

git add -- "${STAGED_PY[@]}"
