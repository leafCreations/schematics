#!/usr/bin/env python3
"""List pytest files pre-commit would run for product paths or a kanban card."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.resolve_prior_lessons import _card_paths, _section_body

_PRODUCT_HEADINGS = ("Product Paths", "Label Paths")
_TARGETED_RE = re.compile(
    r"^pre-commit pytest: (\d+) file\(s\) — (.+)$",
    re.MULTILINE,
)


def extract_product_paths(text: str) -> list[str]:
    """Product (or legacy Label) path bullets from a kanban card body."""
    paths: list[str] = []
    seen: set[str] = set()
    for heading in _PRODUCT_HEADINGS:
        body = _section_body(text, heading)
        if body is None:
            continue
        for path in _card_paths(body):
            if path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def simulate_hook(paths: list[str]) -> tuple[int, str]:
    """Run pre-commit-pytest.sh in list-only mode for ``paths``."""
    env = os.environ.copy()
    env["PRE_COMMIT_PYTEST_LIST_ONLY"] = "1"
    env["PRE_COMMIT_PYTEST_PATHS"] = "\n".join(paths)
    result = subprocess.run(
        ["bash", str(REPO_ROOT / "scripts/pre-commit-pytest.sh")],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout
    if result.stderr:
        output = f"{output}{result.stderr}"
    return result.returncode, output


def parse_targeted_files(output: str) -> list[str]:
    """Extract test file paths from hook stdout (empty when full suite / skipped)."""
    match = _TARGETED_RE.search(output)
    if not match:
        return []
    return match.group(2).split()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Simulate scripts/pre-commit-pytest.sh for Product Paths "
            "(draft card Tests → Files; cross-check before Review)."
        ),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Repo-relative product paths (e.g. helpers/sprite_baker/foo.py)",
    )
    parser.add_argument(
        "--from-card",
        metavar="CARD.md",
        help="Read Product Paths from a kanban card under .devtool/features/",
    )
    parser.add_argument(
        "--files-only",
        action="store_true",
        help="Print one test file per line (targeted runs only)",
    )
    args = parser.parse_args(argv)

    paths = list(args.paths)
    if args.from_card:
        card_path = Path(args.from_card)
        if not card_path.is_absolute():
            card_path = REPO_ROOT / card_path
        if not card_path.is_file():
            print(f"resolve_card_tests: card not found: {card_path}", file=sys.stderr)
            return 1
        paths = extract_product_paths(card_path.read_text(encoding="utf-8"))

    if not paths:
        print(
            "resolve_card_tests: no paths — pass paths or --from-card CARD.md",
            file=sys.stderr,
        )
        return 1

    code, output = simulate_hook(paths)
    if args.files_only:
        for path in parse_targeted_files(output):
            print(path)
    else:
        print(output, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
