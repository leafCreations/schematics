from __future__ import annotations

from pathlib import Path

from PIL import Image

from helpers.block_picker import enumerate_token_materials
from helpers.paths import ENTITY_BED_TEXTURES_FOLDER, resolve_entity_bed_textures_folder
from helpers.registry_blocks import resolve_token_color
from helpers.sprite_baker.bed_schematic import (
    compose_bed_inventory_schematic,
    compose_bed_side_schematic,
    compose_bed_top_schematic,
)
from helpers.sprite_baker.compose_simple import parse_bake_key
from helpers.sprite_baker.demo import SpriteBakeError
from helpers.types import BlockRegistryEntry, TextureType
from registries.loader import BLOCK_REGISTRY


def is_bed_bakeable(entry: BlockRegistryEntry) -> bool:
    return entry.get("behavior") == "bed"


def is_bed_bake_key(key: str, *, view: TextureType = "top") -> bool:
    if "#top:" in key or "#side:" in key:
        return False

    parsed = parse_bake_key(key)

    if view == "inventory" and parsed.token == "BED" and parsed.variant is None:
        return True

    if view == "inventory":
        return False

    entry = BLOCK_REGISTRY.get(parsed.token)
    return entry is not None and is_bed_bakeable(entry)


def list_bed_colors(*, bed_textures_dir: Path | None = None) -> list[str]:
    resolved_dir = bed_textures_dir or resolve_entity_bed_textures_folder()
    colors: set[str] = set(enumerate_token_materials("minecraft:{color}_bed"))

    if resolved_dir.is_dir():
        colors.update(path.stem for path in resolved_dir.glob("*.png"))

    if not colors:
        colors.add("red")

    return sorted(colors)


def list_bed_bake_keys(
    view: TextureType = "top",
    *,
    bed_textures_dir: Path | None = None,
) -> list[str]:
    from registries.loader import build_registry_texture_mapping

    if view == "inventory":
        keys = [f"BED:{color}" for color in list_bed_colors(bed_textures_dir=bed_textures_dir)]
        keys.append("BED")
        return sorted(set(keys))

    mapping = build_registry_texture_mapping(view)
    base_keys = [key for key in mapping if is_bed_bake_key(key, view=view)]
    color_keys: list[str] = []

    for color in list_bed_colors(bed_textures_dir=bed_textures_dir):
        for key in base_keys:
            if key == "BED":
                color_keys.append(f"BED:{color}")
                continue

            if key.startswith("BED#"):
                color_keys.append(key.replace("BED", f"BED:{color}", 1))

    return sorted(set(base_keys + color_keys))


def resolve_bed_part(parsed_variant: str | None, entry: BlockRegistryEntry) -> str:
    if parsed_variant in {"head", "foot"}:
        return parsed_variant

    return entry.get("defaults", {}).get("part", "head")


def resolve_bed_color_from_key(key: str, entry: BlockRegistryEntry) -> str:
    parsed = parse_bake_key(key)

    if parsed is None:
        raise SpriteBakeError(f"Invalid bake key: {key}")

    return resolve_token_color(entry, parsed)


def _bed_atlas_color_candidates(
    color: str,
    entry: BlockRegistryEntry,
) -> list[str]:
    candidates: list[str] = [color]
    default_color = entry.get("color_default")

    if default_color and default_color not in candidates:
        candidates.append(default_color)

    if "red" not in candidates:
        candidates.append("red")

    return candidates


def _load_bed_atlas(
    color: str,
    entry: BlockRegistryEntry,
    *,
    bed_textures_dir: Path | None = None,
) -> Image.Image:
    resolved_dir = bed_textures_dir or resolve_entity_bed_textures_folder()

    for candidate in _bed_atlas_color_candidates(color, entry):
        atlas_path = resolved_dir / f"{candidate}.png"

        if atlas_path.exists():
            return Image.open(atlas_path).convert("RGBA")

    raise SpriteBakeError(f"Bed entity texture not found for color {color!r} under {resolved_dir}")


def compose_bed(
    *,
    key: str,
    view: TextureType | str,
    size: int,
    textures_dir: Path,
    bed_textures_dir: Path | None = None,
) -> Image.Image:
    del textures_dir  # Beds bake from entity/bed atlases, not block textures.

    parsed = parse_bake_key(key)
    entry = BLOCK_REGISTRY.get(parsed.token)

    if entry is None:
        raise SpriteBakeError(f"Unknown registry token: {parsed.token}")

    if not is_bed_bakeable(entry):
        behavior = entry.get("behavior")
        raise SpriteBakeError(f"{parsed.token} is not a bed block (behavior={behavior})")

    color = resolve_bed_color_from_key(key, entry)
    part = resolve_bed_part(parsed.variant, entry)
    atlas = _load_bed_atlas(color, entry, bed_textures_dir=bed_textures_dir)

    if view == "inventory":
        return compose_bed_inventory_schematic(atlas=atlas, size=size)

    if view == "top":
        return compose_bed_top_schematic(part=part, atlas=atlas, size=size)

    if view == "side":
        return compose_bed_side_schematic(part=part, atlas=atlas, size=size)

    raise SpriteBakeError(f"Unsupported bed bake view: {view}")


def compose_bed_entry(
    *,
    size: int,
    key: str,
    view: TextureType = "top",
    textures_dir: Path,
    bed_textures_dir: Path = ENTITY_BED_TEXTURES_FOLDER,
    **_kwargs,
) -> Image.Image:
    return compose_bed(
        key=key,
        view=view,
        size=size,
        textures_dir=textures_dir,
        bed_textures_dir=bed_textures_dir,
    )
