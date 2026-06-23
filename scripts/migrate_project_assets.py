#!/usr/bin/env python3
"""Move project-owned custom templates and generated sprites out of minecraft_*/."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.migrate_project_assets import (
    apply_project_asset_migration,
    plan_project_asset_migration,
)
from helpers.paths import ASSETS_ROOT, GENERATED_ASSETS_FOLDER, PROJECT_CUSTOM_FOLDER


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Move textures/block/custom and generated/ from versioned Minecraft "
            "extracts into assets/project/."
        ),
    )
    parser.add_argument(
        "--assets-root",
        type=Path,
        default=ASSETS_ROOT,
        help=f"Assets parent directory (default: {ASSETS_ROOT})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report files that would be migrated without copying or deleting.",
    )
    parser.add_argument(
        "--keep-legacy",
        action="store_true",
        help="Copy into assets/project/ but leave legacy folders in place.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    plan = plan_project_asset_migration(args.assets_root.resolve())

    print(f"Custom sources: {len(plan.custom_sources)}")
    print(f"Generated sources: {len(plan.generated_sources)}")
    print(f"Custom files to migrate: {len(plan.custom_files)}")
    print(f"Generated files to migrate: {len(plan.generated_files)}")
    print(f"Target custom folder: {PROJECT_CUSTOM_FOLDER}")
    print(f"Target generated folder: {GENERATED_ASSETS_FOLDER}")

    if args.dry_run:
        return 0

    custom_copied, generated_copied = apply_project_asset_migration(
        plan,
        remove_legacy=not args.keep_legacy,
    )
    print(f"Copied {custom_copied} custom files and {generated_copied} generated files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
