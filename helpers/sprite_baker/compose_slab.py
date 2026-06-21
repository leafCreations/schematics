from __future__ import annotations

from pathlib import Path

from PIL import Image

from helpers.sprite_baker.compose_simple import parse_bake_key
from helpers.sprite_baker.demo import SpriteBakeError, bake_texture_file
from helpers.sprite_baker.plank_materials import expand_material_bake_keys, list_slab_materials
from helpers.types import BlockRegistryEntry, TextureType
from registries.loader import (
    BLOCK_REGISTRY,
    find_block_texture_path,
    get_render_textures,
    resolve_registry_texture_filename,
)


def is_slab_bakeable(entry: BlockRegistryEntry) -> bool:
    return entry.get("behavior") == "slab"


def list_slab_bake_keys(
    view: TextureType = "top",
    *,
    textures_dir: Path | None = None,
) -> list[str]:
    from registries.loader import build_registry_texture_mapping

    mapping = build_registry_texture_mapping(view)
    base_keys: list[str] = []

    for key in mapping:
        parsed = parse_bake_key(key)
        entry = BLOCK_REGISTRY.get(parsed.token)

        if entry is not None and is_slab_bakeable(entry):
            base_keys.append(key)

    if textures_dir is None:
        return sorted(base_keys)

    return expand_material_bake_keys(
        base_keys,
        token="SLAB",
        materials=list_slab_materials(textures_dir=textures_dir),
    )


def resolve_slab_placement(parsed_variant: str | None, entry: BlockRegistryEntry) -> str:
    if parsed_variant in {"top", "bottom"}:
        return parsed_variant

    return entry.get("defaults", {}).get("type", "bottom")


def _resolve_material(parsed_material: str | None, entry: BlockRegistryEntry) -> str:
    material = parsed_material or entry.get("material_default")

    if not material:
        raise SpriteBakeError("SLAB requires a material or material_default")

    return material


def _load_texture(textures_dir: Path, filename: str, size: int) -> Image.Image:
    texture_path = find_block_texture_path(textures_dir, filename)

    if texture_path is None:
        raise SpriteBakeError(f"Texture source not found: {filename}")

    return bake_texture_file(texture_path, size)


def _load_first_available_texture(
    textures_dir: Path,
    filenames: tuple[str, ...],
    size: int,
) -> Image.Image:
    for filename in filenames:
        texture_path = find_block_texture_path(textures_dir, filename)

        if texture_path is not None:
            return bake_texture_file(texture_path, size)

    raise SpriteBakeError(f"Texture source not found: {', '.join(filenames)}")


def _compose_half_block(texture: Image.Image, *, placement: str) -> Image.Image:
    size = texture.size[0]
    half = size // 2
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    if placement == "bottom":
        canvas.paste(texture, (0, half))
    elif placement == "top":
        canvas.paste(texture.crop((0, 0, size, half)), (0, 0))
    else:
        raise SpriteBakeError(f"Unsupported slab placement: {placement}")

    return canvas


def compose_slab(
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

    if not is_slab_bakeable(entry):
        behavior = entry.get("behavior")
        raise SpriteBakeError(f"{parsed.token} is not a slab block (behavior={behavior})")

    material = _resolve_material(parsed.material, entry)
    placement = resolve_slab_placement(parsed.variant, entry)

    if view == "top":
        filename = resolve_registry_texture_filename(
            entry,
            "top",
            material=material,
            variant=parsed.variant,
        )
        if isinstance(filename, str):
            candidates = (filename, f"{material}_planks.png", f"{material}.png")
        else:
            candidates = (f"{material}_planks.png", f"{material}.png")

        texture = _load_first_available_texture(textures_dir, candidates, size)
        return _compose_half_block(texture, placement=placement)

    if view == "side":
        render_textures = get_render_textures(entry)
        side_filename = render_textures.get("side")

        if isinstance(side_filename, str):
            side_filename = side_filename.format(material=material)
        else:
            side_filename = f"{material}_slab.png"

        if isinstance(side_filename, str):
            candidates = (
                side_filename,
                f"{material}_slab.png",
                f"{material}_planks.png",
                f"{material}.png",
            )
        else:
            candidates = (f"{material}_slab.png", f"{material}_planks.png", f"{material}.png")

        texture = _load_first_available_texture(textures_dir, candidates, size)

        return _compose_half_block(texture, placement=placement)

    raise SpriteBakeError(f"Unsupported slab bake view: {view}")


def compose_slab_entry(
    *,
    size: int,
    key: str,
    view: TextureType = "top",
    textures_dir: Path,
    **_kwargs,
) -> Image.Image:
    return compose_slab(key=key, view=view, size=size, textures_dir=textures_dir)
