"""Tests for commit-issue kanban card creation on pre-commit failure."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from scripts.create_commit_issue_card import (
    _extract_failed_test_files,
    _extract_ruff_rule_ids,
    build_card_body,
    create_commit_issue_card,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ON_FAILURE = REPO_ROOT / "scripts/on_pre_commit_failure.sh"


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


def test_extract_ruff_rule_ids_from_sim110_log():
    log = """
SIM110 Use `return any(source.exists() and source.stat().st_mtime > cache_mtime
for source in source_paths)` instead of `for` loop
  --> helpers/sprite_baker/cache.py:72:5
Found 2 errors (1 fixed, 1 remaining).
"""
    assert _extract_ruff_rule_ids(log) == ["SIM110"]


def test_build_card_body_ruff_includes_ruff_rules_section():
    log = """
SIM110 Use `return any(x for x in xs)` instead of `for` loop
  --> helpers/foo.py:1:1
"""
    _, _, body = build_card_body(hook="ruff", log_text=log, failed_test_files=["helpers/foo.py"])
    assert "## Ruff rules" in body
    assert "`SIM110`" in body
    assert "## Problem" in body


def test_create_commit_issue_card_ruff_writes_ruff_rules_frontmatter(tmp_path: Path):
    features = tmp_path / "features"
    log = """
SIM110 Use `return any(x for x in xs)` instead of `for` loop
  --> helpers/foo.py:1:1
"""
    path = create_commit_issue_card(
        hook="ruff",
        log_text=log,
        features_dir=features,
    )
    text = path.read_text(encoding="utf-8")
    assert path.name.startswith("commit-issue-ruff-")
    assert 'ruffRules: ["SIM110"]' in text
    assert "## Ruff rules" in text
    assert "`SIM110`" in text


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


def test_on_pre_commit_failure_skips_card_without_pre_commit(tmp_path: Path):
    """Manual agent runs of pre-commit-pytest.sh must not spawn commit-issue cards."""
    log = tmp_path / "hook.log"
    log.write_text("FAILED tests/test_x.py::test_y - boom\n", encoding="utf-8")
    env = {key: value for key, value in os.environ.items() if key != "PRE_COMMIT"}
    env["SKIP_COMMIT_ISSUE_CARD"] = "0"
    proc = subprocess.run(
        [str(ON_FAILURE), "pytest", str(log)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "commit-issue card created" not in proc.stdout


def test_on_pre_commit_failure_creates_card_during_pre_commit(tmp_path: Path):
    log = tmp_path / "hook.log"
    log.write_text("FAILED tests/test_x.py::test_y - boom\n", encoding="utf-8")
    features = tmp_path / "features"
    env = os.environ.copy()
    env["PRE_COMMIT"] = "1"
    env["SKIP_COMMIT_ISSUE_CARD"] = "0"
    env["COMMIT_ISSUE_FEATURES_DIR"] = str(features)
    proc = subprocess.run(
        [str(ON_FAILURE), "pytest", str(log)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "commit-issue card created" in proc.stdout
    assert list(features.glob("commit-issue-pytest-*.md"))
