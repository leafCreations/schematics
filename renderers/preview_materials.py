"""Materials list PNG for in-app preview (preview session dir only)."""

from __future__ import annotations

from pathlib import Path

from helpers.context import SchematicContext
from renderers.materials import render_materials_inventory_to_path


def preview_materials_png_path(schematics_dir: Path) -> Path:
    return schematics_dir / "Materials_list.png"


def render_preview_materials(ctx: SchematicContext) -> None:
    """Render one materials inventory PNG into the preview session dir."""
    render_materials_inventory_to_path(ctx, preview_materials_png_path(ctx.output_schematics_dir))
