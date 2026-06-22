"""Log/stem material resolution for overworld and nether wood blocks."""

from __future__ import annotations

from helpers.block_catalog import load_block_catalog
from helpers.block_picker import enumerate_token_materials

LOG_BLOCK_TEMPLATE = "minecraft:{material}_log"
PLANKS_BLOCK_TEMPLATE = "minecraft:{material}_planks"
STEM_BLOCK_TEMPLATE = "minecraft:{material}_stem"


def _plank_materials(*, catalog: dict | None = None) -> set[str]:
    return set(enumerate_token_materials(PLANKS_BLOCK_TEMPLATE, catalog=catalog))


def log_block_suffix(material: str, *, catalog: dict | None = None) -> str:
    """Return ``log`` or ``stem`` for a wood material's Minecraft block suffix."""
    resolved_catalog = load_block_catalog() if catalog is None else catalog

    if f"minecraft:{material}_log" in resolved_catalog:
        return "log"

    if (
        f"minecraft:{material}_stem" in resolved_catalog
        and f"minecraft:{material}_planks" in resolved_catalog
    ):
        return "stem"

    return "log"


def resolve_log_block_id(material: str, *, catalog: dict | None = None) -> str:
    suffix = log_block_suffix(material, catalog=catalog)
    return f"minecraft:{material}_{suffix}"


def enumerate_log_materials(*, catalog: dict | None = None) -> tuple[str, ...]:
    """Return catalog-backed materials for the LOG token (logs and nether stems)."""
    materials = set(enumerate_token_materials(LOG_BLOCK_TEMPLATE, catalog=catalog))
    plank_materials = _plank_materials(catalog=catalog)

    for material in enumerate_token_materials(STEM_BLOCK_TEMPLATE, catalog=catalog):
        if material in plank_materials:
            materials.add(material)

    return tuple(sorted(materials))
