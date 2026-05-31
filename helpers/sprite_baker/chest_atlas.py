from __future__ import annotations

from dataclasses import dataclass

from PIL import Image


@dataclass(frozen=True)
class ChestAtlasRegion:
    left: int
    top: int
    width: int
    height: int

    def crop(self, atlas: Image.Image) -> Image.Image:
        return atlas.crop(
            (
                self.left,
                self.top,
                self.left + self.width,
                self.top + self.height,
            )
        )


# Minecraft entity/chest/normal*.png front-face layout (64x64 atlas).
LATCH = ChestAtlasRegion(0, 0, 4, 5)
LID_FRONT = ChestAtlasRegion(14, 14, 14, 5)
BASE_FRONT = ChestAtlasRegion(14, 28, 14, 10)

PART_ATLAS_FILES = {
    "single": "normal.png",
    "left": "normal_left.png",
    "right": "normal_right.png",
}
