import os
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

from helpers.paths import (
    BLOCK_TEXTURES_FOLDER,
    GENERATED_ASSETS_FOLDER,
    resolve_project_custom_folder,
)
from helpers.sprite_baker.cache import load_generated_sprite
from helpers.types import MappedTextureImages, MappedTextureNames, TextureType

REGISTRIES_DIR = Path(__file__).parent
BEHAVIORS_DIR = REGISTRIES_DIR / "behaviors"
PALETTES_DIR = REGISTRIES_DIR / "palettes"
LEGACY_REGISTRY_PATH = REGISTRIES_DIR / "blocks.yaml"


def load_behavior_registry() -> dict[str, Any]:
    registry: dict[str, Any] = {}

    if BEHAVIORS_DIR.is_dir():
        for path in sorted(BEHAVIORS_DIR.glob("*.yaml")):
            entries = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

            if not isinstance(entries, dict):
                raise ValueError(f"{path} must contain a YAML mapping of registry tokens")

            for token, entry in entries.items():
                if token in registry:
                    raise ValueError(f"Duplicate registry token {token!r} in {path}")

                registry[token] = entry

        return registry

    if LEGACY_REGISTRY_PATH.is_file():
        legacy = yaml.safe_load(LEGACY_REGISTRY_PATH.read_text(encoding="utf-8")) or {}
        return legacy

    raise FileNotFoundError(
        f"No behavior registry found; expected {BEHAVIORS_DIR}/*.yaml or {LEGACY_REGISTRY_PATH}"
    )


def load_block_palettes() -> dict[str, dict[str, Any]]:
    palettes: dict[str, dict[str, Any]] = {}

    if not PALETTES_DIR.is_dir():
        return palettes

    for path in sorted(PALETTES_DIR.glob("*.yaml")):
        palette = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

        if not isinstance(palette, dict):
            raise ValueError(f"{path} must contain a YAML mapping")

        palettes[path.stem] = palette

    return palettes


BLOCK_REGISTRY = load_behavior_registry()
BLOCK_PALETTES = load_block_palettes()


def reload_registries() -> None:
    """Reload behavior and palette YAML from disk (editor startup, tests)."""
    fresh_registry = load_behavior_registry()
    fresh_palettes = load_block_palettes()
    BLOCK_REGISTRY.clear()
    BLOCK_REGISTRY.update(fresh_registry)
    BLOCK_PALETTES.clear()
    BLOCK_PALETTES.update(fresh_palettes)

    from helpers.block_picker import clear_picker_entry_cache
    from helpers.registry_lookup import clear_registry_lookup_caches

    clear_picker_entry_cache()
    clear_registry_lookup_caches()


def _default_texture_name(block_id: str) -> str:
    _namespace, block_name = block_id.split(":", 1) if ":" in block_id else ("minecraft", block_id)
    return f"{block_name}.png"


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
    generated_keys = _generated_bake_keys("inventory")
    generated_root = GENERATED_ASSETS_FOLDER

    for key in set(mapping.keys()) | generated_keys:
        texture = _load_token_texture(
            "inventory",
            key,
            mapping=mapping,
            assets_dir=assets_dir,
            block_px=block_px,
            generated_keys=generated_keys,
            generated_root=generated_root,
        )

        if texture is not None:
            loaded[key] = texture

    return loaded


def _format_registry_value(
    value: str | None,
    entry: dict[str, Any],
    *,
    material: str | None = None,
    color: str | None = None,
    variant: str | None = None,
) -> str | None:
    if value is None:
        return None

    defaults = entry.get("defaults", {})
    resolved_color = (
        color
        or material
        or entry.get("color_default")
        or entry.get("material_default")
        or defaults.get("color")
        or ""
    )
    resolved_material = material or entry.get("material_default") or defaults.get("material") or ""
    kind = "log"

    if entry.get("behavior") == "log" and resolved_material:
        from helpers.log_materials import log_block_suffix

        kind = log_block_suffix(resolved_material)

    return value.format(
        material=resolved_material,
        color=resolved_color,
        kind=kind,
        variant=variant or defaults.get("variant") or "",
        type=defaults.get("type") or "",
        shape=defaults.get("shape") or "",
        part=defaults.get("part") or "",
    )


def get_render_textures(entry: dict[str, Any]) -> dict[str, Any]:
    """Return render texture map, including shorthand ``render.top`` / ``render.side``."""
    render = entry.get("render", {})
    textures = dict(render.get("textures", {}))

    for face in ("top", "side"):
        face_texture = render.get(face)

        if face not in textures and isinstance(face_texture, str):
            textures[face] = face_texture

    return textures


def _get_texture_from_render(
    entry: dict[str, Any],
    texture_type: TextureType,
    *,
    material: str | None = None,
    variant: str | None = None,
) -> str | None:
    textures = get_render_textures(entry)
    defaults = entry.get("defaults", {})

    texture_value = textures.get(texture_type)

    if isinstance(texture_value, dict):
        nested_keys = [
            variant or defaults.get("variant"),
            defaults.get("direction"),
            defaults.get("shape"),
            defaults.get("half"),
            defaults.get("part"),
            defaults.get("type"),
        ]

        for key in nested_keys:
            if key and texture_value.get(key):
                return _format_registry_value(
                    texture_value[key],
                    entry,
                    material=material,
                    variant=variant,
                )

        return None

    if isinstance(texture_value, str):
        return _format_registry_value(texture_value, entry, material=material, variant=variant)

    return None


def _get_default_minecraft_block(
    entry: dict[str, Any],
    *,
    material: str | None = None,
    variant: str | None = None,
) -> str | None:
    if entry.get("behavior") == "log" and material:
        from helpers.log_materials import resolve_log_block_id

        return resolve_log_block_id(material)

    minecraft = entry.get("minecraft", {})

    block_id = minecraft.get("block")
    if block_id:
        return _format_registry_value(block_id, entry, material=material, variant=variant)

    variants = minecraft.get("variants", {})
    if not variants:
        return None

    default_variant = variant or entry.get("defaults", {}).get("variant")

    if default_variant and default_variant in variants:
        return _format_registry_value(
            variants[default_variant].get("block"),
            entry,
            material=material,
            variant=variant,
        )

    first_variant = next(iter(variants.values()), {})
    return _format_registry_value(
        first_variant.get("block"),
        entry,
        material=material,
        variant=variant,
    )


def resolve_registry_texture_filename(
    entry: dict[str, Any],
    texture_type: TextureType = "top",
    *,
    material: str | None = None,
    variant: str | None = None,
) -> str | None:
    texture_name = _get_texture_from_render(
        entry,
        texture_type,
        material=material,
        variant=variant,
    )

    if texture_name:
        return texture_name

    block_id = _get_default_minecraft_block(entry, material=material, variant=variant)

    if not block_id:
        return None

    return _default_texture_name(block_id)


def _resolve_registry_texture(
    entry: dict[str, Any],
    texture_type: TextureType = "top",
    *,
    material: str | None = None,
    variant: str | None = None,
) -> str | None:
    return resolve_registry_texture_filename(
        entry,
        texture_type,
        material=material,
        variant=variant,
    )


def build_registry_texture_mapping(
    texture_type: TextureType = "top",
) -> MappedTextureNames:
    return _build_registry_texture_mapping(texture_type)


def _build_registry_texture_mapping(
    texture_type: TextureType = "top",
) -> MappedTextureNames:
    mapping = {}

    for raw_token, entry in BLOCK_REGISTRY.items():
        texture_name = _resolve_registry_texture(entry, texture_type)

        if texture_name:
            mapping[raw_token] = texture_name

        render_textures = get_render_textures(entry)
        texture_value = render_textures.get(texture_type)

        if isinstance(texture_value, dict):
            for texture_key, nested_texture_name in texture_value.items():
                formatted_texture = _format_registry_value(nested_texture_name, entry)

                if formatted_texture:
                    mapping[f"{raw_token}#{texture_key}"] = formatted_texture
                    mapping[f"{raw_token}#{texture_type}:{texture_key}"] = formatted_texture

        # Flat render texture maps like FENCE (post/end/straight).
        # Skips top/side when the base token already resolves that face.
        if texture_type in {"top", "side"}:
            for texture_key, texture_name in render_textures.items():
                if not isinstance(texture_name, str):
                    continue

                if texture_key == texture_type:
                    continue

                if texture_type == "top" and texture_key == "side":
                    continue

                if texture_type == "side" and texture_key == "top":
                    continue

                formatted_texture = _format_registry_value(texture_name, entry)

                if formatted_texture:
                    mapping[f"{raw_token}#{texture_key}"] = formatted_texture

        if texture_type == "top":
            minecraft_variants = entry.get("minecraft", {}).get("variants", {})
            default_variant = entry.get("defaults", {}).get("variant")

            for variant, variant_data in minecraft_variants.items():
                if variant == default_variant:
                    continue

                block_id = _format_registry_value(variant_data.get("block"), entry)

                if block_id:
                    key = f"{raw_token}#{variant}"
                    if key not in mapping:
                        mapping[key] = _default_texture_name(block_id)

            base_texture = mapping.get(raw_token)
            defaults = entry.get("defaults", {})
            default_keys = {
                defaults.get("variant"),
                defaults.get("type"),
            }

            for variant in entry.get("ui", {}).get("variants", []):
                if variant in default_keys:
                    continue

                if base_texture and f"{raw_token}#{variant}" not in mapping:
                    mapping[f"{raw_token}#{variant}"] = base_texture

    return mapping


def find_block_texture_path(assets_dir: str | Path, filename: str) -> Path | None:
    path = _find_texture_path(str(assets_dir), filename)

    if path is None:
        return None

    return Path(path)


def _find_texture_path(assets_dir: str, filename: str) -> str | None:
    normalized_filename = filename.lstrip("/\\")

    custom_folder = str(resolve_project_custom_folder())

    for folder in [
        assets_dir,
        os.path.join(assets_dir, "block_assets"),
        os.path.join(assets_dir, "item_assets"),
        os.path.join(assets_dir, "custom"),
        custom_folder,
    ]:
        path = os.path.join(folder, normalized_filename)

        if os.path.exists(path):
            return path

    return None


def _generated_bake_keys(texture_type: TextureType) -> set[str]:
    """Registry mapping keys plus procedurally baked color/part variants on disk."""
    keys: set[str] = set()

    from helpers.sprite_baker.compose_bed import list_bed_bake_keys
    from helpers.sprite_baker.compose_campfire import list_campfire_bake_keys
    from helpers.sprite_baker.compose_chest import list_chest_bake_keys
    from helpers.sprite_baker.compose_door import list_door_bake_keys
    from helpers.sprite_baker.compose_fence import list_fence_bake_keys
    from helpers.sprite_baker.compose_lantern import list_lantern_bake_keys
    from helpers.sprite_baker.compose_log import list_log_bake_keys
    from helpers.sprite_baker.compose_simple import list_planks_bake_keys, list_simple_bake_keys
    from helpers.sprite_baker.compose_slab import list_slab_bake_keys
    from helpers.sprite_baker.compose_stairs import list_stairs_bake_keys
    from helpers.sprite_baker.compose_torch import list_torch_bake_keys
    from helpers.sprite_baker.compose_trapdoor import list_trapdoor_bake_keys
    from helpers.sprite_baker.compose_wall import list_wall_bake_keys

    keys.update(list_simple_bake_keys(texture_type))
    keys.update(list_bed_bake_keys(texture_type))
    keys.update(list_chest_bake_keys(texture_type))
    keys.update(list_door_bake_keys(texture_type, textures_dir=BLOCK_TEXTURES_FOLDER))
    keys.update(list_fence_bake_keys(texture_type, textures_dir=BLOCK_TEXTURES_FOLDER))
    keys.update(list_wall_bake_keys(texture_type, textures_dir=BLOCK_TEXTURES_FOLDER))
    keys.update(list_log_bake_keys(texture_type, textures_dir=BLOCK_TEXTURES_FOLDER))
    keys.update(list_planks_bake_keys(textures_dir=BLOCK_TEXTURES_FOLDER))
    keys.update(list_slab_bake_keys(texture_type, textures_dir=BLOCK_TEXTURES_FOLDER))
    keys.update(list_stairs_bake_keys(texture_type, textures_dir=BLOCK_TEXTURES_FOLDER))
    keys.update(list_trapdoor_bake_keys(texture_type, textures_dir=BLOCK_TEXTURES_FOLDER))
    keys.update(list_torch_bake_keys(texture_type))
    keys.update(list_lantern_bake_keys(texture_type))
    keys.update(list_campfire_bake_keys(texture_type))

    return keys


def _load_token_texture(
    texture_type: TextureType,
    token: str,
    *,
    mapping: MappedTextureNames,
    assets_dir: str,
    block_px: int,
    generated_keys: set[str],
    generated_root: Path = GENERATED_ASSETS_FOLDER,
) -> Image.Image | None:
    generated = load_generated_sprite(
        texture_type,
        token,
        block_px,
        generated_root=generated_root,
    )

    if generated is not None:
        return generated

    # Bake procedurally composed sprites for registry keys (including variant keys
    # listed by _generated_bake_keys() that are not in the flat texture mapping).
    if token in generated_keys:
        from helpers.sprite_baker.runtime_bake import try_runtime_bake_sprite

        baked = try_runtime_bake_sprite(
            texture_type,
            token,
            block_px,
            textures_dir=Path(assets_dir),
            generated_root=generated_root,
        )

        if baked is not None:
            return baked

    filename = mapping.get(token)

    if filename is None:
        return None

    path = _find_texture_path(assets_dir, filename)

    if path is None:
        return None

    from helpers.block_texture_load import load_block_texture_image

    return load_block_texture_image(Path(path), block_px)


def compile_texture_set(
    texture_type: TextureType,
    assets_dir: str,
    block_px: int,
) -> MappedTextureImages:
    mapping = _build_registry_texture_mapping(texture_type)
    loaded = {}
    generated_keys = _generated_bake_keys(texture_type)
    generated_root = GENERATED_ASSETS_FOLDER

    for token in set(mapping.keys()) | generated_keys:
        texture = _load_token_texture(
            texture_type,
            token,
            mapping=mapping,
            assets_dir=assets_dir,
            block_px=block_px,
            generated_keys=generated_keys,
            generated_root=generated_root,
        )

        if texture is not None:
            loaded[token] = texture

    return loaded
