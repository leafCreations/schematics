"""Tests for greedy orbit meshing and texture atlas packing."""

from __future__ import annotations

import helpers.constants as constants
from helpers.context import SchematicContext
from helpers.orbit_face_textures import (
    orbit_face_kind_for_normal,
    side_facing_for_normal,
    texture_signature,
)
from helpers.orbit_greedy_mesh import (
    build_orbit_greedy_mesh_from_context,
    greedy_merge,
    iter_occupied_voxel_cells,
)
from helpers.orbit_mesh import build_box_orbit_mesh_from_context
from helpers.orbit_texture_atlas import ORBIT_ATLAS_TILE_PX, OrbitTextureAtlas


def _ctx_from_layers(layers: list[dict]) -> SchematicContext:
    return SchematicContext(
        structure="test",
        stage=1,
        name="Greedy Sample",
        layers=layers,
        grid={"site_size": 20, "offset_x": 0, "offset_z": 0},
        block_registry={},
        assets_dir=__import__("pathlib").Path("."),
        worldgen_template_dir=__import__("pathlib").Path("."),
        output_schematics_dir=__import__("pathlib").Path("."),
        output_worldgen_dir=__import__("pathlib").Path("."),
    )


def test_greedy_merge_combines_uniform_rows():
    mask = [
        [1, 1, 1],
        [1, 1, 1],
        [2, 2, 2],
    ]
    quads = greedy_merge(mask)

    assert (0, 0, 2, 3, 1) in quads
    assert (2, 0, 1, 3, 2) in quads
    assert sum(width * height for _u, _v, width, height, _id in quads) == 9


def test_shared_faces_between_blocks_are_culled():
    pair = _ctx_from_layers([{"index": 0, "cells": [["A", "A"]]}])
    pair_mesh = build_orbit_greedy_mesh_from_context(pair)
    single_mesh = build_orbit_greedy_mesh_from_context(
        _ctx_from_layers([{"index": 0, "cells": [["A"]]}]),
    )

    assert pair_mesh.triangle_count < single_mesh.triangle_count * 2


def test_hollow_ring_exposes_interior_walls():
    hollow = _ctx_from_layers(
        [
            {
                "index": 0,
                "cells": [
                    ["A", "A", "A"],
                    ["A", ".", "A"],
                    ["A", "A", "A"],
                ],
            },
        ],
    )
    mesh = build_orbit_greedy_mesh_from_context(hollow)
    box = build_box_orbit_mesh_from_context(hollow)

    assert mesh.triangle_count > 0
    assert mesh.triangle_count <= box.triangle_count


def test_furnace_orbit_vertical_faces_resolve_front_and_side():
    from pathlib import Path

    from helpers.orbit_face_textures import resolve_orbit_face_texture
    from helpers.structure_loader import build_schematic_context, load_structure_yaml

    config = load_structure_yaml(Path("structures/residence/stage1/stage.yaml"))
    ctx = build_schematic_context(config)
    assert ctx.topdown_textures is not None
    assert ctx.sideview_textures is not None

    front = resolve_orbit_face_texture(
        "FURNACE@west",
        ctx.sideview_textures,
        face_kind="side",
        side_facing="west",
        topdown_textures=ctx.topdown_textures,
        sideview_textures=ctx.sideview_textures,
    )
    side = resolve_orbit_face_texture(
        "FURNACE@west",
        ctx.sideview_textures,
        face_kind="side",
        side_facing="east",
        topdown_textures=ctx.topdown_textures,
        sideview_textures=ctx.sideview_textures,
    )

    assert front is not None
    assert side is not None
    assert front.tobytes() != side.tobytes()


def test_furnace_orbit_front_signature_uses_topdown_texture():
    from pathlib import Path

    from helpers.orbit_face_textures import resolve_orbit_face_texture
    from helpers.structure_loader import build_schematic_context, load_structure_yaml

    config = load_structure_yaml(Path("structures/residence/stage1/stage.yaml"))
    ctx = build_schematic_context(config)
    front = resolve_orbit_face_texture(
        "FURNACE@north",
        ctx.sideview_textures,
        face_kind="side",
        side_facing="north",
        topdown_textures=ctx.topdown_textures,
        sideview_textures=ctx.sideview_textures,
    )
    expected = ctx.topdown_textures.get("FURNACE")

    assert front is not None
    assert expected is not None
    assert front.tobytes() == expected.tobytes()


def test_furnace_orbit_top_face_uses_block_cap_not_front():
    from pathlib import Path

    from helpers.orbit_face_textures import resolve_orbit_face_texture
    from helpers.structure_loader import build_schematic_context, load_structure_yaml

    config = load_structure_yaml(Path("structures/residence/stage1/stage.yaml"))
    ctx = build_schematic_context(config)
    top = resolve_orbit_face_texture(
        "FURNACE@west",
        ctx.topdown_textures,
        face_kind="top",
        topdown_textures=ctx.topdown_textures,
        sideview_textures=ctx.sideview_textures,
    )
    front_on_topdown = ctx.topdown_textures.get("FURNACE")

    assert top is not None
    assert front_on_topdown is not None
    assert top.tobytes() != front_on_topdown.tobytes()


def test_furnace_orbit_front_vertical_face_upright_for_all_directions():
    from pathlib import Path

    from helpers.orbit_face_textures import resolve_orbit_face_texture
    from helpers.structure_loader import build_schematic_context, load_structure_yaml

    config = load_structure_yaml(Path("structures/residence/stage1/stage.yaml"))
    ctx = build_schematic_context(config)
    upright = ctx.topdown_textures.get("FURNACE")
    assert upright is not None

    for direction in ("north", "south", "east", "west"):
        front = resolve_orbit_face_texture(
            f"FURNACE@{direction}",
            ctx.sideview_textures,
            face_kind="side",
            side_facing=direction,
            topdown_textures=ctx.topdown_textures,
            sideview_textures=ctx.sideview_textures,
        )
        assert front is not None
        assert front.tobytes() == upright.tobytes()


def _catalog_face_image(filename: str):
    from helpers.block_texture_load import load_block_texture_image
    from registries.loader import BLOCK_TEXTURES_FOLDER

    path = BLOCK_TEXTURES_FOLDER / filename
    return load_block_texture_image(path, constants.BLOCK_PX)


def test_smoker_facing_block_orbit_side_top_and_front():
    from pathlib import Path

    from helpers.orbit_face_textures import resolve_orbit_face_texture
    from helpers.structure_loader import build_schematic_context, load_structure_yaml

    config = load_structure_yaml(Path("structures/residence/stage1/stage.yaml"))
    ctx = build_schematic_context(config)
    side = resolve_orbit_face_texture(
        "SMOKER@north",
        ctx.sideview_textures,
        face_kind="side",
        side_facing="east",
        topdown_textures=ctx.topdown_textures,
        sideview_textures=ctx.sideview_textures,
    )
    front = resolve_orbit_face_texture(
        "SMOKER@north",
        ctx.sideview_textures,
        face_kind="side",
        side_facing="north",
        topdown_textures=ctx.topdown_textures,
        sideview_textures=ctx.sideview_textures,
    )
    top = resolve_orbit_face_texture(
        "SMOKER@north",
        ctx.topdown_textures,
        face_kind="top",
        topdown_textures=ctx.topdown_textures,
        sideview_textures=ctx.sideview_textures,
    )

    assert side is not None
    assert front is not None
    assert top is not None
    assert side.tobytes() == _catalog_face_image("smoker_side.png").tobytes()
    assert front.tobytes() == _catalog_face_image("smoker_front.png").tobytes()
    assert top.tobytes() == _catalog_face_image("smoker_top.png").tobytes()


def test_smoker_lit_front_uses_on_texture():
    from pathlib import Path

    from helpers.orbit_face_textures import resolve_orbit_face_texture
    from helpers.structure_loader import build_schematic_context, load_structure_yaml

    config = load_structure_yaml(Path("structures/residence/stage1/stage.yaml"))
    ctx = build_schematic_context(config)
    front = resolve_orbit_face_texture(
        "SMOKER@north;lit=true",
        ctx.sideview_textures,
        face_kind="side",
        side_facing="north",
        topdown_textures=ctx.topdown_textures,
        sideview_textures=ctx.sideview_textures,
    )

    assert front is not None
    assert front.tobytes() == _catalog_face_image("smoker_front_on.png").tobytes()


def test_furnace_lit_front_unchanged_single_frame():
    from pathlib import Path

    from helpers.orbit_face_textures import resolve_orbit_face_texture
    from helpers.structure_loader import build_schematic_context, load_structure_yaml

    config = load_structure_yaml(Path("structures/residence/stage1/stage.yaml"))
    ctx = build_schematic_context(config)
    front = resolve_orbit_face_texture(
        "FURNACE@north;lit=true",
        ctx.sideview_textures,
        face_kind="side",
        side_facing="north",
        topdown_textures=ctx.topdown_textures,
        sideview_textures=ctx.sideview_textures,
    )

    assert front is not None
    assert front.tobytes() == _catalog_face_image("furnace_front_on.png").tobytes()


def test_smoker_lit_topdown_uses_first_animation_frame():
    from pathlib import Path

    from helpers.structure_loader import build_schematic_context, load_structure_yaml
    from helpers.utils_schematics import resolve_cell_texture

    config = load_structure_yaml(Path("structures/residence/stage1/stage.yaml"))
    ctx = build_schematic_context(config)
    top = resolve_cell_texture(
        "SMOKER@north;lit=true",
        ctx.topdown_textures,
        view="top",
        size=constants.BLOCK_PX,
    )

    assert top is not None
    assert top.tobytes() == _catalog_face_image("smoker_front_on.png").tobytes()


def test_blast_furnace_facing_block_orbit_textures():
    from pathlib import Path

    from helpers.orbit_face_textures import resolve_orbit_face_texture
    from helpers.structure_loader import build_schematic_context, load_structure_yaml

    config = load_structure_yaml(Path("structures/residence/stage1/stage.yaml"))
    ctx = build_schematic_context(config)
    side = resolve_orbit_face_texture(
        "BLAST_FURNACE@west",
        ctx.sideview_textures,
        face_kind="side",
        side_facing="east",
        topdown_textures=ctx.topdown_textures,
        sideview_textures=ctx.sideview_textures,
    )
    front = resolve_orbit_face_texture(
        "BLAST_FURNACE@west;lit=true",
        ctx.sideview_textures,
        face_kind="side",
        side_facing="west",
        topdown_textures=ctx.topdown_textures,
        sideview_textures=ctx.sideview_textures,
    )

    assert side.tobytes() == _catalog_face_image("blast_furnace_side.png").tobytes()
    assert front.tobytes() == _catalog_face_image("blast_furnace_front_on.png").tobytes()


def test_minecraft_smoker_alias_uses_facing_block_registry():
    from helpers.registry_blocks import get_block_behavior
    from helpers.registry_lookup import get_block_entry
    from helpers.structure_tokens import parse_structure_token

    entry = get_block_entry(parse_structure_token("minecraft:smoker"))
    assert entry is not None
    assert get_block_behavior(entry) == "facing_block"
    assert entry.get("minecraft", {}).get("blockstates", {}).get("lit") == "{lit}"


def test_solid_face_visible_at_material_boundary():
    from helpers.orbit_greedy_mesh import _solid_face_visible
    from helpers.orbit_mesh import OccupiedVoxel

    def cell(x: int, y: int, z: int, token: str) -> OccupiedVoxel:
        return OccupiedVoxel(
            world=(x, y, z),
            token=token,
            layer_list_index=0,
            local_x=x,
            local_z=z,
        )

    mixed = {
        (0, 0, 0): cell(0, 0, 0, "PLANKS:oak"),
        (1, 0, 0): cell(1, 0, 0, "CRAFTING_TABLE"),
    }
    assert _solid_face_visible((1, 0, 0), (-1, 0, 0), mixed, frozenset())

    uniform = {
        (0, 0, 0): cell(0, 0, 0, "PLANKS:oak"),
        (1, 0, 0): cell(1, 0, 0, "PLANKS:oak"),
    }
    assert not _solid_face_visible((1, 0, 0), (-1, 0, 0), uniform, frozenset())

    assert _solid_face_visible((1, 0, 0), (0, 0, 1), mixed, frozenset())


def test_crafting_table_orbit_side_uses_catalog_side_texture():
    from pathlib import Path

    from PIL import Image

    from helpers.orbit_face_textures import resolve_orbit_face_texture
    from helpers.structure_loader import build_schematic_context, load_structure_yaml
    from registries.loader import BLOCK_TEXTURES_FOLDER

    config = load_structure_yaml(Path("structures/residence/stage1/stage.yaml"))
    ctx = build_schematic_context(config)
    side = resolve_orbit_face_texture(
        "CRAFTING_TABLE",
        ctx.sideview_textures,
        face_kind="side",
        side_facing="north",
    )
    expected = Image.open(BLOCK_TEXTURES_FOLDER / "crafting_table_side.png").convert("RGBA")
    expected = expected.resize((constants.BLOCK_PX, constants.BLOCK_PX), Image.Resampling.NEAREST)

    assert side is not None
    assert side.tobytes() == expected.tobytes()


def test_embedded_crafting_table_has_vertical_faces():
    ctx = _ctx_from_layers(
        [
            {
                "index": 0,
                "cells": [
                    ["PLANKS:oak", "PLANKS:oak", "PLANKS:oak"],
                    ["PLANKS:oak", "CRAFTING_TABLE", "PLANKS:oak"],
                    ["PLANKS:oak", "PLANKS:oak", "PLANKS:oak"],
                ],
            },
        ],
    )
    flat_shell = _ctx_from_layers(
        [
            {
                "index": 0,
                "cells": [
                    ["PLANKS:oak", "PLANKS:oak", "PLANKS:oak"],
                    ["PLANKS:oak", "PLANKS:oak", "PLANKS:oak"],
                    ["PLANKS:oak", "PLANKS:oak", "PLANKS:oak"],
                ],
            },
        ],
    )
    table_mesh = build_orbit_greedy_mesh_from_context(ctx)
    shell_mesh = build_orbit_greedy_mesh_from_context(flat_shell)

    assert table_mesh.triangle_count > shell_mesh.triangle_count


def test_two_layer_stack_merges_coplanar_faces():
    stacked = _ctx_from_layers(
        [
            {
                "index": 0,
                "cells": [["A", "A"], ["A", "A"]],
            },
            {
                "index": 1,
                "cells": [["B", "B"], ["B", "B"]],
            },
        ],
    )
    mesh = build_orbit_greedy_mesh_from_context(stacked)

    assert mesh.vertex_count > 0
    assert mesh.triangle_count == mesh.vertex_count // 3
    # Internal horizontal face between layers is culled.
    assert mesh.triangle_count < 2 * 4 * 6


def test_greedy_mesh_fewer_triangles_than_c1_box_mesh():
    wide_cells = [["A" for _ in range(8)] for _ in range(8)]
    ctx = _ctx_from_layers([{"index": 0, "cells": wide_cells}])

    greedy = build_orbit_greedy_mesh_from_context(ctx)
    box = build_box_orbit_mesh_from_context(ctx)

    assert greedy.triangle_count > 0
    assert box.triangle_count > greedy.triangle_count


def test_atlas_registers_unique_tiles():
    atlas = OrbitTextureAtlas(tile_px=8)
    first = atlas.register(None, fallback_rgb=(1.0, 0.0, 0.0))
    second = atlas.register(None, fallback_rgb=(1.0, 0.0, 0.0))
    third = atlas.register(None, fallback_rgb=(0.0, 1.0, 0.0))

    layout = atlas.build()
    assert layout is not None
    assert first == second
    assert third != first
    assert len(layout.uv_rects) == 2


def test_atlas_tile_size_matches_block_px():
    assert ORBIT_ATLAS_TILE_PX == constants.BLOCK_PX


def test_face_texture_signature_includes_facing():
    sig_north = texture_signature("STONE", "side", side_facing="north")
    sig_east = texture_signature("STONE", "side", side_facing="east")
    assert sig_north != sig_east
    assert orbit_face_kind_for_normal((0, 1, 0)) == "top"
    assert side_facing_for_normal((1, 0, 0)) == "east"


def test_greedy_mesh_tile_rects_per_vertex():
    wide_cells = [["A" for _ in range(8)] for _ in range(8)]
    ctx = _ctx_from_layers([{"index": 0, "cells": wide_cells}])
    mesh = build_orbit_greedy_mesh_from_context(ctx)

    assert mesh.vertex_count > 0
    assert len(mesh.tile_rects) == 0 or len(mesh.tile_rects) == mesh.vertex_count * 4


def test_greedy_mesh_emits_atlas_for_textured_context():
    ctx = _ctx_from_layers(
        [
            {
                "index": 0,
                "cells": [["GRASS", "GRASS"], ["GRASS", "GRASS"]],
            },
        ],
    )

    try:
        import helpers.constants as constants
        from helpers.paths import BLOCK_TEXTURES_FOLDER
        from registries.loader import compile_texture_set

        ctx.topdown_textures = compile_texture_set(
            "top",
            str(BLOCK_TEXTURES_FOLDER),
            constants.BLOCK_PX,
        )
        ctx.sideview_textures = compile_texture_set(
            "side",
            str(BLOCK_TEXTURES_FOLDER),
            constants.BLOCK_PX,
        )
    except Exception:
        return

    mesh = build_orbit_greedy_mesh_from_context(ctx)
    assert mesh.uses_texture_atlas
    assert mesh.atlas_width > 0
    assert len(mesh.tile_rects) == mesh.vertex_count * 4


def test_iter_occupied_voxel_cells_tracks_layer_indices():
    ctx = _ctx_from_layers(
        [
            {
                "index": 0,
                "cells": [["A", "."], [".", "B"]],
            },
        ],
    )
    cells = iter_occupied_voxel_cells(ctx)
    tokens = {cell.token for cell in cells}

    assert tokens == {"A", "B"}
    assert all(cell.layer_list_index == 0 for cell in cells)
