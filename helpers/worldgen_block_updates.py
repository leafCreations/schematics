"""Worldgen helpers for blocks that need a scheduled update after placement.

Minecraft 26.1 still renders beds through a special block renderer. Amulet writes
the correct blockstates to disk but does not queue the block-update tick that
vanilla placement would, so beds can load as invisible hitboxes until a neighbor
changes. Scheduling a zero-delay block tick forces the renderer to initialize.
"""

from __future__ import annotations

from amulet.api.chunk import Chunk

from helpers.registry_blocks import get_block_behavior, resolve_minecraft_block_id
from helpers.registry_lookup import get_block_entry
from helpers.structure_tokens import ParsedToken

_BLOCK_UPDATE_BEHAVIORS = frozenset({"bed"})


def behavior_needs_block_update(behavior: str | None) -> bool:
    return behavior in _BLOCK_UPDATE_BEHAVIORS


def schedule_block_update(
    chunk: Chunk,
    world_x: int,
    world_y: int,
    world_z: int,
    block_id: str,
) -> None:
    """Queue a zero-delay block tick at world coordinates."""
    ticks = chunk.misc.setdefault("block_ticks", {})
    ticks[(world_x, world_y, world_z)] = (block_id, 0, 0)


def place_worldgen_block(
    chunk: Chunk,
    *,
    local_x: int,
    world_y: int,
    local_z: int,
    world_x: int,
    world_z: int,
    block,
    parsed: ParsedToken,
) -> None:
    """Place a block and schedule any follow-up updates the client expects."""
    chunk.set_block(local_x, world_y, local_z, block)

    entry = get_block_entry(parsed)
    if entry is None:
        return

    behavior = get_block_behavior(entry)
    if not behavior_needs_block_update(behavior):
        return

    block_id = resolve_minecraft_block_id(entry, parsed)
    schedule_block_update(chunk, world_x, world_y, world_z, block_id)
