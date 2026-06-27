"""Tests for orbit partial-block mesh geometry."""

from __future__ import annotations

import pytest

from helpers.context import SchematicContext
from helpers.orbit_greedy_mesh import (
    build_orbit_greedy_mesh_from_context,
    iter_occupied_voxel_cells,
)
from helpers.orbit_partial_mesh import (
    box_face_occluded,
    group_orbit_boxes_by_world,
    iter_all_orbit_boxes,
    iter_orbit_boxes_for_cell,
)


def _ctx_from_layers(layers: list[dict]) -> SchematicContext:
    return SchematicContext(
        structure="test",
        stage=1,
        name="Partial Sample",
        layers=layers,
        grid={"site_size": 20, "offset_x": 0, "offset_z": 0},
        block_registry={},
        assets_dir=__import__("pathlib").Path("."),
        worldgen_template_dir=__import__("pathlib").Path("."),
        output_schematics_dir=__import__("pathlib").Path("."),
        output_worldgen_dir=__import__("pathlib").Path("."),
    )


def _normal_counts(mesh) -> dict[tuple[int, int, int], int]:
    counts: dict[tuple[int, int, int], int] = {}
    for index in range(0, len(mesh.normals), 3):
        key = (
            int(mesh.normals[index]),
            int(mesh.normals[index + 1]),
            int(mesh.normals[index + 2]),
        )
        counts[key] = counts.get(key, 0) + 1
    return counts


def test_slab_box_is_half_height():
    ctx = _ctx_from_layers([{"index": 0, "cells": [["SLAB:oak"]]}])
    cell = iter_occupied_voxel_cells(ctx)[0]
    boxes = iter_orbit_boxes_for_cell(cell, ctx.layers[0]["cells"])

    assert len(boxes) == 1
    assert boxes[0].max_corner[1] - boxes[0].min_corner[1] == 0.5


def test_stairs_emit_two_boxes():
    ctx = _ctx_from_layers([{"index": 0, "cells": [["STAIRS:oak"]]}])
    cell = iter_occupied_voxel_cells(ctx)[0]
    boxes = iter_orbit_boxes_for_cell(cell, ctx.layers[0]["cells"])

    assert len(boxes) == 3
    heights = {round(box.max_corner[1] - box.min_corner[1], 2) for box in boxes}
    assert 0.5 in heights


def test_fence_post_and_arm_boxes():
    ctx = _ctx_from_layers(
        [
            {
                "index": 0,
                "cells": [
                    ["FENCE:oak", "FENCE:oak"],
                ],
            },
        ],
    )
    cells = iter_occupied_voxel_cells(ctx)
    boxes = iter_all_orbit_boxes(cells, {0: ctx.layers[0]["cells"]})

    assert len(boxes) > 2


def test_stairs_mesh_uses_partial_geometry():
    ctx = _ctx_from_layers([{"index": 0, "cells": [["STAIRS:oak"]]}])
    partial = build_orbit_greedy_mesh_from_context(ctx)
    cell = iter_occupied_voxel_cells(ctx)[0]
    boxes = iter_orbit_boxes_for_cell(cell, ctx.layers[0]["cells"])

    assert len(boxes) == 3
    assert partial.vertex_count > 0
    assert 0.5 in partial.positions


def test_slab_mesh_half_height_bounds():
    ctx = _ctx_from_layers([{"index": 0, "cells": [["SLAB:oak"]]}])
    partial = build_orbit_greedy_mesh_from_context(ctx)

    y_values = [partial.positions[index] for index in range(1, len(partial.positions), 3)]
    assert max(y_values) == 0.5
    assert min(y_values) == 0.0


def test_slab_deck_7x7_minus_y_faces_culled():
    row = ["SLAB:oak"] * 7
    ctx = _ctx_from_layers([{"index": 5, "cells": [row] * 7}])
    cells = iter_occupied_voxel_cells(ctx)
    cache = {0: ctx.layers[0]["cells"]}
    boxes = iter_all_orbit_boxes(cells, cache)
    boxes_by_world = group_orbit_boxes_by_world(boxes)

    visible_minus_y = 0
    for index, box in enumerate(boxes):
        if not box_face_occluded(
            box,
            (0, -1, 0),
            boxes,
            skip_index=index,
            boxes_by_world=boxes_by_world,
        ):
            visible_minus_y += 1

    assert visible_minus_y == 0


def test_isolated_slab_minus_y_face_visible():
    ctx = _ctx_from_layers([{"index": 0, "cells": [["SLAB:oak"]]}])
    cells = iter_occupied_voxel_cells(ctx)
    cache = {0: ctx.layers[0]["cells"]}
    boxes = iter_all_orbit_boxes(cells, cache)
    boxes_by_world = group_orbit_boxes_by_world(boxes)

    assert not box_face_occluded(
        boxes[0],
        (0, -1, 0),
        boxes,
        skip_index=0,
        boxes_by_world=boxes_by_world,
    )


def test_adjacent_slabs_occlude_shared_vertical_face():
    ctx = _ctx_from_layers(
        [{"index": 0, "cells": [["SLAB:oak", "SLAB:oak"]]}],
    )
    cells = iter_occupied_voxel_cells(ctx)
    cache = {0: ctx.layers[0]["cells"]}
    boxes = iter_all_orbit_boxes(cells, cache)
    boxes_by_world = group_orbit_boxes_by_world(boxes)

    left_index, left_box = 0, boxes[0]
    assert box_face_occluded(
        left_box,
        (1, 0, 0),
        boxes,
        skip_index=left_index,
        boxes_by_world=boxes_by_world,
    )


def test_slab_minus_y_occluded_by_solid_below():
    ctx = _ctx_from_layers(
        [
            {"index": 0, "cells": [["minecraft:stone"]]},
            {"index": 1, "cells": [["SLAB:oak"]]},
        ],
    )
    cells = iter_occupied_voxel_cells(ctx)
    cache = {index: ctx.layers[index]["cells"] for index in range(len(ctx.layers))}
    boxes = iter_all_orbit_boxes(cells, cache)
    boxes_by_world = group_orbit_boxes_by_world(boxes)
    slab_box = next(box for box in boxes if box.cell.token == "SLAB:oak")
    slab_index = boxes.index(slab_box)

    assert box_face_occluded(
        slab_box,
        (0, -1, 0),
        boxes,
        skip_index=slab_index,
        boxes_by_world=boxes_by_world,
    )


def test_slab_deck_mesh_has_no_minus_y_normals():
    row = ["SLAB:oak"] * 7
    ctx = _ctx_from_layers([{"index": 5, "cells": [row] * 7}])
    mesh = build_orbit_greedy_mesh_from_context(ctx)

    assert _normal_counts(mesh).get((0, -1, 0), 0) == 0


def test_isolated_slab_mesh_keeps_minus_y_normals():
    ctx = _ctx_from_layers([{"index": 0, "cells": [["SLAB:oak"]]}])
    mesh = build_orbit_greedy_mesh_from_context(ctx)

    assert _normal_counts(mesh).get((0, -1, 0), 0) > 0


def test_residence_stage1_roof_slab_minus_y_faces_culled():
    from pathlib import Path

    from helpers.structure_loader import build_schematic_context, load_structure_yaml

    config = load_structure_yaml(Path("structures/residence/stage1/stage.yaml"))
    ctx = build_schematic_context(config)
    cells = iter_occupied_voxel_cells(ctx)
    cache = {index: ctx.layers[index]["cells"] for index in range(len(ctx.layers))}
    roof_slabs = [cell for cell in cells if cell.token == "SLAB:oak" and cell.world[1] == 5]
    boxes = iter_all_orbit_boxes(roof_slabs, cache)
    boxes_by_world = group_orbit_boxes_by_world(
        iter_all_orbit_boxes(cells, cache),
    )

    visible_minus_y = 0
    for index, box in enumerate(boxes):
        if not box_face_occluded(
            box,
            (0, -1, 0),
            boxes,
            skip_index=index,
            boxes_by_world=boxes_by_world,
        ):
            visible_minus_y += 1

    assert visible_minus_y == 0
    assert len(boxes) == 49


def _stair_boxes_for_token(token: str):
    ctx = _ctx_from_layers([{"index": 0, "cells": [[token]]}])
    cell = iter_occupied_voxel_cells(ctx)[0]
    return iter_orbit_boxes_for_cell(cell, ctx.layers[0]["cells"])


def _upper_stair_box(boxes):
    return next(box for box in boxes if box.role == "tread")


def _stair_tread_box(boxes):
    treads = [box for box in boxes if box.role == "tread"]
    assert len(treads) == 1
    return treads[0]


def test_stairs_straight_upper_tread_rotates_with_direction():
    south = _upper_stair_box(_stair_boxes_for_token("STAIRS:oak@south"))
    north = _upper_stair_box(_stair_boxes_for_token("STAIRS:oak@north"))
    east = _upper_stair_box(_stair_boxes_for_token("STAIRS:oak@east"))
    west = _upper_stair_box(_stair_boxes_for_token("STAIRS:oak@west"))

    # @south tread occupies +z (south) half — back covers north neighbor (matches 2D mask).
    assert south.min_corner[2] == pytest.approx(0.5)
    assert south.max_corner[2] == 1.0
    assert north.min_corner[2] == pytest.approx(0.0)
    assert north.max_corner[2] == pytest.approx(0.5)
    assert east.min_corner[0] == pytest.approx(0.5)
    assert east.max_corner[0] == 1.0
    assert west.min_corner[0] == pytest.approx(0.0)
    assert west.max_corner[0] == pytest.approx(0.5)


def test_stairs_corner_outer_left_rotates_with_direction():
    south = _upper_stair_box(_stair_boxes_for_token("STAIRS:oak@south#outer_left"))
    east = _upper_stair_box(_stair_boxes_for_token("STAIRS:oak@east#outer_left"))

    assert south.min_corner[0] == 0.5
    assert south.min_corner[2] == pytest.approx(0.5)
    assert south.max_corner[2] == 1.0
    assert east.min_corner[0] == pytest.approx(0.5)
    assert east.max_corner[2] == pytest.approx(0.5)
    assert east.min_corner[2] == pytest.approx(0.0)


def test_stairs_half_top_flips_vertical_placement():
    bottom = _stair_boxes_for_token("STAIRS:oak@south")
    top = _stair_boxes_for_token("STAIRS:oak@south;half=top")

    bottom_tread = _stair_tread_box(bottom)
    top_tread = _stair_tread_box(top)

    assert bottom_tread.min_corner[1] == 0.5
    assert top_tread.max_corner[1] == 0.5


def _is_stair_riser_box(box) -> bool:
    return box.role == "riser"


def test_straight_stair_riser_box_at_tread_edge():
    south_boxes = _stair_boxes_for_token("STAIRS:oak@south")
    assert len(south_boxes) == 3
    riser = min(south_boxes, key=lambda box: box.max_corner[2] - box.min_corner[2])
    assert riser.max_corner[2] - riser.min_corner[2] == pytest.approx(0.125)
    assert riser.min_corner[2] == pytest.approx(0.5)
    assert riser.min_corner[1] == pytest.approx(0.5)

    north_boxes = _stair_boxes_for_token("STAIRS:oak@north")
    riser_n = min(north_boxes, key=lambda box: box.max_corner[2] - box.min_corner[2])
    assert riser_n.max_corner[2] == pytest.approx(0.5)
    assert riser_n.min_corner[2] == pytest.approx(0.375)

    east_boxes = _stair_boxes_for_token("STAIRS:oak@east")
    riser_e = min(east_boxes, key=lambda box: box.max_corner[0] - box.min_corner[0])
    assert riser_e.min_corner[0] == pytest.approx(0.5)
    assert riser_e.max_corner[0] - riser_e.min_corner[0] == pytest.approx(0.125)


def test_stair_run_riser_boxes_not_cross_occluded():
    ctx = _ctx_from_layers(
        [{"index": 0, "cells": [["STAIRS:oak@south", "STAIRS:oak@south"]]}],
    )
    cells = iter_occupied_voxel_cells(ctx)
    cache = {0: ctx.layers[0]["cells"]}
    boxes = iter_all_orbit_boxes(cells, cache)
    risers = [(index, box) for index, box in enumerate(boxes) if _is_stair_riser_box(box)]
    assert len(risers) == 2
    for index, riser in risers:
        assert not box_face_occluded(riser, (0, 0, -1), boxes, skip_index=index)


def test_residence_stage1_straight_stairs_have_riser_boxes():
    from pathlib import Path

    from helpers.structure_loader import build_schematic_context, load_structure_yaml

    config = load_structure_yaml(Path("structures/residence/stage1/stage.yaml"))
    ctx = build_schematic_context(config)
    cells = iter_occupied_voxel_cells(ctx)
    cache = {index: ctx.layers[index]["cells"] for index in range(len(ctx.layers))}
    boxes = iter_all_orbit_boxes(cells, cache)
    l0_stairs = [c for c in cells if c.layer_list_index == 0 and "STAIR" in c.token]
    for stair in l0_stairs:
        cell_boxes = [box for box in boxes if box.cell.world == stair.world]
        assert len(cell_boxes) == 3
        assert sum(1 for box in cell_boxes if _is_stair_riser_box(box)) == 1


def test_stair_run_emits_outward_riser_faces():
    ctx = _ctx_from_layers(
        [{"index": 0, "cells": [["STAIRS:oak@south", "STAIRS:oak@south"]]}],
    )
    mesh = build_orbit_greedy_mesh_from_context(ctx)
    counts = _normal_counts(mesh)

    assert counts.get((0, 0, -1), 0) > 0


def test_residence_stage1_north_stair_riser_not_occluded():
    from pathlib import Path

    from helpers.structure_loader import build_schematic_context, load_structure_yaml

    config = load_structure_yaml(Path("structures/residence/stage1/stage.yaml"))
    ctx = build_schematic_context(config)
    cells = iter_occupied_voxel_cells(ctx)
    cache = {index: ctx.layers[index]["cells"] for index in range(len(ctx.layers))}
    boxes = iter_all_orbit_boxes(cells, cache)
    upper = max(
        (box for box in boxes if box.cell.world == (4, 0, 9)),
        key=lambda box: box.min_corner[1],
    )
    upper_index = boxes.index(upper)

    assert not box_face_occluded(upper, (0, 0, -1), boxes, skip_index=upper_index)


def test_stair_riser_visible_against_north_solid_neighbor():
    ctx = _ctx_from_layers(
        [
            {
                "index": 0,
                "cells": [
                    ["minecraft:mossy_cobblestone", "STAIRS:oak@north"],
                ],
            },
        ],
    )
    cells = iter_occupied_voxel_cells(ctx)
    cache = {0: ctx.layers[0]["cells"]}
    boxes = iter_all_orbit_boxes(cells, cache)
    upper = max(
        (box for box in boxes if "STAIR" in box.cell.token),
        key=lambda box: box.min_corner[1],
    )
    upper_index = boxes.index(upper)

    assert not box_face_occluded(
        upper,
        (0, 0, -1),
        boxes,
        skip_index=upper_index,
    )


def test_adjacent_stair_cells_do_not_cross_occlude():
    ctx = _ctx_from_layers(
        [{"index": 0, "cells": [["STAIRS:oak@south", "STAIRS:oak@south"]]}],
    )
    cells = iter_occupied_voxel_cells(ctx)
    cache = {0: ctx.layers[0]["cells"]}
    boxes = iter_all_orbit_boxes(cells, cache)
    upper_boxes = [(index, box) for index, box in enumerate(boxes) if box.role == "tread"]
    assert len(upper_boxes) == 2

    left_index, left_box = upper_boxes[0]
    assert not box_face_occluded(
        left_box,
        (1, 0, 0),
        boxes,
        skip_index=left_index,
    )


def test_solid_faces_partially_restored_toward_stair_neighbor_below():
    """Greedy shell skips full faces toward stairs; open-half quads are restored."""
    ctx = _ctx_from_layers(
        [
            {
                "index": 0,
                "cells": [
                    ["PLANKS:oak", "PLANKS:oak"],
                    ["STAIRS:oak@south", "STAIRS:oak@south"],
                ],
            },
        ],
    )
    mesh = build_orbit_greedy_mesh_from_context(ctx)

    south_normals = sum(
        1
        for index in range(0, len(mesh.normals), 3)
        if mesh.normals[index + 2] > 0.9 and abs(mesh.positions[index + 2] - 1.0) < 0.01
    )

    assert 0 < south_normals < 48


def test_lower_stair_slab_top_face_visible_on_open_half():
    boxes = _stair_boxes_for_token("STAIRS:oak@north")
    lower = next(box for box in boxes if box.role == "lower")
    index = boxes.index(lower)
    assert not box_face_occluded(lower, (0, 1, 0), boxes, skip_index=index)


def test_stair_riser_top_face_occluded_by_tread():
    boxes = _stair_boxes_for_token("STAIRS:oak@south")
    riser = next(box for box in boxes if _is_stair_riser_box(box))
    index = boxes.index(riser)
    assert box_face_occluded(riser, (0, 1, 0), boxes, skip_index=index)


def test_solid_emits_upper_strip_face_toward_bottom_slab():
    ctx = _ctx_from_layers([{"index": 0, "cells": [["SLAB:oak", "LOG"]]}])
    mesh = build_orbit_greedy_mesh_from_context(ctx)

    upper_west_strip = False
    for index in range(0, len(mesh.normals), 3):
        nx = mesh.normals[index]
        if nx > -0.9:
            continue

        x = mesh.positions[index]
        y = mesh.positions[index + 1]
        if abs(x - 1.0) < 0.01 and y >= 0.49:
            upper_west_strip = True

    assert upper_west_strip


def test_solid_emits_lower_strip_face_toward_top_slab():
    ctx = _ctx_from_layers([{"index": 0, "cells": [["SLAB:oak#top", "LOG"]]}])
    mesh = build_orbit_greedy_mesh_from_context(ctx)

    lower_west_strip = False
    for index in range(0, len(mesh.normals), 3):
        nx = mesh.normals[index]
        if nx > -0.9:
            continue

        x = mesh.positions[index]
        y = mesh.positions[index + 1]
        if abs(x - 1.0) < 0.01 and y <= 0.51:
            lower_west_strip = True

    assert lower_west_strip


def test_solid_emits_open_half_strip_beside_cobblestone_and_stair():
    ctx = _ctx_from_layers(
        [{"index": 0, "cells": [["minecraft:cobblestone", "STAIRS:oak@south"]]}],
    )
    mesh = build_orbit_greedy_mesh_from_context(ctx)

    east_face_vertices = 0
    for index in range(0, len(mesh.normals), 3):
        if mesh.normals[index] < 0.9:
            continue
        if abs(mesh.positions[index] - 1.0) < 0.01:
            east_face_vertices += 1

    assert east_face_vertices > 0


def test_solid_emits_restored_face_toward_partial_stair_neighbor():
    from helpers.orbit_partial_mesh import iter_solid_neighbor_face_restore_rects

    ctx = _ctx_from_layers(
        [{"index": 0, "cells": [["minecraft:cobblestone", "STAIRS:oak@south"]]}],
    )
    cells = iter_occupied_voxel_cells(ctx)
    layer_cells_cache = {0: ctx.layers[0]["cells"]}
    boxes = iter_all_orbit_boxes(cells, layer_cells_cache)
    boxes_by_world = group_orbit_boxes_by_world(boxes)
    cobble = next(cell for cell in cells if cell.token == "minecraft:cobblestone")
    stair_world = (cobble.world[0] + 1, cobble.world[1], cobble.world[2])

    rects = iter_solid_neighbor_face_restore_rects(
        cobble.world,
        (1, 0, 0),
        boxes_by_world,
        stair_world,
    )

    assert rects
    assert len(rects) < 4


def test_orbit_slab_face_textures_are_opaque():
    from pathlib import Path

    from helpers.orbit_face_textures import (
        orbit_face_kind_for_normal,
        pick_textures_for_face_kind,
        resolve_orbit_face_texture,
        side_facing_for_normal,
    )
    from helpers.structure_loader import build_schematic_context, load_structure_yaml

    config = load_structure_yaml(Path("structures/residence/stage1/stage.yaml"))
    ctx = build_schematic_context(config)
    layer_cells = ctx.layers[5]["cells"]

    for normal in ((0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
        face_kind = orbit_face_kind_for_normal(normal)
        textures = pick_textures_for_face_kind(
            face_kind,
            ctx.topdown_textures,
            ctx.sideview_textures,
        )
        assert textures is not None
        image = resolve_orbit_face_texture(
            "SLAB:oak",
            textures,
            face_kind=face_kind,
            side_facing=side_facing_for_normal(normal),
            layer_cells=layer_cells,
            cell_x=3,
            cell_z=3,
        )
        assert image is not None
        pixels = image.load()
        transparent = sum(
            1 for x in range(image.width) for y in range(image.height) if pixels[x, y][3] < 13
        )
        assert transparent == 0


def test_orbit_stair_face_textures_are_opaque():
    from pathlib import Path

    from helpers.orbit_face_textures import (
        orbit_face_kind_for_normal,
        pick_textures_for_face_kind,
        resolve_orbit_face_texture,
        side_facing_for_normal,
    )
    from helpers.structure_loader import build_schematic_context, load_structure_yaml

    config = load_structure_yaml(Path("structures/test/stage1/stage.yaml"))
    ctx = build_schematic_context(config)
    for normal in ((0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
        face_kind = orbit_face_kind_for_normal(normal)
        textures = pick_textures_for_face_kind(
            face_kind,
            ctx.topdown_textures,
            ctx.sideview_textures,
        )
        assert textures is not None
        image = resolve_orbit_face_texture(
            "STAIRS:oak@north",
            textures,
            face_kind=face_kind,
            side_facing=side_facing_for_normal(normal),
            layer_cells=ctx.layers[0]["cells"],
            cell_x=1,
            cell_z=4,
        )
        assert image is not None
        pixels = image.load()
        transparent = sum(
            1 for x in range(image.width) for y in range(image.height) if pixels[x, y][3] < 13
        )
        assert transparent == 0


def test_orbit_cobblestone_stair_face_textures_are_opaque():
    from pathlib import Path

    from helpers.orbit_face_textures import resolve_orbit_face_texture
    from helpers.structure_loader import build_schematic_context, load_structure_yaml

    config = load_structure_yaml(Path("structures/well/stage1/stage.yaml"))
    ctx = build_schematic_context(config)
    textures = ctx.topdown_textures
    assert textures is not None
    image = resolve_orbit_face_texture(
        "STAIRS:cobblestone@south",
        textures,
        face_kind="top",
        layer_cells=ctx.layers[0]["cells"],
        cell_x=1,
        cell_z=1,
    )
    assert image is not None
    pixels = image.load()
    transparent = sum(
        1 for x in range(image.width) for y in range(image.height) if pixels[x, y][3] < 13
    )
    assert transparent == 0


def test_orbit_fence_side_texture_uses_masked_bake():
    """Fence orbit side faces use masked 2D bakes; shader alpha discard shows rail gaps."""
    from pathlib import Path

    from helpers.orbit_face_textures import (
        pick_textures_for_face_kind,
        resolve_orbit_face_texture,
        side_facing_for_normal,
    )
    from helpers.structure_loader import build_schematic_context, load_structure_yaml

    config = load_structure_yaml(Path("structures/residence/stage1/stage.yaml"))
    ctx = build_schematic_context(config)
    textures = pick_textures_for_face_kind(
        "side",
        ctx.topdown_textures,
        ctx.sideview_textures,
    )
    assert textures is not None
    image = resolve_orbit_face_texture(
        "FENCE:oak",
        textures,
        face_kind="side",
        side_facing=side_facing_for_normal((0, 0, 1)),
        layer_cells=ctx.layers[0]["cells"],
        cell_x=3,
        cell_z=3,
    )
    assert image is not None
    pixels = image.load()
    transparent = sum(
        1 for x in range(image.width) for y in range(image.height) if pixels[x, y][3] < 13
    )
    assert transparent > 0


def test_orbit_wall_side_texture_uses_masked_bake():
    from pathlib import Path

    from helpers.orbit_face_textures import (
        pick_textures_for_face_kind,
        resolve_orbit_face_texture,
        side_facing_for_normal,
    )
    from helpers.structure_loader import build_schematic_context, load_structure_yaml

    config = load_structure_yaml(Path("structures/well/stage1/stage.yaml"))
    ctx = build_schematic_context(config)
    textures = pick_textures_for_face_kind(
        "side",
        ctx.topdown_textures,
        ctx.sideview_textures,
    )
    assert textures is not None
    image = resolve_orbit_face_texture(
        "WALL:cobblestone",
        textures,
        face_kind="side",
        side_facing=side_facing_for_normal((0, 0, 1)),
        layer_cells=ctx.layers[0]["cells"],
        cell_x=1,
        cell_z=1,
    )
    assert image is not None
    pixels = image.load()
    transparent = sum(
        1 for x in range(image.width) for y in range(image.height) if pixels[x, y][3] < 13
    )
    assert transparent > 0
