#!/usr/bin/env bash
# Install worldgen (Amulet) dependencies into the active or project .venv.
#
# Usage:
#   source .venv/bin/activate
#   ./scripts/install_worldgen.sh            # build from source (slow)
#   ./scripts/install_worldgen.sh --reuse    # copy from ~/Documents/github/venv
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  echo "Activate the project venv first: source .venv/bin/activate" >&2
  exit 1
fi

PYTHON="${VIRTUAL_ENV}/bin/python"
PIP="${VIRTUAL_ENV}/bin/pip"
PY_VERSION="$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

if [[ "$PY_VERSION" != "3.11" ]]; then
  echo "Worldgen requires Python 3.11 (this venv is Python ${PY_VERSION})." >&2
  exit 1
fi

reuse_from="${WORLDGEN_SOURCE_VENV:-$HOME/Documents/github/venv}"

if [[ "${1:-}" == "--reuse" ]]; then
  if [[ ! -x "${reuse_from}/bin/python" ]]; then
    echo "Reuse venv not found: ${reuse_from}" >&2
    exit 1
  fi

  src_site="$("$reuse_from/bin/python" -c 'import site; print(site.getsitepackages()[0])')"
  dst_site="$("$PYTHON" -c 'import site; print(site.getsitepackages()[0])')"

  echo "Copying prebuilt Amulet packages from ${reuse_from} ..."

  shopt -s nullglob
  for item in \
    "${src_site}"/amulet* \
    "${src_site}"/mutf8* \
    "${src_site}"/leveldb* \
    "${src_site}"/rocksdb* \
    "${src_site}"/PyMCTranslate* \
    "${src_site}"/pymctranslate*; do
    base="$(basename "$item")"
    rm -rf "${dst_site:?}/${base}"
    cp -a "$item" "${dst_site}/"
  done
  shopt -u nullglob

  "$PIP" install "numpy~=1.17" "lz4~=4.3" "portalocker~=2.4"
  echo "Worldgen packages copied."
  "$PYTHON" -c "import amulet; print('amulet import ok')"
  exit 0
fi

echo "Installing build tools into ${VIRTUAL_ENV} ..."
"$PIP" install "cmake>=4.1" ninja versioneer pybind11 "amulet-pybind11-extensions==1.0.0"

echo "Building amulet-rocksdb==1.0.3 (this compiles RocksDB and can take several minutes) ..."
PATH="${VIRTUAL_ENV}/bin:${PATH}" "$PIP" install --no-build-isolation "amulet-rocksdb==1.0.3"

echo "Installing remaining Amulet runtime packages ..."
"$PIP" install "amulet-core==1.9.40"

iterable_hpp="${VIRTUAL_ENV}/lib/python3.11/site-packages/amulet/pybind11_extensions/iterable.hpp"
if [[ ! -f "$iterable_hpp" ]]; then
  mkdir -p "$(dirname "$iterable_hpp")"
  cat >"$iterable_hpp" <<'EOF'
#pragma once
#include "iterator.hpp"
EOF
fi

"$PYTHON" -c "import amulet; print('amulet import ok')"
