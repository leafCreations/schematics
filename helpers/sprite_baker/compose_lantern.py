from __future__ import annotations

from pathlib import Path

from PIL import Image

from helpers.sprite_baker.block_model import (
    alpha_bbox,
    has_block_model,
    render_block_model,
)
from helpers.sprite_baker.compose_simple import parse_bake_key
from helpers.sprite_baker.demo import SpriteBakeError
from helpers.types import BlockRegistryEntry, TextureType
from registries.loader import BLOCK_REGISTRY


def is_lantern_bakeable(entry: BlockRegistryEntry) -> bool:
    return entry.get("behavior") == "lantern"


def is_lantern_bake_key(key: str, *, view: TextureType = "top") -> bool:
    if "#top:" in key or "#side:" in key:
        return False

    parsed = parse_bake_key(key)
    entry = BLOCK_REGISTRY.get(parsed.token)
    return entry is not None and is_lantern_bakeable(entry)


def _lantern_variants(entry: BlockRegistryEntry) -> dict:
    return entry.get("minecraft", {}).get("variants", {})


def resolve_lantern_variant(parsed_variant: str | None, entry: BlockRegistryEntry) -> str:
    variants = _lantern_variants(entry)
    default = entry.get("defaults", {}).get("variant", "normal")

    if parsed_variant and parsed_variant in variants:
        return parsed_variant

    return default


def resolve_lantern_model_name(entry: BlockRegistryEntry, variant: str) -> str:
    variant_data = _lantern_variants(entry).get(variant, {})
    block_id = variant_data.get("block", "")

    if not block_id:
        raise SpriteBakeError(f"No minecraft block for variant {variant!r}")

    return block_id.split(":", 1)[-1]


def list_lantern_bake_keys(view: TextureType = "top") -> list[str]:
    from registries.loader import build_registry_texture_mapping

    mapping = build_registry_texture_mapping(view)
    keys = [key for key in mapping if is_lantern_bake_key(key, view=view)]

    for token, entry in BLOCK_REGISTRY.items():
        if not is_lantern_bakeable(entry):
            continue

        if token not in keys:
            keys.append(token)

        default_variant = entry.get("defaults", {}).get("variant", "normal")

        for variant in _lantern_variants(entry):
            if variant == default_variant:
                continue

            variant_key = f"{token}#{variant}"

            if variant_key not in keys:
                keys.append(variant_key)

    return sorted(set(keys))


def _crop_bbox(image: Image.Image, bbox: tuple[int, int, int, int]) -> Image.Image:
    min_x, min_y, max_x, max_y = bbox
    return image.crop((min_x, min_y, max_x + 1, max_y + 1))


def _compose_lantern_top_hanging(model_name: str, size: int) -> Image.Image:
    """Top-down sprite with a visible chain toward the block above.

    Block model chains extend on the Y axis and disappear in a pure X/Z projection,
    so the east profile is scaled and composited above the cage.
    """
    body = render_block_model(model_name, size, direction="hanging_top")
    profile = render_block_model(model_name, size, direction="east")

    body_bb = alpha_bbox(body)
    profile_bb = alpha_bbox(profile)

    if body_bb is None or profile_bb is None:
        return body

    body_top = body_bb[1]
    profile_top = profile_bb[1]
    chain_bottom = min(body_top + 2, profile_bb[3] + 1)

    if chain_bottom <= profile_top:
        return body

    strip = profile.crop((profile_bb[0], profile_top, profile_bb[2] + 1, chain_bottom))
    strip_bb = alpha_bbox(strip)

    if strip_bb is None:
        return body

    strip = _crop_bbox(strip, strip_bb)
    target_height = max(3, body_top)

    if strip.height < target_height:
        scale = target_height / strip.height
        new_width = max(1, int(round(strip.width * scale)))
        strip = strip.resize((new_width, target_height), Image.Resampling.NEAREST)

    result = body.copy()
    paste_x = (size - strip.width) // 2
    paste_y = max(0, body_top - strip.height)
    result.alpha_composite(strip, (paste_x, paste_y))
    return result


def compose_lantern(
    *,
    key: str,
    view: TextureType | str,
    size: int,
    textures_dir: Path,
) -> Image.Image:
    del textures_dir

    parsed = parse_bake_key(key)
    entry = BLOCK_REGISTRY.get(parsed.token)

    if entry is None:
        raise SpriteBakeError(f"Unknown registry token: {parsed.token}")

    if not is_lantern_bakeable(entry):
        behavior = entry.get("behavior")
        raise SpriteBakeError(f"{parsed.token} is not a lantern block (behavior={behavior})")

    variant = resolve_lantern_variant(parsed.variant, entry)
    model_name = resolve_lantern_model_name(entry, variant)

    if not has_block_model(model_name):
        raise SpriteBakeError(f"Lantern model not found: {model_name}")

    if view == "top":
        return _compose_lantern_top_hanging(model_name, size)

    return render_block_model(
        model_name,
        size,
        direction="east",
    )


def compose_lantern_entry(
    *,
    size: int,
    key: str,
    view: TextureType = "top",
    textures_dir: Path,
    **_kwargs,
) -> Image.Image:
    return compose_lantern(key=key, view=view, size=size, textures_dir=textures_dir)
