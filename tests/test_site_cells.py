from ui.site_cells import build_site_display_grid, site_preview_layer_index


def test_build_site_display_grid_marks_padding():
    metadata = {
        "grid": {
            "site_width": 5,
            "site_depth": 5,
            "offset_x": 1,
            "offset_z": 1,
        }
    }
    layer = [
        ["A", "B"],
        ["C", "D"],
    ]
    site_ground = [["GRASS" for _ in range(5)] for _ in range(5)]

    display, width, depth, offset_x, offset_z = build_site_display_grid(
        metadata,
        [{"cells": layer}],
        layer,
        site_ground,
    )

    assert (width, depth) == (5, 5)
    assert (offset_x, offset_z) == (1, 1)
    assert display[0][0] == "GRASS"
    assert display[1][1] == "A"
    assert display[2][2] == "D"
    assert display[2][4] == "GRASS"


def test_site_preview_layer_index_uses_first_site_structure_layer():
    metadata = {"grid": {"site_structure_layers": [2, 0]}}
    assert site_preview_layer_index(metadata, 5) == 2


def test_site_preview_layer_index_defaults_to_zero():
    assert site_preview_layer_index({}, 3) == 0
