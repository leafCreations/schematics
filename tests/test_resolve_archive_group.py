"""Tests for resolve_archive_group.py — archive-group membership."""

from __future__ import annotations

from pathlib import Path

from scripts.resolve_archive_group import iter_archive_group_cards, main


def _write_card(
    path: Path,
    *,
    status: str,
    archive_group: str,
    order: str = "a0",
    epic: str | None = None,
) -> None:
    epic_line = f'epic: "{epic}"\n' if epic else ""
    path.write_text(
        f'---\nstatus: "{status}"\n{epic_line}'
        f'archiveGroup: "{archive_group}"\norder: "{order}"\n---\n\n# card\n',
        encoding="utf-8",
    )


def test_iter_archive_group_active_and_done(tmp_path: Path):
    features = tmp_path / "features"
    done = features / "done"
    done.mkdir(parents=True)

    _write_card(
        features / "active.md",
        status="review",
        archive_group="TestGroup",
        order="a1",
    )
    _write_card(
        done / "closed-member.md",
        status="done",
        archive_group="TestGroup",
        order="a0",
    )

    report = iter_archive_group_cards("TestGroup", features_dir=features)
    assert len(report.active) == 1
    assert len(report.done) == 1
    assert report.is_complete is False


def test_iter_archive_group_complete_when_no_active(tmp_path: Path):
    features = tmp_path / "features"
    done = features / "done"
    archived = features / "archived"
    done.mkdir(parents=True)
    archived.mkdir(parents=True)

    _write_card(done / "only-done.md", status="done", archive_group="DoneGroup")
    _write_card(
        archived / "old.md",
        status="done",
        archive_group="DoneGroup",
    )

    report = iter_archive_group_cards("DoneGroup", features_dir=features)
    assert report.is_complete is True
    assert len(report.done) == 1
    assert len(report.archived) == 1


def test_main_status_json(tmp_path: Path):
    features = tmp_path / "features"
    done = features / "done"
    done.mkdir(parents=True)
    _write_card(done / "member.md", status="done", archive_group="JsonGroup")

    assert (
        main(
            [
                "--group",
                "JsonGroup",
                "--status",
                "--json",
                "--features-dir",
                str(features),
            ]
        )
        == 0
    )
