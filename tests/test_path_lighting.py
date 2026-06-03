from helpers.path_lighting import iter_lighting_fence_cells_from_ground
from helpers.path_strip import TRIM_BLOCK, is_trim_token, resolve_trim_block


def test_trim_run_lighting_vertical_and_horizontal():
    ground = [["GRASS"] * 30 for _ in range(30)]

    for site_z in range(10, 26):
        ground[site_z][2] = TRIM_BLOCK
        ground[site_z][3] = "DIRT_PATH"
        ground[site_z][4] = "DIRT_PATH"
        ground[site_z][5] = "DIRT_PATH"
        ground[site_z][6] = TRIM_BLOCK

    for site_x in range(7, 25):
        ground[16][site_x] = TRIM_BLOCK
        ground[17][site_x] = "DIRT_PATH"

    posts = set(iter_lighting_fence_cells_from_ground(ground))

    assert (2, 20) in posts
    assert (6, 20) in posts
    assert (16, 16) in posts
    assert (23, 16) in posts
    assert (29, 20) not in posts


def test_residence_stage1_fence_posts_only_on_configured_trim():
    from pathlib import Path

    import yaml

    from helpers.structure_loader import build_schematic_context

    base = Path("structures/residence/stage1")
    with open(base / "structure.yaml") as f:
        cfg = yaml.safe_load(f)
    cfg["layers"] = []
    for lf in cfg["layer_files"]:
        with open(base / lf) as f:
            cfg["layers"].append(yaml.safe_load(f))
    ctx = build_schematic_context(cfg)
    trim_block = resolve_trim_block(ctx.grid)
    posts = set(
        iter_lighting_fence_cells_from_ground(ctx.site_ground, trim_block=trim_block),
    )

    assert (29, 27) not in posts

    for site_x, site_z in posts:
        assert is_trim_token(ctx.site_ground[site_z][site_x], trim_block=trim_block)


def test_lighting_only_on_gravel_trim_cells():
    ground = [["GRASS"] * 15 for _ in range(25)]

    for site_z in range(5, 20):
        ground[site_z][2] = TRIM_BLOCK
        ground[site_z][3] = "DIRT_PATH"
        ground[site_z][4] = TRIM_BLOCK

    posts = list(iter_lighting_fence_cells_from_ground(ground))

    for site_x, site_z in posts:
        assert ground[site_z][site_x] == TRIM_BLOCK


def test_lighting_skips_path_variety_in_center_band():
    """GRAVEL/DIRT in the path band must not receive fence posts when trim is COBBLESTONE."""
    ground = [["GRASS"] * 8 for _ in range(20)]

    for site_z in range(4, 18):
        ground[site_z][1] = "COBBLESTONE"
        ground[site_z][2] = "GRAVEL"
        ground[site_z][3] = "DIRT_PATH"
        ground[site_z][4] = "DIRT"
        ground[site_z][5] = "COBBLESTONE"

    posts = set(
        iter_lighting_fence_cells_from_ground(ground, trim_block="COBBLESTONE"),
    )

    assert (1, 14) in posts
    assert (5, 14) in posts
    assert (2, 14) not in posts
    assert (3, 14) not in posts
    assert (4, 14) not in posts


def test_short_trim_run_has_no_posts():
    ground = [["GRASS"] * 6 for _ in range(12)]

    for site_z in range(2, 10):
        ground[site_z][1] = "COBBLESTONE"
        ground[site_z][2] = "DIRT_PATH"
        ground[site_z][3] = "COBBLESTONE"

    posts = set(
        iter_lighting_fence_cells_from_ground(ground, trim_block="COBBLESTONE"),
    )

    assert posts == set()
