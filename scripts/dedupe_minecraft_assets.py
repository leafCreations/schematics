#!/usr/bin/env python3
"""Deduplicate pruned Minecraft extracts into base + version overlays."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.minecraft_asset_dedupe import build_version_overlays, materialize_version
from helpers.minecraft_asset_manifest import discover_versioned_asset_roots
from helpers.paths import (
    ASSETS_ROOT,
    DEFAULT_MINECRAFT_VERSION,
    MINECRAFT_ASSETS_FOLDER,
    VERSIONS_ASSETS_FOLDER,
    minecraft_version_dir_name,
)


def _format_bytes(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    if size >= 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size} B"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build assets/versions/base plus per-version overlays from pruned "
            "minecraft_* extracts, then materialize a merged active tree."
        ),
    )
    parser.add_argument(
        "--assets-root",
        type=Path,
        default=ASSETS_ROOT,
        help=f"Assets parent directory (default: {ASSETS_ROOT})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=VERSIONS_ASSETS_FOLDER,
        help=f"Output root for base + overlays (default: {VERSIONS_ASSETS_FOLDER})",
    )
    parser.add_argument(
        "--source",
        action="append",
        nargs=2,
        metavar=("VERSION", "PATH"),
        dest="sources",
        help="Explicit version label and source directory (repeatable).",
    )
    parser.add_argument(
        "--materialize",
        type=str,
        default=DEFAULT_MINECRAFT_VERSION,
        help=(
            "Materialize this version to assets/minecraft using hardlinks "
            f"(default: {DEFAULT_MINECRAFT_VERSION}). Use 'none' to skip."
        ),
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove existing output/materialized trees before writing.",
    )
    return parser.parse_args()


def _default_sources(assets_root: Path) -> dict[str, Path]:
    sources: dict[str, Path] = {}
    for path in discover_versioned_asset_roots(assets_root):
        name = path.name.removeprefix("minecraft_")
        version = name.replace("_", ".")
        sources[version] = path
    return sources


def main() -> int:
    args = _parse_args()
    assets_root = args.assets_root.resolve()
    output_root = args.output.resolve()

    if args.sources:
        sources = {version: Path(path).resolve() for version, path in args.sources}
    else:
        sources = _default_sources(assets_root)

    if len(sources) < 2:
        raise SystemExit("Need at least two versioned source directories to dedupe.")

    print("Sources:")
    for version, path in sorted(sources.items()):
        print(f"  {version}: {path}")

    stats = build_version_overlays(sources, output_root, clean_output=args.clean)
    print(
        f"Wrote {stats.base_files} shared files to {output_root / 'base'} "
        f"({_format_bytes(stats.bytes_in_base)})"
    )
    for version, count in sorted(stats.overlay_files.items()):
        print(f"  overlay {version}: {count} files")

    print(f"Overlay total: {_format_bytes(stats.bytes_in_overlays)}")

    if args.materialize != "none":
        version_dir = minecraft_version_dir_name(args.materialize)
        linked = materialize_version(
            output_root,
            version_dir,
            MINECRAFT_ASSETS_FOLDER,
            clean_target=args.clean,
        )
        print(f"Materialized {args.materialize} to {MINECRAFT_ASSETS_FOLDER} ({linked} files)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
