"""Shared facing + lit helpers for ``facing_block`` registry behaviors."""

from __future__ import annotations

from helpers.campfire_state import LIT_STATE, explicit_lit
from helpers.types import BlockRegistryEntry

_MINECRAFT_FUNCTIONAL_ALIASES: dict[str, str] = {
    "minecraft:smoker": "SMOKER",
    "minecraft:blast_furnace": "BLAST_FURNACE",
}


def minecraft_functional_alias_token(block_id: str) -> str | None:
    return _MINECRAFT_FUNCTIONAL_ALIASES.get(block_id)


def entry_has_lit_blockstate(entry: BlockRegistryEntry) -> bool:
    blockstates = entry.get("minecraft", {}).get("blockstates", {})
    return "lit" in blockstates


def resolve_facing_block_lit(parsed, entry: BlockRegistryEntry) -> bool:
    explicit = explicit_lit(parsed)
    if explicit is not None:
        return explicit

    default_lit = entry.get("defaults", {}).get("lit", "false")
    return str(default_lit).lower() in {"true", "1", "yes"}


__all__ = [
    "LIT_STATE",
    "entry_has_lit_blockstate",
    "explicit_lit",
    "minecraft_functional_alias_token",
    "resolve_facing_block_lit",
]
