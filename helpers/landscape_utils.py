import random

import helpers.grid as grid_utils
import helpers.utils_schematics as schematics_utils
from helpers.context import SchematicContext
from helpers.types import SiteLayer, SiteMap

# Landscaping Rules
PATH_WIDTH = 3
TRIM_BLOCK = "GRAVEL"  # Gravel Block for path trim
TRIM_WIDTH = 1
LIGHTING_SPACING = 7
LIGHTING_START_OFFSET = 10


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


def _get_site_size(ctx: SchematicContext) -> int:
    return int(ctx.grid.get("site_size", 30))


def _get_offset_x(ctx: SchematicContext) -> int:
    return int(ctx.grid.get("offset_x", 0))


def _get_offset_z(ctx: SchematicContext) -> int:
    return int(ctx.grid.get("offset_z", 0))


def generate_landscape_y_minus_1_sitelayer(ctx: SchematicContext) -> SiteLayer:
    site_size = _get_site_size(ctx)
    offset_x = _get_offset_x(ctx)
    offset_z = _get_offset_z(ctx)
    structure_depth = grid_utils.get_structure_depth(ctx)

    grid: SiteLayer = [["GRASS" for _ in range(site_size)] for _ in range(site_size)]

    stair_global_center_x = offset_x + 4
    stair_global_bottom_z = offset_z + (structure_depth - 1)
    path_start_z = stair_global_bottom_z + 1

    for z in range(path_start_z, site_size):
        path_left = stair_global_center_x - (PATH_WIDTH // 2)
        path_right = stair_global_center_x + (PATH_WIDTH // 2)
        trim_left = path_left - TRIM_WIDTH
        trim_right = path_right + TRIM_WIDTH

        for x in range(site_size):
            if path_left <= x <= path_right:
                grid[z][x] = _get_random_path_block()
            elif trim_left <= x <= trim_right:
                grid[z][x] = TRIM_BLOCK

    return grid


def generate_full_3d_landscape_sitemap(ctx: SchematicContext) -> SiteMap:
    site_size = _get_site_size(ctx)
    offset_x = _get_offset_x(ctx)
    offset_z = _get_offset_z(ctx)
    structure_width = grid_utils.get_structure_width(ctx)
    structure_depth = grid_utils.get_structure_depth(ctx)

    site_map: SiteMap = {
        y: [["." for _ in range(site_size)] for _ in range(site_size)] for y in [-1, 0, 1]
    }

    y_minus_1 = generate_landscape_y_minus_1_sitelayer(ctx)

    stair_global_center_x = offset_x + 4
    stair_global_bottom_z = offset_z + (structure_depth - 1)
    path_start_z = stair_global_bottom_z + 1

    for z in range(site_size):
        for x in range(site_size):
            site_map[-1][z][x] = y_minus_1[z][x]

    for z in range(path_start_z, site_size):
        path_left = stair_global_center_x - (PATH_WIDTH // 2)
        path_right = stair_global_center_x + (PATH_WIDTH // 2)
        trim_left = path_left - TRIM_WIDTH
        trim_right = path_right + TRIM_WIDTH
        relative_z = z - path_start_z

        if (
            relative_z >= LIGHTING_START_OFFSET
            and (relative_z - LIGHTING_START_OFFSET) % LIGHTING_SPACING == 0
        ):
            if trim_left >= 0:
                site_map[0][z][trim_left] = "FENCE"
                site_map[1][z][trim_left] = "TORCH"

            if trim_right < site_size:
                site_map[0][z][trim_right] = "FENCE"
                site_map[1][z][trim_right] = "TORCH"

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
