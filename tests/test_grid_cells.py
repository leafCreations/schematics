import pytest

from helpers.grid_cells import (
    count_cells_trimmed_by_resize,
    empty_cells,
    occupied_cell_positions,
    resize_cells,
    resize_structure_layers,
)
from helpers.grid_placement import structure_site_size_error


def test_resize_cells_grows_with_dots():
    cells = [["A", "."], [".", "B"]]
    resized = resize_cells(cells, 3, 3)

    assert resized == [
        ["A", ".", "."],
        [".", "B", "."],
        [".", ".", "."],
    ]


def test_resize_cells_shrinks_from_east_and_south():
    cells = [["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]]
    resized = resize_cells(cells, 2, 2)

    assert resized == [["A", "B"], ["D", "E"]]


def test_count_cells_trimmed_by_resize():
    cells = [["A", "B"], ["C", "."]]
    assert count_cells_trimmed_by_resize(cells, 2, 2) == 0
    assert count_cells_trimmed_by_resize(cells, 1, 2) == 1
    assert count_cells_trimmed_by_resize(cells, 2, 1) == 1


def test_resize_structure_layers_updates_every_layer():
    layers = [
        {"cells": [["A", "."], [".", "."]]},
        {"cells": [[".", "B"], [".", "."]]},
    ]
    resize_structure_layers(layers, 3, 1)

    assert layers[0]["cells"] == [["A", ".", "."]]
    assert layers[1]["cells"] == [[".", "B", "."]]


def test_occupied_cell_positions():
    cells = [["A", "."], [".", "B"]]
    assert occupied_cell_positions(cells) == [(0, 0), (1, 1)]


def test_occupied_cell_positions_empty_layer():
    assert occupied_cell_positions([[".", "."]]) == []


def test_empty_cells_minimum_size():
    assert empty_cells(1, 1) == [["."]]


def test_resize_cells_rejects_invalid_size():
    with pytest.raises(ValueError, match="at least 1"):
        resize_cells([], 0, 1)


def test_structure_site_size_error():
    assert structure_site_size_error(10, 5, 30, 30) is None
    err = structure_site_size_error(31, 5, 30, 30)
    assert err is not None
    assert "cannot be larger" in err
