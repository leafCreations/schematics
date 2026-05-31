from __future__ import annotations

from dataclasses import dataclass

from PIL import Image


@dataclass(frozen=True)
class BedAtlasRegion:
    left: int
    top: int
    width: int = 16
    height: int = 16

    def crop(self, atlas: Image.Image) -> Image.Image:
        return atlas.crop(
            (
                self.left,
                self.top,
                self.left + self.width,
                self.top + self.height,
            )
        )


# Minecraft entity/bed/{color}.png layout (64x64 atlas).
HEAD_TOP = BedAtlasRegion(0, 0)
FOOT_TOP = BedAtlasRegion(0, 16)
HEAD_END = BedAtlasRegion(0, 32)
FOOT_END = BedAtlasRegion(16, 32)

TOP_PART_REGIONS = {
    "head": HEAD_TOP,
    "foot": FOOT_TOP,
}

SIDE_PART_REGIONS = {
    "head": HEAD_END,
    "foot": FOOT_END,
}
