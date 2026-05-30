from helpers import path_geometry


def test_get_path_geometry(ctx):
    geom = path_geometry.get_path_geometry(ctx)

    assert geom.stair_center_x == 14
    assert geom.path_start_z == 7
    assert geom.path_left == 13
    assert geom.path_right == 15
    assert geom.trim_left == 12
    assert geom.trim_right == 16
    assert geom.site_size == 30


def test_get_path_geometry_uses_grid_stair_local_x(ctx):
    ctx.grid["stair_local_x"] = 6

    geom = path_geometry.get_path_geometry(ctx)

    assert geom.stair_center_x == 16
    assert geom.path_left == 15
    assert geom.path_right == 17


def test_path_geometry_path_and_trim(ctx):
    geom = path_geometry.get_path_geometry(ctx)

    assert not geom.is_path_row(6)
    assert geom.is_path_row(7)
    assert geom.is_path_row(29)
    assert not geom.is_path_row(30)

    assert geom.is_on_path(14, 20)
    assert not geom.is_on_path(12, 20)
    assert not geom.is_on_path(14, 6)

    assert geom.is_on_trim(12, 20)
    assert geom.is_on_trim(16, 20)
    assert not geom.is_on_trim(14, 20)


def test_path_geometry_lighting(ctx):
    geom = path_geometry.get_path_geometry(ctx)

    assert not geom.is_lighting_row(16)
    assert geom.is_lighting_row(17)
    assert geom.is_lighting_row(24)
    assert not geom.is_lighting_row(31)

    assert geom.is_lighting_column(12)
    assert geom.is_lighting_column(16)
    assert not geom.is_lighting_column(14)
