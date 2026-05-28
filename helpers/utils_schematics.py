from collections import Counter

from PIL import Image, ImageChops

import helpers.utils as utils
from helpers.structure_tokens import parse_structure_token
from helpers.types import BackgroundColor, RawToken, Token
from registries.loader import BLOCK_REGISTRY


def get_blockstate_value(blockstate: str | None, key: str) -> str | None:
    if not blockstate:
        return None

    for part in blockstate.split(","):
        name, _, value = part.partition("=")

        if name.strip() == key:
            return value.strip()

    return None


def resolve_token_for_render(raw_token: RawToken) -> tuple[Token, str | None]:
    parsed = parse_structure_token(raw_token)

    if parsed is None:
        return ".", None

    token = parsed.token
    entry = BLOCK_REGISTRY.get(token)

    if not entry:
        return token, utils.normalize_direction(parsed.direction)

    if parsed.direction:
        return token, utils.normalize_direction(parsed.direction)

    defaults = entry.get("defaults", {})
    default_direction = utils.normalize_direction(defaults.get("direction"))

    if default_direction is not None:
        return token, default_direction

    minecraft = entry.get("minecraft", {})
    blockstates = minecraft.get("blockstates", {})

    facing = blockstates.get("facing")

    if isinstance(facing, str):
        facing = facing.format(
            direction=parsed.direction or defaults.get("direction", ""),
            variant=parsed.variant or defaults.get("variant", ""),
            material=parsed.material or entry.get("material_default", ""),
            part=parsed.variant or defaults.get("part", ""),
        )

    return token, utils.normalize_direction(facing)


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


def _get_raw_token_direction(raw_token: RawToken) -> str | None:
    if "@" not in raw_token:
        return None

    direction = raw_token.split("@", 1)[1]
    direction = direction.split("#", 1)[0]
    direction = direction.split(":", 1)[0]

    return utils.normalize_direction(direction)


def paste_topdown_token(img, textures, raw_token: RawToken, xy, size=None, draw=None) -> bool:
    parsed = parse_structure_token(raw_token)

    if parsed is None:
        return False

    base_token, direction = resolve_token_for_render(raw_token)

    entry = BLOCK_REGISTRY.get(parsed.token, {})
    defaults = entry.get("defaults", {})
    render_textures = entry.get("render", {}).get("textures", {})

    texture_keys = []

    if raw_token in textures:
        texture_keys.append(raw_token)

    if parsed.variant:
        texture_keys.append(f"{parsed.token}#{parsed.variant}")

    for default_key in (
        defaults.get("shape"),
        defaults.get("type"),
        defaults.get("part"),
        "top",
        "post",
        "straight",
        "single",
        "bottom",
        "lower",
        "upper",
    ):
        if default_key and default_key in render_textures:
            texture_keys.append(f"{parsed.token}#{default_key}")

    texture_keys.append(base_token)

    texture_key = next((key for key in texture_keys if key in textures), None)

    if texture_key is None:
        return False

    tex = textures[texture_key]
    tex = get_texture_for_render(base_token, tex)

    if size is not None and tex.size != (size, size):
        tex = tex.resize((size, size), resample=Image.Resampling.NEAREST)

    if direction:
        tex = utils.rotate_directional_texture(tex, direction)

    img.paste(tex, xy, tex if tex.mode == "RGBA" else None)
    return True


def paste_sideview_token(img, textures, raw_token: RawToken, xy, size=None, draw=None) -> bool:
    parsed = parse_structure_token(raw_token)

    if parsed is None:
        return False

    base_token, resolved_direction = resolve_token_for_render(raw_token)

    entry = BLOCK_REGISTRY.get(parsed.token, {})
    defaults = entry.get("defaults", {})
    render_textures = entry.get("render", {}).get("textures", {})

    direction = parsed.direction or resolved_direction or defaults.get("direction")

    texture_keys = []

    raw_base_token = raw_token.split("@", 1)[0].split("#", 1)[0]
    clean_base_token = raw_base_token.split(":", 1)[0]

    if direction:
        texture_keys.extend(
            [
                f"{raw_base_token}#side:{direction}",
                f"{raw_base_token}#{direction}",
                f"{clean_base_token}#side:{direction}",
                f"{clean_base_token}#{direction}",
                f"{parsed.token}#side:{direction}",
                f"{parsed.token}#{direction}",
            ]
        )

    if raw_token in textures:
        texture_keys.append(raw_token)

    if parsed.variant:
        texture_keys.append(f"{parsed.token}#{parsed.variant}")

    for default_key in (
        defaults.get("shape"),
        defaults.get("type"),
        defaults.get("part"),
        "side",
        "post",
        "straight",
        "single",
        "bottom",
        "lower",
        "upper",
    ):
        if default_key and default_key in render_textures:
            texture_keys.append(f"{parsed.token}#{default_key}")

    texture_keys.append(base_token)

    texture_key = next((key for key in texture_keys if key in textures), None)

    if texture_key is None:
        return False

    tex = textures[texture_key]

    if size is not None and tex.size != (size, size):
        tex = tex.resize((size, size), resample=Image.Resampling.NEAREST)

    img.paste(tex, xy, tex if tex.mode == "RGBA" else None)
    return True


def get_background_color(token: Token, default=(245, 245, 245)) -> BackgroundColor | None:
    entry = BLOCK_REGISTRY.get(token, {})
    render = entry.get("render", {})

    background_color = render.get("background_color")

    if not background_color:
        return default

    if isinstance(background_color, str):
        hex_color = background_color.lstrip("#")

        if len(hex_color) == 6:
            return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    if isinstance(background_color, list | tuple) and len(background_color) == 3:
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


def collect_inventory_counts(
    raw_tokens: list[RawToken],
) -> tuple[Counter, dict[str, Token]]:
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


def get_texture_for_render(token: Token, texture: Image.Image) -> Image.Image:
    background_color = get_background_color(token, default=None)

    if background_color is None:
        return texture

    solid = Image.new("RGBA", texture.size, tuple(background_color) + (255,))

    return ImageChops.multiply(texture, solid)
