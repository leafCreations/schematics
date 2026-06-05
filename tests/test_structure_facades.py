from renderers.structure_facades import (
    Y_LABEL_WIDTH,
    _build_structure_elevation_layout,
    structure_facade_row_labels,
)
from tests.test_layer_visibility import _minimal_ctx


def test_structure_facade_row_labels_include_y_level():
    ctx = _minimal_ctx(
        {"index": -1, "group": "Basement", "cells": [["STONE"]]},
        {"index": 0, "group": "Floor 1", "cells": [["PLANKS:oak"]]},
    )
    labels = structure_facade_row_labels(ctx, [0, 1])
    assert labels == ["Basement (Y=-1)", "Floor 1 (Y=0)"]


def test_structure_facade_layout_reserves_y_label_column():
    ctx = _minimal_ctx(
        {"index": 0, "cells": [["STONE"]]},
    )
    layout = _build_structure_elevation_layout(ctx)
    assert layout["y_label_width"] == Y_LABEL_WIDTH
    assert layout["img_w"] >= Y_LABEL_WIDTH
