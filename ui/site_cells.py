"""Map site coordinates to structure layer cells for the site preview grid."""

from __future__ import annotations

from dataclasses import replace

from helpers.grid import resolve_site_dimensions
from helpers.grid_placement import structure_dimensions_from_layers
from helpers.landscape_utils import (
    generate_full_3d_landscape_sitemap,
    resolve_open_site_display_token,
)
from ui.editor_materials import build_editor_materials_context

# Open site cells use ground-layer tokens (e.g. GRASS, DIRT_PATH).
SiteDisplayToken = str


def structure_offset(metadata: dict) -> tuple[int, int]:
    grid = metadata.get("grid", {})
    return int(grid.get("offset_x", 0)), int(grid.get("offset_z", 0))


def site_preview_layer_index(metadata: dict, layer_count: int) -> int:
    """Layer list index used for the site tab preview (first ``site_structure_layers`` entry)."""
    grid = metadata.get("grid", {})
    indices = grid.get("site_structure_layers")

    if isinstance(indices, list) and indices:
        index = int(indices[0])

        if 0 <= index < layer_count:
            return index

    return 0


def build_editor_site_context(
    metadata: dict,
    layers: list[dict],
    site_ground: list[list[str]],
):
    """Minimal schematic context for site-map generation in the editor."""
    return replace(
        build_editor_materials_context(),
        layers=layers,
        grid=dict(metadata.get("grid", {})),
        site_ground=site_ground,
    )


def build_site_display_grid(
    metadata: dict,
    layers: list[dict],
    layer_cells: list[list[str]],
    site_ground: list[list[str]],
) -> tuple[list[list[SiteDisplayToken]], int, int, int, int]:
    """Return display grid (rows=z, cols=x), site size, and structure offset.

    Structure footprint cells show layer tokens; open site cells show ground plus
    path lighting overlays (fence/torch) from the same rules as path rendering.
    """
    site_width, site_depth = resolve_site_dimensions(metadata.get("grid", {}))
    offset_x, offset_z = structure_offset(metadata)
    structure_width, structure_depth = structure_dimensions_from_layers(
        [{"cells": layer_cells}],
    )
    ctx = build_editor_site_context(metadata, layers, site_ground)
    site_map = generate_full_3d_landscape_sitemap(ctx)

    display: list[list[SiteDisplayToken]] = []

    for site_z in range(site_depth):
        row: list[SiteDisplayToken] = []

        for site_x in range(site_width):
            local_x = site_x - offset_x
            local_z = site_z - offset_z

            if (
                0 <= local_x < structure_width
                and 0 <= local_z < structure_depth
                and local_z < len(layer_cells)
                and local_x < len(layer_cells[local_z])
            ):
                row.append(layer_cells[local_z][local_x])
            else:
                row.append(
                    resolve_open_site_display_token(site_map, site_x, site_z),
                )

        display.append(row)

    return display, site_width, site_depth, offset_x, offset_z
