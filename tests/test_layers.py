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
    assert get_layer_display_name({"name": "Y=2", "group": "Floor 1", "index": 2}) == "Y=2"


def test_get_layer_display_name_falls_back_to_group():
    assert get_layer_display_name({"group": "Floor 1", "index": 0}) == "Floor 1"


def test_get_layer_display_name_falls_back_to_index():
    assert get_layer_display_name({"index": 3}) == "Layer 3"


def test_get_layer_display_name_default():
    assert get_layer_display_name({}) == "Layer"
