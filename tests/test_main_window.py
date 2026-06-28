"""Main window orchestration tests (no full Qt display required)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QMainWindow

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


def test_open_recent_menu_does_not_load_entries_during_startup(monkeypatch):
    import ui.main_window as main_window

    real_main_window = main_window.MainWindow

    class MenuOnlyWindow(QMainWindow):
        def __init__(self, _document, *, structure: str, stage: int, parent=None):
            super().__init__(parent)
            self._structure = structure
            self._stage = stage
            self._status = type("_Status", (), {"showMessage": lambda *_a, **_k: None})()
            self._dirty_layers = set()
            self._dirty_structure = False
            self._document = type(
                "_Doc", (), {"metadata": {"structure": structure, "stage": stage}}
            )()
            self._on_new_structure_placeholder = lambda: None
            self._on_open_structure = lambda: None
            self._on_save = lambda: None
            self._save_all = lambda: None
            self._refresh_open_recent_menu = real_main_window._refresh_open_recent_menu.__get__(
                self,
                MenuOnlyWindow,
            )
            self._open_recent_entry = lambda *_args, **_kwargs: None
            self._clear_recent_entries = lambda *_args, **_kwargs: None
            real_main_window._init_file_menu(self)

    monkeypatch.setattr("registries.loader.reload_registries", lambda: None)
    monkeypatch.setattr("ui.main_window.open_structure", lambda *_args, **_kwargs: object())
    monkeypatch.setattr("ui.main_window.add_recent_structure", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        "ui.main_window.load_recent_structures",
        lambda: (_ for _ in ()).throw(AssertionError("load_recent_structures called at startup")),
    )
    monkeypatch.setattr("ui.main_window.MainWindow", MenuOnlyWindow)

    application = QApplication.instance() or QApplication([])

    window = main_window.build_main_window("residence", stage=1)
    window.close()
    del application


def test_resolve_startup_target_uses_cli_structure_when_provided():
    from ui.main_window import _resolve_startup_target

    assert _resolve_startup_target("residence", 3) == ("residence", 3)
    assert _resolve_startup_target("residence", None) == ("residence", 1)


def test_resolve_startup_target_uses_first_valid_recent(monkeypatch):
    from ui.main_window import _resolve_startup_target

    monkeypatch.setattr(
        "ui.main_window.load_recent_structures",
        lambda: [("missing", 1), ("well", 2)],
    )

    def fake_open(structure: str, stage: int):
        if structure == "missing":
            raise FileNotFoundError("missing")

        return {"structure": structure, "stage": stage}

    monkeypatch.setattr("ui.main_window.open_structure", fake_open)
    assert _resolve_startup_target(None, None) == ("well", 2)


def test_resolve_startup_target_returns_none_without_recent(monkeypatch):
    from ui.main_window import _resolve_startup_target

    monkeypatch.setattr("ui.main_window.load_recent_structures", lambda: [])

    assert _resolve_startup_target(None, None) is None


def test_resolve_structure_stage_from_selected_dir_accepts_stage_folder(tmp_path: Path):
    from ui.main_window import _resolve_structure_stage_from_selected_dir

    stage_dir = tmp_path / "structures" / "well" / "stage4"
    stage_dir.mkdir(parents=True)
    (stage_dir / "structure.yaml").write_text("structure: well\nstage: 4\n", encoding="utf-8")

    assert _resolve_structure_stage_from_selected_dir(stage_dir) == ("well", 4)


def test_resolve_structure_stage_from_selected_dir_rejects_non_stage_folder(tmp_path: Path):
    from ui.main_window import _resolve_structure_stage_from_selected_dir

    structure_dir = tmp_path / "structures" / "well"
    structure_dir.mkdir(parents=True)
    (structure_dir / "structure.yaml").write_text("structure: well\nstage: 1\n", encoding="utf-8")

    assert _resolve_structure_stage_from_selected_dir(structure_dir) is None


def test_structure_stage_choices_from_structure_folder(tmp_path: Path):
    from ui.main_window import _structure_stage_choices

    structure_dir = tmp_path / "structures" / "well"
    (structure_dir / "stage1").mkdir(parents=True)
    (structure_dir / "stage2").mkdir(parents=True)
    (structure_dir / "notes").mkdir(parents=True)
    (structure_dir / "stage1" / "structure.yaml").write_text(
        "structure: well\nstage: 1\n",
        encoding="utf-8",
    )
    (structure_dir / "stage2" / "structure.yaml").write_text(
        "structure: well\nstage: 2\n",
        encoding="utf-8",
    )

    assert _structure_stage_choices(structure_dir) == [("well", 1), ("well", 2)]


def test_pick_structure_stage_uses_stage_folder_directly(monkeypatch, tmp_path: Path):
    from ui.main_window import _pick_structure_stage

    stage_dir = tmp_path / "structures" / "well" / "stage3"
    stage_dir.mkdir(parents=True)
    (stage_dir / "structure.yaml").write_text("structure: well\nstage: 3\n", encoding="utf-8")

    monkeypatch.setattr("ui.main_window.STRUCTURES_FOLDER", tmp_path / "structures")
    monkeypatch.setattr(
        "ui.main_window.QFileDialog.getExistingDirectory", lambda *_a, **_k: str(stage_dir)
    )

    assert _pick_structure_stage(None) == ("well", 3)


def test_pick_structure_stage_selects_stage_when_structure_folder_chosen(
    monkeypatch, tmp_path: Path
):
    from ui.main_window import _pick_structure_stage

    structure_dir = tmp_path / "structures" / "well"
    (structure_dir / "stage1").mkdir(parents=True)
    (structure_dir / "stage2").mkdir(parents=True)
    (structure_dir / "stage1" / "structure.yaml").write_text(
        "structure: well\nstage: 1\n",
        encoding="utf-8",
    )
    (structure_dir / "stage2" / "structure.yaml").write_text(
        "structure: well\nstage: 2\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("ui.main_window.STRUCTURES_FOLDER", tmp_path / "structures")
    monkeypatch.setattr(
        "ui.main_window.QFileDialog.getExistingDirectory",
        lambda *_a, **_k: str(structure_dir),
    )
    monkeypatch.setattr(
        "ui.main_window._select_stage_for_structure",
        lambda _parent, _structure, _stages: ("well", 2),
    )

    assert _pick_structure_stage(None) == ("well", 2)


def test_pick_structure_stage_warns_when_no_valid_stages(monkeypatch, tmp_path: Path):
    from ui.main_window import _pick_structure_stage

    empty_dir = tmp_path / "structures" / "orphan"
    empty_dir.mkdir(parents=True)
    warnings: list[str] = []

    monkeypatch.setattr("ui.main_window.STRUCTURES_FOLDER", tmp_path / "structures")
    monkeypatch.setattr(
        "ui.main_window.QFileDialog.getExistingDirectory",
        lambda *_a, **_k: str(empty_dir),
    )
    monkeypatch.setattr(
        "ui.main_window.QMessageBox.warning",
        lambda _parent, _title, text: warnings.append(text),
    )

    assert _pick_structure_stage(None) is None
    assert warnings
    assert "No valid stages found" in warnings[0]


def test_restart_editor_allows_open_during_preview_render(monkeypatch):
    from ui.main_window import MainWindow

    calls: list[tuple[str, int]] = []
    monkeypatch.setattr(
        "ui.main_window.open_structure_in_editor_process",
        lambda structure, stage: calls.append((structure, stage)),
    )
    monkeypatch.setattr("ui.main_window.clear_preview_session_dir", lambda *_a, **_k: None)

    window = MainWindow.__new__(MainWindow)
    window._render_thread = object()
    window._render_is_preview = True
    window._preview_session_id = "test-session"
    window._preview_stale = False

    MainWindow._restart_editor_for_structure(window, "well", 2)
    assert calls == [("well", 2)]


def test_restart_editor_blocks_open_during_export_render(monkeypatch):
    from ui.main_window import MainWindow

    calls: list[tuple[str, int]] = []
    warnings: list[str] = []
    monkeypatch.setattr(
        "ui.main_window.open_structure_in_editor_process",
        lambda structure, stage: calls.append((structure, stage)),
    )
    monkeypatch.setattr(
        "ui.main_window.QMessageBox.warning",
        lambda _parent, _title, text: warnings.append(text),
    )

    window = MainWindow.__new__(MainWindow)
    window._render_thread = object()
    window._render_is_preview = False

    MainWindow._restart_editor_for_structure(window, "well", 2)
    assert calls == []
    assert warnings
    assert "opening another structure" in warnings[0]


def test_on_open_structure_informs_when_already_editing_target(monkeypatch):
    from ui.main_window import MainWindow

    messages: list[str] = []
    restart_calls: list[tuple[str, int]] = []

    monkeypatch.setattr("ui.main_window._pick_structure_stage", lambda _parent: ("residence", 1))
    monkeypatch.setattr("ui.main_window.add_recent_structure", lambda *_a, **_k: None)

    window = MainWindow.__new__(MainWindow)
    window._structure = "residence"
    window._stage = 1
    window._document = type("_Doc", (), {"metadata": {"structure": "residence", "stage": 1}})()
    window._dirty_layers = set()
    window._dirty_structure = False
    window._status = type(
        "_Status",
        (),
        {"showMessage": lambda self, message, *_args, **_kwargs: messages.append(message)},
    )()
    window._restart_editor_for_structure = lambda structure, stage: restart_calls.append(
        (structure, stage)
    )

    MainWindow._on_open_structure(window)
    assert restart_calls == []
    assert messages
    assert "Already editing residence stage 1" in messages[0]


def test_open_recent_entry_informs_when_already_editing_target(monkeypatch):
    from ui.main_window import MainWindow

    messages: list[str] = []
    restart_calls: list[tuple[str, int]] = []

    monkeypatch.setattr("ui.main_window.add_recent_structure", lambda *_a, **_k: None)

    window = MainWindow.__new__(MainWindow)
    window._structure = "residence"
    window._stage = 1
    window._document = type("_Doc", (), {"metadata": {"structure": "residence", "stage": 1}})()
    window._dirty_layers = set()
    window._dirty_structure = False
    window._status = type(
        "_Status",
        (),
        {"showMessage": lambda self, message, *_args, **_kwargs: messages.append(message)},
    )()
    window._restart_editor_for_structure = lambda structure, stage: restart_calls.append(
        (structure, stage)
    )

    MainWindow._open_recent_entry(window, "residence", 1)
    assert restart_calls == []
    assert messages
    assert "Already editing residence stage 1" in messages[0]


def _inspector_apply_stub_window():
    from PySide6.QtWidgets import QApplication

    from ui.main_window import MainWindow
    from ui.widgets.properties_panel import PropertiesPanel

    if QApplication.instance() is None:
        QApplication([])

    window = MainWindow.__new__(MainWindow)
    window._eraser_active = False
    window._current_layer_index = 0
    window._document = type(
        "_Doc",
        (),
        {"layers": [{"cells": [["SLAB:cobblestone#top"]]}]},
    )()
    window._properties_panel = PropertiesPanel()
    window._structure_tab_active = lambda: True
    return window


def test_apply_inspector_to_selected_slab_variant_updates_cell():
    from helpers.block_picker import picker_entry_for_token
    from ui.main_window import MainWindow

    window = _inspector_apply_stub_window()
    set_cell_calls: list[tuple[int, int, str]] = []
    window._set_cell = lambda row, col, token, **kwargs: set_cell_calls.append((row, col, token))

    entry = picker_entry_for_token("SLAB")
    assert entry is not None
    window._properties_panel.show_picker_entry(entry, emit_brush=False)
    window._properties_panel.show_grid_cell(0, 0, "SLAB:cobblestone#top")
    window._properties_panel.sync_brush_from_cell("SLAB:cobblestone#top")

    window._properties_panel._variant_combo.setCurrentText("(default)")
    MainWindow._apply_inspector_to_selected_cell(window)

    assert set_cell_calls == [(0, 0, "SLAB:cobblestone")]


def test_apply_inspector_skips_when_palette_entry_does_not_match_cell():
    from helpers.block_picker import picker_entry_for_token
    from ui.main_window import MainWindow

    window = _inspector_apply_stub_window()
    set_cell_calls: list[tuple[int, int, str]] = []
    window._set_cell = lambda row, col, token, **kwargs: set_cell_calls.append((row, col, token))

    slab_entry = picker_entry_for_token("SLAB")
    planks_entry = picker_entry_for_token("PLANKS")
    assert slab_entry is not None and planks_entry is not None

    window._properties_panel.show_picker_entry(slab_entry, emit_brush=False)
    window._properties_panel.show_grid_cell(0, 0, "SLAB:cobblestone#top")
    window._properties_panel.show_picker_entry(planks_entry, emit_brush=True)

    window._properties_panel._material_combo.setCurrentIndex(1)
    MainWindow._apply_inspector_to_selected_cell(window)

    assert set_cell_calls == []


def test_apply_inspector_trapdoor_open_uses_build_placement_token():
    from helpers.block_picker import picker_entry_for_token
    from ui.main_window import MainWindow

    window = _inspector_apply_stub_window()
    window._document.layers[0]["cells"][0][0] = "TRAPDOOR:oak@south;open=false"
    set_cell_calls: list[tuple[int, int, str]] = []
    window._set_cell = lambda row, col, token, **kwargs: set_cell_calls.append((row, col, token))

    entry = picker_entry_for_token("TRAPDOOR")
    assert entry is not None
    window._properties_panel.show_picker_entry(
        entry,
        emit_brush=False,
        brush_token="TRAPDOOR:oak@south;open=false",
    )
    window._properties_panel.show_grid_cell(0, 0, "TRAPDOOR:oak@south;open=false")

    window._properties_panel._open_combo.setCurrentText("true")
    MainWindow._apply_inspector_to_selected_cell(window)

    assert set_cell_calls == [(0, 0, "TRAPDOOR:oak@south;open=true")]


def test_main_window_viewer_hud_properties_and_f3_wired():
    from unittest.mock import MagicMock

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from ui.main_window import MainWindow

    application = QApplication.instance() or QApplication([])
    _ = application

    window = MainWindow.__new__(MainWindow)
    QMainWindow.__init__(window)
    window._preview_panel = MagicMock()
    window._preview_panel.is_3d_mode.return_value = False
    window._tabs = MagicMock()
    window._tabs.currentIndex.return_value = 0
    MainWindow._init_viewer_menu(window)

    assert hasattr(window, "_viewer_hud_properties_action")
    assert window._viewer_hud_properties_action.toolTip() == "HUD Properties"
    assert window._viewer_camera_hud_action.toolTip() == "Show HUD panel"
    assert hasattr(window, "_viewer_hud_f3_shortcut")
    assert window._viewer_hud_f3_shortcut.key() == Qt.Key.Key_F3


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
