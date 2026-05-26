from typing import Counter
from registries.loader import BLOCK_REGISTRY
from PIL import Image, ImageChops
import helpers.utils as utils
from helpers.types import Token, RawToken

def resolve_schematic_token(raw_token: RawToken) -> Token:
    """Return (base_token, direction) for schematic rendering/counting.

    Direction comes only from BLOCK_REGISTRY[token]["schematic"]["direction"].
    """

    token = raw_token.split("@")[0]

    if token == ".":
        return ".", None

    entry = BLOCK_REGISTRY.get(token)

    if entry:
        schematic = entry.get("schematic", {})
        direction = utils.normalize_direction(schematic.get("direction"))
        return token, direction

    return token, None

def show_interior_view(token: Token) -> bool:
    """Return whether this block should appear in interior/path overlays.

    blocks.yaml may define showInteriorView: false at the token root
    to hide interior-only blocks from landscaping/path views.
    Missing values default to True.
    """
    if token == ".":
        return False

    entry = BLOCK_REGISTRY.get(token, {})
    schematic = entry.get("schematic", {})
    return schematic.get("showInteriorView", True) is not False

def paste_schematic_token(img, textures, raw_token: RawToken, xy, size=None, draw=None) -> bool:
    """Paste a token texture using the raw token, not the stripped base token.

    Any schematic token with a parsed direction will rotate.
    Tokens without direction render in their default orientation.
    """
    base_token, direction = resolve_schematic_token(raw_token)

    if base_token not in textures:
        return False

    tex = textures[base_token]

    if size is not None and tex.size != (size, size):
        tex = tex.resize((size, size), resample=Image.Resampling.NEAREST)

    if direction is not None:
        tex = utils.rotate_directional_texture(tex, direction)

    img.paste(
        tex,
        xy,
        tex if tex.mode == "RGBA" else None
    )    

    return True

def get_background_color(token: Token, default=(245, 245, 245)) -> tuple[int, int, int] | None:
    entry = BLOCK_REGISTRY.get(token, {})
    schematic = entry.get("schematic", {})

    background_color = schematic.get("background_color")

    if not background_color:
        return default

    if isinstance(background_color, str):
        hex_color = background_color.lstrip("#")

        if len(hex_color) == 6:
            return tuple(
                int(hex_color[i:i + 2], 16)
                for i in (0, 2, 4)
            )

    if isinstance(background_color, (list, tuple)) and len(background_color) == 3:
        return tuple(background_color)

    return default

def get_display_name(token: Token) -> str:
    entry = BLOCK_REGISTRY.get(token)

    if entry:
        return entry.get("display_name", token)

    return token

def get_inventory_group(token: Token) -> str:
    entry = BLOCK_REGISTRY.get(token, {})

    category = entry.get("category")
    if category:
        return category

    return get_display_name(token)

def collect_inventory_counts(raw_tokens: list[RawToken]) -> tuple[Counter, dict[str, Token]]:
    grouped_counts = Counter()
    group_icons = {}

    for token in raw_tokens:
        if token == ".":
            continue

        group_name = get_inventory_group(token)
        grouped_counts[group_name] += 1

        if group_name not in group_icons:
            group_icons[group_name] = token

    return grouped_counts, group_icons

def material_sort_key(item: tuple[str, int]) -> str:
    token, _count = item
    return get_display_name(token).lower()

SIDE_VIEW_TORCH_BACKING_BY_VIEW = {
    "N": {"in"},
    "S": {"is"},
    "E": {"ie"},
    "W": {"iw"},
}

SIDE_VIEW_TORCH_TOKENS = {"in", "is", "ie", "iw", "it"}

def paste_side_view_token(img, textures, raw_token: RawToken, xy, block_px, view_key=None) -> bool:
    x, y = xy

    base_token, direction = resolve_schematic_token(raw_token)
    token = raw_token.split("@")[0]

    if token in SIDE_VIEW_TORCH_TOKENS:
        should_show_backing = token in SIDE_VIEW_TORCH_BACKING_BY_VIEW.get(view_key, set())

        if should_show_backing and "P" in textures:
            img.paste(
                textures["P"],
                (x, y),
                textures["P"] if textures["P"].mode == "RGBA" else None
            )

        if "i" in textures:
            torch_size = int(block_px * 0.60)
            offset = (block_px - torch_size) // 2
            torch_tex = textures["i"].resize(
                (torch_size, torch_size),
                resample=Image.Resampling.NEAREST
            )
            img.paste(
                torch_tex,
                (x + offset, y + offset),
                torch_tex if torch_tex.mode == "RGBA" else None
            )
        return True

    if base_token in textures:
        tex = textures[base_token]

        if tex.size != (block_px, block_px):
            tex = tex.resize(
                (block_px, block_px),
                resample=Image.Resampling.NEAREST
            )

        if direction is not None:
            tex = utils.rotate_directional_texture(tex, direction)

        img.paste(
            tex,
            (x, y),
            tex if tex.mode == "RGBA" else None
        )
        return True

    return False

def get_texture_for_render(token: Token, texture: Image.Image) -> Image.Image:
    background_color = get_background_color(token, default=None)

    if background_color is None:
        return texture

    solid = Image.new(
        "RGBA",
        texture.size,
        tuple(background_color) + (255,)
    )

    return ImageChops.multiply(texture, solid)