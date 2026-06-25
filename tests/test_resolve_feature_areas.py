"""Tests for feature area registry resolver."""

from __future__ import annotations

import io
from contextlib import redirect_stdout

from scripts.resolve_feature_areas import (
    format_lesson_pointers,
    load_registry,
    main,
    resolve_areas,
    resolve_lesson_pointers,
)


def test_resolve_areas_returns_paths():
    paths, unknown = resolve_areas(["File Menu"])
    assert not unknown
    assert "ui/main_window.py" in paths


def test_resolve_areas_handlers_only():
    handlers, unknown = resolve_areas(["Open Structures Workflow"], handlers_only=True)
    assert not unknown
    assert "MainWindow._on_open_structure" in handlers
    assert "ui/reload.py" not in handlers


def test_resolve_areas_unknown_label():
    paths, unknown = resolve_areas(["Not A Real Area"])
    assert paths == []
    assert unknown == ["Not A Real Area"]


def test_load_registry_includes_lesson_keys():
    areas = load_registry()
    render = areas["Render Preview"]
    assert "orbit-animated-texture-strip" in render["lesson_signatures"]
    assert "docs/render-types.md" in render["lesson_docs"]
    agent = areas["Agent Workflow"]
    assert "precommit-stash-old-hooks" in agent["lesson_signatures"]
    assert "docs/development.md" in agent["lesson_docs"]


def test_resolve_lesson_pointers_single_area():
    pointers, unknown = resolve_lesson_pointers(["Render Preview"])
    assert not unknown
    assert "orbit-animated-texture-strip" in pointers["lesson_signatures"]
    assert pointers["lesson_docs"] == ["docs/render-types.md"]


def test_resolve_lesson_pointers_unions_dual_labels():
    pointers, unknown = resolve_lesson_pointers(["Render Preview", "Agent Workflow"])
    assert not unknown
    assert "orbit-animated-texture-strip" in pointers["lesson_signatures"]
    assert "precommit-stash-old-hooks" in pointers["lesson_signatures"]
    assert "docs/render-types.md" in pointers["lesson_docs"]
    assert "docs/development.md" in pointers["lesson_docs"]


def test_resolve_lesson_pointers_unknown_label():
    pointers, unknown = resolve_lesson_pointers(["Not A Real Area"])
    assert pointers == {"lesson_signatures": [], "lesson_docs": []}
    assert unknown == ["Not A Real Area"]


def test_format_lesson_pointers_renders_yaml_like_block():
    text = format_lesson_pointers(
        {
            "lesson_signatures": ["orbit-animated-texture-strip"],
            "lesson_docs": ["docs/render-types.md"],
        }
    )
    assert "lesson_signatures:" in text
    assert "  - orbit-animated-texture-strip" in text
    assert "lesson_docs:" in text
    assert "  - docs/render-types.md" in text


def test_main_lessons_flag_prints_pointers():
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(["--lessons", "Render Preview"])
    assert code == 0
    out = buf.getvalue()
    assert "orbit-animated-texture-strip" in out
    assert "docs/render-types.md" in out


def test_main_lessons_unknown_label_exits_nonzero():
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(["--lessons", "Not A Real Area"])
    assert code == 1
