from helpers import landscape_utils
from helpers.path_strip import TRIM_BLOCK

SITE_GROUND_Y = landscape_utils.SITE_GROUND_Y


def test_resolve_path_view_cell_ground_layer():
    site_map = {
        SITE_GROUND_Y: [["GRASS"]],
        0: [["."]],
        1: [["."]],
    }

    cell = landscape_utils.resolve_path_view_cell(SITE_GROUND_Y, 0, 0, site_map)

    assert cell["active_token"] == "GRASS"
    assert cell["is_ground_layer"] is True
    assert cell["is_ghost"] is False


def test_resolve_path_view_cell_structure_overlay():
    site_map = {
        SITE_GROUND_Y: [["GRASS"]],
        0: [["PLANKS:oak"]],
        1: [["."]],
    }

    cell = landscape_utils.resolve_path_view_cell(0, 0, 0, site_map)

    assert cell["active_token"] == "PLANKS:oak"
    assert cell["is_ghost"] is False


def test_resolve_path_view_cell_y_minus_one_shows_paths_when_no_structure():
    site_map = {
        SITE_GROUND_Y: [["DIRT_PATH"]],
        -1: [["."]],
        0: [["."]],
        1: [["."]],
    }

    cell = landscape_utils.resolve_path_view_cell(-1, 0, 0, site_map)

    assert cell["active_token"] == "DIRT_PATH"
    assert cell["is_ground_layer"] is True
    assert cell["is_ghost"] is False


def test_resolve_path_view_cell_y_minus_one_shows_structure_over_paths():
    site_map = {
        SITE_GROUND_Y: [["GRASS"]],
        -1: [["STONE"]],
        0: [["."]],
        1: [["."]],
    }

    cell = landscape_utils.resolve_path_view_cell(-1, 0, 0, site_map)

    assert cell["active_token"] == "STONE"
    assert cell["is_ghost"] is False


def test_resolve_path_view_cell_ghosts_base_when_no_overlay():
    site_map = {
        SITE_GROUND_Y: [["GRASS"]],
        0: [["."]],
        1: [["."]],
    }

    cell = landscape_utils.resolve_path_view_cell(0, 0, 0, site_map)

    assert cell["active_token"] == "GRASS"
    assert cell["is_ghost"] is True


def test_generate_full_3d_landscape_uses_ctx_site_ground(ctx):
    """Path render pipeline (path_view → generate_full_3d_landscape_sitemap) reads editor ground."""
    site_width = 30
    site_depth = 30
    custom = [["GRASS" for _ in range(site_width)] for _ in range(site_depth)]
    custom[12][9] = "DIRT_PATH"
    custom[12][10] = TRIM_BLOCK

    ctx.site_ground = custom
    site_map = landscape_utils.generate_full_3d_landscape_sitemap(ctx)

    assert site_map[SITE_GROUND_Y][12][9] == "DIRT_PATH"
    assert site_map[SITE_GROUND_Y][12][10] == TRIM_BLOCK
    assert site_map[SITE_GROUND_Y][0][0] == "GRASS"


def test_generate_full_3d_landscape_vertical_path_lighting(ctx):
    """Column-painted paths place fences on east/west trim, spaced along z."""
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
    ctx.site_ground = custom
    site_map = landscape_utils.generate_full_3d_landscape_sitemap(ctx)

    assert site_map[0][20][2] == "FENCE"
    assert site_map[1][20][2] == "TORCH"
    assert site_map[0][20][6] == "FENCE"
    assert site_map[SITE_GROUND_Y][15][4] == "DIRT_PATH"
    assert site_map[0][15][2] == "."


def test_generate_full_3d_landscape_auto_path_when_site_ground_missing(ctx):
    ctx.grid["path_orientation"] = "vertical"
    ctx.site_ground = None
    site_map = landscape_utils.generate_full_3d_landscape_sitemap(ctx)

    # Auto path below structure footprint (path_start_z=7, center x=11).
    assert site_map[SITE_GROUND_Y][10][11] not in ("GRASS", ".")
    assert site_map[SITE_GROUND_Y][6][11] == "GRASS"


def test_path_view_shows_only_y_minus_one_zero_one(ctx):
    ctx.layers = [
        {"index": -2, "cells": [["BEDROCK"]]},
        {"index": -1, "cells": [["STONE"]]},
        {"index": 0, "cells": [["PLANKS:oak"]]},
        {"index": 5, "cells": [["BRICKS"]]},
    ]
    assert landscape_utils.path_view_y_keys(ctx) == [-1, 0, 1]


def test_path_view_projects_structure_at_y_minus_one_zero_one(ctx):
    ctx.layers = [
        {
            "index": -2,
            "cells": [
                ["BEDROCK", "BEDROCK"],
                ["BEDROCK", "BEDROCK"],
            ],
        },
        {
            "index": -1,
            "cells": [
                ["STONE", "STONE"],
                ["STONE", "STONE"],
            ],
        },
        {
            "index": 0,
            "cells": [
                ["PLANKS:oak", "PLANKS:oak"],
                ["PLANKS:oak", "PLANKS:oak"],
            ],
        },
    ]
    ctx.grid["offset_x"] = 0
    ctx.grid["offset_z"] = 0
    ctx.grid["site_width"] = 2
    ctx.grid["site_depth"] = 2

    site_map = landscape_utils.generate_full_3d_landscape_sitemap(ctx)
    assert -2 not in site_map
    assert site_map[-1][0][0] == "STONE"
    assert site_map[0][0][0] == "PLANKS:oak"
    assert site_map[1][0][0] == "."
