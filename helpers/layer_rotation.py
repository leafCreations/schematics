"""Rotate structure layer cell grids (top-down, north-up)."""

from __future__ import annotations

from helpers.structure_tokens import (
    EMPTY_CELL,
    ParsedToken,
    format_structure_token,
    parse_structure_token,
)

_DIRECTION_CW = {
    "north": "east",
    "east": "south",
    "south": "west",
    "west": "north",
}

_DIRECTION_CCW = {
    "north": "west",
    "west": "south",
    "south": "east",
    "east": "north",
}


def _normalize_cells(cells: list[list[str]]) -> list[list[str]]:
    if not cells:
        return [[EMPTY_CELL]]

    width = max(len(row) for row in cells)

    return [list(row) + [EMPTY_CELL] * (width - len(row)) for row in cells]


def _rotate_direction(direction: str | None, *, clockwise: bool) -> str | None:
    if not direction:
        return None

    table = _DIRECTION_CW if clockwise else _DIRECTION_CCW
    rotated = table.get(direction.lower())

    if rotated is None:
        return direction

    if direction.isupper():
        return rotated.upper()

    if direction[0].isupper():
        return rotated.capitalize()

    return rotated


def rotate_cell_token(raw: str, *, clockwise: bool) -> str:
    """Rotate a single cell token with the layer (position + facing)."""
    if raw == EMPTY_CELL:
        return raw

    parsed = parse_structure_token(raw)

    if parsed is None:
        return raw

    rotation = parsed.rotation

    if rotation:
        delta = 90 if clockwise else -90
        rotation = (rotation + delta) % 360

    return format_structure_token(
        ParsedToken(
            token=parsed.token,
            material=parsed.material,
            direction=_rotate_direction(parsed.direction, clockwise=clockwise),
            variant=parsed.variant,
            rotation=rotation,
            states=parsed.states,
        )
    )


def rotate_layer_cells(cells: list[list[str]], *, clockwise: bool) -> list[list[str]]:
    """Rotate the full layer grid 90° (clockwise or counter-clockwise when viewed from above)."""
    normalized = _normalize_cells(cells)
    depth = len(normalized)
    width = len(normalized[0])

    if clockwise:
        rotated: list[list[str]] = [[EMPTY_CELL] * depth for _ in range(width)]

        for row in range(depth):
            for col in range(width):
                rotated[col][depth - 1 - row] = rotate_cell_token(
                    normalized[row][col],
                    clockwise=True,
                )

        return rotated

    rotated = [[EMPTY_CELL] * depth for _ in range(width)]

    for row in range(depth):
        for col in range(width):
            rotated[width - 1 - col][row] = rotate_cell_token(
                normalized[row][col],
                clockwise=False,
            )

    return rotated
