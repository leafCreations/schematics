import random
from helpers.context import SchematicContext
from helpers.types import SiteLayer, SiteMap
import helpers.utils_schematics as schematics_utils

# Landscaping Rules
PATH_WIDTH = 3
TRIM_BLOCK = "g" # Gravel Block for path trim
TRIM_WIDTH = 1
LIGHTING_SPACING = 7
LIGHTING_START_OFFSET = 10


def _get_random_path_block() -> str:
    roll = random.random()
    if roll < 0.60: return "dp"
    elif roll < 0.75: return "g"
    elif roll < 0.90: return "d"
    elif roll < 0.97: return "C"
    else: return "M"

def generate_landscape_y_minus_1_sitelayer(ctx: SchematicContext) -> SiteLayer:
    grid: SiteLayer = [["G" for _ in range(ctx.site_size)] for _ in range(ctx.site_size)]
    stair_global_center_x = ctx.offset_x + 4
    stair_global_bottom_z = ctx.offset_z + (ctx.struct_h - 1)
    path_start_z = stair_global_bottom_z + 1
    
    for z in range(path_start_z, ctx.site_size):
        path_left = stair_global_center_x - (PATH_WIDTH // 2)
        path_right = stair_global_center_x + (PATH_WIDTH // 2)
        trim_left = path_left - TRIM_WIDTH
        trim_right = path_right + TRIM_WIDTH
        for x in range(ctx.site_size):
            if path_left <= x <= path_right: grid[z][x] = _get_random_path_block()
            elif trim_left <= x <= trim_right: grid[z][x] = TRIM_BLOCK
    return grid

def generate_full_3d_landscape_sitemap(ctx: SchematicContext) -> SiteMap:
    site_map: SiteMap = {y: [["." for _ in range(ctx.site_size)] for _ in range(ctx.site_size)] for y in [-1, 0, 1]}
    y_minus_1 = generate_landscape_y_minus_1_sitelayer(ctx)
    
    stair_global_center_x = ctx.offset_x + 4
    stair_global_bottom_z = ctx.offset_z + (ctx.struct_h - 1)
    path_start_z = stair_global_bottom_z + 1
    
    for z in range(ctx.site_size):
        for x in range(ctx.site_size): site_map[-1][z][x] = y_minus_1[z][x]
            
    for z in range(path_start_z, ctx.site_size):
        path_left = stair_global_center_x - (PATH_WIDTH // 2)
        path_right = stair_global_center_x + (PATH_WIDTH // 2)
        trim_left = path_left - TRIM_WIDTH
        trim_right = path_right + TRIM_WIDTH
        relative_z = z - path_start_z
        if relative_z >= LIGHTING_START_OFFSET and (relative_z - LIGHTING_START_OFFSET) % LIGHTING_SPACING == 0:
            if trim_left >= 0:
                site_map[0][z][trim_left] = "o"
                site_map[1][z][trim_left] = "i"
            if trim_right < ctx.site_size:
                site_map[0][z][trim_right] = "o"
                site_map[1][z][trim_right] = "i"

    for y in [0, 1]:
        for local_z in range(ctx.struct_h):
            tokens = ctx.data[y][local_z].split()
            global_z = ctx.offset_z + local_z
            for local_x in range(ctx.struct_w):
                global_x = ctx.offset_x + local_x
                t, _direction = schematics_utils.resolve_token_for_render(tokens[local_x])
                if t != "." and schematics_utils.show_interior_view(t):
                    site_map[y][global_z][global_x] = t
    return site_map