"""World-export block normalization for Amulet / Minecraft 1.26."""

from __future__ import annotations

from amulet.api.block import Block
from PyMCTranslate import new_translation_manager

from helpers.registry_blocks import (
    get_block_behavior,
    resolve_minecraft_block_id,
    resolve_token_color,
    resolve_token_fields,
)
from helpers.structure_tokens import ParsedToken
from helpers.types import BlockRegistryEntry

_BLOCK_ENTITY_BEHAVIORS = frozenset({"chest"})
_BED_BEHAVIOR = "bed"
_JAVA_VERSION = ("java", (26, 1, 0))


def resolve_worldgen_export_block_id(
    entry: BlockRegistryEntry,
    parsed: ParsedToken,
) -> str:
    """Return the Minecraft block id written to region files for world export."""
    if get_block_behavior(entry) == _BED_BEHAVIOR:
        color = resolve_token_color(entry, parsed)
        return f"minecraft:{color}_bed"

    return resolve_minecraft_block_id(entry, parsed)


def _normalize_bed_for_worldgen_export(
    block: Block,
    entry: BlockRegistryEntry,
    parsed: ParsedToken,
) -> Block:
    """Map unified ``minecraft:bed`` registry blocks to per-color 26.1 bed blocks."""
    color = resolve_token_color(entry, parsed)
    props = dict(block.properties)
    props.pop("color", None)

    if props:
        return Block(block.namespace, f"{color}_bed", props)

    _, direction, variant, defaults = resolve_token_fields(entry, parsed)
    part = variant or defaults.get("part", "head")
    facing = direction or defaults.get("direction", "north")
    return Block(
        block.namespace,
        f"{color}_bed",
        {
            "facing": facing,
            "occupied": "false",
            "part": part,
        },
    )


def normalize_block_for_worldgen_export(
    block: Block,
    entry: BlockRegistryEntry,
    parsed: ParsedToken,
) -> Block:
    """Return a block form that survives Amulet export on Minecraft Java 26.1.

    Chests placed as ``minecraft:chest`` do not get tile entities, so Minecraft
    removes them on load. Converting to the universal chest block lets
    PyMCTranslate attach the chest tile entity during ``from_universal``.

    Beds in the editor registry use unified ``minecraft:bed`` with a ``color``
    property (26.2 style). Java 26.1 still expects ``minecraft:{color}_bed``,
    so world export rewrites beds before Amulet encodes the chunk palette.
    """
    behavior = get_block_behavior(entry)

    if behavior == _BED_BEHAVIOR:
        return _normalize_bed_for_worldgen_export(block, entry, parsed)

    if behavior not in _BLOCK_ENTITY_BEHAVIORS:
        return block

    version = new_translation_manager().get_version(*_JAVA_VERSION)
    universal_block, _, _ = version.block.to_universal(block)

    if isinstance(universal_block, Block):
        return universal_block

    return block
