from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from ui.widgets.grid import LayerGridWidget

pytest.importorskip("PySide6")


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_paint_drag_end_cell_without_move_uses_anchor(qapp):
    grid = LayerGridWidget()
    grid._paint_drag_anchor = (4, 7)
    grid._paint_drag_moved = False

    end_row, end_col = grid._paint_drag_end_cell(grid.viewport().rect().center())

    assert (end_row, end_col) == (4, 7)


def test_paint_drag_end_cell_with_move_uses_release_index(qapp):
    grid = LayerGridWidget()
    grid.set_layer_cells([[".", ".", "."], [".", ".", "."], [".", ".", "."]])
    grid.show()
    qapp.processEvents()

    grid._paint_drag_anchor = (0, 0)
    grid._paint_drag_moved = True

    item = grid.item(2, 2)
    assert item is not None
    center = grid.visualItemRect(item).center()

    end_row, end_col = grid._paint_drag_end_cell(center)

    assert (end_row, end_col) == (2, 2)
    grid.close()


def test_active_cell_tracking(qapp):
    grid = LayerGridWidget()
    grid.set_layer_cells([["PLANKS:oak", "."], [".", "."]])

    assert grid.active_cell() is None

    grid.set_active_cell(0, 0)
    assert grid.active_cell() == (0, 0)
    assert grid.is_active_cell(0, 0)
    assert not grid.is_active_cell(1, 0)

    grid.set_active_cell(0, 0)
    grid.set_active_cell(1, 0)
    assert grid.active_cell() == (1, 0)

    grid.clear_active_cell()
    assert grid.active_cell() is None
