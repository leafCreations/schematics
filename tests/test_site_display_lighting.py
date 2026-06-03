from ui.site_cells import build_site_display_grid


def test_site_display_shows_fence_posts_on_vertical_path():
    metadata = {
        "grid": {
            "site_width": 12,
            "site_depth": 30,
            "offset_x": 0,
            "offset_z": 0,
            "path_orientation": "vertical",
            "path_width": 3,
        }
    }
    layers = [{"cells": [["PLANKS"]]}]
    site_ground = [["GRASS" for _ in range(12)] for _ in range(30)]

    for site_z in range(10, 26):
        site_ground[site_z][2] = "GRAVEL"
        site_ground[site_z][3] = "DIRT_PATH"
        site_ground[site_z][4] = "DIRT_PATH"
        site_ground[site_z][5] = "DIRT_PATH"
        site_ground[site_z][6] = "GRAVEL"

    display, *_ = build_site_display_grid(
        metadata,
        layers,
        layers[0]["cells"],
        site_ground,
    )

    assert display[20][2] == "FENCE"
    assert display[20][6] == "FENCE"
    assert display[15][4] == "DIRT_PATH"


def test_site_display_no_fences_when_site_ground_has_no_paths():
    metadata = {
        "grid": {
            "site_width": 12,
            "site_depth": 30,
            "offset_x": 0,
            "offset_z": 0,
            "path_orientation": "vertical",
            "path_width": 3,
        }
    }
    layers = [{"cells": [["."]]}]
    site_ground = [["GRASS" for _ in range(12)] for _ in range(30)]

    display, *_ = build_site_display_grid(
        metadata,
        layers,
        layers[0]["cells"],
        site_ground,
    )

    assert "FENCE" not in {cell for row in display for cell in row}
    assert "TORCH" not in {cell for row in display for cell in row}
