from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from helpers.block_picker import picker_entry_for_block_id, picker_entry_for_token
from ui.widgets.properties_panel import PropertiesPanel

pytest.importorskip("PySide6")


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_show_picker_entry_brush_token_preserves_slab_material(qapp):
    panel = PropertiesPanel()
    entry = picker_entry_for_token("SLAB")
    assert entry is not None

    emissions: list[str] = []
    panel.brush_changed.connect(lambda: emissions.append(panel.build_placement_token() or ""))

    panel.show_picker_entry(entry, brush_token="SLAB:cobblestone#top")

    assert panel._material_combo.currentText() == "cobblestone"
    assert panel._variant_combo.currentText() == "top"
    assert panel.build_placement_token() == "SLAB:cobblestone#top"
    assert emissions == ["SLAB:cobblestone#top"]


def test_show_picker_entry_without_brush_token_uses_material_default(qapp):
    panel = PropertiesPanel()
    entry = picker_entry_for_token("SLAB")
    assert entry is not None

    panel.show_picker_entry(entry, emit_brush=False)

    assert panel._material_combo.currentText() == entry.material_default
    assert panel.build_placement_token() == f"SLAB:{entry.material_default}"


def test_show_picker_entry_brush_token_preserves_stairs_material_and_direction(qapp):
    panel = PropertiesPanel()
    entry = picker_entry_for_token("STAIRS")
    assert entry is not None

    panel.show_picker_entry(
        entry,
        emit_brush=False,
        brush_token="STAIRS:cobblestone@east#outer_left",
    )

    assert panel._material_combo.currentText() == "cobblestone"
    assert panel._direction_combo.currentText() == "east"
    assert panel._variant_combo.currentText() == "outer_left"
    assert panel.build_placement_token() == "STAIRS:cobblestone@east#outer_left"


def test_show_grid_cell_emits_active_cell_changed(qapp):
    panel = PropertiesPanel()
    emissions: list[tuple[int, int]] = []
    panel.active_cell_changed.connect(lambda row, col: emissions.append((row, col)))

    panel.show_grid_cell(2, 3, "PLANKS:oak")

    assert emissions == [(2, 3)]
    assert panel.selected_cell() == (2, 3)


def test_clear_grid_cell_emits_active_cell_cleared(qapp):
    panel = PropertiesPanel()
    cleared: list[bool] = []
    panel.active_cell_cleared.connect(lambda: cleared.append(True))

    panel.show_grid_cell(0, 0, ".")
    panel.clear_grid_cell()

    assert cleared == [True]
    assert panel.selected_cell() is None


def test_trapdoor_open_state_in_build_placement_token(qapp):
    panel = PropertiesPanel()
    entry = picker_entry_for_token("TRAPDOOR")
    assert entry is not None

    panel.show_picker_entry(entry, emit_brush=False)
    assert panel.build_placement_token() == "TRAPDOOR:oak@north;open=false"

    panel._open_combo.setCurrentText("true")
    assert panel.build_placement_token() == "TRAPDOOR:oak@north;open=true"


def test_campfire_facing_and_lit_in_build_placement_token(qapp):
    panel = PropertiesPanel()
    entry = picker_entry_for_block_id("minecraft:campfire", palette="lighting")

    panel.show_picker_entry(entry, emit_brush=False)
    assert panel.build_placement_token() == "minecraft:campfire@north;lit=true"

    panel._direction_combo.setCurrentText("west")
    panel._lit_combo.setCurrentText("false")
    assert panel.build_placement_token() == "minecraft:campfire@west;lit=false"


def test_show_picker_entry_trapdoor_brush_token_preserves_open_state(qapp):
    panel = PropertiesPanel()
    entry = picker_entry_for_token("TRAPDOOR")
    assert entry is not None

    panel.show_picker_entry(
        entry,
        emit_brush=False,
        brush_token="TRAPDOOR:spruce@west;open=true",
    )

    assert panel._material_combo.currentText() == "spruce"
    assert panel._direction_combo.currentText() == "west"
    assert panel._open_combo.currentText() == "true"
    assert panel.build_placement_token() == "TRAPDOOR:spruce@west;open=true"


def test_brush_inspector_changed_emits_on_variant_combo_not_on_picker_entry(qapp):
    panel = PropertiesPanel()
    entry = picker_entry_for_token("SLAB")
    assert entry is not None

    inspector_signals: list[bool] = []
    panel.brush_inspector_changed.connect(lambda: inspector_signals.append(True))

    panel.show_picker_entry(entry, brush_token="SLAB:cobblestone#top")
    assert inspector_signals == []

    panel._variant_combo.setCurrentText("(default)")
    assert inspector_signals == [True]
    assert panel.build_placement_token() == "SLAB:cobblestone"
