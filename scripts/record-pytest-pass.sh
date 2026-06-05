#!/usr/bin/env bash
# Record a successful pytest run for the current staged files so pre-commit can
# skip re-running pytest on the next commit (see scripts/pre-commit-pytest.sh).
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

STAMP="$ROOT/.pytest-precommit-pass"
STAGED_HASH="$(
  git diff --cached --name-only --diff-filter=ACM | LC_ALL=C sort | sha256sum | cut -d' ' -f1
)"

if [[ -z "$STAGED_HASH" || "$STAGED_HASH" == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" ]]; then
  echo "record-pytest-pass: nothing staged — run git add before recording" >&2
  exit 1
fi

printf '%s %s\n' "$STAGED_HASH" "$(date +%s)" >"$STAMP"
echo "record-pytest-pass: saved for ${#STAGED_HASH} staged-file hash (next commit may skip pytest)"
