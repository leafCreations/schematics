from PIL import Image, ImageDraw

import helpers.cells as cell_utils
import helpers.constants as constants
import helpers.facade_projection as facade_projection
import helpers.grid as grid_utils
import helpers.paths as paths
import helpers.render_image as render_image
from helpers.context import SchematicContext
from helpers.layer_visibility import visible_layer_array_indices
from helpers.layers import get_layer_display_name
from helpers.types import (
    FacadeElevations,
    RawToken,
    StructureFacadeLayout,
)

Y_LABEL_WIDTH = 140


def structure_facade_row_labels(
    ctx: SchematicContext,
    visible_layer_indices: list[int],
) -> list[str]:
    return [
        get_layer_display_name(ctx.layers[layer_index]) for layer_index in visible_layer_indices
    ]


def _build_structure_elevation_layout(ctx: SchematicContext) -> StructureFacadeLayout:
    block_px = constants.BLOCK_PX
    top_margin = 60
    panel_gap = 50
    side_count = 4

    struct_w = grid_utils.get_structure_width(ctx)
    struct_h = grid_utils.get_structure_depth(ctx)
    visible_layers = visible_layer_array_indices(ctx.layers, ctx.grid)
    max_layers = max(len(visible_layers), 1)

    panel_w = max(struct_w, struct_h) * block_px
    panel_h = max_layers * block_px
    y_label_width = Y_LABEL_WIDTH
    img_w = y_label_width + (panel_w * side_count) + (panel_gap * (side_count + 1))
    img_h = top_margin + panel_h + 60

    return StructureFacadeLayout(
        block_px=block_px,
        top_margin=top_margin,
        panel_gap=panel_gap,
        y_label_width=y_label_width,
        panel_w=panel_w,
        panel_h=panel_h,
        img_w=img_w,
        img_h=img_h,
        max_layers=max_layers,
        visible_layer_indices=visible_layers,
        view_keys=["N", "S", "W", "E"],
        headings={
            "N": "NORTH FAÇADE (Rear)",
            "S": "SOUTH FAÇADE (Front Door)",
            "W": "WEST FAÇADE (Left Side)",
            "E": "EAST FAÇADE (Right Side)",
        },
    )


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
    struct_w = grid_utils.get_structure_width(ctx)
    struct_h = grid_utils.get_structure_depth(ctx)
    layer_keys = layout["visible_layer_indices"]

    def get_token(layer_array_index: int, x: int, z: int) -> RawToken:
        return cell_utils.get_structure_cell(ctx, layer_array_index, x, z)

    return facade_projection.collect_facade_elevations(
        layer_keys,
        struct_w,
        struct_h,
        get_token,
        is_visible=facade_projection.is_structure_cell_visible,
    )


def _draw_structure_y_row_labels(
    draw: ImageDraw.ImageDraw,
    ctx: SchematicContext,
    layout: StructureFacadeLayout,
    sy: int,
) -> None:
    block_px = layout["block_px"]
    panel_h = layout["panel_h"]
    label_x = layout["panel_gap"]

    for row, layer_array_index in enumerate(layout["visible_layer_indices"]):
        row_top = sy + panel_h - ((row + 1) * block_px)
        label = get_layer_display_name(ctx.layers[layer_array_index])
        draw.text((label_x, row_top + 6), label, fill=(80, 80, 80))


def _draw_structure_elevation_panels(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    ctx: SchematicContext,
    struct_elevations: FacadeElevations,
    layout: StructureFacadeLayout,
):
    current_y = layout["top_margin"] + 20
    _draw_structure_y_row_labels(draw, ctx, layout, current_y)

    current_x = layout["panel_gap"] + layout["y_label_width"]

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
    visible_layers = layout["visible_layer_indices"]

    token_count = _get_view_token_count(ctx, view_key)

    for row, layer_array_index in enumerate(visible_layers):
        row_tokens = elevation.get(layer_array_index, [])

        for i in range(token_count):
            raw_token = row_tokens[i] if i < len(row_tokens) else "."
            bx = sx + (i * block_px)
            by = sy + panel_h - ((row + 1) * block_px)

            facade_projection.draw_facade_cell(
                img,
                draw,
                ctx,
                raw_token,
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


def render_structure_facades(ctx: SchematicContext):
    layout = _build_structure_elevation_layout(ctx)
    struct_elevations = _collect_structure_elevations(ctx, layout)

    img, draw = render_image.create_canvas(layout["img_w"], layout["img_h"])

    _draw_structure_elevation_title(draw)
    _draw_structure_elevation_panels(img, draw, ctx, struct_elevations, layout)

    output_path = paths.schematic_output_path(ctx, "structure_facades.png")
    img.save(output_path)
