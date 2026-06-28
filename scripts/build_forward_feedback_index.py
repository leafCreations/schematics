#!/usr/bin/env python3
"""Build docs/forward-feedback-index.yaml from gc5 forward-feedback on closed cards.

Scans ``done/`` and ``archived/`` for ``## Forward-looking feedback`` sections.
Separate SSOT from ``docs/lessons-index.yaml`` — questions, not promoted lessons.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.forward_feedback_index_lib import (
    DEFAULT_INDEX_PATH as INDEX_PATH,
)
from scripts.forward_feedback_index_lib import (
    apply_duplicate_status,
    merge_resolution_overlays,
    render_index_yaml,
)
from scripts.lessons_coverage_lib import (
    ForwardFeedbackItem,
    iter_labeled_lesson_cards,
    parse_forward_feedback_items,
)
from scripts.resolve_prior_lessons import REPO_ROOT as RPL_REPO_ROOT


def question_fingerprint(question: str) -> str:
    """Stable 8-char fingerprint for exact question text (strip whitespace)."""
    return hashlib.sha256(question.strip().encode()).hexdigest()[:8]


def make_ff_uid(card_rel: str, item: ForwardFeedbackItem) -> str:
    """Stable ff-* id from source card, category, seq, and question fingerprint."""
    stem = Path(card_rel).stem
    cat_slug = item.category.lower().replace(" ", "-")
    fingerprint = question_fingerprint(item.question)
    return f"ff-{stem}-{cat_slug}-{item.seq:02d}-{fingerprint}"


def apply_duplicate_of(
    items: list[dict[str, Any]],
) -> list[str]:
    """Mark later items sharing a question fingerprint with duplicate_of; return warnings."""
    canonical_by_fp: dict[str, str] = {}
    warnings: list[str] = []
    for record in items:
        fp = question_fingerprint(str(record["question"]))
        uid = str(record["id"])
        prior = canonical_by_fp.get(fp)
        if prior is not None:
            record["duplicate_of"] = prior
            warnings.append(
                f"forward-feedback dedup: {uid} duplicate_of {prior} (fingerprint {fp})"
            )
        else:
            canonical_by_fp[fp] = uid
    return warnings


def _item_to_record(
    item: ForwardFeedbackItem,
    *,
    uid: str,
    source_card: str,
    completed_at: str | None,
    status: str = "open",
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "id": uid,
        "source_card": source_card,
        "category": item.category,
        "question": item.question,
        "status": status,
        "seq": item.seq,
    }
    if item.risk_level is not None:
        record["risk_level"] = item.risk_level
    if item.impact_scope:
        record["impact_scope"] = item.impact_scope
    if item.importance:
        record["importance"] = item.importance
    if item.references:
        record["references"] = item.references
    if item.mitigation:
        record["mitigation"] = item.mitigation
    if item.detail:
        record["detail"] = item.detail
    if item.priority:
        record["priority"] = item.priority
    if completed_at:
        record["completed_at"] = completed_at
    return record


def build_index(
    *,
    repo_root: Path = REPO_ROOT,
) -> tuple[dict[str, Any], list[str]]:
    """Return index payload and advisory dedup warnings from closed cards."""
    features_root = repo_root / ".devtool" / "features"
    empty_payload = {
        "version": 1,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "items": [],
    }
    if not features_root.is_dir():
        return empty_payload, []

    items: list[dict[str, Any]] = []
    for card_path, text, meta in iter_labeled_lesson_cards(features_dir=features_root):
        ff_items = parse_forward_feedback_items(text)
        if not ff_items:
            continue
        rel_card = card_path.relative_to(repo_root).as_posix()
        completed_at = str(meta.get("completedAt") or "")[:10] or None
        for item in ff_items:
            uid = make_ff_uid(rel_card, item)
            items.append(
                _item_to_record(
                    item,
                    uid=uid,
                    source_card=rel_card,
                    completed_at=completed_at,
                )
            )

    dedup_warnings = apply_duplicate_of(items)
    overlay_path = repo_root / "docs" / "forward-feedback-index.yaml"
    merge_resolution_overlays(items, index_path=overlay_path)
    for record in items:
        apply_duplicate_status(record)
    items.sort(key=lambda row: (row["id"], row["source_card"]))
    payload = {
        "version": 1,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "items": items,
    }
    return payload, dedup_warnings


def write_index(
    payload: dict[str, Any],
    *,
    output_path: Path = INDEX_PATH,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_index_yaml(payload), encoding="utf-8")


def index_is_current(
    payload: dict[str, Any],
    *,
    output_path: Path = INDEX_PATH,
) -> bool:
    if not output_path.is_file():
        return False
    expected = render_index_yaml(payload)
    actual = output_path.read_text(encoding="utf-8")
    return actual == expected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 when committed index is stale",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print YAML to stdout instead of writing",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=INDEX_PATH,
        help=f"output path (default: {INDEX_PATH.relative_to(REPO_ROOT)})",
    )
    args = parser.parse_args(argv)

    payload, dedup_warnings = build_index(repo_root=RPL_REPO_ROOT)
    for line in dedup_warnings:
        print(line, file=sys.stderr)
    if args.dry_run:
        print(render_index_yaml(payload), end="")
        return 0
    if args.check:
        if index_is_current(payload, output_path=args.output):
            return 0
        print(f"stale: regenerate {args.output}", file=sys.stderr)
        return 1
    write_index(payload, output_path=args.output)
    item_count = len(payload.get("items") or [])
    print(f"wrote {item_count} items to {args.output}")
    if dedup_warnings:
        print(
            f"forward-feedback dedup: {len(dedup_warnings)} duplicate fingerprint(s)",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
