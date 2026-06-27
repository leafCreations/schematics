#!/usr/bin/env bash
# Optional pre-commit hook: lessons coverage audit when local kanban done/ exists.
# Not enabled in .pre-commit-config.yaml by default — add manually if desired.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FEATURES="${ROOT}/.devtool/features"
DONE="${FEATURES}/done"
ARCHIVED="${FEATURES}/archived"

if [[ ! -d "${DONE}" && ! -d "${ARCHIVED}" ]]; then
  echo "lessons-coverage: skip (.devtool/features/done/ and archived/ absent)"
  exit 0
fi

exec python3 "${ROOT}/scripts/check_lessons_coverage.py" --json
