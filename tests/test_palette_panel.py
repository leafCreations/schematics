from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from helpers.block_picker import picker_entry_for_token
from tests.palette_helpers import palette_section_entry_counts, terrain_section_entry_counts
from ui.widgets.palette_panel import PalettePanel

pytest.importorskip("PySide6")


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _panel_entry(panel: PalettePanel, palette_name: str, token: str):
    palette = panel._palettes_by_name[palette_name]
    return next(entry for entry in palette.entries if entry.token == token)


def test_select_entry_does_not_emit_entry_selected(qapp):
    panel = PalettePanel()
    entry = _panel_entry(panel, "building", "SLAB")

    emissions: list[object] = []
    panel.entry_selected.connect(emissions.append)

    panel.select_entry(entry)

    assert emissions == []
    assert panel._block_list.currentItem() is not None
    assert panel._block_list.currentItem().data(256) == entry


def test_category_change_does_not_emit_entry_selected(qapp):
    panel = PalettePanel()
    stairs = picker_entry_for_token("STAIRS")
    assert stairs is not None

    emissions: list[object] = []
    panel.entry_selected.connect(emissions.append)

    building_index = panel._category_combo.findData("building")
    assert building_index >= 0
    panel._category_combo.setCurrentIndex(building_index)

    assert emissions == []
    assert panel._block_list.currentItem() is None


def test_terrain_palette_shows_dimension_filter(qapp):
    panel = PalettePanel()
    section_counts = terrain_section_entry_counts()
    terrain_index = panel._category_combo.findData("terrain")
    assert terrain_index >= 0

    panel._category_combo.setCurrentIndex(terrain_index)

    assert panel._dimension_combo.count() == 3
    assert panel._dimension_combo.currentData() == "overworld"
    assert panel._block_list.count() == section_counts["overworld"]
    assert panel._block_list.count() > 0


def test_natural_palette_shows_dimension_filter(qapp):
    panel = PalettePanel()
    section_counts = palette_section_entry_counts("natural")
    natural_index = panel._category_combo.findData("natural")
    assert natural_index >= 0

    panel._category_combo.setCurrentIndex(natural_index)

    assert panel._dimension_combo.count() == 4
    assert panel._dimension_combo.currentData() == "overworld"
    assert panel._block_list.count() == section_counts["overworld"]
    assert panel._block_list.count() > 0


def test_natural_palette_defaults_to_site_dimension(qapp):
    panel = PalettePanel()
    section_counts = palette_section_entry_counts("natural")
    panel.set_site_dimension("end")

    natural_index = panel._category_combo.findData("natural")
    assert natural_index >= 0

    panel._category_combo.setCurrentIndex(natural_index)

    assert panel._dimension_combo.currentData() == "end"
    assert panel._block_list.count() == section_counts["end"]
    assert panel._block_list.count() > 0


def test_ore_palette_shows_dimension_filter(qapp):
    panel = PalettePanel()
    section_counts = palette_section_entry_counts("ore")
    ore_index = panel._category_combo.findData("ore")
    assert ore_index >= 0

    panel._category_combo.setCurrentIndex(ore_index)

    assert panel._dimension_combo.count() == 3
    assert panel._dimension_combo.currentData() == "overworld"
    assert panel._block_list.count() == section_counts["overworld"]
    assert panel._block_list.count() > 0


def test_palette_defaults_to_site_dimension(qapp):
    panel = PalettePanel()
    section_counts = terrain_section_entry_counts()
    panel.set_site_dimension("nether")

    terrain_index = panel._category_combo.findData("terrain")
    assert terrain_index >= 0

    panel._category_combo.setCurrentIndex(terrain_index)

    assert panel._dimension_combo.currentData() == "nether"
    assert panel._block_list.count() == section_counts["nether"]
    assert panel._block_list.count() > 0


def test_category_blocks_are_sorted_alphabetically(qapp):
    panel = PalettePanel()
    terrain_index = panel._category_combo.findData("terrain")
    assert terrain_index >= 0

    panel._category_combo.setCurrentIndex(terrain_index)

    labels = [panel._block_list.item(row).text() for row in range(panel._block_list.count())]
    assert labels == sorted(labels, key=str.casefold)


def test_search_replaces_block_list_globally(qapp):
    panel = PalettePanel()
    building_index = panel._category_combo.findData("building")
    assert building_index >= 0

    panel._category_combo.setCurrentIndex(building_index)
    panel._search_edit.setText("cobblestone")

    assert panel._category_combo.isHidden()
    assert panel._block_list.count() > 0

    block_count = panel._block_list.count()
    tokens = {panel._block_list.item(row).data(256).token for row in range(block_count)}
    assert "minecraft:cobblestone" in tokens

    labels = [panel._block_list.item(row).text() for row in range(panel._block_list.count())]
    assert any("Natural" in label or "Terrain" in label for label in labels)


def test_search_finds_terrain_variant_without_category(qapp):
    panel = PalettePanel()
    panel._search_edit.setText("smooth stone")

    entries = [panel._block_list.item(row).data(256) for row in range(panel._block_list.count())]
    assert any(entry.token == "minecraft:stone" for entry in entries)
    assert all(entry.palette == "natural" for entry in entries if entry.token == "minecraft:stone")


def test_clearing_search_restores_category_browsing(qapp):
    panel = PalettePanel()
    building_index = panel._category_combo.findData("building")
    assert building_index >= 0

    panel._category_combo.setCurrentIndex(building_index)
    building_count = panel._block_list.count()

    panel._search_edit.setText("slab")
    assert panel._block_list.count() != building_count

    panel._search_edit.clear()
    assert not panel._category_combo.isHidden()
    assert panel._block_list.count() == building_count


def test_select_entry_clears_search_when_filtered_out(qapp):
    panel = PalettePanel()
    entry = _panel_entry(panel, "building", "SLAB")

    panel._search_edit.setText("zzznomatch")
    panel.select_entry(entry)

    assert panel._search_edit.text() == ""
    assert panel._block_list.currentItem() is not None


def test_select_entry_highlights_match_during_search(qapp):
    panel = PalettePanel()
    cobblestone = _panel_entry(panel, "natural", "minecraft:cobblestone")
    panel._search_edit.setText("cobblestone")

    panel.select_entry(cobblestone)

    assert panel._search_edit.text() == "cobblestone"
    assert panel._block_list.currentItem() is not None
    assert panel._block_list.currentItem().data(256) == cobblestone


def test_palette_panel_filters_26_2_blocks_for_26_1_2(qapp):
    panel = PalettePanel()
    panel.set_structure_version("26.1.2")

    palette = panel._palettes_by_name["natural"]
    catalog_blocks = {entry.token for entry in palette.entries if entry.is_catalog_block}

    assert "minecraft:cinnabar" not in catalog_blocks
    assert "minecraft:sulfur" not in catalog_blocks
    assert "minecraft:stone_bricks" in catalog_blocks
