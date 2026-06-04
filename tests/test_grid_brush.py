from helpers.grid_brush import (
    outline_rect_cell_indices,
    rect_cell_indices,
    region_cell_indices,
    square_cell_indices,
)


def test_square_cell_indices_size_one():
    assert square_cell_indices(2, 3, 1, rows=5, cols=5) == [(2, 3)]


def test_square_cell_indices_size_three_centered():
    assert set(square_cell_indices(2, 2, 3, rows=5, cols=5)) == {
        (1, 1),
        (1, 2),
        (1, 3),
        (2, 1),
        (2, 2),
        (2, 3),
        (3, 1),
        (3, 2),
        (3, 3),
    }


def test_outline_rect_cell_indices():
    indices = outline_rect_cell_indices(1, 1, 3, 3, rows=5, cols=5)
    assert (1, 1) in indices
    assert (3, 3) in indices
    assert (2, 2) not in indices
    assert len(indices) == 8


def test_region_cell_indices_outline_mode():
    fill = region_cell_indices(0, 0, 2, 2, rows=5, cols=5, mode="fill")
    outline = region_cell_indices(0, 0, 2, 2, rows=5, cols=5, mode="outline")
    assert len(fill) == 9
    assert len(outline) == 8


def test_rect_cell_indices():
    indices = rect_cell_indices(1, 2, 3, 4, rows=5, cols=6)
    assert (1, 2) in indices
    assert (3, 4) in indices
    assert (2, 3) in indices
    assert len(indices) == 9  # 3 rows × 3 cols (inclusive corners)


def test_square_cell_indices_clamps_to_grid():
    indices = square_cell_indices(0, 0, 5, rows=3, cols=3)
    assert indices
    assert all(0 <= row < 3 and 0 <= col < 3 for row, col in indices)
