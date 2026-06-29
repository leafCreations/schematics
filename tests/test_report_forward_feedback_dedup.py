"""Tests for scripts/report_forward_feedback_dedup.py."""

from __future__ import annotations

from scripts.build_forward_feedback_index import question_fingerprint
from scripts.report_forward_feedback_dedup import (
    cluster_duplicate_fingerprints,
    filter_suppressed_dedup_warnings,
    format_report_lines,
)


def test_cluster_groups_same_fingerprint():
    records = [
        {
            "id": "ff-a",
            "question": "N/A",
            "status": "answered",
            "source_card": ".devtool/features/archived/a.md",
        },
        {
            "id": "ff-b",
            "question": "N/A",
            "status": "duplicate",
            "source_card": ".devtool/features/archived/b.md",
            "duplicate_of": "ff-a",
        },
    ]
    clusters = cluster_duplicate_fingerprints(records)
    assert len(clusters) == 1
    assert clusters[0]["canonical_id"] == "ff-a"
    assert clusters[0]["duplicate_ids"] == ["ff-b"]
    assert "none — all terminal" in clusters[0]["action"]


def test_format_report_includes_inspect_script():
    lines = format_report_lines(
        [
            {
                "fingerprint": "abc123",
                "question": "Same?",
                "canonical_id": "ff-canonical",
                "canonical_status": "answered",
                "canonical_source": "x.md",
                "duplicate_ids": ["ff-dup"],
                "duplicate_statuses": ["duplicate"],
                "action": "none — all terminal (rebuild warning only; no open backlog action)",
            }
        ],
        rebuild_warning_count=1,
    )
    text = "\n".join(lines)
    assert "report_forward_feedback_dedup.py" in text
    assert "Rebuild stderr: 1" in text
    assert "ff-canonical" in text


def test_filter_suppressed_dedup_warnings_drops_terminal_cluster():
    question = "N/A"
    fp = question_fingerprint(question)
    items = [
        {"id": "ff-a", "question": question, "status": "answered"},
        {"id": "ff-b", "question": question, "status": "duplicate", "duplicate_of": "ff-a"},
    ]
    raw = [f"forward-feedback dedup: ff-b duplicate_of ff-a (fingerprint {fp})"]
    assert filter_suppressed_dedup_warnings(items, raw) == []


def test_filter_suppressed_dedup_warnings_keeps_open_cluster():
    question = "Still open?"
    fp = question_fingerprint(question)
    items = [
        {"id": "ff-a", "question": question, "status": "open"},
        {"id": "ff-b", "question": question, "status": "open", "duplicate_of": "ff-a"},
    ]
    raw = [f"forward-feedback dedup: ff-b duplicate_of ff-a (fingerprint {fp})"]
    assert filter_suppressed_dedup_warnings(items, raw) == raw
