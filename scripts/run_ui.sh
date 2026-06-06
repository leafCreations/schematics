#!/usr/bin/env bash
set -euo pipefail

STRUCTURE="${1:-residence}"
STAGE="${2:-1}"

python -m ui --structure "$STRUCTURE" --stage "$STAGE"