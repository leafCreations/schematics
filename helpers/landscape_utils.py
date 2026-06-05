import helpers.grid as grid_utils
import helpers.path_geometry as path_geometry
import helpers.path_lighting as path_lighting
import helpers.path_strip as path_strip
import helpers.utils_schematics as schematics_utils
from helpers.context import SchematicContext
from helpers.layer_groups import is_layer_render_visible
from helpers.layer_management import layer_worldgen_index
from helpers.types import Cell, SiteLayer, SiteMap

TRIM_BLOCK = path_strip.TRIM_BLOCK
SITE_GROUND_Y = -1000
PATH_VIEW_Y_LEVELS = (-1, 0, 1)
PATH_LIGHTING_Y_LEVELS = (0, 1)


def path_view_y_keys(_ctx: SchematicContext) -> list[int]:
    """Path top-down columns: structure worldgen Y levels -1, 0, and 1."""
    return list(PATH_VIEW_Y_LEVELS)


def _site_map_y_keys(_ctx: SchematicContext) -> list[int]:
    return [SITE_GROUND_Y, *PATH_VIEW_Y_LEVELS]


def _site_layer_has_content(layer: SiteLayer, site_width: int, site_depth: int) -> bool:
    for z in range(min(site_depth, len(layer))):
        row = layer[z]

        for x in range(min(site_width, len(row))):
            if row[x] != ".":
                return True

    return False


def generate_landscape_y_minus_1_sitelayer(ctx: SchematicContext) -> SiteLayer:
    site_width = grid_utils.get_site_width(ctx)
    site_depth = grid_utils.get_site_depth(ctx)
    geom = path_geometry.get_path_geometry(ctx)
    path_width = path_strip.resolve_path_width(ctx.grid)

    grid: SiteLayer = [["GRASS" for _ in range(site_width)] for _ in range(site_depth)]

    trim_block = path_strip.resolve_trim_block(ctx.grid)
    variety_blocks = path_strip.resolve_path_variety_blocks(ctx.grid)

    for z in range(geom.path_start_z, site_depth):
        path_strip.paint_path_row(
            grid[z],
            geom.path_center_x,
            path_width,
            z,
            trim_block=trim_block,
            variety_blocks=variety_blocks,
        )

    return grid


def apply_lighting_overlays_to_site_map(
    site_map: SiteMap,
    ctx: SchematicContext,
    geom: path_geometry.PathGeometry,
) -> None:
    offset_x = grid_utils.get_offset_x(ctx)
    offset_z = grid_utils.get_offset_z(ctx)
    structure_width = grid_utils.get_structure_width(ctx)
    structure_depth = grid_utils.get_structure_depth(ctx)

    if ctx.site_ground is not None:
        trim_block = path_strip.resolve_trim_block(ctx.grid)
        fence_cells = path_lighting.iter_lighting_fence_cells_from_ground(
            ctx.site_ground,
            trim_block=trim_block,
        )
    else:
        fence_cells = geom.iter_lighting_fence_cells()

    for site_x, site_z in fence_cells:
        local_x = site_x - offset_x
        local_z = site_z - offset_z

        if 0 <= local_x < structure_width and 0 <= local_z < structure_depth:
            continue

        site_map[0][site_z][site_x] = "FENCE"
        site_map[1][site_z][site_x] = "TORCH"


def apply_structure_overlays_to_site_map(site_map: SiteMap, ctx: SchematicContext) -> None:
    offset_x = grid_utils.get_offset_x(ctx)
    offset_z = grid_utils.get_offset_z(ctx)
    structure_width = grid_utils.get_structure_width(ctx)
    structure_depth = grid_utils.get_structure_depth(ctx)

    for layer_array_index, layer in enumerate(ctx.layers):
        if not is_layer_render_visible(layer, layer_array_index, ctx.grid):
            continue

        site_y = layer_worldgen_index(layer, layer_array_index)

        if site_y not in site_map:
            continue

        cells = layer.get("cells", [])

        for local_z in range(min(structure_depth, len(cells))):
            row = cells[local_z]
            global_z = offset_z + local_z

            if global_z >= grid_utils.get_site_depth(ctx):
                continue

            for local_x in range(min(structure_width, len(row))):
                global_x = offset_x + local_x

                if global_x >= grid_utils.get_site_width(ctx):
                    continue

                raw_token = row[local_x]
                token, _direction = schematics_utils.resolve_token_for_render(raw_token)

                if token != "." and schematics_utils.show_interior_view(token):
                    site_map[site_y][global_z][global_x] = raw_token


def generate_full_3d_landscape_sitemap(ctx: SchematicContext) -> SiteMap:
    site_width = grid_utils.get_site_width(ctx)
    site_depth = grid_utils.get_site_depth(ctx)
    geom = path_geometry.get_path_geometry(ctx)

    site_map: SiteMap = {
        y: [["." for _ in range(site_width)] for _ in range(site_depth)]
        for y in _site_map_y_keys(ctx)
    }

    if ctx.site_ground is not None:
        y_minus_1 = ctx.site_ground
    else:
        y_minus_1 = generate_landscape_y_minus_1_sitelayer(ctx)

    for z in range(site_depth):
        for x in range(site_width):
            site_map[SITE_GROUND_Y][z][x] = y_minus_1[z][x]

    apply_lighting_overlays_to_site_map(site_map, ctx, geom)
    apply_structure_overlays_to_site_map(site_map, ctx)

    return site_map


def resolve_open_site_display_token(
    site_map: SiteMap,
    site_x: int,
    site_z: int,
) -> str:
    """Top-down token for open site cells (lighting overlays above ground).

    Fence posts (y=0) take precedence over torches (y=1) so the site grid shows
    trim-line placement; path renders still draw both layers separately.
    """
    for layer_y in PATH_LIGHTING_Y_LEVELS:
        if layer_y not in site_map:
            continue

        token = site_map[layer_y][site_z][site_x]

        if token != ".":
            return token

    return site_map[SITE_GROUND_Y][site_z][site_x]


def resolve_path_view_cell(
    layer_y: int,
    x: int,
    z: int,
    site_map: SiteMap,
) -> Cell:
    base_token = site_map[SITE_GROUND_Y][z][x]
    overlay_token = site_map[layer_y][z][x]

    if layer_y == SITE_GROUND_Y:
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

    # Y=-1 is the site ground column: show paths at full strength when no structure.
    if layer_y == PATH_VIEW_Y_LEVELS[0]:
        return Cell(
            base_token=base_token,
            active_token=base_token,
            is_ghost=False,
            is_ground_layer=True,
        )

    return Cell(
        base_token=base_token,
        active_token=base_token,
        is_ghost=True,
        is_ground_layer=False,
    )
