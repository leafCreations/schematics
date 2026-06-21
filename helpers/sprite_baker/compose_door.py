from __future__ import annotations

from pathlib import Path

from PIL import Image

from helpers.sprite_baker.compose_simple import parse_bake_key
from helpers.sprite_baker.demo import SpriteBakeError, bake_texture_file
from helpers.sprite_baker.plank_materials import (
    copper_family_texture_material,
    expand_material_bake_keys,
    list_door_materials,
)
from helpers.types import BlockRegistryEntry, TextureType
from registries.loader import (
    BLOCK_REGISTRY,
    find_block_texture_path,
    get_render_textures,
    resolve_registry_texture_filename,
)

DOOR_TOP_STRIP_ROWS = 4
DOOR_TOP_INSET = 1


def door_texture_material(material: str) -> str:
    return copper_family_texture_material(material)


def is_door_bakeable(entry: BlockRegistryEntry) -> bool:
    return entry.get("behavior") == "door"


def is_door_bake_key(key: str, *, view: TextureType = "top") -> bool:
    if "#top:" in key or "#side:" in key:
        return False

    parsed = parse_bake_key(key)

    if view == "inventory" and parsed.variant is not None:
        return False

    entry = BLOCK_REGISTRY.get(parsed.token)

    return entry is not None and is_door_bakeable(entry)


def list_door_bake_keys(
    view: TextureType = "top",
    *,
    textures_dir: Path | None = None,
) -> list[str]:
    from registries.loader import build_registry_texture_mapping

    if view == "inventory":
        if textures_dir is None:
            return ["DOOR"]

        keys = [f"DOOR:{material}" for material in list_door_materials(textures_dir=textures_dir)]
        keys.append("DOOR")
        return sorted(set(keys))

    mapping = build_registry_texture_mapping(view)
    base_keys = [key for key in mapping if is_door_bake_key(key, view=view)]

    if textures_dir is None:
        return sorted(base_keys)

    return expand_material_bake_keys(
        base_keys,
        token="DOOR",
        materials=list_door_materials(textures_dir=textures_dir),
    )


def resolve_door_half(parsed_variant: str | None, entry: BlockRegistryEntry) -> str:
    if parsed_variant in {"lower", "upper"}:
        return parsed_variant

    return entry.get("defaults", {}).get("half", "lower")


def _resolve_material(parsed_material: str | None, entry: BlockRegistryEntry) -> str:
    material = parsed_material or entry.get("material_default")

    if not material:
        raise SpriteBakeError("DOOR requires a material or material_default")

    return material


def _load_texture(textures_dir: Path, filename: str, size: int) -> Image.Image:
    texture_path = find_block_texture_path(textures_dir, filename)

    if texture_path is None:
        raise SpriteBakeError(f"Texture source not found: {filename}")

    return bake_texture_file(texture_path, size)


def _compose_door_top_panel(
    texture: Image.Image,
    *,
    strip_rows: int = DOOR_TOP_STRIP_ROWS,
    inset: int = DOOR_TOP_INSET,
) -> Image.Image:
    """North-facing plan-view door: edge bar with compressed panel detail.

    A door seen from above is a thin slab on one block edge, not the full face
    texture used for side elevation. Squash the face art into a short strip so
    material and panel pattern stay recognizable at schematic scale.
    """
    size = texture.size[0]
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rows = min(strip_rows, size)
    inner_width = max(1, size - (2 * inset))
    strip = texture.resize((inner_width, rows), Image.Resampling.NEAREST)
    canvas.paste(strip, (inset, 0))
    return canvas


def _resolve_door_side_filename(
    entry: BlockRegistryEntry,
    *,
    material: str,
    half: str,
) -> str:
    texture_material = door_texture_material(material)
    render_textures = get_render_textures(entry)
    filename = render_textures.get(half)

    if isinstance(filename, str):
        return filename.format(material=texture_material)

    resolved = resolve_registry_texture_filename(
        entry,
        "side",
        material=texture_material,
        variant=half,
    )

    if resolved is None:
        suffix = "bottom" if half == "lower" else "top"
        return f"{texture_material}_door_{suffix}.png"

    return resolved


def _compose_door_inventory(
    entry: BlockRegistryEntry,
    *,
    material: str,
    textures_dir: Path,
    size: int,
) -> Image.Image:
    half = max(1, size // 2)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    upper_filename = _resolve_door_side_filename(entry, material=material, half="upper")
    lower_filename = _resolve_door_side_filename(entry, material=material, half="lower")
    upper = _load_texture(textures_dir, upper_filename, size)
    lower = _load_texture(textures_dir, lower_filename, size)

    canvas.paste(upper.resize((size, half), Image.Resampling.NEAREST), (0, 0))
    canvas.paste(lower.resize((size, half), Image.Resampling.NEAREST), (0, half))
    return canvas


def compose_door(
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

    if not is_door_bakeable(entry):
        behavior = entry.get("behavior")
        raise SpriteBakeError(f"{parsed.token} is not a door block (behavior={behavior})")

    material = _resolve_material(parsed.material, entry)
    half = resolve_door_half(parsed.variant, entry)

    if view == "inventory":
        return _compose_door_inventory(
            entry, material=material, textures_dir=textures_dir, size=size
        )

    if view == "top":
        filename = _resolve_door_side_filename(entry, material=material, half="lower")
        texture = _load_texture(textures_dir, filename, size)
        return _compose_door_top_panel(texture)

    if view == "side":
        filename = _resolve_door_side_filename(entry, material=material, half=half)
        return _load_texture(textures_dir, filename, size)

    raise SpriteBakeError(f"Unsupported door bake view: {view}")


def compose_door_entry(
    *,
    size: int,
    key: str,
    view: TextureType = "top",
    textures_dir: Path,
    **_kwargs,
) -> Image.Image:
    return compose_door(key=key, view=view, size=size, textures_dir=textures_dir)
