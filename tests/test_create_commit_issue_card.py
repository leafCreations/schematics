"""Tests for commit-issue kanban card creation on pre-commit failure."""

from __future__ import annotations

from pathlib import Path

from scripts.create_commit_issue_card import (
    _extract_failed_test_files,
    build_card_body,
    create_commit_issue_card,
)


def test_extract_failed_test_files_dedupes_and_preserves_order():
    log = """
FAILED tests/test_a.py::test_one - assert False
FAILED tests/test_b.py::test_two - assert False
FAILED tests/test_a.py::test_three - assert False
"""
    assert _extract_failed_test_files(log) == [
        "tests/test_a.py",
        "tests/test_b.py",
    ]


def test_build_card_body_includes_problem_and_failed_tests():
    log = "FAILED tests/test_worldgen.py::test_chest - assert 0 >= 2\n"
    _, _, body = build_card_body(hook="pytest", log_text=log)
    assert "## Problem" in body
    assert "## Failed Tests" in body
    assert "`tests/test_worldgen.py`" in body
    assert "Pre-commit pytest failed" in body


def test_create_commit_issue_card_writes_todo_card(tmp_path: Path):
    features = tmp_path / "features"
    log = tmp_path / "hook.log"
    log.write_text("FAILED tests/test_x.py::test_y - boom\n", encoding="utf-8")

    path = create_commit_issue_card(
        hook="pytest",
        log_text=log.read_text(encoding="utf-8"),
        features_dir=features,
    )

    text = path.read_text(encoding="utf-8")
    assert path.name.startswith("commit-issue-pytest-")
    assert 'status: "todo"' in text
    assert 'labels: ["commit-issue"]' in text
    assert "## Problem" in text
    assert "## Failed Tests" in text
    assert "`tests/test_x.py`" in text
