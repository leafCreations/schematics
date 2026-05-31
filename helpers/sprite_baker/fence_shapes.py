from __future__ import annotations

from PIL import Image, ImageDraw

from helpers.fence_adjacency import _CANONICAL_CONNECTIONS, FENCE_VARIANTS


def build_fence_top_mask(size: int, connections: frozenset[str]) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)

    def scaled(value: int) -> int:
        return (value * size + 8) // 16

    x0 = scaled(6)
    x1 = scaled(9)
    north = "north" in connections
    south = "south" in connections
    east = "east" in connections
    west = "west" in connections
    horizontal = east or west

    if not connections:
        draw.rectangle((x0, scaled(4), x1, scaled(9)), fill=255)
        return mask

    if horizontal:
        draw.rectangle((0, scaled(1), size - 1, scaled(3)), fill=255)
        draw.rectangle((0, scaled(7), size - 1, scaled(9)), fill=255)

    y0 = scaled(0) if north else scaled(4)
    y1 = scaled(15) if south else scaled(9)
    draw.rectangle((x0, y0, x1, y1), fill=255)

    return mask


def build_fence_top_mask_for_variant(size: int, variant: str) -> Image.Image:
    if variant not in FENCE_VARIANTS:
        raise ValueError(f"Unsupported fence variant: {variant}")

    return build_fence_top_mask(size, _CANONICAL_CONNECTIONS[variant])


def build_fence_side_mask(size: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)

    def scaled(value: int) -> int:
        return (value * size + 8) // 16

    x0 = scaled(6)
    x1 = scaled(9)
    draw.rectangle((x0, scaled(0), x1, size - 1), fill=255)
    draw.rectangle((0, scaled(1), size - 1, scaled(3)), fill=255)
    draw.rectangle((0, scaled(7), size - 1, scaled(9)), fill=255)
    return mask


def apply_texture_mask(texture: Image.Image, mask: Image.Image) -> Image.Image:
    canvas = Image.new("RGBA", texture.size, (0, 0, 0, 0))
    canvas.paste(texture, (0, 0), mask)
    return canvas
