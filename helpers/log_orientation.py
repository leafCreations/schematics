from __future__ import annotations

from helpers.structure_tokens import ParsedToken
from helpers.types import BlockRegistryEntry

LOG_ORIENTATIONS = frozenset({"vertical", "east_west", "north_south"})

_ORIENTATION_TO_AXIS = {
    "vertical": "y",
    "east_west": "x",
    "north_south": "z",
}

_DIRECTION_TO_ORIENTATION = {
    "E": "east_west",
    "W": "east_west",
    "N": "north_south",
    "S": "north_south",
}


def orientation_to_axis(orientation: str) -> str:
    return _ORIENTATION_TO_AXIS[orientation]


def resolve_log_orientation(parsed: ParsedToken, entry: BlockRegistryEntry) -> str:
    if parsed.variant in LOG_ORIENTATIONS:
        return parsed.variant

    direction_orientation = _DIRECTION_TO_ORIENTATION.get(parsed.direction or "")
    if direction_orientation:
        return direction_orientation

    return entry.get("defaults", {}).get("orientation", "vertical")
