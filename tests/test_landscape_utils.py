from helpers import landscape_utils


def test_resolve_path_view_cell_ground_layer():
    site_map = {
        -1: [["GRASS"]],
        0: [["."]],
        1: [["."]],
    }

    cell = landscape_utils.resolve_path_view_cell(-1, 0, 0, site_map)

    assert cell["active_token"] == "GRASS"
    assert cell["is_ground_layer"] is True
    assert cell["is_ghost"] is False


def test_resolve_path_view_cell_structure_overlay():
    site_map = {
        -1: [["GRASS"]],
        0: [["PLANKS:oak"]],
        1: [["."]],
    }

    cell = landscape_utils.resolve_path_view_cell(0, 0, 0, site_map)

    assert cell["active_token"] == "PLANKS:oak"
    assert cell["is_ghost"] is False


def test_resolve_path_view_cell_ghosts_base_when_no_overlay():
    site_map = {
        -1: [["GRASS"]],
        0: [["."]],
        1: [["."]],
    }

    cell = landscape_utils.resolve_path_view_cell(0, 0, 0, site_map)

    assert cell["active_token"] == "GRASS"
    assert cell["is_ghost"] is True
