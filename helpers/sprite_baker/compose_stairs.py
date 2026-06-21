from __future__ import annotations

from pathlib import Path

from PIL import Image

from helpers.sprite_baker.compose_simple import parse_bake_key
from helpers.sprite_baker.demo import SpriteBakeError, bake_texture_file
from helpers.sprite_baker.plank_materials import expand_material_bake_keys, list_stairs_materials
from helpers.sprite_baker.stair_shapes import (
    STAIR_SHAPES,
    apply_texture_mask,
    build_stair_side_mask,
    build_stair_top_mask,
)
from helpers.types import BlockRegistryEntry, TextureType
from registries.loader import BLOCK_REGISTRY, find_block_texture_path


def is_stairs_bakeable(entry: BlockRegistryEntry) -> bool:
    return entry.get("behavior") == "stairs"


def is_stairs_bake_key(key: str) -> bool:
    if "#top:" in key:
        return False

    parsed = parse_bake_key(key)
    entry = BLOCK_REGISTRY.get(parsed.token)

    if entry is None or not is_stairs_bakeable(entry):
        return False

    return not (parsed.variant == "straight" and key.endswith("#straight"))


def list_stairs_bake_keys(
    view: TextureType = "top",
    *,
    textures_dir: Path | None = None,
) -> list[str]:
    from registries.loader import build_registry_texture_mapping

    mapping = build_registry_texture_mapping(view)
    base_keys = [key for key in mapping if is_stairs_bake_key(key)]

    if textures_dir is None:
        return sorted(base_keys)

    return expand_material_bake_keys(
        base_keys,
        token="STAIRS",
        materials=list_stairs_materials(textures_dir=textures_dir),
    )


def resolve_stair_shape(parsed_variant: str | None, entry: BlockRegistryEntry) -> str:
    if parsed_variant in STAIR_SHAPES:
        return parsed_variant

    return entry.get("defaults", {}).get("shape", "straight")


def _resolve_material(parsed_material: str | None, entry: BlockRegistryEntry) -> str:
    material = parsed_material or entry.get("material_default")

    if not material:
        raise SpriteBakeError("STAIRS requires a material or material_default")

    return material


def _load_planks_texture(textures_dir: Path, material: str, size: int) -> Image.Image:
    candidates = (
        f"{material}_planks.png",
        f"{material}.png",
        f"{material}_stairs.png",
    )

    for filename in candidates:
        texture_path = find_block_texture_path(textures_dir, filename)

        if texture_path is not None:
            return bake_texture_file(texture_path, size)

    raise SpriteBakeError(
        f"Texture source not found for stairs material {material!r}; tried {', '.join(candidates)}"
    )


def compose_stairs(
    *,
    key: str,
    view: TextureType,
    size: int,
    textures_dir: Path,
) -> Image.Image:
    parsed = parse_bake_key(key)
    entry = BLOCK_REGISTRY.get(parsed.token)

    if entry is None:
        raise SpriteBakeError(f"Unknown registry token: {parsed.token}")

    if not is_stairs_bakeable(entry):
        behavior = entry.get("behavior")
        raise SpriteBakeError(f"{parsed.token} is not a stairs block (behavior={behavior})")

    material = _resolve_material(parsed.material, entry)
    shape = resolve_stair_shape(parsed.variant, entry)
    planks = _load_planks_texture(textures_dir, material, size)

    if view == "top":
        mask = build_stair_top_mask(size, shape)
    elif view == "side":
        mask = build_stair_side_mask(size, shape)
    else:
        raise SpriteBakeError(f"Unsupported stairs bake view: {view}")

    return apply_texture_mask(planks, mask)


def compose_stairs_entry(
    *,
    size: int,
    key: str,
    view: TextureType = "top",
    textures_dir: Path,
    **_kwargs,
) -> Image.Image:
    return compose_stairs(key=key, view=view, size=size, textures_dir=textures_dir)
