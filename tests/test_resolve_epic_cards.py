"""Tests for resolve_epic_cards.py — epic membership and closed registry."""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.resolve_epic_cards import (
    append_closed_epic,
    is_epic_closed,
    iter_epic_cards,
    load_closed_epics,
    validate_new_epic_name,
)


def _write_card(
    path: Path,
    *,
    status: str,
    epic: str,
    order: str = "a0",
) -> None:
    path.write_text(
        f'---\nstatus: "{status}"\nepic: "{epic}"\norder: "{order}"\n---\n\n# card\n',
        encoding="utf-8",
    )


def test_iter_epic_cards_active_and_done(tmp_path: Path):
    features = tmp_path / "features"
    done = features / "done"
    done.mkdir(parents=True)

    _write_card(features / "active.md", status="review", epic="TestEpic", order="a1")
    _write_card(done / "closed-member.md", status="done", epic="TestEpic", order="a0")

    report = iter_epic_cards("TestEpic", features_dir=features)
    assert len(report.active) == 1
    assert len(report.done) == 1
    assert report.is_complete is False


def test_iter_epic_cards_complete_when_no_active(tmp_path: Path):
    features = tmp_path / "features"
    done = features / "done"
    done.mkdir(parents=True)
    _write_card(done / "only-done.md", status="done", epic="DoneEpic")

    report = iter_epic_cards("DoneEpic", features_dir=features)
    assert report.is_complete is True


def test_validate_new_epic_name_rejects_closed(tmp_path: Path, monkeypatch):
    registry = tmp_path / "epics-closed.yaml"
    registry.write_text(
        yaml.safe_dump({"closed": [{"name": "OldEpic", "closed": "2026-06-27"}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "scripts.resolve_epic_cards.EPICS_CLOSED_PATH",
        registry,
    )

    assert is_epic_closed("OldEpic", registry_path=registry) is True
    assert validate_new_epic_name("OldEpic", registry_path=registry) is not None
    assert validate_new_epic_name("FreshEpic", registry_path=registry) is None


def test_append_closed_epic_idempotent(tmp_path: Path, monkeypatch):
    registry = tmp_path / "epics-closed.yaml"
    registry.write_text("closed: []\n", encoding="utf-8")
    monkeypatch.setattr("scripts.resolve_epic_cards.EPICS_CLOSED_PATH", registry)

    append_closed_epic(
        "GovernanceEpicLifecycle",
        closed_date="2026-06-27",
        anchor="archived/agent-governance-epic-completion-audit-2026-06-27.md",
        registry_path=registry,
    )
    append_closed_epic(
        "GovernanceEpicLifecycle",
        closed_date="2026-06-27",
        anchor="archived/agent-governance-epic-completion-audit-2026-06-27.md",
        registry_path=registry,
    )

    closed = load_closed_epics(registry)
    assert len(closed) == 1
    assert closed[0]["name"] == "GovernanceEpicLifecycle"


def test_main_validate_new_exit_code(tmp_path: Path, monkeypatch):
    from scripts.resolve_epic_cards import main

    registry = tmp_path / "epics-closed.yaml"
    registry.write_text(
        yaml.safe_dump({"closed": [{"name": "ClosedEpic", "closed": "2026-06-27"}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr("scripts.resolve_epic_cards.EPICS_CLOSED_PATH", registry)

    assert main(["--validate-new", "ClosedEpic"]) == 1
    assert main(["--validate-new", "NewEpic"]) == 0
