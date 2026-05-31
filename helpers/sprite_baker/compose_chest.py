from __future__ import annotations

from pathlib import Path

from PIL import Image

from helpers.paths import ENTITY_CHEST_TEXTURES_FOLDER
from helpers.sprite_baker.chest_schematic import (
    compose_chest_inventory_schematic,
    compose_chest_side_schematic,
    compose_chest_top_schematic,
)
from helpers.sprite_baker.compose_simple import parse_bake_key
from helpers.sprite_baker.demo import SpriteBakeError
from helpers.types import BlockRegistryEntry, TextureType
from registries.loader import BLOCK_REGISTRY


def is_chest_bakeable(entry: BlockRegistryEntry) -> bool:
    return entry.get("behavior") == "chest"


def is_chest_bake_key(key: str, *, view: TextureType = "top") -> bool:
    if "#top:" in key or "#side:" in key:
        return False

    parsed = parse_bake_key(key)

    if view == "inventory" and parsed.token == "CHEST" and parsed.variant is None:
        return True

    if view == "inventory" and parsed.variant not in {None, "single"}:
        return False

    entry = BLOCK_REGISTRY.get(parsed.token)
    return entry is not None and is_chest_bakeable(entry)


def list_chest_bake_keys(view: TextureType = "top") -> list[str]:
    from registries.loader import build_registry_texture_mapping

    if view == "inventory":
        return ["CHEST", "CHEST#single"]

    mapping = build_registry_texture_mapping(view)
    keys = [key for key in mapping if is_chest_bake_key(key, view=view)]
    return sorted(keys)


def resolve_chest_part(parsed_variant: str | None, entry: BlockRegistryEntry) -> str:
    if parsed_variant in {"single", "left", "right"}:
        return parsed_variant

    return entry.get("defaults", {}).get("variant", "single")


def compose_chest(
    *,
    key: str,
    view: TextureType | str,
    size: int,
    textures_dir: Path,
    chest_textures_dir: Path = ENTITY_CHEST_TEXTURES_FOLDER,
) -> Image.Image:
    del textures_dir  # Chests bake from schematic templates and entity/chest atlases.

    parsed = parse_bake_key(key)
    entry = BLOCK_REGISTRY.get(parsed.token)

    if entry is None:
        raise SpriteBakeError(f"Unknown registry token: {parsed.token}")

    if not is_chest_bakeable(entry):
        behavior = entry.get("behavior")
        raise SpriteBakeError(f"{parsed.token} is not a chest block (behavior={behavior})")

    part = resolve_chest_part(parsed.variant, entry)

    if view == "inventory":
        return compose_chest_inventory_schematic(size=size)

    if view == "top":
        return compose_chest_top_schematic(part=part, size=size)

    if view == "side":
        return compose_chest_side_schematic(
            part=part,
            size=size,
            chest_textures_dir=chest_textures_dir,
        )

    raise SpriteBakeError(f"Unsupported chest bake view: {view}")


def compose_chest_entry(
    *,
    size: int,
    key: str,
    view: TextureType = "top",
    textures_dir: Path,
    chest_textures_dir: Path = ENTITY_CHEST_TEXTURES_FOLDER,
    **_kwargs,
) -> Image.Image:
    return compose_chest(
        key=key,
        view=view,
        size=size,
        textures_dir=textures_dir,
        chest_textures_dir=chest_textures_dir,
    )
