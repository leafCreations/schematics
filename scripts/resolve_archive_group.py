#!/usr/bin/env python3
"""Resolve kanban cards by archiveGroup — status summary for batch archive."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FEATURES_DIR = REPO_ROOT / ".devtool" / "features"

_ACTIVE_STATUSES = frozenset({"todo", "in-progress", "review"})

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.resolve_prior_lessons import _parse_frontmatter  # noqa: E402


@dataclass
class ArchiveGroupCardRow:
    """One kanban card tied to an archive group."""

    path: Path
    rel_path: str
    status: str
    bucket: str
    order: str | None
    epic: str | None


@dataclass
class ArchiveGroupReport:
    """Aggregate archive-group membership across todo / done / archived."""

    group: str
    active: list[ArchiveGroupCardRow]
    done: list[ArchiveGroupCardRow]
    archived: list[ArchiveGroupCardRow]

    @property
    def is_complete(self) -> bool:
        """True when no active cards remain and at least one member exists."""
        total = len(self.active) + len(self.done) + len(self.archived)
        return total > 0 and len(self.active) == 0

    def to_dict(self) -> dict:
        def rows(items: list[ArchiveGroupCardRow]) -> list[dict]:
            return [
                {
                    "path": item.rel_path,
                    "status": item.status,
                    "bucket": item.bucket,
                    "order": item.order,
                    "epic": item.epic,
                }
                for item in items
            ]

        return {
            "group": self.group,
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


def _read_group_row(
    path: Path,
    *,
    bucket: str,
    group: str,
) -> ArchiveGroupCardRow | None:
    if not path.is_file() or path.suffix != ".md":
        return None
    text = path.read_text(encoding="utf-8")
    meta = _parse_frontmatter(text)
    if str(meta.get("archiveGroup") or "") != group:
        return None
    status = str(meta.get("status") or "")
    if bucket == "active" and status not in _ACTIVE_STATUSES:
        return None
    if bucket == "done" and status != "done":
        return None
    if bucket == "archived" and status != "done":
        return None
    order_raw = meta.get("order")
    order = str(order_raw) if order_raw is not None else None
    epic_raw = meta.get("epic")
    epic = str(epic_raw) if epic_raw is not None else None
    try:
        rel = str(path.relative_to(REPO_ROOT))
    except ValueError:
        rel = str(path)
    return ArchiveGroupCardRow(
        path=path,
        rel_path=rel,
        status=status,
        bucket=bucket,
        order=order,
        epic=epic,
    )


def iter_archive_group_cards(
    group: str,
    *,
    features_dir: Path | None = None,
) -> ArchiveGroupReport:
    """Collect cards whose frontmatter ``archiveGroup`` matches (PascalCase)."""
    root = features_dir or DEFAULT_FEATURES_DIR
    active: list[ArchiveGroupCardRow] = []
    done: list[ArchiveGroupCardRow] = []
    archived: list[ArchiveGroupCardRow] = []

    for directory, bucket in _card_dirs(root):
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            row = _read_group_row(path, bucket=bucket, group=group)
            if row is None:
                continue
            if bucket == "active":
                active.append(row)
            elif bucket == "done":
                done.append(row)
            else:
                archived.append(row)

    return ArchiveGroupReport(
        group=group,
        active=active,
        done=done,
        archived=archived,
    )


def format_status_report(report: ArchiveGroupReport) -> str:
    """Human-readable archive-group status summary."""
    lines = [
        f"Archive group: {report.group}",
        f"Complete (no active cards): {'yes' if report.is_complete else 'no'}",
        f"Active: {len(report.active)} | Done: {len(report.done)} | "
        f"Archived: {len(report.archived)}",
    ]
    if report.active:
        lines.append("\nActive cards:")
        for row in report.active:
            order = row.order or "?"
            lines.append(f"  - [{order}] {row.rel_path} ({row.status})")
    if report.done:
        lines.append("\nDone (awaiting batch archive):")
        for row in report.done:
            order = row.order or "?"
            lines.append(f"  - [{order}] {row.rel_path}")
    if report.archived:
        lines.append("\nArchived:")
        for row in report.archived:
            order = row.order or "?"
            lines.append(f"  - [{order}] {row.rel_path}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--group",
        help="Archive group name (PascalCase frontmatter value)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print membership summary for --group",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON (with --status)",
    )
    parser.add_argument(
        "--features-dir",
        type=Path,
        default=DEFAULT_FEATURES_DIR,
        help="Kanban features root (default: .devtool/features)",
    )
    args = parser.parse_args(argv)

    if not args.group:
        parser.error("--group is required")

    if args.status:
        report = iter_archive_group_cards(args.group, features_dir=args.features_dir)
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(format_status_report(report))
        return 0

    parser.error("--status is required with --group")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
