import random

from helpers.path_strip import (
    DEFAULT_PATH_VARIETY_BLOCKS,
    DIRT_PATH_BLOCK,
    PATH_VARIETY_OPTIONS,
    TRIM_BLOCK,
    clear_all_paths,
    erase_path_at_site,
    is_path_related_token,
    paint_path_at_site,
    paint_path_column,
    paint_path_row,
    path_strip_bounds,
    random_path_block,
    resolve_path_orientation,
    resolve_path_variety_blocks,
    resolve_trim_block,
)
from helpers.site_ground import GRASS_BLOCK


def test_path_strip_bounds_width_three():
    assert path_strip_bounds(10, 3) == (9, 11, 8, 12)


def test_paint_path_row_applies_trim_path_trim():
    row = [GRASS_BLOCK] * 7
    rng = random.Random(0)
    paint_path_row(row, center_x=3, path_width=3, site_z=0, rng=rng)

    assert row[0] == GRASS_BLOCK
    assert row[1] == TRIM_BLOCK
    assert row[2] not in (GRASS_BLOCK, TRIM_BLOCK)
    assert row[3] not in (GRASS_BLOCK, TRIM_BLOCK)
    assert row[4] not in (GRASS_BLOCK, TRIM_BLOCK)
    assert row[5] == TRIM_BLOCK
    assert row[6] == GRASS_BLOCK


def test_paint_path_at_site_row():
    ground = [[GRASS_BLOCK] * 5 for _ in range(3)]
    paint_path_at_site(ground, site_x=2, site_z=1, path_width=3, rng=random.Random(1))

    assert ground[1][0] == TRIM_BLOCK
    assert ground[1][4] == TRIM_BLOCK
    assert ground[0][1] == GRASS_BLOCK


def test_random_path_block_returns_known_tokens():
    token = random_path_block(random.Random(0))
    assert token in {DIRT_PATH_BLOCK, *PATH_VARIETY_OPTIONS}


def test_paint_path_column_vertical_strip():
    ground = [[GRASS_BLOCK] * 5 for _ in range(7)]
    paint_path_column(ground, site_x=2, center_z=3, path_width=3, rng=random.Random(0))

    assert ground[0][2] == GRASS_BLOCK
    assert ground[1][2] == TRIM_BLOCK
    assert ground[2][2] not in (GRASS_BLOCK, TRIM_BLOCK)
    assert ground[4][2] not in (GRASS_BLOCK, TRIM_BLOCK)
    assert ground[5][2] == TRIM_BLOCK
    assert ground[1][0] == GRASS_BLOCK


def test_paint_path_at_site_vertical_orientation():
    ground = [[GRASS_BLOCK] * 5 for _ in range(5)]
    paint_path_at_site(
        ground,
        site_x=2,
        site_z=2,
        path_width=3,
        orientation="vertical",
        rng=random.Random(1),
    )

    assert ground[2][2] not in (GRASS_BLOCK,)
    assert ground[4][0] == GRASS_BLOCK


def test_paint_path_skips_structure_footprint():
    ground = [[GRASS_BLOCK] * 9 for _ in range(8)]
    paint_path_at_site(
        ground,
        site_x=7,
        site_z=2,
        path_width=3,
        orientation="vertical",
        offset_x=2,
        offset_z=1,
        structure_width=4,
        structure_depth=3,
        rng=random.Random(0),
    )

    for z in range(1, 4):
        for x in range(2, 6):
            assert ground[z][x] == GRASS_BLOCK

    assert ground[0][7] == TRIM_BLOCK
    assert ground[2][7] != GRASS_BLOCK


def test_paint_path_rejects_anchor_on_structure():
    ground = [[GRASS_BLOCK] * 5 for _ in range(5)]
    assert not paint_path_at_site(
        ground,
        site_x=3,
        site_z=2,
        path_width=3,
        offset_x=1,
        offset_z=1,
        structure_width=3,
        structure_depth=3,
    )
    assert all(cell == GRASS_BLOCK for row in ground for cell in row)


def test_random_path_block_only_dirt_path_when_no_variety():
    assert random_path_block(variety_blocks=[]) == DIRT_PATH_BLOCK


def test_random_path_block_respects_variety_subset():
    rng = random.Random(0)
    tokens = {random_path_block(rng, variety_blocks=["minecraft:dirt"]) for _ in range(50)}
    assert "minecraft:dirt" in tokens
    assert tokens <= {DIRT_PATH_BLOCK, "minecraft:dirt"}


def test_resolve_trim_and_variety_defaults():
    assert resolve_trim_block({}) == TRIM_BLOCK
    assert resolve_path_variety_blocks({}) == list(DEFAULT_PATH_VARIETY_BLOCKS)


def test_resolve_path_orientation_defaults_horizontal():
    assert resolve_path_orientation({}) == "horizontal"
    assert resolve_path_orientation({"path_orientation": "vertical"}) == "vertical"
    assert resolve_path_orientation({"path_orientation": "invalid"}) == "horizontal"


def test_repaint_existing_path_only_updates_strip_at_click():
    """Repaint on existing path updates only the strip band at the click."""
    ground = [[GRASS_BLOCK] * 20]
    paint_path_row(ground[0], center_x=2, path_width=3, site_z=0, rng=random.Random(0))
    paint_path_row(ground[0], center_x=12, path_width=3, site_z=0, rng=random.Random(0))

    paint_path_at_site(
        ground,
        site_x=3,
        site_z=0,
        path_width=3,
        orientation="horizontal",
        trim_block="minecraft:cobblestone",
        rng=random.Random(1),
    )

    assert ground[0][1] == "minecraft:cobblestone"
    assert ground[0][5] == "minecraft:cobblestone"
    assert ground[0][0] == TRIM_BLOCK
    assert ground[0][10] == TRIM_BLOCK


def test_repaint_existing_path_respects_orientation_axis():
    ground = [[GRASS_BLOCK] * 8 for _ in range(8)]
    paint_path_row(ground[4], center_x=3, path_width=3, site_z=4, rng=random.Random(0))
    paint_path_column(ground, site_x=3, center_z=4, path_width=3, rng=random.Random(0))
    horizontal_trim = {x for x in range(8) if ground[4][x] == TRIM_BLOCK}

    paint_path_at_site(
        ground,
        site_x=3,
        site_z=4,
        path_width=3,
        orientation="vertical",
        trim_block="minecraft:cobblestone",
        rng=random.Random(2),
    )

    for z in range(8):
        if ground[z][3] in (TRIM_BLOCK, "minecraft:cobblestone"):
            assert ground[z][3] == "minecraft:cobblestone"

    assert {x for x in horizontal_trim if ground[4][x] == TRIM_BLOCK} == horizontal_trim

    paint_path_at_site(
        ground,
        site_x=3,
        site_z=4,
        path_width=3,
        orientation="horizontal",
        trim_block="minecraft:cobblestone",
        rng=random.Random(3),
    )

    assert ground[4][1] == "minecraft:cobblestone"
    assert ground[4][5] == "minecraft:cobblestone"


def test_erase_path_at_site_clears_entire_row():
    ground = [[GRASS_BLOCK] * 12 for _ in range(3)]
    paint_path_row(ground[0], center_x=2, path_width=3, site_z=0, rng=random.Random(0))
    paint_path_row(ground[2], center_x=8, path_width=3, site_z=2, rng=random.Random(1))

    assert erase_path_at_site(
        ground,
        site_x=4,
        site_z=0,
        path_width=3,
        orientation="horizontal",
    )

    assert ground[0] == [GRASS_BLOCK] * 12
    assert any(is_path_related_token(token) for token in ground[2])


def test_erase_path_at_site_clears_entire_column():
    ground = [[GRASS_BLOCK] * 5 for _ in range(7)]
    paint_path_column(ground, site_x=2, center_z=3, path_width=3, rng=random.Random(0))

    assert erase_path_at_site(
        ground,
        site_x=2,
        site_z=3,
        path_width=3,
        orientation="vertical",
    )

    assert all(ground[z][2] == GRASS_BLOCK for z in range(7))


def test_clear_all_paths():
    ground = [[GRASS_BLOCK] * 5 for _ in range(3)]
    paint_path_at_site(ground, site_x=2, site_z=1, path_width=3, rng=random.Random(1))

    assert clear_all_paths(ground) > 0
    assert all(cell == GRASS_BLOCK for row in ground for cell in row)
