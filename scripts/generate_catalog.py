#!/usr/bin/env python3
"""Generate registries/generated/catalog.json from Minecraft assets."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.block_catalog import (
    CATALOG_PATH,
    generate_block_catalog,
    save_block_catalog,
)
from helpers.paths import ASSET_FOLDER


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate block catalog from assets/blockstates and assets/lang/en_us.json",
    )
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=ASSET_FOLDER,
        help="Assets root containing blockstates/ and lang/ (default: assets/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=CATALOG_PATH,
        help=f"Output catalog path (default: {CATALOG_PATH.relative_to(PROJECT_ROOT)})",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    catalog = generate_block_catalog(assets_dir=args.assets_dir)
    output_path = save_block_catalog(catalog, path=args.output)
    print(f"Wrote {len(catalog)} entries to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
