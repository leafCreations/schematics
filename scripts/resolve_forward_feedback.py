#!/usr/bin/env python3
"""Query ranked forward-feedback questions from docs/forward-feedback-index.yaml.

Filter by gc5 category and status; print top-N within category by risk, scope, importance.
Link spawned cards or set resolution status via CLI (ff2).

**Feedback spawn path (fcp2):** after parent Card Done spawns a ``feedback`` todo and index rebuild,
link the row to the child card::

  python3 scripts/resolve_forward_feedback.py --link ff-* --card .devtool/features/feedback-….md

When the user closes the ``feedback`` card, set ``answered`` via ``--id`` / ``--set-status``.
Signature: ``forward-feedback-resolution-tracking``, ``card-done-feedback-spawn``.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.forward_feedback_index_lib import (
    DEFAULT_INDEX_PATH,
    DEFAULT_STALE_DAYS,
    VALID_FF_STATUSES,
    aggregate_open_stats,
    find_item,
    find_stale_high_risk_open,
    format_open_report_lines,
    load_index,
    normalize_card_path,
    save_index,
)
from scripts.forward_feedback_index_lib import (
    REPO_ROOT as FF_REPO_ROOT,
)
from scripts.lessons_coverage_lib import (
    ForwardFeedbackItem,
    forward_feedback_rank_key,
    normalize_forward_feedback_category,
)

INDEX_PATH = DEFAULT_INDEX_PATH


def _record_to_item(record: dict[str, Any]) -> ForwardFeedbackItem:
    return ForwardFeedbackItem(
        category=str(record.get("category") or ""),
        question=str(record.get("question") or ""),
        risk_level=record.get("risk_level"),
        impact_scope=record.get("impact_scope"),
        importance=record.get("importance"),
        references=record.get("references"),
        mitigation=record.get("mitigation"),
        detail=record.get("detail"),
        priority=record.get("priority"),
        seq=int(record.get("seq") or 0),
    )


def filter_items(
    records: list[dict[str, Any]],
    *,
    category: str | None = None,
    status: str | None = "open",
    include_spawned: bool = False,
    include_duplicates: bool = False,
) -> list[dict[str, Any]]:
    """Filter index rows by category and status."""
    filtered: list[dict[str, Any]] = []
    for record in records:
        row_status = str(record.get("status") or "open")
        if not include_duplicates and (row_status == "duplicate" or record.get("duplicate_of")):
            continue
        if status and row_status != status and not (include_spawned and row_status == "spawned"):
            continue
        if category and record.get("category") != category:
            continue
        filtered.append(record)
    return filtered


def rank_items(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Within-category rank: risk desc, impact scope, importance, age tie-break."""
    return sorted(
        records,
        key=lambda row: forward_feedback_rank_key(
            _record_to_item(row),
            completed_at=row.get("completed_at"),
        ),
    )


def format_item(record: dict[str, Any], *, index: int | None = None) -> str:
    prefix = f"{index}. " if index is not None else ""
    parts = [
        f"{prefix}[{record.get('id')}] {record.get('category')}: {record.get('question')}",
    ]
    meta: list[str] = []
    if record.get("status"):
        meta.append(f"status={record['status']}")
    if record.get("risk_level") is not None:
        meta.append(f"risk={record['risk_level']}")
    if record.get("impact_scope"):
        meta.append(f"scope={record['impact_scope']}")
    if record.get("importance"):
        meta.append(f"importance={record['importance']}")
    if record.get("source_card"):
        meta.append(f"card={record['source_card']}")
    if record.get("spawned"):
        meta.append(f"spawned={len(record['spawned'])}")
    if meta:
        parts.append(f"  ({', '.join(meta)})")
    return "\n".join(parts)


def run_open_report(
    *,
    index_path: Path = INDEX_PATH,
    stale_days: int | None = None,
) -> list[str]:
    """Aggregate open backlog stats; optional stale advisory section (ff3)."""
    payload = load_index(index_path)
    records = payload.get("items") or []
    if not isinstance(records, list):
        records = []
    stats = aggregate_open_stats(records)
    stale_items = None
    if stale_days is not None:
        stale_items = find_stale_high_risk_open(records, stale_days=stale_days)
    return format_open_report_lines(
        stats,
        stale_items=stale_items,
        stale_days=stale_days,
    )


def resolve_forward_feedback(
    *,
    category: str | None = None,
    status: str = "open",
    top: int | None = None,
    include_spawned: bool = False,
    include_duplicates: bool = False,
    index_path: Path = INDEX_PATH,
) -> list[dict[str, Any]]:
    payload = load_index(index_path)
    records = payload.get("items") or []
    if not isinstance(records, list):
        records = []
    filtered = filter_items(
        records,
        category=category,
        status=status,
        include_spawned=include_spawned,
        include_duplicates=include_duplicates,
    )
    ranked = rank_items(filtered)
    if top is not None and top >= 0:
        return ranked[:top]
    return ranked


def link_ff_item(
    item_id: str,
    card_path: str | Path,
    *,
    index_path: Path = INDEX_PATH,
    repo_root: Path = FF_REPO_ROOT,
) -> dict[str, Any]:
    """Append spawned card path and set status=spawned (ff2)."""
    payload = load_index(index_path)
    records = payload.get("items") or []
    if not isinstance(records, list):
        raise KeyError(item_id)
    record = find_item(records, item_id)
    if record is None:
        raise KeyError(item_id)
    rel_card = normalize_card_path(card_path, repo_root=repo_root)
    spawned = list(record.get("spawned") or [])
    if rel_card not in spawned:
        spawned.append(rel_card)
    record["spawned"] = spawned
    record["status"] = "spawned"
    if not record.get("resolution"):
        record["resolution"] = f"spawned:{rel_card}"
    save_index(payload, index_path)
    return record


def set_ff_status(
    item_id: str,
    status: str,
    *,
    resolution: str | None = None,
    answered_at: str | None = None,
    index_path: Path = INDEX_PATH,
) -> dict[str, Any]:
    """Update resolution status fields on one index row."""
    if status not in VALID_FF_STATUSES:
        raise ValueError(f"invalid status: {status}")
    payload = load_index(index_path)
    records = payload.get("items") or []
    if not isinstance(records, list):
        raise KeyError(item_id)
    record = find_item(records, item_id)
    if record is None:
        raise KeyError(item_id)
    record["status"] = status
    if resolution is not None:
        record["resolution"] = resolution
    if answered_at is not None:
        record["answered_at"] = answered_at
    elif status == "answered" and not record.get("answered_at"):
        record["answered_at"] = datetime.now(UTC).replace(microsecond=0).date().isoformat()
    save_index(payload, index_path)
    return record


def _mutation_requested(args: argparse.Namespace) -> bool:
    return bool(args.link or args.set_status or args.id and (args.resolution or args.answered_at))


def _run_mutation(args: argparse.Namespace) -> int:
    item_id = args.link or args.id
    if not item_id:
        print("--id or --link required for mutations", file=sys.stderr)
        return 2
    try:
        if args.link:
            if not args.card:
                print("--card required with --link", file=sys.stderr)
                return 2
            record = link_ff_item(item_id, args.card, index_path=args.index)
        else:
            status = args.set_status or "open"
            if args.set_status is None and not (args.resolution or args.answered_at):
                print("--set-status required with --id", file=sys.stderr)
                return 2
            record = set_ff_status(
                item_id,
                status,
                resolution=args.resolution,
                answered_at=args.answered_at,
                index_path=args.index,
            )
    except KeyError:
        print(f"unknown ff id: {item_id}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(format_item(record))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--category",
        help="gc5 category filter (aliases: rules→Rule, codebase→Codebase, …)",
    )
    parser.add_argument(
        "--status",
        default="open",
        help="item status filter for queries (default: open)",
    )
    parser.add_argument(
        "--top",
        type=int,
        help="return top N ranked items within filters",
    )
    parser.add_argument(
        "--include-spawned",
        action="store_true",
        help="include status=spawned when filtering --status open",
    )
    parser.add_argument(
        "--include-duplicates",
        action="store_true",
        help="include duplicate_of rows and status=duplicate (default: exclude)",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=INDEX_PATH,
        help="index yaml path",
    )
    parser.add_argument(
        "--link",
        metavar="FF_ID",
        help="link spawned kanban card to ff-* item (requires --card)",
    )
    parser.add_argument(
        "--card",
        help="repo-relative or absolute kanban card path for --link",
    )
    parser.add_argument(
        "--id",
        metavar="FF_ID",
        help="ff-* item id for --set-status or resolution edits",
    )
    parser.add_argument(
        "--set-status",
        choices=sorted(VALID_FF_STATUSES),
        help="set resolution status on --id",
    )
    parser.add_argument(
        "--resolution",
        help="resolution note (with --id or implied by --link)",
    )
    parser.add_argument(
        "--answered-at",
        help="ISO date when marking answered (default: today UTC)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="print open counts by category and risk band (ff3 metrics)",
    )
    parser.add_argument(
        "--stale-days",
        type=int,
        metavar="N",
        help=(
            "with --report or parity --forward-feedback-stale: flag high-risk open "
            f"items with no spawn after N days (default: {DEFAULT_STALE_DAYS})"
        ),
    )
    args = parser.parse_args(argv)

    if _mutation_requested(args):
        return _run_mutation(args)

    if args.report:
        stale_days = args.stale_days if args.stale_days is not None else None
        if args.stale_days is not None and args.stale_days < 0:
            print("--stale-days must be >= 0", file=sys.stderr)
            return 2
        for line in run_open_report(index_path=args.index, stale_days=stale_days):
            print(line)
        return 0

    category = None
    if args.category:
        category = normalize_forward_feedback_category(args.category)
        if category is None:
            print(f"unknown category: {args.category}", file=sys.stderr)
            return 2

    status = args.status if args.status else None
    results = resolve_forward_feedback(
        category=category,
        status=status or "open",
        top=args.top,
        include_spawned=args.include_spawned,
        include_duplicates=args.include_duplicates,
        index_path=args.index,
    )

    if not results:
        print("no matching forward-feedback items")
        return 0

    for index, record in enumerate(results, start=1):
        print(format_item(record, index=index if args.top else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
