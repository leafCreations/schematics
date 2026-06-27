#!/usr/bin/env bash
# Create a kanban commit-issue card after a pre-commit hook fails.
# Cards are created only during actual git commit (PRE_COMMIT=1), not when agents
# run scripts/pre-commit-pytest.sh manually during implementation.
# Set SKIP_COMMIT_ISSUE_CARD=1 to disable (e.g. CI or scripted retries).
set -euo pipefail

if [[ "${SKIP_COMMIT_ISSUE_CARD:-}" == "1" ]]; then
  exit 0
fi

if [[ "${PRE_COMMIT:-}" != "1" ]]; then
  exit 0
fi

HOOK="${1:?hook name required (ruff|validate-palettes|pytest)}"
LOG="${2:?log file path required}"

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
else
  echo "on_pre_commit_failure: python not found; skipping commit-issue card" >&2
  exit 0
fi

"$PYTHON" "$ROOT/scripts/create_commit_issue_card.py" --hook "$HOOK" --log "$LOG" \
  ${COMMIT_ISSUE_FEATURES_DIR:+--features-dir "$COMMIT_ISSUE_FEATURES_DIR"} || {
  echo "on_pre_commit_failure: could not create commit-issue card (see above)" >&2
  exit 0
}
