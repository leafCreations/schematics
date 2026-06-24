"""Tests for feature area registry resolver."""

from __future__ import annotations

from scripts.resolve_feature_areas import resolve_areas


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
