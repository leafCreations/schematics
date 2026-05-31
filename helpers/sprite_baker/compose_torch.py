from __future__ import annotations

from pathlib import Path

from PIL import Image

from helpers.sprite_baker.block_model import has_block_model, render_block_model
from helpers.sprite_baker.compose_simple import parse_bake_key
from helpers.sprite_baker.demo import SpriteBakeError
from helpers.types import BlockRegistryEntry, TextureType
from registries.loader import BLOCK_REGISTRY

TORCH_VARIANTS = frozenset({"normal", "soul", "wall"})

TORCH_MODELS = {
    "normal": "torch",
    "soul": "soul_torch",
    "wall": "wall_torch",
}


def is_torch_bakeable(entry: BlockRegistryEntry) -> bool:
    return entry.get("behavior") == "torch"


def is_torch_bake_key(key: str, *, view: TextureType = "top") -> bool:
    if "#top:" in key or "#side:" in key:
        return False

    parsed = parse_bake_key(key)
    entry = BLOCK_REGISTRY.get(parsed.token)
    return entry is not None and is_torch_bakeable(entry)


def list_torch_bake_keys(view: TextureType = "top") -> list[str]:
    from registries.loader import build_registry_texture_mapping

    mapping = build_registry_texture_mapping(view)
    keys = [key for key in mapping if is_torch_bake_key(key, view=view)]

    if view == "inventory":
        keys.extend(key for key in ("TORCH", "TORCH#soul", "TORCH#wall") if key not in keys)

    return sorted(set(keys))


def resolve_torch_variant(parsed_variant: str | None, entry: BlockRegistryEntry) -> str:
    if parsed_variant in TORCH_VARIANTS:
        return parsed_variant

    return entry.get("defaults", {}).get("variant", "normal")


def _render_direction(view: TextureType | str, variant: str) -> str:
    if view == "top" and variant != "wall":
        return "down"

    return "east"


def compose_torch(
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

    if not is_torch_bakeable(entry):
        behavior = entry.get("behavior")
        raise SpriteBakeError(f"{parsed.token} is not a torch block (behavior={behavior})")

    variant = resolve_torch_variant(parsed.variant, entry)
    model_name = TORCH_MODELS[variant]

    if not has_block_model(model_name):
        raise SpriteBakeError(f"Torch model not found: {model_name}")

    return render_block_model(
        model_name,
        size,
        direction=_render_direction(view, variant),
    )


def compose_torch_entry(
    *,
    size: int,
    key: str,
    view: TextureType = "top",
    textures_dir: Path,
    **_kwargs,
) -> Image.Image:
    return compose_torch(key=key, view=view, size=size, textures_dir=textures_dir)
