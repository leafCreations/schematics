from __future__ import annotations

from pathlib import Path
from typing import Literal

from PIL import Image

from helpers.paths import PROJECT_CUSTOM_FOLDER
from helpers.sprite_baker.template_fit import fit_template_to_cell

ChestFaceRole = Literal["front", "back", "end"]

CHEST_TOP_TEMPLATE_PATH = PROJECT_CUSTOM_FOLDER / "chest_top.png"
CHEST_TOP_LEFT_TEMPLATE_PATH = PROJECT_CUSTOM_FOLDER / "chest_top_left.png"
CHEST_TOP_RIGHT_TEMPLATE_PATH = PROJECT_CUSTOM_FOLDER / "chest_top_right.png"
CHEST_FRONT_TEMPLATE_PATH = PROJECT_CUSTOM_FOLDER / "chest_front.png"
CHEST_FRONT_LEFT_TEMPLATE_PATH = PROJECT_CUSTOM_FOLDER / "chest_front_left.png"
CHEST_FRONT_RIGHT_TEMPLATE_PATH = PROJECT_CUSTOM_FOLDER / "chest_front_right.png"
CHEST_BACK_LEFT_TEMPLATE_PATH = PROJECT_CUSTOM_FOLDER / "chest_back_left.png"
CHEST_BACK_RIGHT_TEMPLATE_PATH = PROJECT_CUSTOM_FOLDER / "chest_back_right.png"
CHEST_SIDE_TEMPLATE_PATH = PROJECT_CUSTOM_FOLDER / "chest_side.png"

# Legacy filenames used by registry bakes and older tests.
CHEST_SINGLE_TEMPLATE_PATH = PROJECT_CUSTOM_FOLDER / "chest.png"
CHEST_DOUBLE_LEFT_TEMPLATE_PATH = CHEST_TOP_LEFT_TEMPLATE_PATH
CHEST_DOUBLE_RIGHT_TEMPLATE_PATH = CHEST_TOP_RIGHT_TEMPLATE_PATH

_TOP_TEMPLATE_PATHS = {
    "single": CHEST_TOP_TEMPLATE_PATH,
    "left": CHEST_TOP_LEFT_TEMPLATE_PATH,
    "right": CHEST_TOP_RIGHT_TEMPLATE_PATH,
}

_FRONT_TEMPLATE_PATHS = {
    "single": CHEST_FRONT_TEMPLATE_PATH,
    "left": CHEST_FRONT_LEFT_TEMPLATE_PATH,
    "right": CHEST_FRONT_RIGHT_TEMPLATE_PATH,
}

_BACK_TEMPLATE_PATHS = {
    "left": CHEST_BACK_LEFT_TEMPLATE_PATH,
    "right": CHEST_BACK_RIGHT_TEMPLATE_PATH,
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


def _side_template_path(*, part: str, face: ChestFaceRole) -> Path:
    if face == "front":
        return _FRONT_TEMPLATE_PATHS.get(part, CHEST_FRONT_TEMPLATE_PATH)

    if face == "back":
        return _BACK_TEMPLATE_PATHS.get(part, CHEST_SIDE_TEMPLATE_PATH)

    return CHEST_SIDE_TEMPLATE_PATH


def chest_compose_source_paths(*, part: str, view: str) -> tuple[Path, ...]:
    """Project template paths used by ``compose_chest`` for cache staleness checks."""
    if view == "inventory":
        return (CHEST_TOP_TEMPLATE_PATH,)

    if view == "top":
        return (_TOP_TEMPLATE_PATHS.get(part, CHEST_TOP_TEMPLATE_PATH),)

    if view == "side":
        paths = [_side_template_path(part=part, face="front")]
        back_path = _BACK_TEMPLATE_PATHS.get(part)
        if back_path is not None:
            paths.append(back_path)
        paths.append(CHEST_SIDE_TEMPLATE_PATH)
        return tuple(paths)

    return ()


def compose_chest_top_schematic(*, part: str, size: int) -> Image.Image:
    template = _load_top_template(part)
    return fit_template_to_cell(template, size)


def compose_chest_inventory_schematic(*, size: int) -> Image.Image:
    return compose_chest_top_schematic(part="single", size=size)


def compose_chest_side_schematic(
    *,
    part: str,
    size: int,
    chest_textures_dir: Path | None = None,
    face: ChestFaceRole = "front",
    include_latch: bool | None = None,
) -> Image.Image:
    del chest_textures_dir

    if include_latch is not None:
        face = "front" if include_latch else "end"

    template = _load_template(_side_template_path(part=part, face=face))
    return fit_template_to_cell(template, size)
