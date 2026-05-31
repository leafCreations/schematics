from __future__ import annotations

from PIL import Image


def _is_template_margin_pixel(red: int, green: int, blue: int, alpha: int) -> bool:
    return alpha > 128 and red > 240 and green > 240 and blue > 240


def template_content_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    xs: list[int] = []
    ys: list[int] = []

    for y in range(image.size[1]):
        for x in range(image.size[0]):
            red, green, blue, alpha = image.getpixel((x, y))

            if alpha > 128 and not _is_template_margin_pixel(red, green, blue, alpha):
                xs.append(x)
                ys.append(y)

    if not xs:
        return None

    return min(xs), min(ys), max(xs), max(ys)


def fit_template_to_cell(template: Image.Image, size: int) -> Image.Image:
    bbox = template_content_bbox(template)

    if bbox is None:
        return template.resize((size, size), Image.Resampling.NEAREST)

    return template.crop(bbox).resize((size, size), Image.Resampling.NEAREST)
