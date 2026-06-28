from __future__ import annotations

from pathlib import Path

from PIL import Image

from helpers.paths import PROJECT_CUSTOM_FOLDER
from helpers.sprite_baker.chest_atlas import BASE_FRONT, LATCH, LID_FRONT, PART_ATLAS_FILES
from helpers.sprite_baker.template_fit import fit_template_to_cell

CHEST_SINGLE_TEMPLATE_PATH = PROJECT_CUSTOM_FOLDER / "chest.png"
CHEST_DOUBLE_LEFT_TEMPLATE_PATH = PROJECT_CUSTOM_FOLDER / "double_chest_left.png"
CHEST_DOUBLE_RIGHT_TEMPLATE_PATH = PROJECT_CUSTOM_FOLDER / "double_chest_right.png"

_TOP_TEMPLATE_PATHS = {
    "single": CHEST_SINGLE_TEMPLATE_PATH,
    "left": CHEST_DOUBLE_LEFT_TEMPLATE_PATH,
    "right": CHEST_DOUBLE_RIGHT_TEMPLATE_PATH,
}


def _load_template(path: Path) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(f"Chest template not found: {path}")

    return Image.open(path).convert("RGBA")


def _load_top_template(part: str) -> Image.Image:
    path = _TOP_TEMPLATE_PATHS.get(part)

    if path is None:
        raise ValueError(f"Unsupported chest top part: {part}")

    return _load_template(path)


def compose_chest_top_schematic(*, part: str, size: int) -> Image.Image:
    template = _load_top_template(part)
    return fit_template_to_cell(template, size)


def compose_chest_inventory_schematic(*, size: int) -> Image.Image:
    return compose_chest_top_schematic(part="single", size=size)


def compose_chest_side_schematic(
    *,
    part: str,
    size: int,
    chest_textures_dir: Path,
    include_latch: bool = True,
) -> Image.Image:
    atlas_name = PART_ATLAS_FILES.get(part)

    if atlas_name is None:
        raise ValueError(f"Unsupported chest side part: {part}")

    atlas_path = chest_textures_dir / atlas_name

    if not atlas_path.exists():
        raise FileNotFoundError(f"Chest entity texture not found: {atlas_path}")

    atlas = Image.open(atlas_path).convert("RGBA")
    lid = LID_FRONT.crop(atlas)
    base = BASE_FRONT.crop(atlas)

    face = Image.new("RGBA", (lid.width, lid.height + base.height), (0, 0, 0, 0))
    face.paste(base, (0, lid.height))
    face.paste(lid, (0, 0))

    if include_latch:
        latch = LATCH.crop(atlas)
        latch_x = (face.width - latch.width) // 2
        latch_y = lid.height - 2
        face.paste(latch, (latch_x, latch_y), latch)

    return fit_template_to_cell(face, size)
