from typing import Literal

from PIL import Image, ImageChops

import helpers.registry_blocks as registry_blocks
import helpers.utils as utils
from helpers.fence_adjacency import (
    classify_fence_variant,
    fence_facing_for_connections,
    resolve_fence_connections,
)
from helpers.log_orientation import resolve_log_orientation
from helpers.structure_tokens import ParsedToken, parse_structure_token
from helpers.types import BackgroundColor, CellGrid, MappedTextureImages, RawToken, Token
from registries.loader import BLOCK_REGISTRY, get_render_textures

TextureView = Literal["top", "side"]

_VIEW_DEFAULT_TEXTURE_KEYS: dict[TextureView, tuple[str, ...]] = {
    "top": ("top", "post", "straight", "single", "bottom", "lower", "upper"),
    "side": ("side", "post", "straight", "single", "bottom", "lower", "upper"),
}


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
            color=registry_blocks.resolve_token_color(entry, parsed),
            part=parsed.variant or defaults.get("part", ""),
        )

    return token, utils.normalize_direction(facing)


def show_interior_view(token: Token) -> bool:
    """Return whether this block appears in site/path overlay views.

    Reads ``visibility.interior`` from blocks.yaml. Defaults to True when omitted.
    """
    if token == ".":
        return False

    entry = BLOCK_REGISTRY.get(token, {})
    visibility = entry.get("visibility", {})
    interior_visible = visibility.get("interior")

    return True if interior_visible is None else interior_visible


def _build_directional_side_keys(
    raw_token: RawToken,
    parsed_token: str,
    direction: str | None,
) -> list[str]:
    if not direction:
        return []

    raw_base_token = raw_token.split("@", 1)[0].split("#", 1)[0]
    clean_base_token = raw_base_token.split(":", 1)[0]

    return [
        f"{raw_base_token}#side:{direction}",
        f"{raw_base_token}#{direction}",
        f"{clean_base_token}#side:{direction}",
        f"{clean_base_token}#{direction}",
        f"{parsed_token}#side:{direction}",
        f"{parsed_token}#{direction}",
    ]


def _build_texture_key_candidates(
    raw_token: RawToken,
    parsed: ParsedToken,
    base_token: Token,
    defaults: dict,
    render_textures: dict,
    textures: MappedTextureImages,
    view: TextureView,
    direction: str | None = None,
) -> list[str]:
    texture_keys: list[str] = []

    if view == "side":
        texture_keys.extend(_build_directional_side_keys(raw_token, parsed.token, direction))

    if parsed.material:
        color_prefix = f"{parsed.token}:{parsed.material}"
        if parsed.variant:
            texture_keys.append(f"{color_prefix}#{parsed.variant}")
        texture_keys.append(color_prefix)

    if raw_token in textures:
        texture_keys.append(raw_token)

    if parsed.variant:
        texture_keys.append(f"{parsed.token}#{parsed.variant}")

    for default_key in (
        defaults.get("shape"),
        defaults.get("type"),
        defaults.get("part"),
        *_VIEW_DEFAULT_TEXTURE_KEYS[view],
    ):
        if default_key and default_key in render_textures:
            texture_keys.append(f"{parsed.token}#{default_key}")

    texture_keys.append(base_token)

    return texture_keys


def _resolve_texture_key(texture_keys: list[str], textures: MappedTextureImages) -> str | None:
    return next((key for key in texture_keys if key in textures), None)


def _resize_texture(tex: Image.Image, size: int | None) -> Image.Image:
    if size is not None and tex.size != (size, size):
        return tex.resize((size, size), resample=Image.Resampling.NEAREST)

    return tex


_CORNER_STAIR_FACING_CCW = {"N": 0, "E": 90, "S": 180, "W": 270}
# Corner stair sprites are baked in south-facing orientation; rotate to match ``@direction``.
_CORNER_STAIR_BAKE_FACING = "S"


def _is_corner_stair_shape(parsed: ParsedToken, entry: dict) -> bool:
    if entry.get("behavior") != "stairs":
        return False

    shape = parsed.variant or entry.get("defaults", {}).get("shape", "straight")
    return shape != "straight"


def _corner_stair_facing_rotation(direction: str | None) -> int:
    if direction is None:
        return 0

    target = _CORNER_STAIR_FACING_CCW.get(direction)
    if target is None:
        return 0

    base = _CORNER_STAIR_FACING_CCW[_CORNER_STAIR_BAKE_FACING]
    return (target - base) % 360


def corner_stair_facing_rotation(direction: str | None) -> int:
    return _corner_stair_facing_rotation(direction)


def is_corner_stair_shape(parsed: ParsedToken, entry: dict) -> bool:
    return _is_corner_stair_shape(parsed, entry)


def _build_log_texture_keys(parsed: ParsedToken, orientation: str) -> list[str]:
    keys: list[str] = []

    if parsed.material:
        if orientation != "vertical":
            keys.append(f"LOG:{parsed.material}#{orientation}")
        keys.append(f"LOG:{parsed.material}")

    if orientation != "vertical":
        keys.append(f"LOG#{orientation}")

    keys.append(parsed.token)
    return keys


def _prepare_topdown_texture(
    tex: Image.Image,
    base_token: Token,
    direction: str | None,
    rotation: int,
    *,
    corner_stair_shape: bool = False,
) -> Image.Image:
    tex = get_texture_for_render(base_token, tex)

    if corner_stair_shape:
        facing_rotation = _corner_stair_facing_rotation(direction)
        if facing_rotation:
            tex = utils.rotate_texture_by_degrees(tex, facing_rotation)
    elif direction:
        tex = utils.rotate_directional_texture(tex, direction)

    if rotation:
        tex = utils.rotate_texture_by_degrees(tex, rotation)

    return tex


def _paste_prepared_texture(img, tex: Image.Image, xy) -> None:
    img.paste(tex, xy, tex if tex.mode == "RGBA" else None)


def _build_fence_texture_keys(parsed: ParsedToken, variant: str) -> list[str]:
    keys: list[str] = []

    if parsed.material:
        keys.append(f"FENCE:{parsed.material}#{variant}")
        keys.append(f"FENCE:{parsed.material}")

    keys.append(f"FENCE#{variant}")
    keys.append(parsed.token)
    return keys


def _paste_token(
    img,
    textures: MappedTextureImages,
    raw_token: RawToken,
    xy,
    view: TextureView,
    size: int | None = None,
    *,
    layer_cells: CellGrid | None = None,
    cell_x: int | None = None,
    cell_z: int | None = None,
) -> bool:
    parsed = parse_structure_token(raw_token)

    if parsed is None:
        return False

    base_token, resolved_direction = resolve_token_for_render(raw_token)
    entry = BLOCK_REGISTRY.get(parsed.token, {})
    defaults = entry.get("defaults", {})
    render_textures = get_render_textures(entry)
    direction = resolved_direction

    if view == "side":
        direction = parsed.direction or resolved_direction or defaults.get("direction")

    if (
        view == "top"
        and entry.get("behavior") == "fence"
        and layer_cells is not None
        and cell_x is not None
        and cell_z is not None
    ):
        connections = resolve_fence_connections(layer_cells, cell_x, cell_z)
        variant = classify_fence_variant(connections)
        direction = fence_facing_for_connections(variant, connections)
        texture_keys = _build_fence_texture_keys(parsed, variant)
    elif view == "top" and entry.get("behavior") == "log":
        orientation = resolve_log_orientation(parsed, entry)
        texture_keys = _build_log_texture_keys(parsed, orientation)
    else:
        texture_keys = _build_texture_key_candidates(
            raw_token,
            parsed,
            base_token,
            defaults,
            render_textures,
            textures,
            view,
            direction if view == "side" else None,
        )

    texture_key = _resolve_texture_key(texture_keys, textures)

    if texture_key is None:
        return False

    tex = textures[texture_key]

    if view == "top":
        tex = _prepare_topdown_texture(
            tex,
            base_token,
            direction,
            parsed.rotation,
            corner_stair_shape=_is_corner_stair_shape(parsed, entry),
        )

        if entry.get("behavior") == "log":
            orientation = resolve_log_orientation(parsed, entry)
            if orientation == "east_west":
                tex = utils.rotate_texture_by_degrees(tex, 90)

    tex = _resize_texture(tex, size)
    _paste_prepared_texture(img, tex, xy)
    return True


def paste_topdown_token(
    img,
    textures,
    raw_token: RawToken,
    xy,
    size=None,
    *,
    layer_cells: CellGrid | None = None,
    cell_x: int | None = None,
    cell_z: int | None = None,
) -> bool:
    return _paste_token(
        img,
        textures,
        raw_token,
        xy,
        "top",
        size,
        layer_cells=layer_cells,
        cell_x=cell_x,
        cell_z=cell_z,
    )


def paste_sideview_token(img, textures, raw_token: RawToken, xy, size=None) -> bool:
    return _paste_token(img, textures, raw_token, xy, "side", size)


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


def get_texture_for_render(token: Token, texture: Image.Image) -> Image.Image:
    background_color = get_background_color(token, default=None)

    if background_color is None:
        return texture

    solid = Image.new("RGBA", texture.size, tuple(background_color) + (255,))

    return ImageChops.multiply(texture, solid)
