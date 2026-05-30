import helpers.utils_schematics as schematics_utils


def test_show_interior_view_defaults_to_true():
    assert schematics_utils.show_interior_view("COBBLESTONE") is True


def test_show_interior_view_respects_registry_false():
    assert schematics_utils.show_interior_view("FURNACE") is False
    assert schematics_utils.show_interior_view("CRAFTING_TABLE") is False


def test_show_interior_view_empty_cell():
    assert schematics_utils.show_interior_view(".") is False
