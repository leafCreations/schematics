"""Per-Y site top-down PNGs for in-app preview (preview session dir only)."""

from __future__ import annotations

from pathlib import Path

import helpers.constants as constants
import helpers.grid as grid_utils
import helpers.landscape_utils as landscape_utils
import helpers.render_image as render_image
from helpers.context import SchematicContext
from renderers.path_view import (
    _draw_path_layer_header,
    _draw_path_layer_panel,
)

_PREVIEW_PADDING = 24
_PREVIEW_TOP_MARGIN = 48
_PREVIEW_HEADING_GAP = 30
_PREVIEW_BOTTOM_MARGIN = 24


def preview_site_topdown_png_path(schematics_dir: Path, layer_y: int) -> Path:
    return schematics_dir / f"Site_topdown_y{layer_y}.png"


def render_preview_site_topdown(ctx: SchematicContext) -> None:
    """Render one PNG per site path Y level into the preview session dir."""
    site_map = landscape_utils.generate_full_3d_landscape_sitemap(ctx)

    for layer_y in landscape_utils.path_view_y_keys(ctx):
        _render_single_site_topdown_layer(ctx, layer_y, site_map)


def _render_single_site_topdown_layer(
    ctx: SchematicContext,
    layer_y: int,
    site_map,
) -> None:
    block_px = constants.BLOCK_PX
    site_width = grid_utils.get_site_width(ctx)
    site_depth = grid_utils.get_site_depth(ctx)
    panel_w = site_width * block_px
    panel_h = site_depth * block_px
    padding = _PREVIEW_PADDING

    img_w = (padding * 2) + panel_w
    img_h = _PREVIEW_TOP_MARGIN + _PREVIEW_HEADING_GAP + panel_h + _PREVIEW_BOTTOM_MARGIN

    img, draw = render_image.create_canvas(img_w, img_h)
    panel_y = _PREVIEW_TOP_MARGIN + _PREVIEW_HEADING_GAP
    panel = {"sx": padding, "sy": panel_y}
    layout = {
        "block_px": block_px,
        "padding": padding,
        "top_margin": _PREVIEW_TOP_MARGIN,
        "panel_w": panel_w,
        "panel_h": panel_h,
    }

    _draw_path_layer_header(draw, layer_y, panel)
    _draw_path_layer_panel(img, draw, ctx, layer_y, panel, layout, site_map)

    output_path = preview_site_topdown_png_path(ctx.output_schematics_dir, layer_y)
    img.save(output_path)
