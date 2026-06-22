from helpers import landscape_utils
from helpers.landscape_utils import SITE_GROUND_Y
from helpers.path_strip import TRIM_BLOCK
from helpers.worldgen_site import (
    WORLDGEN_SITE_GROUND_INDEX,
    iter_path_lighting_placements,
    iter_site_ground_placements,
    site_map_y_to_world_y,
)


def test_site_map_y_to_world_y_uses_ground_index(ctx):
    ctx.grid["worldgen_base_y"] = -60
    assert site_map_y_to_world_y(-60, SITE_GROUND_Y) == -61
    assert site_map_y_to_world_y(-60, 0) == -60
    assert site_map_y_to_world_y(-60, 1) == -59


def test_iter_site_ground_placements_covers_site_footprint(ctx):
    site_width = 12
    site_depth = 15
    custom = [["GRASS" for _ in range(site_width)] for _ in range(site_depth)]
    custom[10][4] = "DIRT_PATH"
    custom[10][3] = TRIM_BLOCK

    ctx.grid["site_width"] = site_width
    ctx.grid["site_depth"] = site_depth
    ctx.site_ground = custom
    site_map = landscape_utils.generate_full_3d_landscape_sitemap(ctx)

    placements = list(iter_site_ground_placements(ctx, site_map))
    by_coord = {(x, y, z): token for x, y, z, token in placements}

    assert len(placements) == site_width * site_depth
    assert by_coord[(4, -61, 10)] == "DIRT_PATH"
    assert by_coord[(3, -61, 10)] == TRIM_BLOCK
    assert by_coord[(0, -61, 0)] == "GRASS"


def test_iter_site_ground_placements_auto_path_when_site_ground_missing(ctx):
    ctx.grid["path_orientation"] = "vertical"
    ctx.grid["site_width"] = 12
    ctx.grid["site_depth"] = 30
    ctx.site_ground = None

    site_map = landscape_utils.generate_full_3d_landscape_sitemap(ctx)
    placements = list(iter_site_ground_placements(ctx, site_map))
    by_coord = {(x, y, z): token for x, y, z, token in placements}

    # Auto path below structure footprint (path_start_z=7, center x=11 with default offsets).
    assert by_coord[(11, -61, 10)] not in ("GRASS", ".")
    assert by_coord[(11, -61, 6)] == "GRASS"


def test_iter_path_lighting_placements_skips_structure_cells(ctx):
    site_width = 12
    site_depth = 30
    custom = [["GRASS" for _ in range(site_width)] for _ in range(site_depth)]

    for site_z in range(10, 26):
        custom[site_z][2] = "GRAVEL"
        custom[site_z][3] = "DIRT_PATH"
        custom[site_z][4] = "DIRT_PATH"
        custom[site_z][5] = "DIRT_PATH"
        custom[site_z][6] = "GRAVEL"

    ctx.grid["path_orientation"] = "vertical"
    ctx.grid["site_width"] = site_width
    ctx.grid["site_depth"] = site_depth
    ctx.grid["offset_x"] = 0
    ctx.grid["offset_z"] = 0
    ctx.layers = [
        {
            "index": 0,
            "cells": [
                ["PLANKS:oak", "PLANKS:oak"],
                ["PLANKS:oak", "PLANKS:oak"],
            ],
        },
    ]
    ctx.site_ground = custom
    site_map = landscape_utils.generate_full_3d_landscape_sitemap(ctx)

    placements = list(iter_path_lighting_placements(ctx, site_map))
    by_coord = {(x, y, z): token for x, y, z, token in placements}

    assert by_coord[(2, -60, 20)] == "FENCE"
    assert by_coord[(2, -59, 20)] == "TORCH"
    assert (0, -60, 0) not in by_coord
    assert (1, -60, 0) not in by_coord


def test_worldgen_site_ground_index_matches_path_view(ctx):
    assert WORLDGEN_SITE_GROUND_INDEX == -1
    assert landscape_utils.PATH_VIEW_Y_LEVELS[0] == WORLDGEN_SITE_GROUND_INDEX
