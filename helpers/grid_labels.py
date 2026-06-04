"""Axis labels for structure layer grids (column numbers, row letters)."""

from __future__ import annotations


def column_axis_label(col: int) -> str:
    """Numeric label for a grid column (0-based index)."""
    return str(col)


def row_axis_label(row: int) -> str:
    """Spreadsheet-style letter label for a grid row (0 -> A, 26 -> AA)."""
    if row < 0:
        raise ValueError("row must be non-negative")

    n = row + 1
    letters: list[str] = []

    while n > 0:
        n, remainder = divmod(n - 1, 26)
        letters.append(chr(ord("A") + remainder))

    return "".join(reversed(letters))


def grid_axis_position(row: int, col: int) -> str:
    """Cell address matching structure grid headers (row letter + column number)."""
    return f"{row_axis_label(row)}{column_axis_label(col)}"


def grid_axis_selection_range(positions: list[tuple[int, int]]) -> str:
    """Bounding box of selected cells as ``A0`` or ``B1: E5``."""
    if not positions:
        return "—"

    rows = [row for row, _col in positions]
    cols = [col for _row, col in positions]
    start = grid_axis_position(min(rows), min(cols))
    end = grid_axis_position(max(rows), max(cols))

    if start == end:
        return start

    return f"{start}: {end}"
