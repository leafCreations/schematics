from contextlib import suppress
from typing import TypeAlias

from PIL import ImageFont

DEJAVU_SANS = "DejaVuSans.ttf"
DEJAVU_SANS_BOLD = "DejaVuSans-Bold.ttf"

Fonts: TypeAlias = dict[str, ImageFont.ImageFont]
FontSpec: TypeAlias = dict[str, tuple[str, int]]


def load_font(path: str, size: int) -> ImageFont.ImageFont:
    with suppress(OSError):
        return ImageFont.truetype(path, size)

    return ImageFont.load_default()


def load_fonts(spec: FontSpec) -> Fonts:
    return {name: load_font(path, size) for name, (path, size) in spec.items()}


def load_layer_panel_fonts() -> Fonts:
    return {
        "floor": ImageFont.load_default(),
        "layer": ImageFont.load_default(),
        "inventory": load_font(DEJAVU_SANS_BOLD, 14),
    }


MATERIALS_FONT_SPEC: FontSpec = {
    "title": (DEJAVU_SANS_BOLD, 26),
    "header": (DEJAVU_SANS_BOLD, 16),
    "body": (DEJAVU_SANS, 15),
    "count": (DEJAVU_SANS_BOLD, 15),
}


def load_materials_fonts() -> Fonts:
    return load_fonts(MATERIALS_FONT_SPEC)
