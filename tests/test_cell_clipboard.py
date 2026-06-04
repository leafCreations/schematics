from helpers.cell_clipboard import CellRegionClipboard, copy_region, paste_region


def test_copy_region_bounding_box_with_gap():
    cells = [
        ["A", "B", "C"],
        ["D", "E", "F"],
    ]
    clipboard = copy_region(cells, [(0, 0), (1, 1)])

    assert clipboard is not None
    assert clipboard.cells == (("A", "."), (".", "E"))


def test_paste_region_clamps_to_layer():
    cells = [
        [".", "."],
        [".", "."],
    ]
    clipboard = CellRegionClipboard(cells=(("X", "Y"),))
    changes = paste_region(cells, clipboard, dest_row=1, dest_col=1)

    assert changes == [(1, 1, "X")]

    for row, col, token in changes:
        cells[row][col] = token

    assert cells[1][1] == "X"
    assert cells[1][0] == "."
