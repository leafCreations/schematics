from pathlib import Path

from PIL import Image

from helpers.paths import BLOCK_TEXTURES_FOLDER


class SpriteBakeError(Exception):
    """Raised when a sprite cannot be baked from available assets."""


def bake_texture_file(source: Path, size: int) -> Image.Image:
    if not source.exists():
        raise SpriteBakeError(f"Texture source not found: {source}")

    texture = Image.open(source).convert("RGBA")
    return texture.resize((size, size), Image.Resampling.NEAREST)


def bake_demo_planks(size: int, *, textures_dir: Path = BLOCK_TEXTURES_FOLDER) -> Image.Image:
    """Bake a demo PLANKS sprite from vanilla oak_planks.png (Phase 0 smoke test)."""
    return bake_texture_file(textures_dir / "oak_planks.png", size)
