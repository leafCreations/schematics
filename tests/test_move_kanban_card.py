"""Tests for scripts/move_kanban_card.py — bounded bucket resolve + move."""

from __future__ import annotations

from pathlib import Path

from scripts.move_kanban_card import main as move_main
from scripts.move_kanban_card import (
    move_kanban_card,
    resolve_kanban_card,
)


def _write_card(
    path: Path,
    *,
    status: str,
    card_id: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'---\nstatus: "{status}"\nid: "{card_id}"\ncompletedAt: null\n---\n\n# card\n',
        encoding="utf-8",
    )


def test_resolve_finds_card_in_done(tmp_path: Path):
    features = tmp_path / "features"
    done = features / "done"
    _write_card(
        done / "closed-card.md",
        status="done",
        card_id="closed-card-2026-06-29",
    )

    by_stem = resolve_kanban_card(stem="closed-card", features_dir=features)
    assert by_stem is not None
    assert by_stem.bucket == "done"

    by_id = resolve_kanban_card(card_id="closed-card-2026-06-29", features_dir=features)
    assert by_id is not None
    assert by_id.path == by_stem.path


def test_move_active_to_done(tmp_path: Path):
    features = tmp_path / "features"
    card_id = "active-card-2026-06-29"
    _write_card(features / "active-card.md", status="review", card_id=card_id)

    resolved = resolve_kanban_card(stem="active-card", features_dir=features)
    assert resolved is not None
    final = move_kanban_card(resolved, target="done", features_dir=features)
    assert final == features / "done" / "active-card.md"
    assert final.is_file()
    assert not (features / "active-card.md").exists()


def test_move_done_to_archived_idempotent(tmp_path: Path):
    features = tmp_path / "features"
    done = features / "done"
    archived = features / "archived"
    card_id = "phase-card-2026-06-29"
    _write_card(done / "phase-card.md", status="done", card_id=card_id)

    resolved = resolve_kanban_card(card_id=card_id, features_dir=features)
    assert resolved is not None
    first = move_kanban_card(resolved, target="archived", features_dir=features)
    assert first == archived / "phase-card.md"

    again = resolve_kanban_card(card_id=card_id, features_dir=features)
    assert again is not None
    second = move_kanban_card(again, target="archived", features_dir=features)
    assert second == first


def test_set_done_updates_frontmatter(tmp_path: Path):
    features = tmp_path / "features"
    card_id = "set-done-card-2026-06-29"
    _write_card(features / "set-done-card.md", status="review", card_id=card_id)

    code = move_main(
        ["set-done-card", "--to", "done", "--set-done", "--features-dir", str(features)],
    )
    assert code == 0
    text = (features / "done" / "set-done-card.md").read_text(encoding="utf-8")
    assert 'status: "done"' in text
    assert "completedAt:" in text
    assert "null" not in text.split("completedAt:")[1].splitlines()[0]


def test_missing_card_exits_nonzero(tmp_path: Path):
    features = tmp_path / "features"
    features.mkdir()
    assert resolve_kanban_card(stem="missing", features_dir=features) is None
    code = move_main(["missing", "--to", "done", "--features-dir", str(features)])
    assert code == 1
