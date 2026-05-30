from PIL import Image, ImageDraw

import helpers.constants as constants
import helpers.facade_projection as facade_projection
import helpers.grid as grid_utils
import helpers.landscape_utils as landscape_utils
import helpers.paths as paths
import helpers.render_image as render_image
from helpers.context import SchematicContext
from helpers.types import (
    FacadeElevations,
    LayerElevations,
    SiteFacadeLayout,
    SiteMap,
    Token,
)


def _build_site_facades_layout(ctx: SchematicContext) -> SiteFacadeLayout:
    block_px = constants.BLOCK_PX
    padding = 60
    top_margin = constants.SITE_FACADES_TOP_MARGIN
    view_keys = ["N", "S", "W", "E"]
    layer_keys = [-1, 0, 1]

    site_size = grid_utils.get_site_size(ctx)
    panel_w = site_size * block_px

    img_w = (panel_w * len(view_keys)) + (padding * (len(view_keys) + 1))
    img_h = top_margin + 50 + (len(layer_keys) * block_px) + 60

    return SiteFacadeLayout(
        block_px=block_px,
        padding=padding,
        top_margin=top_margin,
        panel_w=panel_w,
        img_w=img_w,
        img_h=img_h,
        view_keys=view_keys,
        layer_keys=layer_keys,
        headings={
            "N": "NORTH ELEVATION (Landscape View)",
            "S": "SOUTH ELEVATION (Landscape View)",
            "W": "WEST ELEVATION (Landscape View)",
            "E": "EAST ELEVATION (Landscape View)",
        },
    )


def _draw_site_facades_title(draw, layout: SiteFacadeLayout):
    draw.text(
        (layout["padding"], 20),
        "SITE CROSS-SECTIONS - 4 COMPASS DIRECTIONAL ENVIRONMENTAL PROJECTIONS",
        fill=(30, 30, 30),
    )


def _collect_site_elevations(ctx: SchematicContext, siteMap: SiteMap) -> FacadeElevations:
    site_size = grid_utils.get_site_size(ctx)
    layer_keys = [-1, 0, 1]

    def get_token(layer_y: int, x: int, z: int) -> Token:
        return siteMap[layer_y][z][x]

    return facade_projection.collect_facade_elevations(
        layer_keys,
        site_size,
        site_size,
        get_token,
    )


def _draw_site_facade_panels(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    ctx: SchematicContext,
    elevations: FacadeElevations,
    layout: SiteFacadeLayout,
):
    current_x = layout["padding"]
    current_y = layout["top_margin"] + 50

    for view_key in layout["view_keys"]:
        _draw_site_facade_heading(draw, view_key, current_x, current_y, layout)

        _draw_site_facade_panel(img, draw, ctx, elevations[view_key], current_x, current_y, layout)

        current_x += layout["panel_w"] + layout["padding"]


def _draw_site_facade_heading(
    draw: ImageDraw.ImageDraw,
    view_key: str,
    current_x: int,
    current_y: int,
    layout: SiteFacadeLayout,
):
    draw.text((current_x, current_y - 22), layout["headings"][view_key], fill=(60, 60, 60))


def _draw_site_facade_panel(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    ctx: SchematicContext,
    panel_data: LayerElevations,
    current_x: int,
    current_y: int,
    layout: SiteFacadeLayout,
):
    site_size = grid_utils.get_site_size(ctx)

    for step, layer_y in enumerate(layout["layer_keys"]):
        pixel_row = (len(layout["layer_keys"]) - 1) - step
        tokens = panel_data[layer_y]

        for col in range(site_size):
            token = tokens[col]
            bx = current_x + (col * layout["block_px"])
            by = current_y + (pixel_row * layout["block_px"])

            facade_projection.draw_facade_cell(
                img,
                draw,
                ctx,
                token,
                bx,
                by,
                layout["block_px"],
                empty_fill=(235, 245, 255),
                empty_outline=None,
                fallback_default=(230, 230, 230),
                fallback_outline=None,
            )


def render_site_facades(ctx: SchematicContext):
    layout = _build_site_facades_layout(ctx)
    siteMap = landscape_utils.generate_full_3d_landscape_sitemap(ctx)
    elevations = _collect_site_elevations(ctx, siteMap)

    img, draw = render_image.create_canvas(layout["img_w"], layout["img_h"])

    _draw_site_facades_title(draw, layout)

    _draw_site_facade_panels(img, draw, ctx, elevations, layout)

    output_path = paths.schematic_output_path(ctx, "site_facades.png")
    img.save(output_path)
