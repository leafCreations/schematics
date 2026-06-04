from unittest.mock import patch

from helpers import cells as cell_utils
from helpers import layer_visibility
from helpers.context import SchematicContext
from helpers.layers import render_layer_group_blueprints


def _minimal_ctx(*layers: dict) -> SchematicContext:
    return SchematicContext(
        structure="test",
        stage=1,
        name="Test",
        layers=list(layers),
        grid={
            "site_width": 4,
            "site_depth": 4,
            "offset_x": 0,
            "offset_z": 0,
            "placement": "center",
        },
        block_registry={},
        assets_dir=__import__("pathlib").Path("."),
        worldgen_template_dir=__import__("pathlib").Path("."),
        output_schematics_dir=__import__("pathlib").Path("out_schem"),
        output_worldgen_dir=__import__("pathlib").Path("out_world"),
    )


def test_is_layer_visible_defaults_true():
    assert layer_visibility.is_layer_visible({"cells": [["."]]})
    assert layer_visibility.is_layer_visible({"cells": [["."]], "visible": True})


def test_is_layer_visible_false_when_hidden():
    assert not layer_visibility.is_layer_visible({"cells": [["."]], "visible": False})


def test_set_layer_visible_omits_key_when_shown():
    layer = {"visible": False}
    layer_visibility.set_layer_visible(layer, True)
    assert "visible" not in layer


def test_get_structure_cell_skips_hidden_layer():
    ctx = _minimal_ctx(
        {"index": 0, "cells": [["STONE"]], "visible": False},
    )
    assert cell_utils.get_structure_cell(ctx, 0, 0, 0) == "."


def test_visible_layer_array_indices():
    layers = [{"visible": False}, {"index": 1}, {"index": 2}]
    assert layer_visibility.visible_layer_array_indices(layers) == [1, 2]


def test_site_facade_layer_keys_skips_empty_overlay_row():
    site_map = {
        -1: [["GRASS"]],
        0: [["."]],
        1: [["STONE"]],
    }
    keys = layer_visibility.site_facade_layer_keys(site_map, site_width=1, site_depth=1)
    assert keys == [-1, 1]


def test_structure_facade_layout_omits_hidden_layer_rows():
    from renderers.structure_facades import _build_structure_elevation_layout

    ctx = _minimal_ctx(
        {"index": 0, "cells": [["STONE"]], "visible": False},
        {"index": 1, "cells": [["WOOD"]]},
    )
    layout = _build_structure_elevation_layout(ctx)
    assert layout["visible_layer_indices"] == [1]
    assert layout["max_layers"] == 1


def test_render_layer_group_skips_hidden_layers():
    ctx = _minimal_ctx(
        {"index": 0, "name": "Floor A", "cells": [["."]]},
        {"index": 1, "name": "Floor B", "cells": [["."]], "visible": False},
    )

    with patch("helpers.layers.render_layer_blueprint") as render:
        render_layer_group_blueprints(ctx, roofs=False)

    assert render.call_count == 1
    assert render.call_args[0][2] == [ctx.layers[0]]
