from __future__ import annotations

from pathlib import Path

from PIL import Image

from helpers.sprite_baker.compose_simple import parse_bake_key
from helpers.sprite_baker.compose_slab import _compose_half_block
from helpers.sprite_baker.demo import SpriteBakeError, bake_texture_file
from helpers.sprite_baker.plank_materials import (
    copper_family_texture_material,
    expand_material_bake_keys,
    list_trapdoor_materials,
)
from helpers.types import BlockRegistryEntry, TextureType
from registries.loader import (
    BLOCK_REGISTRY,
    find_block_texture_path,
    resolve_registry_texture_filename,
)


def is_trapdoor_bakeable(entry: BlockRegistryEntry) -> bool:
    return entry.get("behavior") == "trapdoor"


def is_trapdoor_bake_key(key: str, *, view: TextureType = "top") -> bool:
    if "#top:" in key or "#side:" in key:
        return False

    parsed = parse_bake_key(key)

    if view == "inventory" and parsed.variant is not None:
        return False

    entry = BLOCK_REGISTRY.get(parsed.token)

    return entry is not None and is_trapdoor_bakeable(entry)


def list_trapdoor_bake_keys(
    view: TextureType = "top",
    *,
    textures_dir: Path | None = None,
) -> list[str]:
    from registries.loader import build_registry_texture_mapping

    if view == "inventory":
        if textures_dir is None:
            return ["TRAPDOOR"]

        keys = [
            f"TRAPDOOR:{material}"
            for material in list_trapdoor_materials(textures_dir=textures_dir)
        ]
        keys.append("TRAPDOOR")
        return sorted(set(keys))

    mapping = build_registry_texture_mapping(view)
    base_keys = [key for key in mapping if is_trapdoor_bake_key(key, view=view)]

    if textures_dir is None:
        return sorted(base_keys)

    return expand_material_bake_keys(
        base_keys,
        token="TRAPDOOR",
        materials=list_trapdoor_materials(textures_dir=textures_dir),
    )


def resolve_trapdoor_half(parsed_variant: str | None, entry: BlockRegistryEntry) -> str:
    if parsed_variant in {"top", "bottom"}:
        return parsed_variant

    return entry.get("defaults", {}).get("half", "bottom")


def _resolve_material(parsed_material: str | None, entry: BlockRegistryEntry) -> str:
    material = parsed_material or entry.get("material_default")

    if not material:
        raise SpriteBakeError("TRAPDOOR requires a material or material_default")

    return material


def _resolve_trapdoor_filename(
    entry: BlockRegistryEntry,
    *,
    material: str,
    view: TextureType,
) -> str:
    texture_material = copper_family_texture_material(material)
    resolved = resolve_registry_texture_filename(
        entry,
        view,
        material=texture_material,
    )

    if resolved is None:
        return f"{texture_material}_trapdoor.png"

    return resolved


def _load_texture(textures_dir: Path, filename: str, size: int) -> Image.Image:
    texture_path = find_block_texture_path(textures_dir, filename)

    if texture_path is None:
        raise SpriteBakeError(f"Texture source not found: {filename}")

    return bake_texture_file(texture_path, size)


def compose_trapdoor(
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

    if not is_trapdoor_bakeable(entry):
        behavior = entry.get("behavior")
        raise SpriteBakeError(f"{parsed.token} is not a trapdoor block (behavior={behavior})")

    material = _resolve_material(parsed.material, entry)
    half = resolve_trapdoor_half(parsed.variant, entry)
    filename = _resolve_trapdoor_filename(entry, material=material, view=view)
    texture = _load_texture(textures_dir, filename, size)

    if view == "inventory":
        return texture

    if view in {"top", "side"}:
        return _compose_half_block(texture, placement=half)

    raise SpriteBakeError(f"Unsupported trapdoor bake view: {view}")


def compose_trapdoor_entry(
    *,
    size: int,
    key: str,
    view: TextureType = "top",
    textures_dir: Path,
    **_kwargs,
) -> Image.Image:
    return compose_trapdoor(key=key, view=view, size=size, textures_dir=textures_dir)
