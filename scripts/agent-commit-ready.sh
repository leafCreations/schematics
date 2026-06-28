#!/usr/bin/env bash
# Agent gate before Review or git commit: ruff → palettes → pytest (pre-commit order).
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

echo "agent-commit-ready: ruff (staged Python)"
"$ROOT/scripts/pre-commit-ruff.sh"

echo "agent-commit-ready: validate-palettes"
"$ROOT/scripts/pre-commit-validate-palettes.sh"

echo "agent-commit-ready: pytest (staged paths)"
"$ROOT/scripts/pre-commit-pytest.sh"

echo "agent-commit-ready: OK — staged hooks green"
