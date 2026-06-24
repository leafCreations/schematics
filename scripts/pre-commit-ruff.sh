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
  LOG="$(mktemp)"
  echo "ruff not found. Run: pip install -e \".[dev]\" in the project venv." | tee "$LOG" >&2
  "$ROOT/scripts/on_pre_commit_failure.sh" ruff "$LOG" || true
  rm -f "$LOG"
  exit 1
fi

mapfile -t STAGED_PY < <(git diff --cached --name-only --diff-filter=ACM -- '*.py' '*.pyi')

if ((${#STAGED_PY[@]} == 0)); then
  exit 0
fi

LOG="$(mktemp)"
trap 'rm -f "$LOG"' EXIT
if ! {
  "$RUFF" check --fix "${STAGED_PY[@]}" && "$RUFF" format "${STAGED_PY[@]}"
} >"$LOG" 2>&1; then
  cat "$LOG"
  "$ROOT/scripts/on_pre_commit_failure.sh" ruff "$LOG" || true
  exit 1
fi

git add -- "${STAGED_PY[@]}"
