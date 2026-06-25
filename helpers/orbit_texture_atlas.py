"""Pack orbit-preview face textures into a single RGBA atlas."""

from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image

import helpers.constants as constants

ORBIT_ATLAS_TILE_PX = constants.BLOCK_PX


@dataclass(frozen=True)
class OrbitAtlasLayout:
    rgba: bytes
    width: int
    height: int
    tile_px: int
    cols: int
    uv_rects: tuple[tuple[float, float, float, float], ...]


class OrbitTextureAtlas:
    """Deduplicate face images and assign stable atlas indices."""

    def __init__(self, tile_px: int = ORBIT_ATLAS_TILE_PX) -> None:
        self._tile_px = tile_px
        self._key_to_id: dict[bytes, int] = {}
        self._tiles: list[Image.Image] = []

    def register(
        self,
        image: Image.Image | None,
        *,
        fallback_rgb: tuple[float, float, float],
    ) -> int:
        tile = self._prepare_tile(image, fallback_rgb)
        key = tile.tobytes()
        existing = self._key_to_id.get(key)
        if existing is not None:
            return existing
        atlas_id = len(self._tiles)
        self._tiles.append(tile)
        self._key_to_id[key] = atlas_id
        return atlas_id

    def build(self) -> OrbitAtlasLayout | None:
        if not self._tiles:
            return None

        count = len(self._tiles)
        cols = max(1, int(math.ceil(math.sqrt(count))))
        rows = (count + cols - 1) // cols
        width = cols * self._tile_px
        height = rows * self._tile_px
        atlas = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        uv_rects: list[tuple[float, float, float, float]] = []
        for index, tile in enumerate(self._tiles):
            col = index % cols
            row = index // cols
            x0 = col * self._tile_px
            y0 = row * self._tile_px
            atlas.paste(tile, (x0, y0))
            u0 = x0 / float(width)
            u1 = (x0 + self._tile_px) / float(width)
            v_top = y0 / float(height)
            v_bottom = (y0 + self._tile_px) / float(height)
            uv_rects.append((u0, v_bottom, u1, v_top))

        return OrbitAtlasLayout(
            rgba=atlas.tobytes(),
            width=width,
            height=height,
            tile_px=self._tile_px,
            cols=cols,
            uv_rects=tuple(uv_rects),
        )

    def _prepare_tile(
        self,
        image: Image.Image | None,
        fallback_rgb: tuple[float, float, float],
    ) -> Image.Image:
        if image is None:
            red = int(max(0.0, min(1.0, fallback_rgb[0])) * 255)
            green = int(max(0.0, min(1.0, fallback_rgb[1])) * 255)
            blue = int(max(0.0, min(1.0, fallback_rgb[2])) * 255)
            return Image.new(
                "RGBA",
                (self._tile_px, self._tile_px),
                (red, green, blue, 255),
            )

        rgba = image.convert("RGBA")
        if rgba.size != (self._tile_px, self._tile_px):
            rgba = rgba.resize(
                (self._tile_px, self._tile_px),
                Image.Resampling.NEAREST,
            )
        return rgba
