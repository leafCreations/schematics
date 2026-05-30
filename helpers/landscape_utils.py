import random

import helpers.grid as grid_utils
import helpers.path_geometry as path_geometry
import helpers.utils_schematics as schematics_utils
from helpers.context import SchematicContext
from helpers.types import Cell, SiteLayer, SiteMap

TRIM_BLOCK = "GRAVEL"
SITE_STRUCTURE_Y_LEVELS = (0, 1)


def _get_random_path_block() -> str:
    roll = random.random()

    if roll < 0.60:
        return "DIRT_PATH"
    if roll < 0.75:
        return "GRAVEL"
    if roll < 0.90:
        return "DIRT"
    if roll < 0.97:
        return "COBBLESTONE"

    return "COBBLESTONE#mossy"


def generate_landscape_y_minus_1_sitelayer(ctx: SchematicContext) -> SiteLayer:
    site_size = grid_utils.get_site_size(ctx)
    geom = path_geometry.get_path_geometry(ctx)

    grid: SiteLayer = [["GRASS" for _ in range(site_size)] for _ in range(site_size)]

    for z in range(geom.path_start_z, site_size):
        for x in range(site_size):
            if geom.is_on_path(x, z):
                grid[z][x] = _get_random_path_block()
            elif geom.is_on_trim(x, z):
                grid[z][x] = TRIM_BLOCK

    return grid


def apply_lighting_overlays_to_site_map(
    site_map: SiteMap,
    ctx: SchematicContext,
    geom: path_geometry.PathGeometry,
) -> None:
    site_size = grid_utils.get_site_size(ctx)

    for z in range(geom.path_start_z, site_size):
        if not geom.is_lighting_row(z):
            continue

        if geom.trim_left >= 0:
            site_map[0][z][geom.trim_left] = "FENCE"
            site_map[1][z][geom.trim_left] = "TORCH"

        if geom.trim_right < site_size:
            site_map[0][z][geom.trim_right] = "FENCE"
            site_map[1][z][geom.trim_right] = "TORCH"


def apply_structure_overlays_to_site_map(site_map: SiteMap, ctx: SchematicContext) -> None:
    offset_x = grid_utils.get_offset_x(ctx)
    offset_z = grid_utils.get_offset_z(ctx)
    structure_width = grid_utils.get_structure_width(ctx)
    structure_depth = grid_utils.get_structure_depth(ctx)
    layer_indices = grid_utils.get_site_structure_layer_indices(ctx)

    for site_y, layer_list_idx in zip(SITE_STRUCTURE_Y_LEVELS, layer_indices, strict=False):
        layer = ctx.layers[layer_list_idx]
        cells = layer.get("cells", [])

        for local_z in range(min(structure_depth, len(cells))):
            row = cells[local_z]
            global_z = offset_z + local_z

            if global_z >= grid_utils.get_site_size(ctx):
                continue

            for local_x in range(min(structure_width, len(row))):
                global_x = offset_x + local_x

                if global_x >= grid_utils.get_site_size(ctx):
                    continue

                raw_token = row[local_x]
                token, _direction = schematics_utils.resolve_token_for_render(raw_token)

                if token != "." and schematics_utils.show_interior_view(token):
                    site_map[site_y][global_z][global_x] = raw_token


def generate_full_3d_landscape_sitemap(ctx: SchematicContext) -> SiteMap:
    site_size = grid_utils.get_site_size(ctx)
    geom = path_geometry.get_path_geometry(ctx)

    site_map: SiteMap = {
        y: [["." for _ in range(site_size)] for _ in range(site_size)] for y in [-1, 0, 1]
    }

    y_minus_1 = generate_landscape_y_minus_1_sitelayer(ctx)

    for z in range(site_size):
        for x in range(site_size):
            site_map[-1][z][x] = y_minus_1[z][x]

    apply_lighting_overlays_to_site_map(site_map, ctx, geom)
    apply_structure_overlays_to_site_map(site_map, ctx)

    return site_map


def resolve_path_view_cell(
    layer_y: int,
    x: int,
    z: int,
    site_map: SiteMap,
) -> Cell:
    base_token = site_map[-1][z][x]
    overlay_token = site_map[layer_y][z][x]

    if layer_y == -1:
        return Cell(
            base_token=base_token,
            active_token=base_token,
            is_ghost=False,
            is_ground_layer=True,
        )

    if overlay_token != ".":
        return Cell(
            base_token=base_token,
            active_token=overlay_token,
            is_ghost=False,
            is_ground_layer=False,
        )

    return Cell(
        base_token=base_token,
        active_token=base_token,
        is_ghost=True,
        is_ground_layer=False,
    )
