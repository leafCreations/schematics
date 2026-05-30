from PIL import Image, ImageDraw

import helpers.grid as grid_utils
import helpers.utils_schematics as schematics_utils
from helpers.context import SchematicContext
from helpers.types import (
    FacadeElevations,
    RawToken,
    StructureFacadeLayout,
    Token,
)


def _build_structure_elevation_layout(ctx: SchematicContext) -> StructureFacadeLayout:
    block_px = 30
    top_margin = 60
    panel_gap = 50
    side_count = 4

    struct_w = grid_utils.get_structure_width(ctx)
    struct_h = grid_utils.get_structure_depth(ctx)
    max_layers = grid_utils.get_structure_height(ctx)

    panel_w = max(struct_w, struct_h) * block_px
    panel_h = max_layers * block_px
    img_w = (panel_w * side_count) + (panel_gap * (side_count + 1))
    img_h = top_margin + panel_h + 60

    return StructureFacadeLayout(
        block_px=block_px,
        top_margin=top_margin,
        panel_gap=panel_gap,
        panel_w=panel_w,
        panel_h=panel_h,
        img_w=img_w,
        img_h=img_h,
        max_layers=max_layers,
        view_keys=["N", "S", "W", "E"],
        headings={
            "N": "NORTH FAÇADE (Rear)",
            "S": "SOUTH FAÇADE (Front Door)",
            "W": "WEST FAÇADE (Left Side)",
            "E": "EAST FAÇADE (Right Side)",
        },
    )


def _create_structure_elevation_image(
    layout: StructureFacadeLayout,
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (layout["img_w"], layout["img_h"]), (255, 255, 255))

    draw = ImageDraw.Draw(img)

    return img, draw


def _draw_structure_elevation_title(draw: ImageDraw.ImageDraw):
    draw.text(
        (50, 20),
        "STRUCTURE SIDE-VIEW ELEVATIONS - ISOLATED BUILDING FAÇADES PROFILE",
        fill=(30, 30, 30),
    )


def _collect_structure_elevations(
    ctx: SchematicContext,
    layout: StructureFacadeLayout,
) -> FacadeElevations:
    max_layers = layout["max_layers"]

    struct_elevations = FacadeElevations(
        N={y: [] for y in range(max_layers)},
        S={y: [] for y in range(max_layers)},
        W={y: [] for y in range(max_layers)},
        E={y: [] for y in range(max_layers)},
    )

    for y in range(max_layers):
        _collect_north_south_elevation_layer(ctx, struct_elevations, y)
        _collect_west_east_elevation_layer(ctx, struct_elevations, y)

    return struct_elevations


def _collect_north_south_elevation_layer(
    ctx: SchematicContext,
    struct_elevations: FacadeElevations,
    layer_y: int,
):
    struct_w = grid_utils.get_structure_width(ctx)
    struct_h = grid_utils.get_structure_depth(ctx)

    for x in range(struct_w):
        north_token = _find_first_visible_token_along_z(ctx, layer_y, x, range(struct_h))
        south_token = _find_first_visible_token_along_z(
            ctx,
            layer_y,
            x,
            range(struct_h - 1, -1, -1),
        )

        struct_elevations["N"][layer_y].append(north_token)
        struct_elevations["S"][layer_y].append(south_token)


def _collect_west_east_elevation_layer(
    ctx: SchematicContext,
    struct_elevations: FacadeElevations,
    layer_y: int,
):
    struct_w = grid_utils.get_structure_width(ctx)
    struct_h = grid_utils.get_structure_depth(ctx)

    for z in range(struct_h):
        west_token = _find_first_visible_token_along_x(ctx, layer_y, z, range(struct_w))
        east_token = _find_first_visible_token_along_x(
            ctx,
            layer_y,
            z,
            range(struct_w - 1, -1, -1),
        )

        struct_elevations["W"][layer_y].append(west_token)
        struct_elevations["E"][layer_y].append(east_token)


def _find_first_visible_token_along_z(
    ctx: SchematicContext,
    layer_y: int,
    x: int,
    z_range: range,
):
    for z in z_range:
        raw_token = _get_raw_token(ctx, layer_y, z, x)
        token, _direction = schematics_utils.resolve_token_for_render(raw_token)

        if token != ".":
            return raw_token

    return "."


def _find_first_visible_token_along_x(
    ctx: SchematicContext,
    layer_y: int,
    z: int,
    x_range: range,
):
    for x in x_range:
        raw_token = _get_raw_token(ctx, layer_y, z, x)
        token, _direction = schematics_utils.resolve_token_for_render(raw_token)

        if token != ".":
            return raw_token

    return "."


def _get_raw_token(ctx: SchematicContext, layer_y: int, z: int, x: int) -> RawToken:
    if layer_y >= len(ctx.layers):
        return "."

    layer = ctx.layers[layer_y]
    cells = layer.get("cells", [])

    if z >= len(cells):
        return "."

    row = cells[z]

    if x >= len(row):
        return "."

    return row[x]


def _draw_structure_elevation_panels(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    ctx: SchematicContext,
    struct_elevations: FacadeElevations,
    layout: StructureFacadeLayout,
):
    current_x = layout["panel_gap"]
    current_y = layout["top_margin"] + 20

    for view_key in layout["view_keys"]:
        _draw_structure_elevation_heading(draw, view_key, current_x, current_y, layout)

        _draw_structure_elevation_panel(
            img,
            draw,
            ctx,
            struct_elevations[view_key],
            view_key,
            current_x,
            current_y,
            layout,
        )

        current_x += layout["panel_w"] + layout["panel_gap"]


def _draw_structure_elevation_panel(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    ctx: SchematicContext,
    elevation: dict[int, list[RawToken]],
    view_key: str,
    sx: int,
    sy: int,
    layout: StructureFacadeLayout,
):
    block_px = layout["block_px"]
    panel_h = layout["panel_h"]
    max_layers = layout["max_layers"]

    token_count = _get_view_token_count(ctx, view_key)

    for layer_y in range(max_layers):
        row_tokens = elevation.get(layer_y, [])

        for i in range(token_count):
            raw_token = row_tokens[i] if i < len(row_tokens) else "."
            token, _direction = schematics_utils.resolve_token_for_render(raw_token)

            bx = sx + (i * block_px)
            by = sy + panel_h - ((layer_y + 1) * block_px)

            _draw_structure_elevation_cell(
                img,
                draw,
                ctx,
                raw_token,
                token,
                bx,
                by,
                block_px,
            )


def _draw_structure_elevation_heading(
    draw: ImageDraw.ImageDraw,
    view_key: str,
    current_x: int,
    current_y: int,
    layout: StructureFacadeLayout,
):
    draw.text((current_x, current_y - 20), layout["headings"][view_key], fill=(60, 60, 60))


def _get_view_token_count(ctx: SchematicContext, view_key: str) -> int:
    if view_key in ["N", "S"]:
        return grid_utils.get_structure_width(ctx)

    return grid_utils.get_structure_depth(ctx)


def _draw_structure_elevation_cell(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    ctx: SchematicContext,
    raw_token: RawToken,
    token: Token,
    bx: int,
    by: int,
    block_px: int,
):
    rect = [bx, by, bx + block_px, by + block_px]

    if token == ".":
        draw.rectangle(rect, fill=(245, 245, 245), outline=(230, 230, 230))
        return

    if ctx.sideview_textures and schematics_utils.paste_sideview_token(
        img,
        ctx.sideview_textures,
        raw_token,
        (bx, by),
        block_px,
        draw,
    ):
        return

    draw.rectangle(
        rect,
        fill=schematics_utils.get_background_color(token, default=(245, 245, 245)),
        outline=(230, 230, 230),
    )


def _build_structure_elevation_output_path(ctx: SchematicContext):
    return ctx.output_schematics_dir / f"{ctx.name.lower().replace(' ', '_')}_structure_facades.png"


def render_structure_facades(ctx: SchematicContext):
    layout = _build_structure_elevation_layout(ctx)
    struct_elevations = _collect_structure_elevations(ctx, layout)

    img, draw = _create_structure_elevation_image(layout)

    _draw_structure_elevation_title(draw)
    _draw_structure_elevation_panels(img, draw, ctx, struct_elevations, layout)

    output_path = _build_structure_elevation_output_path(ctx)
    img.save(output_path)
