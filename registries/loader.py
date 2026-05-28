import os
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

import helpers.utils as utils
from helpers.types import MappedTextureImages, MappedTextureNames, TextureType

REGISTRY_PATH = Path(__file__).parent / "blocks.yaml"

with open(REGISTRY_PATH) as f:
    BLOCK_REGISTRY = yaml.safe_load(f)


def _build_inventory_texture_mapping() -> MappedTextureNames:
    mapping = {}

    for raw_token, entry in BLOCK_REGISTRY.items():
        inventory_image = entry.get("render", {}).get("inventory_image")

        if inventory_image:
            formatted_texture = _format_registry_value(inventory_image, entry)

            if formatted_texture:
                mapping[raw_token] = formatted_texture

    return mapping


def compile_inventory_texture_set(
    assets_dir: str,
    block_px: int,
) -> MappedTextureImages:
    mapping = _build_inventory_texture_mapping()
    loaded = {}

    for token, filename in mapping.items():
        path = _find_texture_path(assets_dir, filename)

        if path is None:
            continue

        loaded[token] = (
            Image.open(path).convert("RGBA").resize((block_px, block_px), Image.Resampling.NEAREST)
        )

    return loaded


def _format_registry_value(value: str | None, entry: dict[str, Any]) -> str | None:
    if value is None:
        return None

    defaults = entry.get("defaults", {})

    return value.format(
        material=entry.get("material_default") or defaults.get("material") or "",
        variant=defaults.get("variant") or "",
        type=defaults.get("type") or "",
        shape=defaults.get("shape") or "",
        part=defaults.get("part") or "",
    )


def _get_texture_from_render(entry: dict[str, Any], texture_type: TextureType) -> str | None:
    render = entry.get("render", {})
    textures = render.get("textures", {})
    defaults = entry.get("defaults", {})

    texture_value = textures.get(texture_type)

    if isinstance(texture_value, dict):
        nested_keys = [
            defaults.get("direction"),
            defaults.get("shape"),
            defaults.get("half"),
            defaults.get("variant"),
            defaults.get("part"),
            defaults.get("type"),
        ]

        for key in nested_keys:
            if key and texture_value.get(key):
                return _format_registry_value(texture_value[key], entry)

        return None

    if isinstance(texture_value, str):
        return _format_registry_value(texture_value, entry)

    return None


def _get_default_minecraft_block(entry: dict[str, Any]) -> str | None:
    minecraft = entry.get("minecraft", {})

    block_id = minecraft.get("block")
    if block_id:
        return _format_registry_value(block_id, entry)

    variants = minecraft.get("variants", {})
    if not variants:
        return None

    default_variant = entry.get("defaults", {}).get("variant")

    if default_variant and default_variant in variants:
        return _format_registry_value(variants[default_variant].get("block"), entry)

    first_variant = next(iter(variants.values()), {})
    return _format_registry_value(first_variant.get("block"), entry)


def _resolve_registry_texture(
    entry: dict[str, Any], texture_type: TextureType = "top"
) -> str | None:
    texture_name = _get_texture_from_render(entry, texture_type)

    if texture_name:
        return texture_name

    block_id = _get_default_minecraft_block(entry)

    if not block_id:
        return None

    return utils.default_texture_name(block_id)


def _build_registry_texture_mapping(
    texture_type: TextureType = "top",
) -> MappedTextureNames:
    mapping = {}

    for raw_token, entry in BLOCK_REGISTRY.items():
        texture_name = _resolve_registry_texture(entry, texture_type)

        if texture_name:
            mapping[raw_token] = texture_name

        render_textures = entry.get("render", {}).get("textures", {})
        texture_value = render_textures.get(texture_type)

        if isinstance(texture_value, str):
            formatted_texture = _format_registry_value(texture_value, entry)

            if formatted_texture:
                mapping[f"{raw_token}#{texture_type}"] = formatted_texture

        elif isinstance(texture_value, dict):
            for texture_key, nested_texture_name in texture_value.items():
                formatted_texture = _format_registry_value(nested_texture_name, entry)

                if formatted_texture:
                    mapping[f"{raw_token}#{texture_key}"] = formatted_texture
                    mapping[f"{raw_token}#{texture_type}:{texture_key}"] = formatted_texture

        # Top/side fallback for flat render texture maps like FENCE.
        # This intentionally skips nested groups like STAIRS.top.
        if texture_type in {"top", "side"}:
            for texture_key, texture_name in render_textures.items():
                if not isinstance(texture_name, str):
                    continue

                formatted_texture = _format_registry_value(texture_name, entry)

                if formatted_texture:
                    mapping[f"{raw_token}#{texture_key}"] = formatted_texture

        if texture_type == "top":
            minecraft_variants = entry.get("minecraft", {}).get("variants", {})

            for variant, variant_data in minecraft_variants.items():
                block_id = _format_registry_value(variant_data.get("block"), entry)

                if block_id:
                    mapping[f"{raw_token}#{variant}"] = utils.default_texture_name(block_id)

    return mapping


def _find_texture_path(assets_dir: str, filename: str) -> str | None:
    normalized_filename = filename.lstrip("/\\")

    for folder in [
        assets_dir,
        os.path.join(assets_dir, "block_assets"),
        os.path.join(assets_dir, "item_assets"),
        os.path.join(assets_dir, "custom"),
    ]:
        path = os.path.join(folder, normalized_filename)

        if os.path.exists(path):
            return path

    return None


def compile_texture_set(
    texture_type: TextureType,
    assets_dir: str,
    block_px: int,
) -> MappedTextureImages:
    mapping = _build_registry_texture_mapping(texture_type)
    loaded = {}

    for token, filename in mapping.items():
        path = _find_texture_path(assets_dir, filename)

        if path is None:
            continue

        loaded[token] = (
            Image.open(path).convert("RGBA").resize((block_px, block_px), Image.Resampling.NEAREST)
        )

    return loaded
