"""Creative-style item icons for the structure editor brush preview."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

import helpers.registry_blocks as registry_blocks
from helpers.catalog_texture_exceptions import is_catalog_block_texture_exception
from helpers.context import SchematicContext
from helpers.materials import draw_inventory_icon, resolve_material_inventory_icon
from helpers.paths import BLOCK_TEXTURES_FOLDER, ITEM_TEXTURES_FOLDER
from helpers.registry_lookup import (
    get_block_entry,
    is_minecraft_block_token,
    load_catalog_texture_image,
)
from helpers.structure_tokens import parse_structure_token
from helpers.types import RawToken
from helpers.utils_schematics import get_texture_for_render
from registries.loader import BLOCK_REGISTRY

_preview_cache: dict[tuple[str, int], Image.Image] = {}
_preview_ctx: SchematicContext | None = None


def _load_resized(path: Path, size: int) -> Image.Image:
    image = Image.open(path).convert("RGBA")

    if image.size != (size, size):
        return image.resize((size, size), Image.Resampling.NEAREST)

    return image


def _item_texture_path(block_name: str) -> Path | None:
    path = ITEM_TEXTURES_FOLDER / f"{block_name}.png"

    return path if path.is_file() else None


def _inventory_image_item_path(entry: dict, parsed) -> Path | None:
    inventory_image = entry.get("render", {}).get("inventory_image")

    if not inventory_image:
        return None

    material = parsed.material or entry.get("material_default")
    color = registry_blocks.resolve_token_color(entry, parsed)
    filename = inventory_image.format(material=material or "", color=color or "")

    if not filename.endswith(".png"):
        filename = f"{filename}.png"

    path = ITEM_TEXTURES_FOLDER / filename

    return path if path.is_file() else None


def _preview_context() -> SchematicContext:
    global _preview_ctx

    if _preview_ctx is None:
        _preview_ctx = SchematicContext(
            structure="preview",
            stage=1,
            name="Preview",
            layers=[],
            grid={},
            block_registry=BLOCK_REGISTRY,
            assets_dir=BLOCK_TEXTURES_FOLDER,
            worldgen_template_dir=BLOCK_TEXTURES_FOLDER,
            output_schematics_dir=BLOCK_TEXTURES_FOLDER,
            output_worldgen_dir=BLOCK_TEXTURES_FOLDER,
        )

    return _preview_ctx


def _draw_material_inventory_preview(
    raw_token: RawToken,
    parsed,
    size: int,
) -> Image.Image | None:
    ctx = _preview_context()
    icon_name = resolve_material_inventory_icon(parsed, ctx)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw_inventory_icon(
        canvas,
        draw,
        ctx,
        icon_name,
        0,
        0,
        size,
        parsed=parsed,
        raw_token=raw_token,
    )

    if canvas.getbbox() is None:
        return None

    return canvas


def load_brush_preview_image(raw_token: RawToken, size: int) -> Image.Image | None:
    """Load a creative-style preview icon (item texture when available)."""
    if raw_token == ".":
        return None

    cache_key = (raw_token, size)

    if cache_key in _preview_cache:
        return _preview_cache[cache_key].copy()

    parsed = parse_structure_token(raw_token)

    if parsed is None:
        return None

    entry = get_block_entry(parsed)

    if entry is None:
        return None

    image: Image.Image | None = None

    if is_minecraft_block_token(parsed) and is_catalog_block_texture_exception(
        registry_blocks.resolve_minecraft_block_id(entry, parsed)
    ):
        image = load_catalog_texture_image(parsed, "top", size)

        if image is not None:
            image = get_texture_for_render(raw_token, image)

    if image is None:
        try:
            block_id = registry_blocks.resolve_minecraft_block_id(entry, parsed)
            block_name = block_id.split(":", 1)[-1]
            item_path = _item_texture_path(block_name)

            if item_path is not None:
                image = _load_resized(item_path, size)
        except ValueError:
            pass

    if image is None:
        item_path = _inventory_image_item_path(entry, parsed)

        if item_path is not None:
            image = _load_resized(item_path, size)

    if image is None and is_minecraft_block_token(parsed):
        image = load_catalog_texture_image(parsed, "top", size)

        if image is not None:
            image = get_texture_for_render(raw_token, image)

    if image is None:
        image = _draw_material_inventory_preview(raw_token, parsed, size)

    if image is not None:
        _preview_cache[cache_key] = image.copy()

    return image


def clear_brush_preview_cache() -> None:
    _preview_cache.clear()


def invalidate_brush_preview_token(raw_token: str) -> None:
    global _preview_cache

    _preview_cache = {key: image for key, image in _preview_cache.items() if key[0] != raw_token}
