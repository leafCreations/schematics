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


def test_copper_lantern_hanging_uses_variant_hanging_model():
    from helpers.orbit_attachable_mesh import resolve_attachable_block_model
    from helpers.registry_lookup import get_block_entry
    from helpers.structure_tokens import parse_structure_token

    ctx = _ctx_from_layers(
        [
            {"index": 0, "cells": [["COPPER_LANTERN#exposed"]]},
            {"index": 1, "cells": [["PLANKS:oak"]]},
        ],
    )
    cell = iter_occupied_voxel_cells(ctx)[0]
    parsed = parse_structure_token("COPPER_LANTERN#exposed")
    entry = get_block_entry(parsed) or {}
    cache = {0: ctx.layers[0]["cells"], 1: ctx.layers[1]["cells"]}
    model_name, rotation_y = resolve_attachable_block_model(
        cell,
        entry,
        parsed,
        layer_cells_cache=cache,
    )

    assert model_name == "exposed_copper_lantern_hanging"
    assert rotation_y == 0


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


def test_wall_torch_uses_block_model_faces_not_sprite_bake_on_aabb():
    from helpers.orbit_block_model_mesh import iter_block_model_face_quads

    quads = iter_block_model_face_quads("wall_torch", 0.0, 0.0, 0.0, rotation_y=0)
    assert len(quads) == 6
    assert all(quad.signature.startswith("bm:wall_torch:") for quad in quads)
    assert all(quad.texture.width > 0 for quad in quads)


def test_wall_torch_rotation_follows_token_direction():
    from helpers.orbit_attachable_mesh import resolve_attachable_block_model
    from helpers.orbit_block_model_mesh import iter_block_model_face_quads
    from helpers.orbit_mesh import OccupiedVoxel
    from helpers.registry_lookup import get_block_entry
    from helpers.structure_tokens import parse_structure_token

    def center_xz(token: str) -> tuple[float, float]:
        parsed = parse_structure_token(token)
        entry = get_block_entry(parsed) or {}
        cell = OccupiedVoxel(world=(0, 0, 0), token=token, layer_list_index=0, local_x=0, local_z=0)
        model_name, rotation_y = resolve_attachable_block_model(cell, entry, parsed)
        quads = iter_block_model_face_quads(model_name, 0.0, 0.0, 0.0, rotation_y=rotation_y)
        xs = [corner[0] for quad in quads for corner in quad.corners]
        zs = [corner[2] for quad in quads for corner in quad.corners]
        return (sum(xs) / len(xs), sum(zs) / len(zs))

    centers = {
        token: center_xz(token)
        for token in (
            "TORCH@north#wall",
            "TORCH@south#wall",
            "TORCH@east#wall",
            "TORCH@west#wall",
        )
    }
    assert len(set(centers.values())) == 4


def test_wall_torch_tip_leans_in_facing_direction():
    from helpers.orbit_attachable_mesh import resolve_attachable_block_model
    from helpers.orbit_block_model_mesh import iter_block_model_face_quads
    from helpers.orbit_mesh import OccupiedVoxel
    from helpers.registry_lookup import get_block_entry
    from helpers.structure_tokens import parse_structure_token

    facing_axis = {"east": (1, 0), "south": (0, 1), "west": (-1, 0), "north": (0, -1)}
    wall_side = {"east": "west", "west": "east", "north": "south", "south": "north"}

    for facing, (fx, fz) in facing_axis.items():
        token = f"TORCH@{facing}#wall"
        parsed = parse_structure_token(token)
        entry = get_block_entry(parsed) or {}
        cell = OccupiedVoxel(world=(5, 1, 5), token=token, layer_list_index=0, local_x=5, local_z=5)
        model_name, rotation_y = resolve_attachable_block_model(cell, entry, parsed)
        quads = iter_block_model_face_quads(model_name, 5.0, 1.0, 5.0, rotation_y=rotation_y)
        points = [corner for quad in quads for corner in quad.corners]
        mount = min(points, key=lambda point: point[1])
        tip = max(points, key=lambda point: point[1])
        lean = (tip[0] - mount[0], tip[2] - mount[2])
        assert lean[0] * fx + lean[1] * fz > 0.0

        mx = mount[0] - 5.5
        mz = mount[2] - 5.5
        on_wall = {
            "west": mx < -0.05,
            "east": mx > 0.05,
            "north": mz < -0.05,
            "south": mz > 0.05,
        }[wall_side[facing]]
        assert on_wall


def test_door_plate_rotates_with_direction():
    ctx_n = _ctx_from_layers([{"index": 0, "cells": [["DOOR:oak@north#lower"]]}])
    ctx_s = _ctx_from_layers([{"index": 0, "cells": [["DOOR:oak@south#lower"]]}])
    north = iter_orbit_boxes_for_cell(
        iter_occupied_voxel_cells(ctx_n)[0],
        ctx_n.layers[0]["cells"],
    )[0]
    south = iter_orbit_boxes_for_cell(
        iter_occupied_voxel_cells(ctx_s)[0],
        ctx_s.layers[0]["cells"],
    )[0]
    assert north.min_corner != south.min_corner


def test_wall_torch_against_plank_culls_back_face():
    alone_ctx = _ctx_from_layers([{"index": 0, "cells": [["TORCH@north#wall"]]}])
    pair_ctx = _ctx_from_layers(
        [{"index": 0, "cells": [["PLANKS:oak", "TORCH@north#wall"]]}],
    )
    plank_ctx = _ctx_from_layers([{"index": 0, "cells": [["PLANKS:oak"]]}])

    alone_mesh = build_orbit_greedy_mesh_from_context(alone_ctx)
    pair_mesh = build_orbit_greedy_mesh_from_context(pair_ctx)
    plank_mesh = build_orbit_greedy_mesh_from_context(plank_ctx)

    assert alone_mesh.triangle_count == 12
    assert plank_mesh.triangle_count == 12
    # Plank keeps six exterior faces; torch loses the face against the plank (−2 tris).
    assert pair_mesh.triangle_count == plank_mesh.triangle_count + alone_mesh.triangle_count - 2
