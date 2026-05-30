from collections.abc import Callable

from PIL import Image, ImageDraw

import helpers.utils_schematics as schematics_utils
from helpers.context import SchematicContext
from helpers.types import FacadeElevations, RawToken

CellGetter = Callable[[int, int, int], RawToken]
VisibilityPredicate = Callable[[RawToken], bool]


def is_non_empty_token(token: RawToken) -> bool:
    return token != "."


def is_structure_cell_visible(raw_token: RawToken) -> bool:
    token, _direction = schematics_utils.resolve_token_for_render(raw_token)
    return token != "."


def find_first_visible_along_z(
    get_token: CellGetter,
    layer_y: int,
    x: int,
    z_range: range,
    is_visible: VisibilityPredicate,
) -> RawToken:
    for z in z_range:
        token = get_token(layer_y, x, z)

        if is_visible(token):
            return token

    return "."


def find_first_visible_along_x(
    get_token: CellGetter,
    layer_y: int,
    z: int,
    x_range: range,
    is_visible: VisibilityPredicate,
) -> RawToken:
    for x in x_range:
        token = get_token(layer_y, x, z)

        if is_visible(token):
            return token

    return "."


def collect_facade_elevations(
    layer_keys: list[int],
    width: int,
    depth: int,
    get_token: CellGetter,
    *,
    is_visible: VisibilityPredicate = is_non_empty_token,
) -> FacadeElevations:
    elevations = FacadeElevations(
        N={layer_y: [] for layer_y in layer_keys},
        S={layer_y: [] for layer_y in layer_keys},
        W={layer_y: [] for layer_y in layer_keys},
        E={layer_y: [] for layer_y in layer_keys},
    )

    for layer_y in layer_keys:
        for x in range(width):
            elevations["N"][layer_y].append(
                find_first_visible_along_z(get_token, layer_y, x, range(depth), is_visible)
            )
            elevations["S"][layer_y].append(
                find_first_visible_along_z(
                    get_token,
                    layer_y,
                    x,
                    range(depth - 1, -1, -1),
                    is_visible,
                )
            )

        for z in range(depth):
            elevations["W"][layer_y].append(
                find_first_visible_along_x(get_token, layer_y, z, range(width), is_visible)
            )
            elevations["E"][layer_y].append(
                find_first_visible_along_x(
                    get_token,
                    layer_y,
                    z,
                    range(width - 1, -1, -1),
                    is_visible,
                )
            )

    return elevations


def draw_facade_cell(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    ctx: SchematicContext,
    raw_token: RawToken,
    bx: int,
    by: int,
    block_px: int,
    *,
    empty_fill: tuple[int, int, int] = (245, 245, 245),
    empty_outline: tuple[int, int, int] | None = (230, 230, 230),
    fallback_default: tuple[int, int, int] = (245, 245, 245),
    fallback_outline: tuple[int, int, int] | None = (230, 230, 230),
) -> None:
    rect = [bx, by, bx + block_px, by + block_px]
    token, _direction = schematics_utils.resolve_token_for_render(raw_token)

    if token == ".":
        if empty_outline is None:
            draw.rectangle(rect, fill=empty_fill)
        else:
            draw.rectangle(rect, fill=empty_fill, outline=empty_outline)
        return

    if ctx.sideview_textures and schematics_utils.paste_sideview_token(
        img,
        ctx.sideview_textures,
        raw_token,
        (bx, by),
        block_px,
    ):
        return

    fill = schematics_utils.get_background_color(token, default=fallback_default)

    if fallback_outline is None:
        draw.rectangle(rect, fill=fill)
    else:
        draw.rectangle(rect, fill=fill, outline=fallback_outline)
