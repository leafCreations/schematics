"""Site ground and path lighting placement for Minecraft world export."""

from __future__ import annotations

from collections.abc import Iterator

import helpers.grid as grid_utils
from helpers.context import SchematicContext
from helpers.landscape_utils import PATH_LIGHTING_Y_LEVELS, SITE_GROUND_Y
from helpers.layer_groups import is_layer_render_visible
from helpers.layer_management import layer_worldgen_index
from helpers.types import SiteMap, Token

WORLDGEN_SITE_GROUND_INDEX = -1
PATH_LIGHTING_TOKENS = frozenset({"FENCE", "TORCH"})


def site_map_y_to_worldgen_index(site_map_y: int) -> int:
    if site_map_y == SITE_GROUND_Y:
        return WORLDGEN_SITE_GROUND_INDEX

    return site_map_y


def site_map_y_to_world_y(base_y: int, site_map_y: int) -> int:
    return base_y + site_map_y_to_worldgen_index(site_map_y)


def _structure_cells_by_worldgen_index(ctx: SchematicContext) -> dict[int, set[tuple[int, int]]]:
    offset_x = grid_utils.get_offset_x(ctx)
    offset_z = grid_utils.get_offset_z(ctx)
    occupied: dict[int, set[tuple[int, int]]] = {}

    for layer_array_index, layer in enumerate(ctx.layers):
        if not is_layer_render_visible(layer, layer_array_index, ctx.grid):
            continue

        worldgen_index = layer_worldgen_index(layer, layer_array_index)
        cells = layer.get("cells", [])
        layer_cells = occupied.setdefault(worldgen_index, set())

        for local_z, row in enumerate(cells):
            for local_x, raw_token in enumerate(row):
                if raw_token == ".":
                    continue

                layer_cells.add((offset_x + local_x, offset_z + local_z))

    return occupied


def iter_site_ground_placements(
    ctx: SchematicContext,
    site_map: SiteMap,
) -> Iterator[tuple[int, int, int, Token]]:
    """Yield ``(global_x, world_y, global_z, token)`` for painted/auto site ground."""
    site_width = grid_utils.get_site_width(ctx)
    site_depth = grid_utils.get_site_depth(ctx)
    ground = site_map.get(SITE_GROUND_Y)

    if ground is None:
        return

    world_y = site_map_y_to_world_y(grid_utils.get_worldgen_base_y(ctx), SITE_GROUND_Y)

    for site_z in range(site_depth):
        row = ground[site_z]

        for site_x in range(site_width):
            token = row[site_x]
            yield site_x, world_y, site_z, token


def iter_path_lighting_placements(
    ctx: SchematicContext,
    site_map: SiteMap,
) -> Iterator[tuple[int, int, int, Token]]:
    """Yield fence/torch cells along path trim after structure layers are placed."""
    site_width = grid_utils.get_site_width(ctx)
    site_depth = grid_utils.get_site_depth(ctx)
    base_y = grid_utils.get_worldgen_base_y(ctx)
    structure_cells = _structure_cells_by_worldgen_index(ctx)

    for site_y in PATH_LIGHTING_Y_LEVELS:
        layer = site_map.get(site_y)

        if layer is None:
            continue

        world_y = base_y + site_y
        occupied = structure_cells.get(site_y, set())

        for site_z in range(site_depth):
            row = layer[site_z]

            for site_x in range(site_width):
                token = row[site_x]

                if token not in PATH_LIGHTING_TOKENS:
                    continue

                if (site_x, site_z) in occupied:
                    continue

                yield site_x, world_y, site_z, token


def iter_site_landscape_placements(
    ctx: SchematicContext,
    site_map: SiteMap,
    *,
    include_ground: bool = True,
    include_lighting: bool = True,
) -> Iterator[tuple[int, int, int, Token]]:
    """Yield site ground and/or path lighting placements for world export."""
    if include_ground:
        yield from iter_site_ground_placements(ctx, site_map)

    if include_lighting:
        yield from iter_path_lighting_placements(ctx, site_map)
