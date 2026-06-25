"""Per-direction site facade PNGs for in-app preview (preview session dir only)."""

from __future__ import annotations

from pathlib import Path

import helpers.grid as grid_utils
import helpers.landscape_utils as landscape_utils
import helpers.render_image as render_image
from helpers.context import SchematicContext
from helpers.layer_visibility import site_facade_layer_keys
from renderers.site_facades import (
    _build_site_facades_layout,
    _collect_site_elevations,
    _draw_site_facade_heading,
    _draw_site_facade_panel,
)
from renderers.structure_facades import FACADE_DIRECTIONS

_PREVIEW_PADDING = 24
_PREVIEW_TOP_MARGIN = 48
_PREVIEW_HEADING_GAP = 30
_PREVIEW_BOTTOM_MARGIN = 24


def preview_site_facade_png_path(schematics_dir: Path, direction: str) -> Path:
    return schematics_dir / f"Site_facades_{direction}.png"


def render_preview_site_facades(ctx: SchematicContext) -> None:
    """Render one PNG per compass direction into the preview session dir."""
    site_map = landscape_utils.generate_full_3d_landscape_sitemap(ctx)
    site_width = grid_utils.get_site_width(ctx)
    site_depth = grid_utils.get_site_depth(ctx)
    layer_keys = site_facade_layer_keys(site_map, site_width=site_width, site_depth=site_depth)
    layout = _build_site_facades_layout(ctx, layer_keys=layer_keys)
    elevations = _collect_site_elevations(ctx, site_map, layer_keys=layer_keys)

    for direction in FACADE_DIRECTIONS:
        _render_single_site_facade_preview(ctx, direction, elevations, layout)


def _render_single_site_facade_preview(
    ctx: SchematicContext,
    direction: str,
    elevations,
    layout,
) -> None:
    block_px = layout["block_px"]
    panel_w = layout["panel_w"]
    panel_h = len(layout["layer_keys"]) * block_px
    padding = _PREVIEW_PADDING

    img_w = (padding * 2) + panel_w
    img_h = _PREVIEW_TOP_MARGIN + _PREVIEW_HEADING_GAP + panel_h + _PREVIEW_BOTTOM_MARGIN

    img, draw = render_image.create_canvas(img_w, img_h)
    panel_x = padding
    panel_y = _PREVIEW_TOP_MARGIN + _PREVIEW_HEADING_GAP

    _draw_site_facade_heading(draw, direction, panel_x, panel_y, layout)
    _draw_site_facade_panel(
        img,
        draw,
        ctx,
        elevations[direction],
        direction,
        panel_x,
        panel_y,
        layout,
    )

    output_path = preview_site_facade_png_path(ctx.output_schematics_dir, direction)
    img.save(output_path)
