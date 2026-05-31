from __future__ import annotations

from pathlib import Path

from PIL import Image

from helpers.fence_adjacency import FENCE_VARIANTS
from helpers.sprite_baker.compose_simple import parse_bake_key
from helpers.sprite_baker.demo import SpriteBakeError, bake_texture_file
from helpers.sprite_baker.fence_model import has_fence_inventory_model, render_fence_inventory_model
from helpers.sprite_baker.fence_shapes import (
    apply_texture_mask,
    build_fence_side_mask,
    build_fence_top_mask_for_variant,
)
from helpers.sprite_baker.plank_materials import expand_material_bake_keys, list_plank_materials
from helpers.types import BlockRegistryEntry, TextureType
from registries.loader import BLOCK_REGISTRY, find_block_texture_path

INVENTORY_MODEL_VARIANTS = frozenset({"post", "straight"})


def is_fence_bakeable(entry: BlockRegistryEntry) -> bool:
    return entry.get("behavior") == "fence"


def is_fence_bake_key(key: str, *, view: TextureType = "top") -> bool:
    if "#top:" in key or "#side:" in key:
        return False

    parsed = parse_bake_key(key)

    if view == "inventory" and parsed.token == "FENCE" and parsed.variant is None:
        return True

    if view == "inventory" and parsed.variant not in {None, "post"}:
        return False

    entry = BLOCK_REGISTRY.get(parsed.token)
    return entry is not None and is_fence_bakeable(entry)


def list_fence_materials(*, textures_dir: Path) -> list[str]:
    return list_plank_materials(textures_dir=textures_dir)


def list_fence_bake_keys(
    view: TextureType = "top",
    *,
    textures_dir: Path,
) -> list[str]:
    from registries.loader import build_registry_texture_mapping

    if view == "inventory":
        keys = [f"FENCE:{material}" for material in list_fence_materials(textures_dir=textures_dir)]
        keys.append("FENCE")
        return sorted(set(keys))

    mapping = build_registry_texture_mapping(view)
    base_keys = [key for key in mapping if is_fence_bake_key(key, view=view)]
    return expand_material_bake_keys(
        base_keys,
        token="FENCE",
        materials=list_fence_materials(textures_dir=textures_dir),
    )


def resolve_fence_variant(parsed_variant: str | None, _entry: BlockRegistryEntry) -> str:
    if parsed_variant in FENCE_VARIANTS:
        return parsed_variant

    return "post"


def _resolve_material(parsed_material: str | None, entry: BlockRegistryEntry) -> str:
    material = parsed_material or entry.get("material_default")

    if not material:
        raise SpriteBakeError("FENCE requires a material or material_default")

    return material


def _load_planks_texture(textures_dir: Path, material: str, size: int) -> Image.Image:
    filename = f"{material}_planks.png"
    texture_path = find_block_texture_path(textures_dir, filename)

    if texture_path is None:
        raise SpriteBakeError(f"Texture source not found: {filename}")

    return bake_texture_file(texture_path, size)


def compose_fence(
    *,
    key: str,
    view: TextureType | str,
    size: int,
    textures_dir: Path,
) -> Image.Image:
    parsed = parse_bake_key(key)
    entry = BLOCK_REGISTRY.get(parsed.token)

    if entry is None:
        raise SpriteBakeError(f"Unknown registry token: {parsed.token}")

    if not is_fence_bakeable(entry):
        behavior = entry.get("behavior")
        raise SpriteBakeError(f"{parsed.token} is not a fence block (behavior={behavior})")

    material = _resolve_material(parsed.material, entry)
    variant = resolve_fence_variant(parsed.variant, entry)

    if view == "inventory" and has_fence_inventory_model(material):
        return render_fence_inventory_model(material, size, direction="east")

    if (
        view == "top"
        and variant in INVENTORY_MODEL_VARIANTS
        and has_fence_inventory_model(material)
    ):
        return render_fence_inventory_model(material, size, direction="down")

    planks = _load_planks_texture(textures_dir, material, size)

    if view == "inventory":
        mask = build_fence_top_mask_for_variant(size, "post")
        return apply_texture_mask(planks, mask)

    if view == "side":
        mask = build_fence_side_mask(size)
        return apply_texture_mask(planks, mask)

    if view == "top":
        mask = build_fence_top_mask_for_variant(size, variant)
        return apply_texture_mask(planks, mask)

    raise SpriteBakeError(f"Unsupported fence bake view: {view}")


def compose_fence_entry(
    *,
    size: int,
    key: str,
    view: TextureType = "top",
    textures_dir: Path,
    **_kwargs,
) -> Image.Image:
    return compose_fence(key=key, view=view, size=size, textures_dir=textures_dir)
