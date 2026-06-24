"""Tests for governance audit kanban card creation."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from scripts.create_governance_audit_card import (
    build_governance_audit_body,
    create_governance_audit_card,
)


def test_build_governance_audit_body_has_fresh_checklist():
    body = build_governance_audit_body()
    assert "# AGENTS.md governance audit" in body
    assert "## Audit checklist" in body
    assert "## Audit findings" in body
    assert "## Label Paths" in body
    assert "- [ ] **Routing:**" in body
    assert "- [x]" not in body
    assert "`docs/feature-areas.yaml`" in body


def test_create_governance_audit_card_writes_todo_card(tmp_path: Path):
    features = tmp_path / "features"
    path = create_governance_audit_card(
        audit_date=date(2026, 9, 24),
        features_dir=features,
    )

    text = path.read_text(encoding="utf-8")
    assert path.name == "agents-md-governance-audit-2026-09-24.md"
    assert 'id: "agents-md-governance-audit-2026-09-24"' in text
    assert 'status: "todo"' in text
    assert "completedAt: null" in text
    assert "- [ ] **Classify:**" in text
    assert "_(Agent fills drift bullets" in text


def test_create_governance_audit_card_refuses_duplicate_without_force(tmp_path: Path):
    features = tmp_path / "features"
    create_governance_audit_card(
        audit_date=date(2026, 9, 24),
        features_dir=features,
    )
    with pytest.raises(FileExistsError):
        create_governance_audit_card(
            audit_date=date(2026, 9, 24),
            features_dir=features,
        )


def test_create_governance_audit_card_force_overwrites(tmp_path: Path):
    features = tmp_path / "features"
    first = create_governance_audit_card(
        audit_date=date(2026, 9, 24),
        features_dir=features,
    )
    first.write_text("stale", encoding="utf-8")

    second = create_governance_audit_card(
        audit_date=date(2026, 9, 24),
        features_dir=features,
        force=True,
    )

    assert second == first
    assert "## Audit checklist" in second.read_text(encoding="utf-8")
