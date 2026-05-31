from __future__ import annotations

from pathlib import Path

from PIL import Image

from helpers.paths import BLOCK_TEXTURES_FOLDER, GENERATED_ASSETS_FOLDER
from helpers.sprite_baker.cache import load_generated_sprite, load_or_bake
from helpers.sprite_baker.registry import get_composer
from helpers.sprite_baker.setup import register_default_composers

_composers_registered = False


def _ensure_composers() -> None:
    global _composers_registered

    if not _composers_registered:
        register_default_composers()
        _composers_registered = True


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
