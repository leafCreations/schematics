"""Tests for scripts/resolve_forward_feedback.py."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml

from scripts.forward_feedback_index_lib import (
    aggregate_open_stats,
    find_stale_high_risk_open,
    is_open_backlog_row,
    risk_band_label,
)
from scripts.lessons_coverage_lib import normalize_forward_feedback_category
from scripts.resolve_forward_feedback import (
    filter_items,
    format_item,
    link_ff_item,
    rank_items,
    resolve_forward_feedback,
    run_open_report,
    set_ff_status,
)

# re-export helper from build tests pattern
from tests.test_build_forward_feedback_index import _gc5_body, _write_closed_card


def write_index_fixture(repo_root: Path) -> Path:
    from scripts.build_forward_feedback_index import build_index, write_index

    payload, _warnings = build_index(repo_root=repo_root)
    index_path = repo_root / "docs" / "forward-feedback-index.yaml"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    write_index(payload, output_path=index_path)
    return index_path


@pytest.fixture
def ff_resolver(tmp_path: Path):
    done = tmp_path / ".devtool" / "features" / "done"
    done.mkdir(parents=True)
    _write_closed_card(
        done,
        "card-a.md",
        body=_gc5_body(codebase_scope="multi-card", codebase_risk=3),
    )
    index_path = write_index_fixture(tmp_path)
    return tmp_path, index_path


def test_normalize_category_aliases():
    assert normalize_forward_feedback_category("rules") == "Rule"
    assert normalize_forward_feedback_category("Codebase") == "Codebase"
    assert normalize_forward_feedback_category("prompt") == "Prompt pattern"
    assert normalize_forward_feedback_category("unknown") is None


def test_filter_items_by_category_and_status(ff_resolver):
    _repo, index_path = ff_resolver
    payload = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    records = payload["items"]
    codebase = filter_items(records, category="Codebase", status="open")
    assert len(codebase) == 1
    assert codebase[0]["category"] == "Codebase"
    assert filter_items(records, category="Codebase", status="closed") == []


def test_rank_items_orders_by_risk_then_scope(ff_resolver):
    _repo, index_path = ff_resolver
    payload = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    records = payload["items"]
    governance = [row for row in records if row["category"] == "Governance"]
    codebase = [row for row in records if row["category"] == "Codebase"]
    ranked = rank_items(governance + codebase)
    assert ranked[0]["category"] == "Governance"
    assert ranked[0]["risk_level"] == 4


def test_resolve_top_n_within_category(ff_resolver):
    _repo, index_path = ff_resolver
    results = resolve_forward_feedback(
        category="Codebase",
        status="open",
        top=1,
        index_path=index_path,
    )
    assert len(results) == 1
    assert results[0]["category"] == "Codebase"


def test_resolve_governance_top_three(ff_resolver):
    _repo, index_path = ff_resolver
    results = resolve_forward_feedback(
        category="Governance",
        status="open",
        top=3,
        index_path=index_path,
    )
    assert len(results) == 1
    assert "registry yaml" in results[0]["question"]


def test_format_item_includes_metadata(ff_resolver):
    _repo, index_path = ff_resolver
    results = resolve_forward_feedback(
        category="Governance",
        index_path=index_path,
    )
    text = format_item(results[0], index=1)
    assert "[ff-" in text
    assert "risk=4" in text
    assert "scope=system-wide" in text


def test_filter_excludes_spawned_by_default(ff_resolver):
    _repo, index_path = ff_resolver
    payload = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    records = payload["items"]
    rule_row = next(row for row in records if row["category"] == "Governance")
    rule_row["status"] = "spawned"
    rule_row["spawned"] = [".devtool/features/inquiry-foo.md"]
    index_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    open_rules = filter_items(records, category="Governance", status="open")
    assert open_rules == []
    with_spawned = filter_items(
        records,
        category="Governance",
        status="open",
        include_spawned=True,
    )
    assert len(with_spawned) == 1


def test_link_ff_item_sets_spawned_and_status(ff_resolver):
    _repo, index_path = ff_resolver
    payload = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    item_id = payload["items"][0]["id"]
    card = ".devtool/features/inquiry-foo.md"
    record = link_ff_item(item_id, card, index_path=index_path, repo_root=_repo)
    assert record["status"] == "spawned"
    assert card in record["spawned"]
    reloaded = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    saved = next(row for row in reloaded["items"] if row["id"] == item_id)
    assert saved["status"] == "spawned"


def test_set_ff_status_answered_sets_date(ff_resolver):
    _repo, index_path = ff_resolver
    payload = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    item_id = payload["items"][0]["id"]
    record = set_ff_status(
        item_id,
        "answered",
        resolution="resolved in epic audit",
        index_path=index_path,
    )
    assert record["status"] == "answered"
    assert record["answered_at"]
    assert record["resolution"] == "resolved in epic audit"


def test_merge_preserves_link_after_rebuild(ff_resolver):
    repo_root, index_path = ff_resolver
    payload = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    item_id = payload["items"][0]["id"]
    link_ff_item(
        item_id,
        ".devtool/features/inquiry-foo.md",
        index_path=index_path,
        repo_root=repo_root,
    )
    from scripts.build_forward_feedback_index import build_index

    rebuilt, _warnings = build_index(repo_root=repo_root)
    saved = next(row for row in rebuilt["items"] if row["id"] == item_id)
    assert saved["status"] == "spawned"
    assert ".devtool/features/inquiry-foo.md" in saved["spawned"]


def test_risk_band_label_buckets():
    assert risk_band_label(4) == "high"
    assert risk_band_label(5) == "high"
    assert risk_band_label(3) == "medium"
    assert risk_band_label(2) == "low"
    assert risk_band_label(None) == "unknown"


def test_aggregate_open_stats_counts_category_and_risk(ff_resolver):
    _repo, index_path = ff_resolver
    payload = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    stats = aggregate_open_stats(payload["items"])
    assert stats["total_open"] >= 1
    assert "Codebase" in stats["by_category"]
    assert stats["by_risk_band"]["high"] >= 0
    assert sum(stats["by_risk_band"].values()) == stats["total_open"]


def test_is_open_backlog_row_excludes_spawned_and_duplicate():
    assert is_open_backlog_row({"status": "open"})
    assert not is_open_backlog_row({"status": "spawned"})
    assert not is_open_backlog_row({"status": "open", "duplicate_of": "ff-other"})


def test_find_stale_high_risk_open_respects_threshold():
    today = date(2026, 6, 27)
    rows = [
        {
            "id": "ff-stale",
            "status": "open",
            "risk_level": 4,
            "completed_at": "2026-05-01",
            "category": "Governance",
            "question": "old?",
        },
        {
            "id": "ff-fresh",
            "status": "open",
            "risk_level": 4,
            "completed_at": "2026-06-20",
            "category": "Governance",
            "question": "new?",
        },
        {
            "id": "ff-spawned",
            "status": "open",
            "risk_level": 5,
            "completed_at": "2026-01-01",
            "spawned": [".devtool/features/foo.md"],
            "category": "Rule",
            "question": "linked?",
        },
    ]
    stale = find_stale_high_risk_open(rows, stale_days=14, today=today)
    assert [row["id"] for row in stale] == ["ff-stale"]


def test_run_open_report_includes_category_lines(ff_resolver):
    _repo, index_path = ff_resolver
    lines = run_open_report(index_path=index_path)
    text = "\n".join(lines)
    assert "Forward feedback open report" in text
    assert "by category:" in text
    assert "by risk band:" in text
    assert "forward-feedback-stale-metrics" in text


def test_run_open_report_stale_section_when_stale_days_set():
    rows = [
        {
            "id": "ff-old",
            "status": "open",
            "risk_level": 4,
            "completed_at": "2026-01-01",
            "category": "Governance",
            "question": "stale question?",
            "source_card": ".devtool/features/done/x.md",
        },
    ]
    from scripts.forward_feedback_index_lib import format_open_report_lines

    stats = aggregate_open_stats(rows)
    lines = format_open_report_lines(
        stats,
        stale_items=find_stale_high_risk_open(
            rows,
            stale_days=30,
            today=date(2026, 6, 27),
        ),
        stale_days=30,
    )
    text = "\n".join(lines)
    assert "stale advisory:" in text
    assert "ff-old" in text


def test_batch_forward_feedback_hygiene_dry_run(tmp_path, monkeypatch):
    from scripts.batch_forward_feedback_hygiene import apply_batch

    index = tmp_path / "forward-feedback-index.yaml"
    payload = {
        "version": 1,
        "items": [
            {
                "id": "ff-test-commit-issue-ruff-01-abc",
                "source_card": ".devtool/features/done/commit-issue-ruff.md",
                "category": "Governance",
                "question": "Should ruff run on commit?",
                "status": "open",
            },
            {
                "id": "ff-test-ccp0-governance-01-def",
                "source_card": (
                    ".devtool/features/archived/agent-kanban-card-capture-policy-"
                    "ccp0-schema-spec-2026-06-29.md"
                ),
                "category": "Governance",
                "question": "Should ff1 auto-skip phase members?",
                "status": "open",
            },
        ],
    }
    index.write_text(yaml.safe_dump(payload), encoding="utf-8")
    stats = apply_batch(dry_run=True, index_path=index)
    assert stats["wont-fix"] == 1
    assert stats["kept_open"] == 1
    reloaded = yaml.safe_load(index.read_text())
    assert reloaded["items"][0]["status"] == "open"
