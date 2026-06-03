from helpers import path_geometry


def test_get_path_geometry(ctx):
    geom = path_geometry.get_path_geometry(ctx)

    # No path_center in grid: defaults to structure width // 2 (3 // 2 = 1) + offset_x 10.
    assert geom.path_center_x == 11
    assert geom.path_start_z == 7
    assert geom.path_left == 10
    assert geom.path_right == 12
    assert geom.trim_left == 9
    assert geom.trim_right == 13
    assert geom.site_width == 30
    assert geom.site_depth == 30


def test_get_path_geometry_uses_grid_path_center_local_x(ctx):
    ctx.grid["path_center_local_x"] = 6

    geom = path_geometry.get_path_geometry(ctx)

    assert geom.path_center_x == 16


def test_get_path_geometry_accepts_deprecated_stair_local_x(ctx):
    ctx.grid.pop("path_center_local_x", None)
    ctx.grid["stair_local_x"] = 6

    geom = path_geometry.get_path_geometry(ctx)

    assert geom.path_center_x == 16


def test_painted_site_ground_ignores_path_center_metadata(ctx):
    ctx.grid["path_center_local_x"] = 99
    ctx.site_ground = [["GRASS"] * 12 for _ in range(15)]
    for site_z in range(5, 12):
        ctx.site_ground[site_z][2] = "GRAVEL"
        ctx.site_ground[site_z][3] = "DIRT_PATH"
        ctx.site_ground[site_z][4] = "GRAVEL"

    geom = path_geometry.get_path_geometry(ctx)

    assert geom.from_site_ground is True
    assert geom.path_center_x == 3
    assert geom.path_left == 3
    assert geom.path_right == 3
    assert geom.trim_left == 2
    assert geom.trim_right == 4


def test_path_geometry_path_and_trim(ctx):
    geom = path_geometry.get_path_geometry(ctx)

    assert not geom.is_path_row(6)
    assert geom.is_path_row(7)
    assert geom.is_path_row(29)
    assert not geom.is_path_row(30)

    assert geom.is_on_path(11, 20)
    assert not geom.is_on_path(9, 20)
    assert not geom.is_on_path(11, 6)

    assert geom.is_on_trim(9, 20)
    assert geom.is_on_trim(13, 20)
    assert not geom.is_on_trim(11, 20)


def test_path_geometry_lighting_vertical_stair_path(ctx):
    ctx.grid["path_orientation"] = "vertical"
    geom = path_geometry.get_path_geometry(ctx)

    assert not geom.is_lighting_row(16)
    assert geom.is_lighting_row(17)
    assert geom.is_lighting_row(24)
    assert not geom.is_lighting_row(31)
    assert not geom.is_lighting_column(14)

    fence_cells = list(geom.iter_lighting_fence_cells())
    assert (9, 17) in fence_cells
    assert (13, 17) in fence_cells


def test_path_geometry_lighting_horizontal_stair_path(ctx):
    ctx.grid["path_orientation"] = "horizontal"
    geom = path_geometry.get_path_geometry(ctx)

    assert geom.is_lighting_column(17)
    assert not geom.is_lighting_row(17)


def test_derive_vertical_path_from_painted_ground():
    site_ground = [["GRASS"] * 12 for _ in range(30)]

    for site_z in range(10, 26):
        site_ground[site_z][2] = "GRAVEL"
        site_ground[site_z][3] = "DIRT_PATH"
        site_ground[site_z][4] = "DIRT_PATH"
        site_ground[site_z][5] = "DIRT_PATH"
        site_ground[site_z][6] = "GRAVEL"

    geom = path_geometry.derive_path_geometry_from_ground(
        site_ground,
        orientation="vertical",
        path_width=3,
    )

    assert geom is not None
    assert geom.orientation == "vertical"
    assert geom.trim_left == 2
    assert geom.trim_right == 6
    assert geom.path_start_z == 10
    assert geom.path_end_z == 25
    posts = set(geom.iter_lighting_fence_cells())
    assert (2, 20) in posts
    assert (6, 20) in posts
