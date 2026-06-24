"""Per-direction structure facade PNGs for in-app preview (preview session dir only)."""

from __future__ import annotations

from pathlib import Path

import helpers.render_image as render_image
from helpers.context import SchematicContext
from renderers.structure_facades import (
    FACADE_DIRECTIONS,
    Y_LABEL_WIDTH,
    _build_structure_elevation_layout,
    _collect_structure_elevations,
    _draw_structure_elevation_heading,
    _draw_structure_elevation_panel,
    _draw_structure_y_row_labels,
)

_PREVIEW_PANEL_GAP = 24
_PREVIEW_TOP_MARGIN = 48
_PREVIEW_BOTTOM_MARGIN = 24


def preview_facade_png_path(schematics_dir: Path, direction: str) -> Path:
    return schematics_dir / f"Structure_facades_{direction}.png"


def render_preview_structure_facades(ctx: SchematicContext) -> None:
    """Render one PNG per compass direction into the preview session dir."""
    layout = _build_structure_elevation_layout(ctx)
    elevations = _collect_structure_elevations(ctx, layout)

    for direction in FACADE_DIRECTIONS:
        _render_single_facade_preview(ctx, direction, elevations, layout)


def _render_single_facade_preview(
    ctx: SchematicContext,
    direction: str,
    elevations,
    layout,
) -> None:
    panel_w = layout["panel_w"]
    panel_h = layout["panel_h"]
    panel_gap = _PREVIEW_PANEL_GAP
    y_label_width = Y_LABEL_WIDTH

    img_w = panel_gap + y_label_width + panel_w + panel_gap
    img_h = _PREVIEW_TOP_MARGIN + 20 + panel_h + _PREVIEW_BOTTOM_MARGIN

    img, draw = render_image.create_canvas(img_w, img_h)

    panel_y = _PREVIEW_TOP_MARGIN + 20
    panel_x = panel_gap + y_label_width
    label_layout = {**layout, "top_margin": _PREVIEW_TOP_MARGIN, "panel_gap": panel_gap}

    _draw_structure_y_row_labels(draw, ctx, label_layout, panel_y)
    _draw_structure_elevation_heading(draw, direction, panel_x, panel_y, layout)
    _draw_structure_elevation_panel(
        img,
        draw,
        ctx,
        elevations[direction],
        direction,
        panel_x,
        panel_y,
        layout,
    )

    output_path = preview_facade_png_path(ctx.output_schematics_dir, direction)
    img.save(output_path)
