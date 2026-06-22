"""Multi-block tokens that should be placed after the surrounding shell."""

from __future__ import annotations

from dataclasses import dataclass

from amulet.api.block import Block

from helpers.registry_blocks import get_block_behavior
from helpers.registry_lookup import get_block_entry
from helpers.structure_tokens import ParsedToken

_DEFERRED_PLACEMENT_BEHAVIORS = frozenset({"bed", "door"})


def behavior_needs_deferred_placement(behavior: str | None) -> bool:
    return behavior in _DEFERRED_PLACEMENT_BEHAVIORS


def parsed_needs_deferred_placement(parsed: ParsedToken) -> bool:
    entry = get_block_entry(parsed)
    if entry is None:
        return False
    return behavior_needs_deferred_placement(get_block_behavior(entry))


@dataclass(frozen=True, slots=True)
class WorldgenPlacement:
    global_x: int
    world_y: int
    global_z: int
    block: Block
    parsed: ParsedToken
