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
