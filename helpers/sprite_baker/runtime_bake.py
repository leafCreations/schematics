from __future__ import annotations

from pathlib import Path

from PIL import Image

from helpers.paths import BLOCK_TEXTURES_FOLDER, GENERATED_ASSETS_FOLDER
from helpers.sprite_baker.cache import load_generated_sprite, load_or_bake
from helpers.sprite_baker.demo import SpriteBakeError
from helpers.sprite_baker.registry import get_composer
from helpers.sprite_baker.setup import register_default_composers

_composers_registered = False


def _ensure_composers() -> None:
    global _composers_registered

    if not _composers_registered:
        register_default_composers()
        _composers_registered = True


def behavior_for_bake_key(key: str) -> str | None:
    from helpers.registry_blocks import get_block_behavior
    from helpers.sprite_baker.compose_simple import parse_bake_key
    from registries.loader import BLOCK_REGISTRY

    try:
        parsed = parse_bake_key(key)
    except SpriteBakeError:
        return None

    entry = BLOCK_REGISTRY.get(parsed.token)

    if entry is None:
        return None

    return get_block_behavior(entry)


def load_or_bake_generated_sprite(
    view: str,
    key: str,
    block_px: int,
    *,
    behavior: str,
    textures_dir: Path | None = None,
    generated_root: Path = GENERATED_ASSETS_FOLDER,
    force: bool = False,
) -> Image.Image | None:
    """Load a cached generated sprite or bake it on demand."""
    _ensure_composers()
    composer = get_composer(behavior)

    if composer is None:
        return load_generated_sprite(view, key, block_px, generated_root=generated_root)

    resolved_textures_dir = textures_dir or BLOCK_TEXTURES_FOLDER

    def bake_fn() -> Image.Image:
        return composer(
            key=key,
            view=view,
            size=block_px,
            textures_dir=resolved_textures_dir,
        )

    image = load_or_bake(
        view,
        key,
        bake_fn,
        generated_root=generated_root,
        force=force,
    )

    if image.size != (block_px, block_px):
        return image.resize((block_px, block_px), Image.Resampling.NEAREST)

    return image


def try_runtime_bake_sprite(
    view: str,
    key: str,
    block_px: int,
    *,
    textures_dir: Path,
    generated_root: Path = GENERATED_ASSETS_FOLDER,
) -> Image.Image | None:
    """Bake a missing generated sprite when a composer exists for the registry key."""
    _ensure_composers()
    behavior = behavior_for_bake_key(key)

    if behavior is None or get_composer(behavior) is None:
        from helpers.sprite_baker.compose_campfire import compose_campfire, is_campfire_bake_key

        if is_campfire_bake_key(key):
            try:
                return load_or_bake(
                    view,
                    key,
                    lambda: compose_campfire(
                        key=key,
                        view=view,
                        size=block_px,
                        textures_dir=textures_dir,
                    ),
                    generated_root=generated_root,
                )
            except SpriteBakeError:
                return None

        return None

    try:
        return load_or_bake_generated_sprite(
            view,
            key,
            block_px,
            behavior=behavior,
            textures_dir=textures_dir,
            generated_root=generated_root,
        )
    except SpriteBakeError:
        return None
