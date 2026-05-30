import random

import helpers.grid as grid_utils
import helpers.path_geometry as path_geometry
import helpers.utils_schematics as schematics_utils
from helpers.context import SchematicContext
from helpers.types import SiteLayer, SiteMap

TRIM_BLOCK = "GRAVEL"


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


def generate_full_3d_landscape_sitemap(ctx: SchematicContext) -> SiteMap:
    site_size = grid_utils.get_site_size(ctx)
    offset_x = grid_utils.get_offset_x(ctx)
    offset_z = grid_utils.get_offset_z(ctx)
    structure_width = grid_utils.get_structure_width(ctx)
    structure_depth = grid_utils.get_structure_depth(ctx)
    geom = path_geometry.get_path_geometry(ctx)

    site_map: SiteMap = {
        y: [["." for _ in range(site_size)] for _ in range(site_size)] for y in [-1, 0, 1]
    }

    y_minus_1 = generate_landscape_y_minus_1_sitelayer(ctx)

    for z in range(site_size):
        for x in range(site_size):
            site_map[-1][z][x] = y_minus_1[z][x]

    for z in range(geom.path_start_z, site_size):
        if not geom.is_lighting_row(z):
            continue

        if geom.trim_left >= 0:
            site_map[0][z][geom.trim_left] = "FENCE"
            site_map[1][z][geom.trim_left] = "TORCH"

        if geom.trim_right < site_size:
            site_map[0][z][geom.trim_right] = "FENCE"
            site_map[1][z][geom.trim_right] = "TORCH"

    for y, layer in enumerate(ctx.layers[:2]):
        cells = layer.get("cells", [])

        for local_z in range(min(structure_depth, len(cells))):
            row = cells[local_z]
            global_z = offset_z + local_z

            if global_z >= site_size:
                continue

            for local_x in range(min(structure_width, len(row))):
                global_x = offset_x + local_x

                if global_x >= site_size:
                    continue

                raw_token = row[local_x]
                token, _direction = schematics_utils.resolve_token_for_render(raw_token)

                if token != "." and schematics_utils.show_interior_view(token):
                    site_map[y][global_z][global_x] = raw_token

    return site_map
