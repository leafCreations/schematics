"""Copy/paste rectangular regions of structure layer cells."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CellRegionClipboard:
    """Copied cell tokens in row-major order (includes '.' for gaps in the selection)."""

    cells: tuple[tuple[str, ...], ...]

    @property
    def height(self) -> int:
        return len(self.cells)

    @property
    def width(self) -> int:
        if not self.cells:
            return 0

        return len(self.cells[0])


def copy_region(
    layer_cells: list[list[str]],
    positions: list[tuple[int, int]],
) -> CellRegionClipboard | None:
    if not positions:
        return None

    rows = [row for row, _col in positions]
    cols = [col for _row, col in positions]
    min_row, max_row = min(rows), max(rows)
    min_col, max_col = min(cols), max(cols)
    selected = set(positions)
    region: list[tuple[str, ...]] = []

    for row in range(min_row, max_row + 1):
        line = tuple(
            layer_cells[row][col] if (row, col) in selected else "."
            for col in range(min_col, max_col + 1)
        )
        region.append(line)

    return CellRegionClipboard(cells=tuple(region))


def paste_region(
    layer_cells: list[list[str]],
    clipboard: CellRegionClipboard,
    dest_row: int,
    dest_col: int,
) -> list[tuple[int, int, str]]:
    """Return ``(row, col, token)`` updates that fit inside the layer."""
    depth = len(layer_cells)
    width = len(layer_cells[0]) if layer_cells else 0
    changes: list[tuple[int, int, str]] = []

    for delta_row, row_tokens in enumerate(clipboard.cells):
        target_row = dest_row + delta_row

        if target_row < 0 or target_row >= depth:
            continue

        for delta_col, token in enumerate(row_tokens):
            target_col = dest_col + delta_col

            if target_col < 0 or target_col >= width:
                continue

            if layer_cells[target_row][target_col] != token:
                changes.append((target_row, target_col, token))

    return changes


def move_region(
    layer_cells: list[list[str]],
    positions: list[tuple[int, int]],
    dest_row: int,
    dest_col: int,
) -> list[tuple[int, int, str]]:
    """Cut a rectangular selection and paste it with top-left at ``dest_row``/``dest_col``."""
    clipboard = copy_region(layer_cells, positions)

    if clipboard is None:
        return []

    rows = [row for row, _col in positions]
    cols = [col for _row, col in positions]
    origin_row, origin_col = min(rows), min(cols)

    if dest_row == origin_row and dest_col == origin_col:
        return []

    if not any(token != "." for row in clipboard.cells for token in row):
        return []

    changes: list[tuple[int, int, str]] = []

    for row, col in positions:
        if layer_cells[row][col] != ".":
            changes.append((row, col, "."))

    scratch = [list(row) for row in layer_cells]

    for row, col, token in changes:
        scratch[row][col] = token

    changes.extend(paste_region(scratch, clipboard, dest_row, dest_col))
    return changes
