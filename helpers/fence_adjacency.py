from __future__ import annotations

from helpers.cells import get_cell
from helpers.registry_blocks import get_block_behavior
from helpers.registry_lookup import get_block_entry
from helpers.structure_tokens import ParsedToken, parse_structure_token
from helpers.types import CellGrid, RawToken

DIRECTION_OFFSETS = {
    "north": (0, -1),
    "south": (0, 1),
    "east": (1, 0),
    "west": (-1, 0),
}

FENCE_CONNECTABLE_BEHAVIORS = frozenset(
    {
        "solid",
        "facing_block",
        "fence",
        "log",
        "slab",
        "stairs",
        "door",
        "bed",
        "chest",
    }
)

FENCE_VARIANTS = frozenset({"post", "end", "straight", "corner", "tee", "cross"})

_CARDINAL_ORDER = ("north", "east", "south", "west")

_CANONICAL_CONNECTIONS = {
    "post": frozenset(),
    "end": frozenset({"north"}),
    "straight": frozenset({"north", "south"}),
    "corner": frozenset({"north", "east"}),
    "tee": frozenset({"north", "east", "south"}),
    "cross": frozenset({"north", "east", "south", "west"}),
}


def should_fence_connect(raw_neighbor: RawToken | None) -> bool:
    if raw_neighbor is None:
        return False

    parsed_neighbor = parse_structure_token(raw_neighbor)

    if parsed_neighbor is None:
        return False

    entry = get_block_entry(parsed_neighbor)

    if entry is None:
        return False

    return get_block_behavior(entry) in FENCE_CONNECTABLE_BEHAVIORS


def resolve_fence_connections(
    cells: CellGrid,
    x: int,
    z: int,
) -> frozenset[str]:
    return frozenset(
        direction
        for direction, (dx, dz) in DIRECTION_OFFSETS.items()
        if should_fence_connect(get_cell(cells, x + dx, z + dz, empty=None))
    )


def classify_fence_variant(connections: frozenset[str]) -> str:
    count = len(connections)

    if count == 0:
        return "post"

    if count == 4:
        return "cross"

    if count == 1:
        return "end"

    if count == 2:
        if {"north", "south"}.issubset(connections) or {"east", "west"}.issubset(connections):
            return "straight"

        return "corner"

    if count == 3:
        return "tee"

    raise ValueError(f"Unsupported fence connection set: {sorted(connections)}")


def _rotate_connections(connections: frozenset[str], steps: int) -> frozenset[str]:
    if not connections:
        return connections

    order = _CARDINAL_ORDER
    return frozenset(order[(order.index(direction) + steps) % 4] for direction in connections)


def fence_facing_for_connections(
    variant: str,
    connections: frozenset[str],
) -> str | None:
    if variant in {"post", "cross"}:
        return None

    canonical = _CANONICAL_CONNECTIONS[variant]

    for steps, direction in enumerate(_CARDINAL_ORDER):
        if _rotate_connections(canonical, steps) == connections:
            return None if direction == "north" else direction[0].upper()

    return None


def resolve_fence_adjacency(
    parsed: ParsedToken,
    cells: CellGrid,
    x: int,
    z: int,
) -> ParsedToken:
    states = tuple(
        (direction, should_fence_connect(get_cell(cells, x + dx, z + dz, empty=None)))
        for direction, (dx, dz) in DIRECTION_OFFSETS.items()
    )

    return ParsedToken(
        token=parsed.token,
        material=parsed.material,
        direction=parsed.direction,
        variant=parsed.variant,
        rotation=parsed.rotation,
        states=states,
    )
