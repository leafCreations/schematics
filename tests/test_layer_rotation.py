from helpers.layer_rotation import rotate_cell_token, rotate_layer_cells


def test_rotate_cell_token_direction_clockwise():
    assert rotate_cell_token("DOOR:oak@north", clockwise=True) == "DOOR:oak@east"
    assert rotate_cell_token("DOOR:oak@north", clockwise=False) == "DOOR:oak@west"


def test_rotate_layer_cells_clockwise_swaps_dimensions():
    cells = [
        ["A", "B", "C"],
        ["D", "E", "F"],
    ]
    rotated = rotate_layer_cells(cells, clockwise=True)

    assert len(rotated) == 3
    assert len(rotated[0]) == 2
    assert rotated[0][1] == "A"
    assert rotated[1][1] == "B"
    assert rotated[2][1] == "C"
    assert rotated[0][0] == "D"
    assert rotated[1][0] == "E"
    assert rotated[2][0] == "F"


def test_rotate_layer_cells_counter_clockwise():
    cells = [
        ["A", "B"],
        ["C", "D"],
    ]
    rotated = rotate_layer_cells(cells, clockwise=False)

    assert rotated == [
        ["B", "D"],
        ["A", "C"],
    ]
