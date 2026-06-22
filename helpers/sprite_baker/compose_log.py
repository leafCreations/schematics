from __future__ import annotations

from pathlib import Path

from PIL import Image

from helpers.log_materials import enumerate_log_materials, log_block_suffix
from helpers.log_orientation import resolve_log_orientation
from helpers.sprite_baker.compose_simple import parse_bake_key
from helpers.sprite_baker.demo import SpriteBakeError, bake_texture_file
from helpers.structure_tokens import parse_structure_token
from helpers.types import BlockRegistryEntry, TextureType
from registries.loader import BLOCK_REGISTRY, find_block_texture_path


def is_log_bakeable(entry: BlockRegistryEntry) -> bool:
    return entry.get("behavior") == "log"


def is_log_bake_key(key: str) -> bool:
    if "#top:" in key or "#side:" in key:
        return False

    parsed = parse_bake_key(key)
    entry = BLOCK_REGISTRY.get(parsed.token)
    return entry is not None and is_log_bakeable(entry)


def list_log_materials(*, textures_dir: Path) -> list[str]:
    materials = list(enumerate_log_materials())

    if materials:
        return materials

    if not textures_dir.exists():
        return ["oak"]

    discovered = {path.stem.removesuffix("_log_top") for path in textures_dir.glob("*_log_top.png")}
    discovered.update(
        path.stem.removesuffix("_stem_top") for path in textures_dir.glob("*_stem_top.png")
    )
    return sorted(discovered) or ["oak"]


def list_log_bake_keys(
    view: TextureType = "top",
    *,
    textures_dir: Path,
) -> list[str]:
    del view

    keys: list[str] = ["LOG", "LOG#east_west", "LOG#north_south"]

    for material in list_log_materials(textures_dir=textures_dir):
        keys.append(f"LOG:{material}")
        keys.append(f"LOG:{material}#east_west")
        keys.append(f"LOG:{material}#north_south")

    return sorted(set(keys))


def resolve_log_orientation_from_key(key: str, entry: BlockRegistryEntry) -> str:
    token = parse_structure_token(key)
    if token is None:
        return entry.get("defaults", {}).get("orientation", "vertical")

    return resolve_log_orientation(token, entry)


def _resolve_material(parsed_material: str | None, entry: BlockRegistryEntry) -> str:
    material = parsed_material or entry.get("material_default")

    if not material:
        raise SpriteBakeError("LOG requires a material or material_default")

    return material


def _load_texture(textures_dir: Path, filename: str, size: int) -> Image.Image:
    texture_path = find_block_texture_path(textures_dir, filename)

    if texture_path is None:
        raise SpriteBakeError(f"Texture source not found: {filename}")

    return bake_texture_file(texture_path, size)


def compose_log(
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

    if not is_log_bakeable(entry):
        behavior = entry.get("behavior")
        raise SpriteBakeError(f"{parsed.token} is not a log block (behavior={behavior})")

    material = _resolve_material(parsed.material, entry)
    orientation = resolve_log_orientation_from_key(key, entry)
    suffix = log_block_suffix(material)

    if view == "top" and orientation == "vertical":
        return _load_texture(textures_dir, f"{material}_{suffix}_top.png", size)

    if view in {"top", "side", "inventory"}:
        return _load_texture(textures_dir, f"{material}_{suffix}.png", size)

    raise SpriteBakeError(f"Unsupported log bake view: {view}")


def compose_log_entry(
    *,
    size: int,
    key: str,
    view: TextureType = "top",
    textures_dir: Path,
    **_kwargs,
) -> Image.Image:
    return compose_log(key=key, view=view, size=size, textures_dir=textures_dir)
