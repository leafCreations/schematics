from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops

from helpers.sprite_baker.demo import SpriteBakeError, bake_texture_file
from helpers.sprite_baker.plank_materials import expand_material_bake_keys, list_plank_materials
from helpers.structure_tokens import parse_structure_token
from helpers.types import BlockRegistryEntry, TextureType
from registries.loader import (
    find_block_texture_path,
    get_render_textures,
    resolve_registry_texture_filename,
)


@dataclass(frozen=True)
class ParsedBakeKey:
    token: str
    material: str | None = None
    variant: str | None = None


def parse_bake_key(key: str) -> ParsedBakeKey:
    parsed = parse_structure_token(key)

    if parsed is None:
        raise SpriteBakeError(f"Invalid bake key: {key}")

    return ParsedBakeKey(
        token=parsed.token,
        material=parsed.material,
        variant=parsed.variant,
    )


FLAT_BAKE_BEHAVIORS = frozenset({"solid", "facing_block"})


def has_flat_render_textures(entry: BlockRegistryEntry) -> bool:
    textures = get_render_textures(entry)

    for texture_key in ("top", "side"):
        texture_value = textures.get(texture_key)

        if isinstance(texture_value, dict):
            return False

    return True


def is_simple_bakeable(entry: BlockRegistryEntry) -> bool:
    if entry.get("behavior", "solid") not in FLAT_BAKE_BEHAVIORS:
        return False

    return has_flat_render_textures(entry)


def list_simple_bake_keys(
    view: TextureType = "top",
    *,
    textures_dir: Path | None = None,
) -> list[str]:
    from helpers.terrain_tokens import iter_terrain_palette_block_ids
    from registries.loader import BLOCK_REGISTRY, build_registry_texture_mapping

    mapping = build_registry_texture_mapping(view)
    keys: list[str] = []

    for key in mapping:
        parsed = parse_bake_key(key)
        entry = BLOCK_REGISTRY.get(parsed.token)

        if entry is not None and is_simple_bakeable(entry):
            keys.append(key)

    if textures_dir is None:
        keys.extend(iter_terrain_palette_block_ids())
        return sorted(dict.fromkeys(keys))

    keys.extend(iter_terrain_palette_block_ids())
    return sorted(
        dict.fromkeys(
            expand_material_bake_keys(
                keys,
                token="PLANKS",
                materials=list_plank_materials(textures_dir=textures_dir),
            )
        )
    )


def list_planks_bake_keys(*, textures_dir: Path) -> list[str]:
    return expand_material_bake_keys(
        ["PLANKS"],
        token="PLANKS",
        materials=list_plank_materials(textures_dir=textures_dir),
    )


def apply_background_tint(entry: BlockRegistryEntry, image: Image.Image) -> Image.Image:
    background_color = entry.get("render", {}).get("background_color")

    if not background_color:
        return image

    if isinstance(background_color, str):
        hex_color = background_color.lstrip("#")

        if len(hex_color) == 6:
            rgb = tuple(int(hex_color[index : index + 2], 16) for index in (0, 2, 4))
            solid = Image.new("RGBA", image.size, rgb + (255,))
            return ImageChops.multiply(image, solid)

    if isinstance(background_color, list | tuple) and len(background_color) == 3:
        solid = Image.new("RGBA", image.size, tuple(background_color) + (255,))
        return ImageChops.multiply(image, solid)

    return image


def compose_simple(
    *,
    key: str,
    view: TextureType,
    size: int,
    textures_dir: Path,
) -> Image.Image:
    from helpers.registry_lookup import get_block_entry
    from helpers.structure_tokens import parse_structure_token

    parsed = parse_bake_key(key)
    structure_parsed = parse_structure_token(key)

    if structure_parsed is None:
        raise SpriteBakeError(f"Invalid bake key: {key}")

    entry = get_block_entry(structure_parsed)

    if entry is None:
        raise SpriteBakeError(f"Unknown registry token: {parsed.token}")

    if not is_simple_bakeable(entry):
        behavior = entry.get("behavior")
        raise SpriteBakeError(
            f"{parsed.token} is not a flat texture block (behavior={behavior})",
        )

    texture_filename = resolve_registry_texture_filename(
        entry,
        view,
        material=parsed.material,
        variant=parsed.variant,
    )

    if texture_filename is None:
        raise SpriteBakeError(f"No {view} texture mapping for {key}")

    texture_path = find_block_texture_path(textures_dir, texture_filename)

    if texture_path is None:
        raise SpriteBakeError(f"Texture source not found for {key}: {texture_filename}")

    image = bake_texture_file(texture_path, size)
    return image


def compose_simple_entry(
    *,
    size: int,
    key: str,
    view: TextureType = "top",
    textures_dir: Path,
    **_kwargs,
) -> Image.Image:
    return compose_simple(key=key, view=view, size=size, textures_dir=textures_dir)
