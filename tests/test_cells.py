from helpers import cells as cell_utils


def test_get_cell_in_bounds(ctx):
    cells = ctx.layers[0]["cells"]

    assert cell_utils.get_cell(cells, 0, 0) == "A"
    assert cell_utils.get_cell(cells, 1, 0) == "B"
    assert cell_utils.get_cell(cells, 0, 1) == "D"
    assert cell_utils.get_cell(cells, 2, 1) == "F"


def test_get_cell_out_of_bounds_returns_empty(ctx):
    cells = ctx.layers[0]["cells"]

    assert cell_utils.get_cell(cells, -1, 0) == "."
    assert cell_utils.get_cell(cells, 3, 0) == "."
    assert cell_utils.get_cell(cells, 0, -1) == "."
    assert cell_utils.get_cell(cells, 0, 2) == "."


def test_get_cell_empty_none(ctx):
    cells = ctx.layers[0]["cells"]

    assert cell_utils.get_cell(cells, -1, 0, empty=None) is None


def test_get_structure_cell(ctx):
    assert cell_utils.get_structure_cell(ctx, 0, 0, 0) == "A"
    assert cell_utils.get_structure_cell(ctx, 0, 2, 1) == "F"
    assert cell_utils.get_structure_cell(ctx, 1, 1, 1) == "4"


def test_get_structure_cell_invalid_layer_returns_empty(ctx):
    assert cell_utils.get_structure_cell(ctx, -1, 0, 0) == "."
    assert cell_utils.get_structure_cell(ctx, 99, 0, 0) == "."


def test_get_structure_cell_at_site_maps_offset(ctx):
    assert cell_utils.get_structure_cell_at_site(ctx, 0, 10, 5) == "A"
    assert cell_utils.get_structure_cell_at_site(ctx, 0, 12, 6) == "F"


def test_get_structure_cell_at_site_outside_structure_returns_empty(ctx):
    assert cell_utils.get_structure_cell_at_site(ctx, 0, 9, 5) == "."
    assert cell_utils.get_structure_cell_at_site(ctx, 0, 10, 4) == "."
