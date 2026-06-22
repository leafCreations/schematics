"""Catalog block render overrides for textures and schematic tints.

Some catalog blocks need non-default block textures (fluids) or background tints
(grass, water, lava) that were previously defined in ``registries/behaviors/terrain.yaml``.
Add entries here as catalog-backed terrain blocks are migrated.
"""

from __future__ import annotations

from dataclasses import dataclass

from helpers.block_catalog import normalize_block_id


@dataclass(frozen=True, slots=True)
class CatalogBlockRenderOverride:
    texture: str | None = None
    background_color: tuple[int, int, int] | None = None


CATALOG_BLOCK_RENDER_OVERRIDES: dict[str, CatalogBlockRenderOverride] = {
    "minecraft:grass_block": CatalogBlockRenderOverride(
        background_color=(85, 255, 85),
    ),
    "minecraft:water": CatalogBlockRenderOverride(
        texture="water_still.png",
        background_color=(63, 118, 228),
    ),
    "minecraft:lava": CatalogBlockRenderOverride(
        texture="lava_still.png",
        background_color=(207, 92, 15),
    ),
}


def is_catalog_block_texture_exception(block_id: str) -> bool:
    return normalize_block_id(block_id) in CATALOG_BLOCK_RENDER_OVERRIDES


def catalog_block_render_override(block_id: str) -> CatalogBlockRenderOverride | None:
    return CATALOG_BLOCK_RENDER_OVERRIDES.get(normalize_block_id(block_id))


def catalog_block_texture_name(block_id: str) -> str | None:
    override = catalog_block_render_override(block_id)

    if override is None or override.texture is None:
        return None

    return override.texture


def catalog_block_background_color(block_id: str) -> tuple[int, int, int] | None:
    override = catalog_block_render_override(block_id)

    if override is None:
        return None

    return override.background_color
