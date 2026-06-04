import pytest

from helpers.grid_labels import (
    column_axis_label,
    grid_axis_position,
    grid_axis_selection_range,
    row_axis_label,
)


def test_column_axis_label():
    assert column_axis_label(0) == "0"
    assert column_axis_label(12) == "12"


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        (0, "A"),
        (1, "B"),
        (25, "Z"),
        (26, "AA"),
        (27, "AB"),
        (701, "ZZ"),
        (702, "AAA"),
    ],
)
def test_row_axis_label(row: int, expected: str) -> None:
    assert row_axis_label(row) == expected


@pytest.mark.parametrize(
    ("row", "col", "expected"),
    [
        (0, 0, "A0"),
        (0, 8, "A8"),
        (2, 12, "C12"),
        (26, 1, "AA1"),
    ],
)
def test_grid_axis_position(row: int, col: int, expected: str) -> None:
    assert grid_axis_position(row, col) == expected


def test_grid_axis_selection_range_empty():
    assert grid_axis_selection_range([]) == "—"


def test_grid_axis_selection_range_single():
    assert grid_axis_selection_range([(1, 1)]) == "B1"


def test_grid_axis_selection_range_box():
    positions = [(row, col) for row in range(1, 5) for col in range(1, 6)]
    assert grid_axis_selection_range(positions) == "B1: E5"
