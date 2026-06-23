#!/usr/bin/env python3
"""Remove unused folders from a pruned Minecraft client resource extract."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.minecraft_asset_manifest import (
    KEEP_DIR_PREFIXES,
    KEEP_FILES,
    apply_prune,
    iter_default_prune_targets,
    plan_prune,
)
from helpers.paths import ASSETS_ROOT


def _format_bytes(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    if size >= 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size} B"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prune a Minecraft client resource extract to the paths used by "
            "structure_scripts (rendering, catalog, sprite baker)."
        ),
    )
    parser.add_argument(
        "--assets-dir",
        type=Path,
        action="append",
        dest="assets_dirs",
        help="Assets root to prune (repeatable). Default: all assets/minecraft_* dirs.",
    )
    parser.add_argument(
        "--assets-root",
        type=Path,
        default=ASSETS_ROOT,
        help=f"Parent folder scanned by --all-versioned (default: {ASSETS_ROOT})",
    )
    parser.add_argument(
        "--all-versioned",
        action="store_true",
        help="Prune every assets/minecraft_* directory under --assets-root.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report files that would be removed without deleting anything.",
    )
    parser.add_argument(
        "--no-preserve-generated",
        action="store_true",
        help="Also remove assets/minecraft/generated/ bake cache if present.",
    )
    parser.add_argument(
        "--list-manifest",
        action="store_true",
        help="Print the keep allowlist and exit.",
    )
    return parser.parse_args()


def _resolve_targets(args: argparse.Namespace) -> list[Path]:
    if args.assets_dirs:
        return [path.resolve() for path in args.assets_dirs]

    if args.all_versioned or not args.assets_dirs:
        targets = list(iter_default_prune_targets(args.assets_root.resolve()))
        if targets:
            return targets

    default = (args.assets_root / "minecraft").resolve()
    if default.is_dir():
        return [default]

    raise SystemExit("No assets directory found. Pass --assets-dir or create assets/minecraft_*.")


def _print_manifest() -> None:
    print("Kept directory prefixes:")
    for prefix in KEEP_DIR_PREFIXES:
        print(f"  {prefix}/")
    print("Kept files:")
    for path in sorted(KEEP_FILES):
        print(f"  {path}")


def _report_plan(plan, *, dry_run: bool) -> None:
    action = "Would remove" if dry_run else "Removed"
    print(f"{action} {plan.remove_count} files ({_format_bytes(plan.bytes_removed)})")
    print(f"Keeping {plan.keep_count} files under {plan.assets_root}")


def main() -> int:
    args = _parse_args()

    if args.list_manifest:
        _print_manifest()
        return 0

    preserve_generated = not args.no_preserve_generated
    exit_code = 0

    for assets_dir in _resolve_targets(args):
        print(f"Pruning {assets_dir}...")
        plan = plan_prune(assets_dir, preserve_generated=preserve_generated)
        _report_plan(plan, dry_run=args.dry_run)

        if not args.dry_run:
            apply_prune(plan)

        print()

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
