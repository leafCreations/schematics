from __future__ import annotations

from pathlib import Path

from PIL import Image

from helpers.sprite_baker.compose_simple import parse_bake_key
from helpers.sprite_baker.demo import SpriteBakeError, bake_texture_file
from helpers.sprite_baker.plank_materials import (
    expand_material_bake_keys,
    list_stairs_materials,
    stairs_texture_filename_candidates,
    stairs_texture_material,
)
from helpers.sprite_baker.stair_shapes import (
    STAIR_RISER_GHOST_ALPHA,
    STAIR_RISER_GHOST_LIGHTEN,
    STAIR_SHAPES,
    apply_texture_mask,
    apply_texture_mask_alpha,
    build_stair_riser_top_mask,
    build_stair_side_mask,
    build_stair_top_mask,
    lighten_texture_for_riser_ghost,
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
    candidates = stairs_texture_filename_candidates(material)
    texture_material = stairs_texture_material(material)

    for filename in candidates:
        texture_path = find_block_texture_path(textures_dir, filename)

        if texture_path is not None:
            return bake_texture_file(texture_path, size)

    raise SpriteBakeError(
        f"Texture source not found for stairs material {material!r}; tried "
        f"{', '.join(candidates)}"
        + (f" (texture alias → {texture_material!r})" if texture_material != material else "")
    )


def _compose_stairs_top(planks: Image.Image, shape: str, size: int) -> Image.Image:
    tread_mask = build_stair_top_mask(size, shape)
    riser_mask = build_stair_riser_top_mask(size, shape)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    riser_texture = lighten_texture_for_riser_ghost(planks, STAIR_RISER_GHOST_LIGHTEN)
    ghost = apply_texture_mask_alpha(riser_texture, riser_mask, STAIR_RISER_GHOST_ALPHA)
    canvas = Image.alpha_composite(canvas, ghost)
    tread = apply_texture_mask(planks, tread_mask)
    return Image.alpha_composite(canvas, tread)


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
        return _compose_stairs_top(planks, shape, size)
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
