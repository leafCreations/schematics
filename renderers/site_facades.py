from PIL import Image, ImageDraw

import helpers.landscape_utils as landscape_utils
import helpers.utils_schematics as schematics_utils
from helpers.context import SchematicContext
from helpers.types import (
    FacadeElevations,
    LayerElevations,
    Layers,
    SiteFacadeLayout,
    SiteMap,
    Token,
)


def _build_site_facades_layout(ctx: SchematicContext) -> SiteFacadeLayout:
    block_px = 30
    padding = 60
    top_margin = 80
    view_keys = ["N", "S", "W", "E"]
    layer_keys = [-1, 0, 1]

    panel_w = ctx.site_size * block_px

    img_w = (panel_w * len(view_keys)) + (padding * (len(view_keys) + 1))
    img_h = top_margin + 50 + (len(layer_keys) * block_px) + 60

    layout = SiteFacadeLayout(
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

    return layout


def _create_site_facades_image(layout: SiteFacadeLayout):
    img = Image.new("RGB", (layout["img_w"], layout["img_h"]), (255, 255, 255))

    draw = ImageDraw.Draw(img)

    return img, draw


def _draw_site_facades_title(draw, layout: SiteFacadeLayout):
    draw.text(
        (layout["padding"], 20),
        "SITE CROSS-SECTIONS - 4 COMPASS DIRECTIONAL ENVIRONMENTAL PROJECTIONS",
        fill=(30, 30, 30),
    )


def _collect_site_elevations(ctx: SchematicContext, siteMap: SiteMap) -> FacadeElevations:
    elevations = FacadeElevations(
        N={layer_y: [] for layer_y in [-1, 0, 1]},
        S={layer_y: [] for layer_y in [-1, 0, 1]},
        W={layer_y: [] for layer_y in [-1, 0, 1]},
        E={layer_y: [] for layer_y in [-1, 0, 1]},
    )

    for layer_y in [-1, 0, 1]:
        _collect_site_north_south_layer(ctx, siteMap, elevations, layer_y)
        _collect_site_west_east_layer(ctx, siteMap, elevations, layer_y)

    return elevations


def _collect_site_north_south_layer(
    ctx: SchematicContext, siteMap: SiteMap, elevations: FacadeElevations, layer_y: int
):
    for x in range(ctx.site_size):
        north_token = _find_first_site_token_along_z(siteMap, layer_y, x, range(ctx.site_size))

        south_token = _find_first_site_token_along_z(
            siteMap, layer_y, x, range(ctx.site_size - 1, -1, -1)
        )

        elevations["N"][layer_y].append(north_token)
        elevations["S"][layer_y].append(south_token)


def _collect_site_west_east_layer(
    ctx: SchematicContext, siteMap: SiteMap, elevations: FacadeElevations, layer_y: int
):
    for z in range(ctx.site_size):
        west_token = _find_first_site_token_along_x(siteMap, layer_y, z, range(ctx.site_size))

        east_token = _find_first_site_token_along_x(
            siteMap, layer_y, z, range(ctx.site_size - 1, -1, -1)
        )

        elevations["W"][layer_y].append(west_token)
        elevations["E"][layer_y].append(east_token)


def _find_first_site_token_along_z(siteMap: SiteMap, layer_y: int, x: int, z_range: range):
    for z in z_range:
        token = siteMap[layer_y][z][x]

        if token != ".":
            return token

    return "."


def _find_first_site_token_along_x(siteMap: SiteMap, layer_y: int, z: int, x_range: range):
    for x in x_range:
        token = siteMap[layer_y][z][x]

        if token != ".":
            return token

    return "."


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
    for step, layer_y in enumerate(layout["layer_keys"]):
        pixel_row = (len(layout["layer_keys"]) - 1) - step
        tokens = panel_data[layer_y]

        for col in range(ctx.site_size):
            token = tokens[col]
            _draw_site_facade_cell(
                img, draw, ctx, token, col, pixel_row, current_x, current_y, layout
            )


def _draw_site_facade_cell(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    ctx: SchematicContext,
    token: Token,
    col: int,
    pixel_row: int,
    current_x: int,
    current_y: int,
    layout: SiteFacadeLayout,
):
    block_px = layout["block_px"]

    bx = current_x + (col * block_px)
    by = current_y + (pixel_row * block_px)

    rect = [bx, by, bx + block_px, by + block_px]

    _draw_site_facade_cell_background(draw, token, rect)

    _draw_site_facade_cell_texture(img, draw, ctx, token, rect, bx, by)


def _draw_site_facade_cell_background(draw: ImageDraw.ImageDraw, token: Token, layers: Layers):
    if token == ".":
        background_color = (235, 245, 255)
    else:
        background_color = schematics_utils.get_background_color(token, default=(235, 245, 255))

    draw.rectangle(layers, fill=background_color)


def _draw_site_facade_cell_texture(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    ctx: SchematicContext,
    token: Token,
    layers: Layers,
    bx: int,
    by: int,
):
    if token in ctx.sideview_textures:
        tex = ctx.sideview_textures[token]

        img.paste(tex, (bx, by), tex if tex.mode == "RGBA" else None)

        return

    if token == ".":
        return

    fallback_color = schematics_utils.get_background_color(token, default=(230, 230, 230))

    draw.rectangle(layers, fill=fallback_color)


def _build_site_facades_output_path(ctx: SchematicContext):
    return ctx.output_schematics_dir / f"{ctx.name.lower().replace(' ', '_')}_site_facades.png"


def render_site_facades(ctx: SchematicContext):
    layout = _build_site_facades_layout(ctx)
    siteMap = landscape_utils.generate_full_3d_landscape_sitemap(ctx)
    elevations = _collect_site_elevations(ctx, siteMap)

    img, draw = _create_site_facades_image(layout)

    _draw_site_facades_title(draw, layout)

    _draw_site_facade_panels(img, draw, ctx, elevations, layout)

    output_path = _build_site_facades_output_path(ctx)
    img.save(output_path)
