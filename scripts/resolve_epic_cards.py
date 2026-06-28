#!/usr/bin/env python3
"""Resolve kanban cards by epic — status summary and closed-epic registry."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FEATURES_DIR = REPO_ROOT / ".devtool" / "features"
EPICS_CLOSED_PATH = REPO_ROOT / "docs" / "epics-closed.yaml"

_ACTIVE_STATUSES = frozenset({"todo", "in-progress", "review"})

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.resolve_prior_lessons import _parse_frontmatter  # noqa: E402


@dataclass
class EpicCardRow:
    """One kanban card tied to an epic."""

    path: Path
    rel_path: str
    status: str
    order: str | None


@dataclass
class EpicStatusReport:
    """Aggregate epic membership across todo / done / archived."""

    epic: str
    active: list[EpicCardRow]
    done: list[EpicCardRow]
    archived: list[EpicCardRow]
    is_closed_registry: bool

    @property
    def is_complete(self) -> bool:
        return len(self.active) == 0

    def to_dict(self) -> dict:
        def rows(items: list[EpicCardRow]) -> list[dict]:
            return [
                {"path": item.rel_path, "status": item.status, "order": item.order}
                for item in items
            ]

        return {
            "epic": self.epic,
            "closed_registry": self.is_closed_registry,
            "complete": self.is_complete,
            "active_count": len(self.active),
            "done_count": len(self.done),
            "archived_count": len(self.archived),
            "active": rows(self.active),
            "done": rows(self.done),
            "archived": rows(self.archived),
        }


def _card_dirs(features_dir: Path) -> list[tuple[Path, str]]:
    return [
        (features_dir, "active"),
        (features_dir / "done", "done"),
        (features_dir / "archived", "archived"),
    ]


def _read_card_row(path: Path, *, bucket: str, features_dir: Path) -> EpicCardRow | None:
    if not path.is_file() or path.suffix != ".md":
        return None
    text = path.read_text(encoding="utf-8")
    meta = _parse_frontmatter(text)
    status = str(meta.get("status") or "")
    if bucket == "active" and status not in _ACTIVE_STATUSES:
        return None
    if bucket == "done" and status != "done":
        return None
    if bucket == "archived" and status != "done":
        return None
    order_raw = meta.get("order")
    order = str(order_raw) if order_raw is not None else None
    try:
        rel = str(path.relative_to(REPO_ROOT))
    except ValueError:
        rel = str(path)
    return EpicCardRow(path=path, rel_path=rel, status=status, order=order)


def iter_epic_cards(
    epic: str,
    *,
    features_dir: Path | None = None,
) -> EpicStatusReport:
    """Collect cards whose frontmatter ``epic`` matches (case-sensitive PascalCase)."""
    root = features_dir or DEFAULT_FEATURES_DIR
    active: list[EpicCardRow] = []
    done: list[EpicCardRow] = []
    archived: list[EpicCardRow] = []

    for directory, bucket in _card_dirs(root):
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            meta = _parse_frontmatter(text)
            if str(meta.get("epic") or "") != epic:
                continue
            row = _read_card_row(path, bucket=bucket, features_dir=root)
            if row is None:
                continue
            if bucket == "active":
                active.append(row)
            elif bucket == "done":
                done.append(row)
            else:
                archived.append(row)

    return EpicStatusReport(
        epic=epic,
        active=active,
        done=done,
        archived=archived,
        is_closed_registry=is_epic_closed(epic),
    )


def load_closed_epics(path: Path | None = None) -> list[dict]:
    """Return closed epic entries from ``docs/epics-closed.yaml``."""
    registry = path or EPICS_CLOSED_PATH
    if not registry.is_file():
        return []
    data = yaml.safe_load(registry.read_text(encoding="utf-8")) or {}
    closed = data.get("closed")
    if not isinstance(closed, list):
        return []
    return [entry for entry in closed if isinstance(entry, dict)]


def is_epic_closed(epic: str, *, registry_path: Path | None = None) -> bool:
    """True when ``epic`` is listed in the closed registry."""
    return any(str(entry.get("name") or "") == epic for entry in load_closed_epics(registry_path))


def validate_new_epic_name(epic: str, *, registry_path: Path | None = None) -> str | None:
    """Return error message when ``epic`` is closed; else None."""
    if is_epic_closed(epic, registry_path=registry_path):
        return (
            f"Epic {epic!r} is closed — use a new PascalCase epic name (see docs/epics-closed.yaml)"
        )
    return None


def append_closed_epic(
    epic: str,
    *,
    closed_date: str,
    anchor: str,
    follow_up: str | None = None,
    registry_path: Path | None = None,
) -> None:
    """Append ``epic`` to the closed registry (idempotent on name)."""
    path = registry_path or EPICS_CLOSED_PATH
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else {}
    if not isinstance(data, dict):
        data = {}
    closed = data.get("closed")
    if not isinstance(closed, list):
        closed = []
    if any(str(entry.get("name") or "") == epic for entry in closed if isinstance(entry, dict)):
        return
    closed.append(
        {
            "name": epic,
            "closed": closed_date,
            "anchor": anchor,
            "follow_up": follow_up,
        }
    )
    data["closed"] = closed
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def format_status_report(report: EpicStatusReport) -> str:
    """Human-readable epic status summary."""
    lines = [
        f"Epic: {report.epic}",
        f"Closed registry: {'yes' if report.is_closed_registry else 'no'}",
        f"Complete (no active cards): {'yes' if report.is_complete else 'no'}",
        f"Active: {len(report.active)} | Done: {len(report.done)} | "
        f"Archived: {len(report.archived)}",
    ]
    if report.active:
        lines.append("\nActive cards:")
        for row in report.active:
            order = row.order or "?"
            lines.append(f"  - [{order}] {row.rel_path} ({row.status})")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epic", help="Epic name (PascalCase frontmatter value)")
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print membership summary for --epic",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON (with --status or --list-closed)",
    )
    parser.add_argument(
        "--list-closed",
        action="store_true",
        help="List closed epics from docs/epics-closed.yaml",
    )
    parser.add_argument(
        "--validate-new",
        metavar="EPIC",
        help="Exit 1 when EPIC is in the closed registry (pre-spawn gate)",
    )
    parser.add_argument(
        "--features-dir",
        type=Path,
        default=DEFAULT_FEATURES_DIR,
        help="Kanban features root (default: .devtool/features)",
    )
    args = parser.parse_args(argv)

    if args.validate_new:
        error = validate_new_epic_name(args.validate_new)
        if error:
            print(error, file=sys.stderr)
            return 1
        return 0

    if args.list_closed:
        closed = load_closed_epics()
        if args.json:
            print(json.dumps({"closed": closed}, indent=2))
        elif closed:
            for entry in closed:
                name = entry.get("name", "?")
                closed_date = entry.get("closed", "?")
                print(f"{name} (closed {closed_date})")
        else:
            print("(no closed epics)")
        return 0

    if not args.epic:
        parser.error("--epic is required unless using --list-closed or --validate-new")

    if args.status:
        report = iter_epic_cards(args.epic, features_dir=args.features_dir)
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(format_status_report(report))
        return 0

    parser.error("--status is required with --epic")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
