from helpers.layers import get_layer_display_name, get_layer_group


def test_get_layer_group_prefers_group_field():
    assert get_layer_group({"group": "Floor 1", "name": "Unused"}) == "Floor 1"


def test_get_layer_group_uses_floor_field():
    assert get_layer_group({"floor": "Basement"}) == "Basement"


def test_get_layer_group_detects_roof_from_name():
    assert get_layer_group({"name": "Main Roof"}) == "Roof"


def test_get_layer_group_splits_colon_name():
    assert get_layer_group({"name": "Floor 2: Bedroom"}) == "Floor 2"


def test_get_layer_display_name_prefers_name():
    assert get_layer_display_name({"name": "Y=2", "group": "Floor 1", "index": 2}) == "Y=2 (Y=2)"


def test_get_layer_display_name_prefers_description():
    assert (
        get_layer_display_name({"group": "Floor 1", "description": "Ground", "index": 0})
        == "Ground (Y=0)"
    )


def test_get_layer_display_name_falls_back_to_group():
    assert get_layer_display_name({"group": "Floor 1", "index": 0}) == "Floor 1 (Y=0)"


def test_get_layer_display_name_falls_back_to_index():
    assert get_layer_display_name({"index": 3}) == "Layer 3 (Y=3)"


def test_get_layer_display_name_default():
    assert get_layer_display_name({}) == "Layer"


def test_render_layer_group_orders_by_worldgen_index():
    from unittest.mock import patch

    from helpers.context import SchematicContext
    from helpers.layers import render_layer_group_blueprints

    ctx = SchematicContext(
        structure="test",
        stage=1,
        name="Test",
        layers=[
            {"index": -1, "group": "Basement", "cells": [["B"]]},
            {"index": 0, "group": "Floor 1", "cells": [["F"]]},
            {"index": -2, "group": "Basement", "cells": [["F"]]},
        ],
        grid={
            "site_width": 1,
            "site_depth": 1,
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

    with patch("helpers.layers.render_layer_blueprint") as render:
        render_layer_group_blueprints(ctx, roofs=False)

    basement_layers = render.call_args_list[0][0][2]
    assert [layer["index"] for layer in basement_layers] == [-2, -1]
