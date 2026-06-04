from helpers import layer_groups
from helpers.layer_management import layer_label


def test_collect_layer_groups_preserves_order():
    layers = [
        {"group": "Floor 1", "cells": [["."]]},
        {"group": "Roof", "cells": [["."]]},
        {"group": "Floor 1", "cells": [["."]]},
    ]
    assert layer_groups.collect_layer_groups(layers) == ["Floor 1", "Roof"]


def test_group_hidden_persisted_on_grid():
    grid: dict = {}
    layer_groups.set_group_hidden(grid, "Roof", hidden=True)
    assert grid["hidden_groups"] == ["Roof"]
    layer_groups.set_group_hidden(grid, "Roof", hidden=False)
    assert "hidden_groups" not in grid


def test_is_layer_render_visible_respects_layer_and_group():
    grid = {"hidden_groups": ["Roof"]}
    floor = {"group": "Floor 1", "cells": [["STONE"]]}
    roof = {"group": "Roof", "cells": [["STONE"]], "visible": False}

    assert layer_groups.is_layer_render_visible(floor, 0, grid)
    assert not layer_groups.is_layer_render_visible(roof, 1, grid)

    roof_visible = {"group": "Roof", "cells": [["STONE"]]}
    assert not layer_groups.is_layer_render_visible(roof_visible, 1, grid)


def test_layer_matches_group_filter():
    layer = {"group": "A", "cells": [["."]]}
    assert layer_groups.layer_matches_group_filter(layer, 0, None)
    assert layer_groups.layer_matches_group_filter(layer, 0, "A")
    assert not layer_groups.layer_matches_group_filter(layer, 0, "B")


def test_visible_layer_array_indices_with_hidden_group():
    layers = [
        {"group": "A", "cells": [["."]]},
        {"group": "B", "cells": [["."]]},
    ]
    assert layer_groups.visible_layer_array_indices(layers, {"hidden_groups": ["B"]}) == [0]


def test_collect_layer_groups_includes_defined_empty_groups():
    layers = [{"group": "Floor 1", "cells": [["."]]}]
    grid = {"groups": ["Roof", "Floor 1"]}
    assert layer_groups.collect_layer_groups(layers, grid) == ["Floor 1", "Roof"]


def test_rename_group_updates_layers_and_grid():
    layers = [
        {"group": "A", "cells": [["."]]},
        {"index": 1, "cells": [["."]]},
    ]
    grid = {"groups": ["A"], "hidden_groups": ["A"]}
    layer_groups.rename_group(layers, grid, "A", "B")
    assert layers[0]["group"] == "B"
    assert layer_label(layers[1], 1) == "Layer 1"
    assert grid["groups"] == ["B"]
    assert grid["hidden_groups"] == ["B"]


def test_remove_group_clears_layer_assignment():
    layers = [{"group": "Roof", "cells": [["."]]}]
    grid = {"groups": ["Roof"], "hidden_groups": ["Roof"]}
    layer_groups.remove_group(layers, grid, "Roof")
    assert "group" not in layers[0]
    assert "groups" not in grid
    assert "hidden_groups" not in grid
