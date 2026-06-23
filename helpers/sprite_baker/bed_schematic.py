from __future__ import annotations

from PIL import Image

from helpers.paths import PROJECT_CUSTOM_FOLDER
from helpers.sprite_baker.bed_atlas import FOOT_TOP
from helpers.sprite_baker.template_fit import fit_template_to_cell

BED_TOP_TEMPLATE_PATH = PROJECT_CUSTOM_FOLDER / "red_bed.png"
BED_SIDE_HEAD_TEMPLATE_PATH = PROJECT_CUSTOM_FOLDER / "red_bed_top.png"
BED_SIDE_FOOT_TEMPLATE_PATH = PROJECT_CUSTOM_FOLDER / "red_bed_bottom.png"


def _is_blanket_pixel(red: int, green: int, blue: int, alpha: int) -> bool:
    return alpha > 128 and red > 90 and green < 130 and blue < 130


def _is_pillow_pixel(red: int, green: int, blue: int, alpha: int) -> bool:
    return alpha > 128 and red > 180 and green > 180 and blue > 180


def _average_blanket_color(image: Image.Image) -> tuple[int, int, int, int]:
    pixels = [
        image.getpixel((x, y))
        for y in range(image.size[1])
        for x in range(image.size[0])
        if image.getpixel((x, y))[3] > 128
    ]

    if not pixels:
        return (128, 128, 128, 255)

    channels = [int(sum(pixel[index] for pixel in pixels) / len(pixels)) for index in range(3)]
    return (*channels, 255)


def _blanket_source_from_atlas(atlas: Image.Image, size: int) -> Image.Image:
    foot = FOOT_TOP.crop(atlas).resize((size, size), Image.Resampling.NEAREST)
    filled = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fallback = _average_blanket_color(foot)

    for y in range(size):
        row_pixels = [foot.getpixel((x, y)) for x in range(size) if foot.getpixel((x, y))[3] > 128]

        if row_pixels:
            row_fallback = (
                int(sum(pixel[0] for pixel in row_pixels) / len(row_pixels)),
                int(sum(pixel[1] for pixel in row_pixels) / len(row_pixels)),
                int(sum(pixel[2] for pixel in row_pixels) / len(row_pixels)),
                255,
            )
        else:
            row_fallback = fallback

        for x in range(size):
            pixel = foot.getpixel((x, y))
            filled.putpixel((x, y), pixel if pixel[3] > 128 else row_fallback)

    return filled


def _recolor_template(template: Image.Image, blanket_source: Image.Image) -> Image.Image:
    size = template.size[0]
    output = template.copy()
    fallback = _average_blanket_color(blanket_source)

    for y in range(size):
        for x in range(size):
            red, green, blue, alpha = template.getpixel((x, y))

            if alpha < 128 or _is_pillow_pixel(red, green, blue, alpha):
                continue

            if _is_blanket_pixel(red, green, blue, alpha):
                replacement = blanket_source.getpixel((x, y))
                if replacement[3] == 0:
                    replacement = fallback
                output.putpixel((x, y), replacement)

    return output


def _load_top_template_half(part: str) -> Image.Image:
    if not BED_TOP_TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Bed top template not found: {BED_TOP_TEMPLATE_PATH}")

    template = Image.open(BED_TOP_TEMPLATE_PATH).convert("RGBA")
    width, height = template.size
    mid = height // 2

    if part == "head":
        return template.crop((0, 0, width, mid))

    if part == "foot":
        return template.crop((0, mid, width, height))

    raise ValueError(f"Unsupported bed top part: {part}")


def _load_side_template(part: str) -> Image.Image:
    path = BED_SIDE_HEAD_TEMPLATE_PATH if part == "head" else BED_SIDE_FOOT_TEMPLATE_PATH

    if not path.exists():
        raise FileNotFoundError(f"Bed side template not found: {path}")

    return Image.open(path).convert("RGBA")


def compose_bed_top_schematic(
    *,
    part: str,
    atlas: Image.Image,
    size: int,
) -> Image.Image:
    template = fit_template_to_cell(_load_top_template_half(part), size)
    blanket_source = _blanket_source_from_atlas(atlas, size)
    return _recolor_template(template, blanket_source)


def compose_bed_side_schematic(
    *,
    part: str,
    atlas: Image.Image,
    size: int,
) -> Image.Image:
    template = _load_side_template(part).resize((size, size), Image.Resampling.NEAREST)
    blanket_source = _blanket_source_from_atlas(atlas, size)
    return _recolor_template(template, blanket_source)


def compose_bed_inventory_schematic(*, atlas: Image.Image, size: int) -> Image.Image:
    half = max(1, size // 2)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    head = compose_bed_top_schematic(part="head", atlas=atlas, size=size)
    foot = compose_bed_top_schematic(part="foot", atlas=atlas, size=size)
    canvas.paste(head.crop((0, 0, size, half)), (0, 0))
    canvas.paste(foot.crop((0, half, size, size)), (0, half))
    return canvas
