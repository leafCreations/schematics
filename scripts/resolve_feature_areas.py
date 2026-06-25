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
_HANDLER_KEY = "handlers"
_LESSON_SIGNATURE_KEY = "lesson_signatures"
_LESSON_DOCS_KEY = "lesson_docs"
MAX_LESSON_SIGNATURES = 8
MAX_LESSON_DOCS = 5


def load_registry() -> dict:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    return data.get("areas", {})


def resolve_areas(
    labels: list[str],
    *,
    include_related: bool = False,
    handlers_only: bool = False,
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
        if handlers_only:
            for handler in entry.get(_HANDLER_KEY, []) or []:
                if handler not in ordered:
                    ordered.append(handler)
            return
        for key in _PATH_KEYS:
            for path in entry.get(key, []) or []:
                if path not in ordered:
                    ordered.append(path)
        if include_related:
            for related in entry.get("related", []):
                add_label(related)

    for label in labels:
        add_label(label)

    return ordered, unknown


def resolve_lesson_pointers(labels: list[str]) -> tuple[dict[str, list[str]], list[str]]:
    """Merge curated ``lesson_signatures`` / ``lesson_docs`` for area labels."""
    areas = load_registry()
    unknown: list[str] = []
    seen_sig: set[str] = set()
    seen_doc: set[str] = set()
    signatures: list[str] = []
    docs: list[str] = []

    for label in labels:
        entry = areas.get(label)
        if entry is None:
            unknown.append(label)
            continue
        for sig in entry.get(_LESSON_SIGNATURE_KEY, []) or []:
            if sig not in seen_sig:
                seen_sig.add(sig)
                signatures.append(sig)
        for doc in entry.get(_LESSON_DOCS_KEY, []) or []:
            if doc not in seen_doc:
                seen_doc.add(doc)
                docs.append(doc)

    return {"lesson_signatures": signatures, "lesson_docs": docs}, unknown


def format_lesson_pointers(pointers: dict[str, list[str]]) -> str:
    """Human-readable lesson pointer block for card review."""
    lines: list[str] = []
    signatures = pointers.get("lesson_signatures") or []
    docs = pointers.get("lesson_docs") or []
    if signatures:
        lines.append("lesson_signatures:")
        for sig in signatures:
            lines.append(f"  - {sig}")
    if docs:
        if lines:
            lines.append("")
        lines.append("lesson_docs:")
        for doc in docs:
            lines.append(f"  - {doc}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("labels", nargs="*", help="Feature area labels (e.g. 'Render Preview')")
    parser.add_argument(
        "--related",
        action="store_true",
        help="Include paths from related feature areas",
    )
    parser.add_argument(
        "--handlers",
        action="store_true",
        help="Print registry handlers (stable entry points) instead of paths",
    )
    parser.add_argument(
        "--lessons",
        action="store_true",
        help="Print curated lesson_signatures and lesson_docs for labels",
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

    if args.lessons:
        pointers, unknown = resolve_lesson_pointers(args.labels)
        if unknown:
            print("Unknown labels:", ", ".join(unknown), file=sys.stderr)
        if not pointers["lesson_signatures"] and not pointers["lesson_docs"]:
            print("(no lesson pointers for resolved labels)", file=sys.stderr)
        else:
            print(format_lesson_pointers(pointers))
        return 1 if unknown else 0

    paths, unknown = resolve_areas(
        args.labels,
        include_related=args.related,
        handlers_only=args.handlers,
    )
    if unknown:
        print("Unknown labels:", ", ".join(unknown), file=sys.stderr)
    for path in paths:
        print(path)
    return 1 if unknown else 0


if __name__ == "__main__":
    raise SystemExit(main())
