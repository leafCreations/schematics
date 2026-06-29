#!/usr/bin/env python3
"""Human-readable report of forward-feedback duplicate fingerprints (ff dedup).

Informational — run after index rebuild or anytime to inspect ``duplicate_of`` clusters
without parsing stderr. Signature: ``forward-feedback-dedup-report``.

Example::

    python3 scripts/report_forward_feedback_dedup.py
    python3 scripts/report_forward_feedback_dedup.py --json
    python3 scripts/report_forward_feedback_dedup.py --rebuild
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_forward_feedback_index import (  # noqa: E402
    build_index,
    question_fingerprint,
)
from scripts.forward_feedback_index_lib import DEFAULT_INDEX_PATH, load_index  # noqa: E402

TERMINAL_FF_STATUSES = frozenset({"answered", "duplicate", "wont-fix", "deferred", "spawned"})


def _canonical_for_group(group: list[dict[str, Any]]) -> dict[str, Any]:
    """Pick canonical row: first without duplicate_of, else earliest id."""
    without = [row for row in group if not row.get("duplicate_of")]
    if without:
        return sorted(without, key=lambda row: str(row.get("id") or ""))[0]
    return sorted(group, key=lambda row: str(row.get("id") or ""))[0]


def _action_for_cluster(
    canonical: dict[str, Any],
    duplicates: list[dict[str, Any]],
) -> str:
    """Advisory action line for operators."""
    statuses = {str(canonical.get("status") or "open")}
    statuses.update(str(row.get("status") or "open") for row in duplicates)
    if statuses <= TERMINAL_FF_STATUSES:
        return "none — all terminal (rebuild warning only; no open backlog action)"
    if "open" in statuses or "discussing" in statuses:
        return "review — open or discussing rows remain in cluster"
    return "review — mixed non-terminal statuses"


def cluster_duplicate_fingerprints(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Group index rows sharing the same question fingerprint (len ≥ 2)."""
    by_fp: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if not isinstance(record, dict):
            continue
        question = str(record.get("question") or "")
        by_fp[question_fingerprint(question)].append(record)

    clusters: list[dict[str, Any]] = []
    for fingerprint, group in sorted(by_fp.items()):
        if len(group) < 2:
            continue
        canonical = _canonical_for_group(group)
        canonical_id = str(canonical.get("id") or "")
        duplicates = [row for row in group if str(row.get("id") or "") != canonical_id]
        clusters.append(
            {
                "fingerprint": fingerprint,
                "question": str(canonical.get("question") or ""),
                "canonical_id": canonical_id,
                "canonical_status": str(canonical.get("status") or "open"),
                "canonical_source": str(canonical.get("source_card") or ""),
                "duplicate_ids": [str(row.get("id") or "") for row in duplicates],
                "duplicate_statuses": [str(row.get("status") or "open") for row in duplicates],
                "action": _action_for_cluster(canonical, duplicates),
            }
        )
    return clusters


def format_report_lines(
    clusters: list[dict[str, Any]],
    *,
    rebuild_warning_count: int | None = None,
) -> list[str]:
    """Plain-text lines for chat / terminal."""
    lines: list[str] = []
    if rebuild_warning_count is not None:
        lines.append(f"Rebuild stderr: {rebuild_warning_count} duplicate fingerprint warning(s)")
    if not clusters:
        lines.append("No duplicate question fingerprints in index.")
        return lines

    lines.append(f"Duplicate fingerprint clusters: {len(clusters)}")
    for idx, cluster in enumerate(clusters, start=1):
        lines.append("")
        lines.append(f"--- Cluster {idx} ---")
        lines.append(f"- **Action:** {cluster['action']}")
        lines.append(f"- **Fingerprint:** {cluster['fingerprint']}")
        q = cluster["question"].replace("\n", " ")
        if len(q) > 80:
            q = q[:77] + "..."
        lines.append(f"- **Question:** {q!r}")
        lines.append(f"- **Canonical:** {cluster['canonical_id']} ({cluster['canonical_status']})")
        lines.append(f"- **Source:** {cluster['canonical_source']}")
        if cluster["duplicate_ids"]:
            dup_line = ", ".join(cluster["duplicate_ids"])
            lines.append(f"- **Duplicates:** {dup_line}")
        lines.append(
            "- **Inspect:** "
            "`python3 scripts/report_forward_feedback_dedup.py` "
            "(Signature: forward-feedback-dedup-report)"
        )
    return lines


def filter_suppressed_dedup_warnings(
    items: list[dict[str, Any]],
    warnings: list[str],
) -> list[str]:
    """Drop stderr lines for fingerprint clusters that are already terminal (ffd2)."""
    clusters = cluster_duplicate_fingerprints(items)
    terminal_fps = {
        cluster["fingerprint"]
        for cluster in clusters
        if str(cluster["action"]).startswith("none — all terminal")
    }
    if not terminal_fps:
        return warnings
    kept: list[str] = []
    for line in warnings:
        marker = "(fingerprint "
        if marker in line:
            fp = line.rsplit(marker, 1)[-1].rstrip(")")
            if fp in terminal_fps:
                continue
        kept.append(line)
    return kept


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--index",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help="forward-feedback index path",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit JSON cluster list",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="run build_index first; include stderr warning count",
    )
    args = parser.parse_args(argv)

    rebuild_count: int | None = None
    if args.rebuild:
        _payload, warnings = build_index(repo_root=REPO_ROOT)
        rebuild_count = len(warnings)

    payload = load_index(args.index)
    records = payload.get("items") or []
    if not isinstance(records, list):
        records = []

    clusters = cluster_duplicate_fingerprints(records)

    if args.json:
        out = {
            "rebuild_warning_count": rebuild_count,
            "cluster_count": len(clusters),
            "clusters": clusters,
        }
        print(json.dumps(out, indent=2))
        return 0

    for line in format_report_lines(clusters, rebuild_warning_count=rebuild_count):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
