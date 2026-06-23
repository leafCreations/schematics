"""Legacy terrain registry tokens and migration to catalog block ids."""

from __future__ import annotations

from helpers.block_catalog import normalize_block_id
from helpers.structure_tokens import ParsedToken, parse_structure_token

LEGACY_TERRAIN_BLOCKS: dict[str, str] = {
    "DIRT": "minecraft:dirt",
    "DIRT_PATH": "minecraft:dirt_path",
    "GRASS": "minecraft:grass_block",
    "GRAVEL": "minecraft:gravel",
    "COBBLESTONE": "minecraft:cobblestone",
    "WATER": "minecraft:water",
    "LAVA": "minecraft:lava",
    "STONE": "minecraft:stone",
}

LEGACY_TERRAIN_VARIANT_BLOCKS: dict[tuple[str, str], str] = {
    ("COBBLESTONE", "mossy"): "minecraft:mossy_cobblestone",
    ("STONE", "smooth"): "minecraft:smooth_stone",
}

GRASS_BLOCK = "minecraft:grass_block"
DIRT_PATH_BLOCK = "minecraft:dirt_path"
TRIM_BLOCK = "minecraft:gravel"

PATH_VARIETY_OPTIONS: tuple[str, ...] = (
    "minecraft:gravel",
    "minecraft:dirt",
    "minecraft:cobblestone",
    "minecraft:mossy_cobblestone",
)

TRIM_BLOCK_OPTIONS: tuple[str, ...] = PATH_VARIETY_OPTIONS

PATH_VARIETY_WEIGHTS: dict[str, float] = {
    "minecraft:gravel": 0.15,
    "minecraft:dirt": 0.15,
    "minecraft:cobblestone": 0.07,
    "minecraft:mossy_cobblestone": 0.03,
}


def legacy_terrain_block_id(parsed: ParsedToken) -> str | None:
    """Map a parsed legacy terrain token to a catalog block id."""
    if parsed.variant:
        variant_block = LEGACY_TERRAIN_VARIANT_BLOCKS.get((parsed.token, parsed.variant))

        if variant_block is not None:
            return variant_block

    return LEGACY_TERRAIN_BLOCKS.get(parsed.token)


def is_legacy_terrain_token(token: str) -> bool:
    parsed = parse_structure_token(token)

    if parsed is None:
        return False

    return legacy_terrain_block_id(parsed) is not None


def migrate_terrain_token(token: str) -> str:
    """Return the catalog block id for a legacy terrain token, or ``token`` unchanged."""
    if token == ".":
        return token

    parsed = parse_structure_token(token)

    if parsed is None:
        return token

    block_id = legacy_terrain_block_id(parsed)

    if block_id is not None:
        return block_id

    return token


def canonical_terrain_token(token: str) -> str:
    """Normalize terrain tokens for comparisons (legacy and catalog ids)."""
    migrated = migrate_terrain_token(token)
    parsed = parse_structure_token(migrated)

    if parsed is not None and parsed.token == "minecraft" and parsed.material:
        return normalize_block_id(f"minecraft:{parsed.material}")

    return migrated


def terrain_tokens_equivalent(left: str, right: str) -> bool:
    return canonical_terrain_token(left) == canonical_terrain_token(right)


def _palette_catalog_block_ids(palette_name: str) -> list[str]:
    from helpers.block_picker import resolve_palette

    palette = resolve_palette(palette_name)

    if palette is None:
        return []

    block_ids: list[str] = []

    for entry in palette.entries:
        block_ids.append(entry.token)

        for _variant_key, variant_block_id in entry.variant_blocks:
            block_ids.append(variant_block_id)

    return block_ids


def iter_terrain_palette_block_ids() -> tuple[str, ...]:
    """Catalog block ids from terrain and natural palettes (for rendering/baking)."""
    block_ids: list[str] = []

    for palette_name in ("terrain", "natural"):
        block_ids.extend(_palette_catalog_block_ids(palette_name))

    return tuple(dict.fromkeys(block_ids))
