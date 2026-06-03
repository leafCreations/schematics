"""Main window orchestration tests (no full Qt display required)."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("PySide6")


def test_build_main_window_open_failure_shows_dialog(monkeypatch):
    messages: list[str] = []
    constructed: list[bool] = []

    monkeypatch.setattr(
        "ui.main_window.QMessageBox.critical",
        lambda _parent, _title, text: messages.append(text),
    )
    monkeypatch.setattr("registries.loader.reload_registries", lambda: None)

    def fail_open(_structure: str, _stage: int):
        raise ValueError("Duplicate layer index values [0]")

    monkeypatch.setattr("ui.main_window.open_structure", fail_open)

    def should_not_construct(*_args, **_kwargs):
        constructed.append(True)
        raise RuntimeError("MainWindow should not be constructed when open fails")

    monkeypatch.setattr("ui.main_window.MainWindow", should_not_construct)

    from ui.main_window import build_main_window

    with pytest.raises(ValueError, match="Duplicate layer index"):
        build_main_window("residence", stage=1)

    assert messages
    assert "failed validation" in messages[0]
    assert not constructed


@pytest.mark.skipif(
    os.environ.get("STRUCTURE_SCRIPTS_UI_TESTS", "") != "1",
    reason="Set STRUCTURE_SCRIPTS_UI_TESTS=1 for full Qt window smoke test",
)
def test_build_main_window_loads_residence_stage1_smoke():
    from PySide6.QtWidgets import QApplication

    from ui.main_window import build_main_window

    application = QApplication.instance() or QApplication([])
    window = build_main_window("residence", stage=1)

    try:
        assert window._document.metadata["structure"] == "residence"
        assert len(window._document.layers) == 6
        assert window._structure_grid._texture_cache is window._grid_texture_cache
    finally:
        window.close()

    del application
