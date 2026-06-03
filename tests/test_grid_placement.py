import pytest

from helpers.grid_placement import (
    apply_placement_to_grid,
    infer_placement,
    nudge_structure_offset,
    offsets_for_placement,
    structure_dimensions_from_layers,
)


def test_offsets_for_center():
    assert offsets_for_placement("center", 30, 30, 9, 10) == (10, 10)


def test_offsets_for_top_left():
    assert offsets_for_placement("top_left", 30, 30, 9, 10) == (0, 0)


def test_offsets_for_bottom_right():
    assert offsets_for_placement("bottom_right", 30, 30, 9, 10) == (21, 20)


def test_offsets_on_rectangular_site():
    assert offsets_for_placement("center", 20, 10, 9, 10) == (5, 0)
    assert offsets_for_placement("bottom_right", 20, 10, 9, 10) == (11, 0)


def test_infer_placement_matches_exact_anchor():
    assert infer_placement(10, 10, 30, 30, 9, 10) == "center"


def test_apply_placement_to_grid_writes_rectangular_site():
    grid = apply_placement_to_grid(
        {"site_size": 30, "offset_x": 0, "offset_z": 0},
        placement="top_right",
        site_width=20,
        site_depth=10,
        structure_width=9,
        structure_depth=10,
    )

    assert grid["placement"] == "top_right"
    assert grid["site_width"] == 20
    assert grid["site_depth"] == 10
    assert "site_size" not in grid
    assert grid["offset_x"] == 11
    assert grid["offset_z"] == 0


def test_structure_dimensions_from_layers():
    layers = [{"cells": [[".", ".", "."], [".", ".", "."]]}]
    assert structure_dimensions_from_layers(layers) == (3, 2)


def test_offsets_reject_oversized_structure():
    with pytest.raises(ValueError, match="does not fit"):
        offsets_for_placement("center", 5, 10, 9, 10)


def test_nudge_structure_offset_shifts_and_updates_placement():
    grid = {
        "site_width": 10,
        "site_depth": 10,
        "offset_x": 2,
        "offset_z": 2,
        "placement": "top_left",
    }
    updated = nudge_structure_offset(
        grid, delta_x=1, delta_z=0, structure_width=3, structure_depth=2
    )

    assert updated is not None
    assert updated["offset_x"] == 3
    assert updated["offset_z"] == 2


def test_nudge_structure_offset_returns_none_when_blocked():
    grid = {"site_width": 5, "site_depth": 5, "offset_x": 0, "offset_z": 0}
    assert (
        nudge_structure_offset(grid, delta_x=-1, delta_z=0, structure_width=3, structure_depth=2)
        is None
    )
