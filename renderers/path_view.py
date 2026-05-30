from PIL import Image

import helpers.cells as cell_utils
import helpers.constants as constants
import helpers.grid as grid_utils
import helpers.landscape_utils as landscape_utils
import helpers.path_geometry as path_geometry
import helpers.paths as paths
import helpers.render_image as render_image
import helpers.utils_schematics as schematics_utils
from helpers.context import SchematicContext
from helpers.types import (
    BackgroundColor,
    Cell,
    Layers,
    PathLayout,
    PathPanel,
    RawToken,
    SiteLayer,
    Token,
)


def _build_path_layout(ctx: SchematicContext) -> PathLayout:
    block_px = constants.BLOCK_PX
    padding = 50
    top_margin = 80
    layers = [-1, 0, 1]

    site_size = grid_utils.get_site_size(ctx)
    panel_dim = site_size * block_px

    img_w = (panel_dim * len(layers)) + (padding * (len(layers) + 1))
    img_h = top_margin + panel_dim + 80

    return PathLayout(
        block_px=block_px,
        padding=padding,
        top_margin=top_margin,
        layers=layers,
        panel_dim=panel_dim,
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
    sx = layout["padding"] + col_idx * (layout["panel_dim"] + layout["padding"])

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
    site_layer: SiteLayer,
):
    site_size = grid_utils.get_site_size(ctx)
    geom = path_geometry.get_path_geometry(ctx)

    for z in range(site_size):
        for x in range(site_size):
            cell = _resolve_path_cell(ctx, layer_y, x, z, site_layer, geom)
            _draw_path_cell(img, draw, ctx, cell, x, z, panel, layout)


def _resolve_path_cell(
    ctx: SchematicContext,
    layer_y: int,
    x: int,
    z: int,
    site_layer: SiteLayer,
    geom: path_geometry.PathGeometry,
) -> Cell:
    base_token = site_layer[z][x]

    cell = Cell(
        base_token=base_token,
        active_token=".",
        is_ghost=False,
        is_ground_layer=False,
    )

    if layer_y == -1:
        cell["active_token"] = base_token
        cell["is_ground_layer"] = True
        return cell

    structure_token = _get_structure_overlay_token(ctx, layer_y, x, z)

    if structure_token != ".":
        cell["active_token"] = structure_token
        return cell

    lighting_token = _get_lighting_overlay_token(ctx, layer_y, x, z, geom)

    if lighting_token != ".":
        cell["active_token"] = lighting_token
        return cell

    cell["active_token"] = base_token
    cell["is_ghost"] = True

    return cell


def _get_structure_overlay_token(ctx: SchematicContext, layer_y: int, x: int, z: int) -> RawToken:
    raw_token = cell_utils.get_structure_cell_at_site(ctx, layer_y, x, z)
    token, _direction = schematics_utils.resolve_token_for_render(raw_token)

    if token == ".":
        return "."

    if not schematics_utils.show_interior_view(token):
        return "."

    return raw_token


def _get_lighting_overlay_token(
    ctx: SchematicContext,
    layer_y: int,
    x: int,
    z: int,
    geom: path_geometry.PathGeometry,
) -> Token:
    if layer_y == 0:
        lighting_token = "FENCE"
    elif layer_y == 1:
        lighting_token = "TORCH"
    else:
        return "."

    if not geom.is_lighting_row(z):
        return "."

    if not geom.is_lighting_column(x):
        return "."

    return lighting_token


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

    rect = [bx, by, bx + block_px, by + block_px]

    base_background_color = _draw_base_path_cell(draw, cell["base_token"], rect)

    _draw_active_path_cell(img, draw, ctx, cell, rect, bx, by, block_px, base_background_color)

    _draw_path_cell_outline(draw, rect, cell["is_ghost"])


def _draw_base_path_cell(draw, base_token: Token, layers: Layers) -> BackgroundColor:
    base_background_color = schematics_utils.get_background_color(
        base_token, default=(245, 245, 245)
    )

    draw.rectangle(layers, fill=base_background_color)

    return base_background_color


def _apply_path_ghost_overlay(img: Image.Image, bx: int, by: int, block_px: int):
    ghost = Image.new("RGBA", (block_px, block_px), (255, 255, 255, 140))
    img.paste(ghost, (bx, by), ghost)


def _draw_active_path_cell(
    img,
    draw,
    ctx: SchematicContext,
    cell: Cell,
    layers: Layers,
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
        draw,
    ):
        if cell["is_ghost"]:
            _apply_path_ghost_overlay(img, bx, by, block_px)

        return

    draw.rectangle(
        layers,
        fill=schematics_utils.get_background_color(token, default=base_background_color),
    )


def _draw_path_cell_outline(draw, layers: Layers, is_ghost: bool):
    draw.rectangle(layers, outline=(40, 40, 40, 12 if is_ghost else 25))


def render_path_focused_blueprint(ctx: SchematicContext):
    layout = _build_path_layout(ctx)
    site_layer = landscape_utils.generate_landscape_y_minus_1_sitelayer(ctx)

    img, draw = render_image.create_canvas(layout["img_w"], layout["img_h"])

    _draw_path_title(draw, layout)

    for col_idx, layer_y in enumerate(layout["layers"]):
        panel = _get_path_panel_position(col_idx, layout)

        _draw_path_layer_header(draw, layer_y, panel)

        _draw_path_layer_panel(img, draw, ctx, layer_y, panel, layout, site_layer)

    output_path = paths.schematic_output_path(ctx, "site_topdown.png")
    img.save(output_path)
