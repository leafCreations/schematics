from __future__ import annotations

from PIL import Image

from helpers.block_catalog import load_block_catalog, normalize_block_id
from helpers.campfire_state import campfire_block_entry, is_campfire_block_id
from helpers.catalog_texture_exceptions import (
    catalog_block_background_color,
    catalog_block_texture_name,
)
from helpers.paths import BLOCK_TEXTURES_FOLDER
from helpers.structure_tokens import ParsedToken
from helpers.terrain_tokens import legacy_terrain_block_id
from helpers.utils import default_texture_name
from registries.loader import (
    BLOCK_REGISTRY,
    find_block_texture_path,
    resolve_registry_texture_filename,
)

_catalog_solid_cache: dict[str, dict] = {}


def clear_registry_lookup_caches() -> None:
    _catalog_solid_cache.clear()


def is_minecraft_block_token(parsed: ParsedToken) -> bool:
    return parsed.token == "minecraft" and bool(parsed.material)


def minecraft_block_id(parsed: ParsedToken) -> str:
    return normalize_block_id(f"{parsed.token}:{parsed.material}")


def solid_entry_for_block_id(block_id: str) -> dict:
    normalized = normalize_block_id(block_id)

    if normalized in _catalog_solid_cache:
        return _catalog_solid_cache[normalized]

    if is_campfire_block_id(normalized):
        entry = campfire_block_entry(normalized)
        _catalog_solid_cache[normalized] = entry
        return entry

    catalog = load_block_catalog()
    catalog_entry = catalog.get(normalized, {})
    texture = (
        catalog_block_texture_name(normalized)
        or catalog_entry.get("texture")
        or default_texture_name(normalized)
    )

    render: dict = {"top": texture}
    background_color = catalog_block_background_color(normalized)

    if background_color is not None:
        render["background_color"] = list(background_color)

    entry = {
        "behavior": "solid",
        "minecraft": {"block": normalized},
        "render": render,
    }
    _catalog_solid_cache[normalized] = entry
    return entry


def get_block_entry(parsed: ParsedToken) -> dict | None:
    if is_minecraft_block_token(parsed):
        from helpers.facing_block_state import minecraft_functional_alias_token

        alias = minecraft_functional_alias_token(minecraft_block_id(parsed))
        if alias is not None:
            return BLOCK_REGISTRY.get(alias)

        return solid_entry_for_block_id(minecraft_block_id(parsed))

    legacy_block_id = legacy_terrain_block_id(parsed)

    if legacy_block_id is not None:
        return solid_entry_for_block_id(legacy_block_id)

    return BLOCK_REGISTRY.get(parsed.token)


def registry_lookup_token(parsed: ParsedToken) -> str:
    if is_minecraft_block_token(parsed):
        return minecraft_block_id(parsed)

    legacy_block_id = legacy_terrain_block_id(parsed)

    if legacy_block_id is not None:
        return legacy_block_id

    return parsed.token


def load_catalog_texture_image(
    parsed: ParsedToken,
    view: str,
    size: int,
) -> Image.Image | None:
    if not is_minecraft_block_token(parsed):
        return None

    entry = solid_entry_for_block_id(minecraft_block_id(parsed))
    texture_name = resolve_registry_texture_filename(entry, view)  # type: ignore[arg-type]

    if texture_name is None:
        return None

    path = find_block_texture_path(BLOCK_TEXTURES_FOLDER, texture_name)

    if path is None:
        return None

    image = Image.open(path).convert("RGBA")
    return image.resize((size, size), Image.Resampling.NEAREST)
