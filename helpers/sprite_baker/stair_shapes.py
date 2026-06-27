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

# ~45% alpha for tread-complement (riser) ghost — distinct from slab void (0) and tread (255).
STAIR_RISER_GHOST_ALPHA = 115
# Lerp riser sample RGB toward white so stone/brick ghosts read lighter than tread at same α.
STAIR_RISER_GHOST_LIGHTEN = 0.28


def lighten_texture_for_riser_ghost(texture: Image.Image, amount: float) -> Image.Image:
    """Blend ``texture`` toward white — riser ghost reads lighter on Top Down grids."""
    if amount <= 0:
        return texture.convert("RGBA")
    rgba = texture.convert("RGBA")
    white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    return Image.blend(rgba, white, amount)


def _draw_stair_top_voids(
    draw: ImageDraw.ImageDraw,
    shape: str,
    *,
    half: int,
    last: int,
    fill: int,
) -> None:
    """Draw tread-complement (L-void) rectangles — shared tread clear and riser fill."""
    if shape == "straight":
        draw.rectangle((0, 0, last, half - 1), fill=fill)
    elif shape == "outer_left":
        draw.rectangle((0, 0, half - 1, half - 1), fill=fill)
    elif shape == "outer_right":
        draw.rectangle((half, 0, last, half - 1), fill=fill)
    elif shape == "inner_left":
        draw.rectangle((half, half, last, last), fill=fill)
    elif shape == "inner_right":
        draw.rectangle((0, half, half - 1, last), fill=fill)


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
    _draw_stair_top_voids(draw, shape, half=half, last=last, fill=0)

    return mask


def build_stair_riser_top_mask(size: int, shape: str) -> Image.Image:
    """Mask for tread-complement regions (L-void) — same geometry as tread clears."""
    if shape not in STAIR_SHAPES:
        raise ValueError(f"Unsupported stair shape: {shape}")

    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    half = size // 2
    last = size - 1

    _draw_stair_top_voids(draw, shape, half=half, last=last, fill=255)

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


def apply_texture_mask_alpha(
    texture: Image.Image,
    mask: Image.Image,
    alpha: int,
) -> Image.Image:
    """Paste ``texture`` through ``mask`` scaled to ``alpha`` (0–255)."""
    if alpha >= 255:
        return apply_texture_mask(texture, mask)
    scaled = mask.point(lambda value: value * alpha // 255 if value else 0)
    return apply_texture_mask(texture, scaled)
