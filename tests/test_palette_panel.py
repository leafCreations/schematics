from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from helpers.block_picker import picker_entry_for_token
from ui.widgets.palette_panel import PalettePanel

pytest.importorskip("PySide6")


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_select_entry_does_not_emit_entry_selected(qapp):
    panel = PalettePanel()
    entry = picker_entry_for_token("SLAB")
    assert entry is not None

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
