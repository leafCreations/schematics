from __future__ import annotations

from PIL import Image, ImageDraw

STAIR_SHAPES = frozenset(
    {
        "straight",
        "outer_left",
        "outer_right",
        "inner_left",
        "inner_right",
    }
)


def build_stair_top_mask(size: int, shape: str) -> Image.Image:
    """Build a south-facing schematic stair mask for top-down view.

    The renderer rotates corner shapes by ``@direction`` so tokens match worldgen.
    """
    if shape not in STAIR_SHAPES:
        raise ValueError(f"Unsupported stair shape: {shape}")

    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    half = size // 2
    last = size - 1

    draw.rectangle((0, 0, last, last), fill=255)

    if shape == "straight":
        draw.rectangle((0, 0, last, half - 1), fill=0)
    elif shape == "outer_left":
        draw.rectangle((0, 0, half - 1, half - 1), fill=0)
    elif shape == "outer_right":
        draw.rectangle((half, 0, last, half - 1), fill=0)
    elif shape == "inner_left":
        draw.rectangle((half, half, last, last), fill=0)
    elif shape == "inner_right":
        draw.rectangle((0, half, half - 1, last), fill=0)

    return mask


def build_stair_side_mask(size: int, shape: str) -> Image.Image:
    """Build a north-facing schematic stair mask for facade side view."""
    if shape not in STAIR_SHAPES:
        raise ValueError(f"Unsupported stair shape: {shape}")

    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    half = size // 2
    last = size - 1

    # Lower step fills the bottom half; upper step adds the top-right quadrant.
    draw.rectangle((0, half, last, last), fill=255)
    draw.rectangle((half, 0, last, half - 1), fill=255)

    if shape == "outer_left":
        draw.rectangle((0, 0, half - 1, half - 1), fill=0)
    elif shape == "outer_right":
        draw.rectangle((half, 0, last, half - 1), fill=0)
    elif shape == "inner_left":
        draw.rectangle((half, half, last, last), fill=0)
    elif shape == "inner_right":
        draw.rectangle((0, half, half - 1, last), fill=0)

    return mask


def apply_texture_mask(texture: Image.Image, mask: Image.Image) -> Image.Image:
    canvas = Image.new("RGBA", texture.size, (0, 0, 0, 0))
    canvas.paste(texture, (0, 0), mask)
    return canvas
