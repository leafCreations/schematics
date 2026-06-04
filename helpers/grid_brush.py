"""Grid brush geometry for structure-layer editing."""

from __future__ import annotations

from typing import Literal

PaintBrushMode = Literal["fill", "outline"]


def square_cell_indices(
    center_row: int,
    center_col: int,
    size: int,
    *,
    rows: int,
    cols: int,
) -> list[tuple[int, int]]:
    """Return ``(row, col)`` pairs in a square brush centered on the click cell."""
    if size < 1:
        size = 1

    row_lo = max(0, center_row - (size - 1) // 2)
    row_hi = min(rows - 1, center_row + size // 2)
    col_lo = max(0, center_col - (size - 1) // 2)
    col_hi = min(cols - 1, center_col + size // 2)

    return [(row, col) for row in range(row_lo, row_hi + 1) for col in range(col_lo, col_hi + 1)]


def rect_cell_indices(
    row_a: int,
    col_a: int,
    row_b: int,
    col_b: int,
    *,
    rows: int,
    cols: int,
) -> list[tuple[int, int]]:
    """Return all cells in the axis-aligned rectangle between two corners."""
    row_lo = max(0, min(row_a, row_b))
    row_hi = min(rows - 1, max(row_a, row_b))
    col_lo = max(0, min(col_a, col_b))
    col_hi = min(cols - 1, max(col_a, col_b))

    return [(row, col) for row in range(row_lo, row_hi + 1) for col in range(col_lo, col_hi + 1)]


def outline_rect_cell_indices(
    row_a: int,
    col_a: int,
    row_b: int,
    col_b: int,
    *,
    rows: int,
    cols: int,
) -> list[tuple[int, int]]:
    """Return perimeter cells of the axis-aligned rectangle between two corners."""
    row_lo = max(0, min(row_a, row_b))
    row_hi = min(rows - 1, max(row_a, row_b))
    col_lo = max(0, min(col_a, col_b))
    col_hi = min(cols - 1, max(col_a, col_b))

    return [
        (row, col)
        for row in range(row_lo, row_hi + 1)
        for col in range(col_lo, col_hi + 1)
        if row in (row_lo, row_hi) or col in (col_lo, col_hi)
    ]


def region_cell_indices(
    row_a: int,
    col_a: int,
    row_b: int,
    col_b: int,
    *,
    rows: int,
    cols: int,
    mode: PaintBrushMode = "fill",
) -> list[tuple[int, int]]:
    if mode == "outline":
        return outline_rect_cell_indices(
            row_a,
            col_a,
            row_b,
            col_b,
            rows=rows,
            cols=cols,
        )

    return rect_cell_indices(row_a, col_a, row_b, col_b, rows=rows, cols=cols)
