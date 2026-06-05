from PIL import Image

import helpers.constants as constants
import helpers.grid as grid_utils
import helpers.landscape_utils as landscape_utils
import helpers.paths as paths
import helpers.render_image as render_image
import helpers.utils_schematics as schematics_utils
from helpers.context import SchematicContext
from helpers.types import (
    BackgroundColor,
    BBox,
    Cell,
    PathLayout,
    PathPanel,
    Token,
)


def _build_path_layout(ctx: SchematicContext) -> PathLayout:
    block_px = constants.BLOCK_PX
    padding = constants.RENDER_PADDING
    top_margin = constants.PATH_VIEW_TOP_MARGIN
    layers = landscape_utils.path_view_y_keys(ctx)

    site_width = grid_utils.get_site_width(ctx)
    site_depth = grid_utils.get_site_depth(ctx)
    panel_w = site_width * block_px
    panel_h = site_depth * block_px

    img_w = (panel_w * len(layers)) + (padding * (len(layers) + 1))
    img_h = top_margin + panel_h + 80

    return PathLayout(
        block_px=block_px,
        padding=padding,
        top_margin=top_margin,
        layers=layers,
        panel_dim=max(panel_w, panel_h),
        panel_w=panel_w,
        panel_h=panel_h,
        img_w=img_w,
        img_h=img_h,
    )


def _draw_path_layer_header(draw, layer_y: int, panel: PathPanel):
    draw.text(
        (panel["sx"], panel["sy"] - 22),
        f"PROPERTY TOP-DOWN BLUEPRINT -> LAYER Y={layer_y}",
        fill=(40, 40, 40),
    )


def _draw_path_title(draw, layout: PathLayout):
    draw.text(
        (layout["padding"], 20),
        "LANDSCAPING SITE MAP PLANS - PATHWAY SECTORS & ALIGNMENT BUFFERS",
        fill=(30, 30, 30),
    )


def _get_path_panel_position(col_idx: int, layout: PathLayout) -> PathPanel:
    sx = layout["padding"] + col_idx * (layout["panel_w"] + layout["padding"])

    sy = layout["top_margin"]

    return {
        "sx": sx,
        "sy": sy,
    }


def _draw_path_layer_panel(
    img,
    draw,
    ctx: SchematicContext,
    layer_y: int,
    panel: PathPanel,
    layout: PathLayout,
    site_map,
):
    site_width = grid_utils.get_site_width(ctx)
    site_depth = grid_utils.get_site_depth(ctx)

    for z in range(site_depth):
        for x in range(site_width):
            cell = landscape_utils.resolve_path_view_cell(layer_y, x, z, site_map)
            _draw_path_cell(img, draw, ctx, cell, x, z, panel, layout)


def _draw_path_cell(
    img,
    draw,
    ctx: SchematicContext,
    cell: Cell,
    x: int,
    z: int,
    panel: PathPanel,
    layout: PathLayout,
):
    block_px = layout["block_px"]

    bx = panel["sx"] + (x * block_px)
    by = panel["sy"] + (z * block_px)

    rect: BBox = [bx, by, bx + block_px, by + block_px]

    base_background_color = _draw_base_path_cell(draw, cell["base_token"], rect)

    _draw_active_path_cell(img, draw, ctx, cell, rect, bx, by, block_px, base_background_color)

    _draw_path_cell_outline(draw, rect, cell["is_ghost"])


def _draw_base_path_cell(draw, base_token: Token, rect: BBox) -> BackgroundColor:
    base_background_color = schematics_utils.get_background_color(
        base_token,
        default=constants.EMPTY_CELL_COLOR,
    )

    draw.rectangle(rect, fill=base_background_color)

    return base_background_color


def _apply_path_ghost_overlay(img: Image.Image, bx: int, by: int, block_px: int):
    ghost = Image.new("RGBA", (block_px, block_px), (255, 255, 255, 140))
    img.paste(ghost, (bx, by), ghost)


def _draw_active_path_cell(
    img,
    draw,
    ctx: SchematicContext,
    cell: Cell,
    rect: BBox,
    bx: int,
    by: int,
    block_px: int,
    base_background_color: BackgroundColor,
):
    active_token = cell["active_token"]

    if active_token == ".":
        return

    if cell["is_ghost"] and active_token == cell["base_token"]:
        return

    token, _direction = schematics_utils.resolve_token_for_render(active_token)

    if ctx.topdown_textures and schematics_utils.paste_topdown_token(
        img,
        ctx.topdown_textures,
        active_token,
        (bx, by),
        block_px,
    ):
        if cell["is_ghost"]:
            _apply_path_ghost_overlay(img, bx, by, block_px)

        return

    draw.rectangle(
        rect,
        fill=schematics_utils.get_background_color(token, default=base_background_color),
    )


def _draw_path_cell_outline(draw, rect: BBox, is_ghost: bool):
    draw.rectangle(rect, outline=(40, 40, 40, 12 if is_ghost else 25))


def render_path_focused_blueprint(ctx: SchematicContext):
    layout = _build_path_layout(ctx)
    site_map = landscape_utils.generate_full_3d_landscape_sitemap(ctx)

    img, draw = render_image.create_canvas(layout["img_w"], layout["img_h"])

    _draw_path_title(draw, layout)

    for col_idx, layer_y in enumerate(layout["layers"]):
        panel = _get_path_panel_position(col_idx, layout)

        _draw_path_layer_header(draw, layer_y, panel)

        _draw_path_layer_panel(img, draw, ctx, layer_y, panel, layout, site_map)

    output_path = paths.schematic_output_path(ctx, "site_topdown.png")
    img.save(output_path)
