#!/usr/bin/env python3
"""Apply fbh0 backlog hygiene batches via resolution overlays (ff2).

Uses the same overlay fields as ``resolve_forward_feedback.py --set-status`` — load once,
mutate, save once. Signature: ``forward-feedback-backlog-hygiene``.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.forward_feedback_index_lib import load_index, save_index

INDEX_PATH = REPO_ROOT / "docs" / "forward-feedback-index.yaml"

CLOSED_EPIC_BATCHES: list[tuple[str, str, str]] = [
    ("forward-feedback-ff", "answered", "ForwardFeedbackRegistry epic closed 2026-06-27"),
    ("docs-governance-split", "answered", "DocsGovernanceSplit epic closed 2026-06-27"),
    ("governance-compact", "answered", "GovernanceCompact epic closed"),
    ("kanban-card-scope", "answered", "KanbanCardScope epic closed 2026-06-28"),
    ("lessons-coverage", "answered", "LessonsCoverageMetric epic closed"),
    ("kanban-cursor-mode", "answered", "KanbanCursorModeGates epic closed"),
    ("precommit-ruff-sim110", "answered", "PrecommitRuffSim110 epic closed 2026-06-29"),
    ("governance-drift", "answered", "GovernanceDrift epics closed 2026-06-29"),
    ("agents-md-area-table", "answered", "AgentsTableSync (gs4) closed"),
    ("agent-governance-epic-completion-audit", "answered", "GovernanceEpicLifecycle gel0"),
    ("agent-governance-gel3-archive-group-batch", "answered", "GovernanceEpicLifecycle gel3"),
    ("agent-governance-gel4-epic-completion-summary", "answered", "GovernanceEpicLifecycle gel4"),
    ("agent-governance-gc7-forward-feedback-audit", "answered", "GovernanceCompact gc7 ff audit"),
    (
        "agent-governance-gc7-handoff-duplication-pair",
        "answered",
        "GovernanceCompact gc7 handoff dedup",
    ),
    ("render-bed-2026", "answered", "OrbitFunctionalFaceTextures epic closed 2026-06-27"),
    ("orbit-bed-chest-facing", "answered", "OrbitFunctionalFaceTextures shipped"),
    ("orbit-bed-colored-texture", "answered", "OrbitFunctionalFaceTextures shipped"),
    ("orbit-render-class-taxonomy", "answered", "Orbit render-class taxonomy shipped"),
    ("agent-orbit-render-or1", "answered", "Orbit render-class doc sync shipped"),
    ("feature-2d-stair-riser", "answered", "2d stair riser ghost feature shipped"),
    ("tighten-foward-feedback", "answered", "Superseded by ff registry + ccp cadence"),
    (
        "agent-card-done-agent-move-qa-complete",
        "answered",
        "GovernanceCompact gc8 agent move shipped",
    ),
    ("floating-camera", "answered", "RenderEngineFloatingCamera epic closed 2026-06-29"),
    ("feature-floating-camera", "answered", "RenderEngineFloatingCamera epic closed 2026-06-29"),
    ("bug-orbit-hud-look-ray", "answered", "Orbit HUD look-ray bug follow-up shipped"),
    ("governance-drift-registry", "answered", "GovernanceDriftAlert epic closed 2026-06-29"),
]

WONT_FIX_PATTERNS = (
    "n/a —",
    "n/a -",
    "already landed",
    "no forward feedback",
)

KEEP_OPEN_SUBSTRINGS = (
    "kanban-card-capture-policy-ccp0",  # valid post-ccp anchor ff — fbh1 scope
)


def _today_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).date().isoformat()


def apply_batch(*, dry_run: bool = False, index_path: Path = INDEX_PATH) -> dict[str, int]:
    payload = load_index(index_path)
    records = payload.get("items") or []
    if not isinstance(records, list):
        records = []

    stats = {"answered": 0, "wont-fix": 0, "duplicate": 0, "skipped": 0, "kept_open": 0}

    for record in records:
        if not isinstance(record, dict):
            continue
        if record.get("status") != "open":
            continue

        card = str(record.get("source_card") or "")
        question = str(record.get("question") or "").lower()

        if any(keep in card for keep in KEEP_OPEN_SUBSTRINGS):
            stats["kept_open"] += 1
            continue

        status: str | None = None
        resolution: str | None = None

        if record.get("duplicate_of"):
            status = "duplicate"
            resolution = f"duplicate_of:{record['duplicate_of']}"
        elif any(p in question for p in WONT_FIX_PATTERNS):
            status = "wont-fix"
            resolution = "fbh0: placeholder / N/A gc5 filler"
        elif "commit-issue" in card:
            status = "wont-fix"
            resolution = "fbh0: commit-issue hook — not durable backlog (cadence rubric)"
        else:
            for sub, batch_status, note in CLOSED_EPIC_BATCHES:
                if sub in card:
                    status = batch_status
                    resolution = f"fbh0: {note}"
                    break

        if status is None:
            stats["skipped"] += 1
            continue

        if not dry_run:
            record["status"] = status
            record["resolution"] = resolution
            if status == "answered" and not record.get("answered_at"):
                record["answered_at"] = _today_iso()

        stats[status if status in stats else "answered"] += 1

    if not dry_run:
        save_index(payload, index_path)

    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print counts only — do not write index",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=INDEX_PATH,
        help="forward-feedback index path",
    )
    args = parser.parse_args(argv)
    stats = apply_batch(dry_run=args.dry_run, index_path=args.index)
    mode = "dry-run" if args.dry_run else "applied"
    print(f"batch_forward_feedback_hygiene ({mode}): {stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
