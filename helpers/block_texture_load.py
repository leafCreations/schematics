"""Load catalog block PNGs, cropping animated strips to the first frame."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


def animation_first_frame(image: Image.Image, texture_path: Path) -> Image.Image:
    """Return the top square frame when a companion ``.mcmeta`` defines animation."""
    mcmeta_path = Path(f"{texture_path}.mcmeta")
    if not mcmeta_path.is_file():
        return image

    try:
        payload = json.loads(mcmeta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return image

    if "animation" not in payload:
        return image

    frame_size = image.width
    if image.height <= frame_size:
        return image

    return image.crop((0, 0, frame_size, frame_size))


def load_block_texture_image(texture_path: Path, size: int) -> Image.Image:
    """Open a block texture, use frame 0 for animated strips, then resize."""
    image = Image.open(texture_path).convert("RGBA")
    image = animation_first_frame(image, texture_path)
    return image.resize((size, size), Image.Resampling.NEAREST)
