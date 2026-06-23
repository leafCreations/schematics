"""Minecraft wall blockstate resolution from schematic adjacency."""

from __future__ import annotations

from helpers.structure_tokens import ParsedToken

_WALL_SIDES = ("north", "south", "east", "west")


def resolve_wall_blockstates(parsed: ParsedToken) -> dict[str, str]:
    """Map fence-style boolean adjacency to vanilla wall blockstates."""
    connections = {direction for direction, connected in parsed.states if connected}

    blockstates = {
        direction: ("low" if direction in connections else "none") for direction in _WALL_SIDES
    }
    blockstates["up"] = "true" if len(connections) <= 1 else "false"
    return blockstates
