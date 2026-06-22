#!/usr/bin/env python3
"""Replace legacy terrain registry tokens with ``minecraft:`` block ids in YAML."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.terrain_tokens import migrate_terrain_token


def _migrate_cell_grid(cells: object) -> tuple[list[list[str]], int]:
    if not isinstance(cells, list):
        return [], 0

    migrated = 0
    rows: list[list[str]] = []

    for row in cells:
        if not isinstance(row, list):
            continue

        new_row: list[str] = []

        for token in row:
            if not isinstance(token, str):
                new_row.append(token)
                continue

            replacement = migrate_terrain_token(token)

            if replacement != token:
                migrated += 1

            new_row.append(replacement)

        rows.append(new_row)

    return rows, migrated


def _migrate_string_list(values: object) -> tuple[list[str], int]:
    if not isinstance(values, list):
        return [], 0

    migrated = 0
    result: list[str] = []

    for value in values:
        if not isinstance(value, str):
            continue

        replacement = migrate_terrain_token(value)

        if replacement != value:
            migrated += 1

        result.append(replacement)

    return result, migrated


def migrate_mapping(data: dict, *, path_prefix: str = "") -> int:
    migrated = 0

    if "cells" in data:
        cells, count = _migrate_cell_grid(data["cells"])

        if count:
            data["cells"] = cells
            migrated += count

    if "site_ground" in data:
        site_ground, count = _migrate_cell_grid(data["site_ground"])

        if count:
            data["site_ground"] = site_ground
            migrated += count

    grid = data.get("grid")

    if isinstance(grid, dict):
        trim_block = grid.get("trim_block")

        if isinstance(trim_block, str):
            replacement = migrate_terrain_token(trim_block)

            if replacement != trim_block:
                grid["trim_block"] = replacement
                migrated += 1

        variety_blocks, count = _migrate_string_list(grid.get("path_variety_blocks"))
        if count:
            grid["path_variety_blocks"] = variety_blocks
            migrated += count

    return migrated


def migrate_yaml_file(path: Path, *, dry_run: bool = False) -> int:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        return 0

    migrated = migrate_mapping(payload)

    if migrated and not dry_run:
        with path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(
                payload,
                handle,
                sort_keys=False,
                allow_unicode=True,
                default_flow_style=False,
            )

    return migrated


def migrate_tree(root: Path, *, dry_run: bool = False) -> tuple[int, int]:
    files_changed = 0
    tokens_migrated = 0

    for path in sorted(root.rglob("*.yaml")):
        count = migrate_yaml_file(path, dry_run=dry_run)

        if count:
            files_changed += 1
            tokens_migrated += count

    return files_changed, tokens_migrated


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Migrate legacy terrain tokens (GRASS, COBBLESTONE#mossy, …) to minecraft: ids."
        ),
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=str(PROJECT_ROOT / "structures"),
        help="Root directory to scan (default: structures/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report changes without writing files",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = Path(args.root).resolve()
    files_changed, tokens_migrated = migrate_tree(root, dry_run=args.dry_run)

    action = "Would migrate" if args.dry_run else "Migrated"
    print(f"{action} {tokens_migrated} token(s) in {files_changed} file(s) under {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
