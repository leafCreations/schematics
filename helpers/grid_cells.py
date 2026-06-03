"""Resize structure layer cell grids."""

from __future__ import annotations


def empty_cells(width: int, depth: int) -> list[list[str]]:
    if width < 1 or depth < 1:
        raise ValueError("Structure width and depth must be at least 1")

    return [["." for _ in range(width)] for _ in range(depth)]


def resize_cells(
    cells: list[list[str]],
    width: int,
    depth: int,
) -> list[list[str]]:
    """Resize a layer grid to ``width`` (x) by ``depth`` (z).

    Grows by padding with ``.`` on the east and south. Shrinks by removing
    columns and rows from the east and south.
    """
    if width < 1 or depth < 1:
        raise ValueError("Structure width and depth must be at least 1")

    if not cells:
        return empty_cells(width, depth)

    current_depth = len(cells)

    resized: list[list[str]] = []

    for z in range(depth):
        if z < current_depth:
            row = cells[z]
            new_row = list(row[:width])

            if len(new_row) < width:
                new_row.extend(["."] * (width - len(new_row)))
        else:
            new_row = ["."] * width

        resized.append(new_row)

    return resized


def count_cells_trimmed_by_resize(
    cells: list[list[str]],
    width: int,
    depth: int,
) -> int:
    """Count non-empty cells that would be removed when shrinking."""
    if not cells:
        return 0

    trimmed = 0

    for z, row in enumerate(cells):
        for x, cell in enumerate(row):
            if cell == ".":
                continue

            if x >= width or z >= depth:
                trimmed += 1

    return trimmed


def resize_structure_layers(
    layers: list[dict],
    width: int,
    depth: int,
) -> None:
    for layer in layers:
        cells = layer.get("cells", [])
        layer["cells"] = resize_cells(cells, width, depth)
