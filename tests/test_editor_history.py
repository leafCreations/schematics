from ui.document import StructureDocument
from ui.editor_history import apply_history_state, capture_history_state


def test_history_roundtrip_preserves_cells_and_grid():
    document = StructureDocument(
        structure_path=__file__,
        metadata={"grid": {"site_width": 10, "site_depth": 10, "offset_x": 1, "offset_z": 2}},
        layer_files=["layer_00.yaml"],
        layer_paths=[__file__],
        layers=[{"cells": [["A", "."], [".", "B"]]}],
        site_ground=[["GRASS"] * 10 for _ in range(10)],
    )
    dirty_layers: set[int] = {0}
    dirty_structure = True

    snapshot = capture_history_state(
        document,
        dirty_layers=dirty_layers,
        dirty_structure=dirty_structure,
    )

    document.metadata["grid"]["offset_x"] = 5
    document.layers[0]["cells"][0][0] = "."
    document.site_ground[0][0] = "DIRT_PATH"
    dirty_layers.clear()
    dirty_structure = False

    dirty_flag = [False]
    apply_history_state(
        document,
        snapshot,
        dirty_layers=dirty_layers,
        dirty_structure_holder=dirty_flag,
    )

    assert document.metadata["grid"]["offset_x"] == 1
    assert document.layers[0]["cells"] == [["A", "."], [".", "B"]]
    assert document.site_ground[0][0] == "GRASS"
    assert dirty_layers == {0}
    assert dirty_flag[0] is True
