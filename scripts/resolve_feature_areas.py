#!/usr/bin/env python3
"""Resolve feature area labels to repo paths (see docs/feature-areas.yaml)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "docs/feature-areas.yaml"

_PATH_KEYS = ("paths", "wiring", "tests")


def load_registry() -> dict:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    return data.get("areas", {})


def resolve_areas(
    labels: list[str],
    *,
    include_related: bool = False,
) -> tuple[list[str], list[str]]:
    areas = load_registry()
    unknown: list[str] = []
    seen: set[str] = set()
    ordered: list[str] = []

    def add_label(label: str) -> None:
        if label in seen:
            return
        seen.add(label)
        entry = areas.get(label)
        if entry is None:
            unknown.append(label)
            return
        for key in _PATH_KEYS:
            for path in entry.get(key, []):
                if path not in ordered:
                    ordered.append(path)
        if include_related:
            for related in entry.get("related", []):
                add_label(related)

    for label in labels:
        add_label(label)

    return ordered, unknown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("labels", nargs="*", help="Feature area labels (e.g. 'Render Preview')")
    parser.add_argument(
        "--related",
        action="store_true",
        help="Include paths from related feature areas",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all registered feature area labels",
    )
    args = parser.parse_args(argv)

    if args.list:
        for label in sorted(load_registry()):
            print(label)
        return 0

    if not args.labels:
        parser.error("labels required unless --list is set")

    paths, unknown = resolve_areas(args.labels, include_related=args.related)
    if unknown:
        print("Unknown labels:", ", ".join(unknown), file=sys.stderr)
    for path in paths:
        print(path)
    return 1 if unknown else 0


if __name__ == "__main__":
    raise SystemExit(main())
