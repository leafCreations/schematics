"""Tests for C4 attachable / multi-cell orbit mesh geometry."""

from __future__ import annotations

from helpers.context import SchematicContext
from helpers.orbit_greedy_mesh import (
    build_orbit_greedy_mesh_from_context,
    iter_occupied_voxel_cells,
)
from helpers.orbit_partial_mesh import (
    iter_all_orbit_boxes,
    iter_orbit_boxes_for_cell,
)


def _ctx_from_layers(layers: list[dict]) -> SchematicContext:
    return SchematicContext(
        structure="test",
        stage=1,
        name="Attachable Sample",
        layers=layers,
        grid={"site_size": 20, "offset_x": 0, "offset_z": 0},
        block_registry={},
        assets_dir=__import__("pathlib").Path("."),
        worldgen_template_dir=__import__("pathlib").Path("."),
        output_schematics_dir=__import__("pathlib").Path("."),
        output_worldgen_dir=__import__("pathlib").Path("."),
    )


def test_torch_boxes_are_thin_not_full_cube():
    ctx = _ctx_from_layers([{"index": 0, "cells": [["TORCH"]]}])
    cell = iter_occupied_voxel_cells(ctx)[0]
    boxes = iter_orbit_boxes_for_cell(cell, ctx.layers[0]["cells"])

    assert boxes
    max_span = max(box.max_corner[0] - box.min_corner[0] for box in boxes)
    assert max_span < 0.5


def test_lantern_standing_vs_hanging_differ_in_height():
    standing_ctx = _ctx_from_layers([{"index": 0, "cells": [["LANTERN"]]}])
    hanging_ctx = _ctx_from_layers(
        [
            {"index": 0, "cells": [["PLANKS:oak"]]},
            {"index": 1, "cells": [["LANTERN"]]},
        ],
    )
    standing_cell = iter_occupied_voxel_cells(standing_ctx)[0]
    hanging_cell = iter_occupied_voxel_cells(hanging_ctx)[1]
    standing = iter_orbit_boxes_for_cell(standing_cell, hanging_ctx.layers[1]["cells"])
    hanging = iter_orbit_boxes_for_cell(
        hanging_cell,
        hanging_ctx.layers[1]["cells"],
        layer_cells_cache={0: hanging_ctx.layers[0]["cells"], 1: hanging_ctx.layers[1]["cells"]},
    )

    standing_top = max(box.max_corner[1] for box in standing)
    hanging_top = max(box.max_corner[1] for box in hanging)
    assert hanging_top > standing_top


def test_bed_pair_spans_two_cells_from_head():
    ctx = _ctx_from_layers(
        [
            {
                "index": 0,
                "cells": [
                    ["BED:blue@north#head", "BED:blue@north#foot"],
                ],
            },
        ],
    )
    cells = iter_occupied_voxel_cells(ctx)
    cache = {0: ctx.layers[0]["cells"]}
    boxes = iter_all_orbit_boxes(cells, cache)

    assert len(boxes) == 1
    assert boxes[0].max_corner[0] - boxes[0].min_corner[0] == 2.0
    assert boxes[0].max_corner[1] - boxes[0].min_corner[1] < 1.0


def test_chest_pair_spans_two_cells_from_left():
    ctx = _ctx_from_layers(
        [
            {
                "index": 0,
                "cells": [
                    ["CHEST@west#left", "CHEST@west#right"],
                ],
            },
        ],
    )
    cells = iter_occupied_voxel_cells(ctx)
    cache = {0: ctx.layers[0]["cells"]}
    boxes = iter_all_orbit_boxes(cells, cache)

    assert len(boxes) == 1
    assert boxes[0].max_corner[0] - boxes[0].min_corner[0] == 2.0
    assert boxes[0].max_corner[1] - boxes[0].min_corner[1] < 1.0


def test_trapdoor_open_is_thin_vertical_plate():
    ctx = _ctx_from_layers([{"index": 0, "cells": [["TRAPDOOR:oak@north;open=true"]]}])
    cell = iter_occupied_voxel_cells(ctx)[0]
    boxes = iter_orbit_boxes_for_cell(cell, ctx.layers[0]["cells"])

    assert boxes
    depth = max(box.max_corner[2] - box.min_corner[2] for box in boxes)
    height = max(box.max_corner[1] - box.min_corner[1] for box in boxes)
    assert depth < 0.25
    assert height > 0.5


def test_trapdoor_closed_bottom_is_low_horizontal_plate():
    ctx = _ctx_from_layers([{"index": 0, "cells": [["TRAPDOOR:oak@north"]]}])
    cell = iter_occupied_voxel_cells(ctx)[0]
    boxes = iter_orbit_boxes_for_cell(cell, ctx.layers[0]["cells"])

    assert boxes
    assert max(box.max_corner[1] for box in boxes) <= 0.25


def test_door_lower_upper_layers_form_continuous_plate():
    """#lower and #upper are separate layer cells — each is a full-height plate."""
    ctx = _ctx_from_layers(
        [
            {"index": 1, "cells": [[".", ".", "DOOR:oak@north#lower"]]},
            {"index": 2, "cells": [[".", ".", "DOOR:oak@north#upper"]]},
        ],
    )
    cells = iter_occupied_voxel_cells(ctx)
    cache = {0: ctx.layers[0]["cells"], 1: ctx.layers[1]["cells"]}
    boxes = iter_all_orbit_boxes(cells, cache)

    assert len(boxes) == 2
    lowers = sorted(boxes, key=lambda box: box.min_corner[1])
    assert lowers[0].max_corner[1] == lowers[1].min_corner[1]
    assert lowers[0].max_corner[1] - lowers[0].min_corner[1] == 1.0


def test_plank_face_toward_lantern_neighbor_is_not_culled():
    """Attachables do not belong in partial_worlds — wall keeps faces beside lanterns."""
    from helpers.orbit_greedy_mesh import _solid_face_visible
    from helpers.orbit_mesh import OccupiedVoxel

    plank = OccupiedVoxel(
        world=(1, 2, 0),
        token="PLANKS:oak",
        layer_list_index=0,
        local_x=1,
        local_z=0,
    )
    voxel_map = {plank.world: plank}
    partial_worlds = frozenset()

    assert _solid_face_visible(plank.world, (0, 0, 1), voxel_map, partial_worlds)


def test_slab_neighbor_still_in_partial_worlds():
    from helpers.orbit_partial_mesh import is_partial_volume_behavior

    assert is_partial_volume_behavior("SLAB:oak")
    assert is_partial_volume_behavior("STAIRS:oak")
    assert not is_partial_volume_behavior("FENCE:oak")
    assert not is_partial_volume_behavior("WALL:cobblestone")
    assert not is_partial_volume_behavior("LANTERN")
    assert not is_partial_volume_behavior("TORCH@east#wall")


def test_plank_face_toward_fence_neighbor_is_not_culled():
    from helpers.orbit_greedy_mesh import _solid_face_visible
    from helpers.orbit_mesh import OccupiedVoxel

    plank = OccupiedVoxel(
        world=(0, 0, 0),
        token="PLANKS:oak",
        layer_list_index=0,
        local_x=0,
        local_z=0,
    )
    voxel_map = {plank.world: plank}
    fence_world = (1, 0, 0)

    assert _solid_face_visible(plank.world, (1, 0, 0), voxel_map, frozenset())
    assert not _solid_face_visible(plank.world, (1, 0, 0), voxel_map, frozenset({fence_world}))


def test_greedy_mesh_plank_beside_fence_has_exterior_face():
    ctx = _ctx_from_layers([{"index": 0, "cells": [["PLANKS:oak", "FENCE:oak"]]}])
    mesh = build_orbit_greedy_mesh_from_context(ctx)
    assert mesh.vertex_count > 0
    assert any(abs(mesh.positions[i] - 1.0) < 1e-6 for i in range(0, len(mesh.positions), 3))


def test_attachables_excluded_from_greedy_full_cube_shell():
    ctx = _ctx_from_layers(
        [
            {
                "index": 0,
                "cells": [
                    ["TORCH", "LANTERN"],
                ],
            },
        ],
    )
    mesh = build_orbit_greedy_mesh_from_context(ctx)
    y_values = [mesh.positions[index] for index in range(1, len(mesh.positions), 3)]
    assert max(y_values) < 1.0
