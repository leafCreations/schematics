"""Tests for 3D orbit preview mesh building."""

from __future__ import annotations

from helpers.context import SchematicContext
from helpers.orbit_mesh import (
    OrbitMeshData,
    build_box_orbit_mesh_from_context,
    build_orbit_mesh_from_context,
    iter_occupied_voxels,
)
from ui.mesh_build_worker import MeshBuildWorker


def _sample_ctx() -> SchematicContext:
    return SchematicContext(
        structure="test",
        stage=1,
        name="Orbit Sample",
        layers=[
            {
                "index": 0,
                "cells": [
                    ["A", "B"],
                    [".", "C"],
                ],
            },
            {
                "index": 1,
                "cells": [
                    ["D"],
                ],
            },
        ],
        grid={"site_size": 20, "offset_x": 2, "offset_z": 3},
        block_registry={},
        assets_dir=__import__("pathlib").Path("."),
        worldgen_template_dir=__import__("pathlib").Path("."),
        output_schematics_dir=__import__("pathlib").Path("."),
        output_worldgen_dir=__import__("pathlib").Path("."),
    )


def test_iter_occupied_voxels_applies_offsets_and_skips_empty():
    occupied = iter_occupied_voxels(_sample_ctx())
    positions = {position for position, _token in occupied}

    assert (2, 0, 3) in positions
    assert (3, 0, 3) in positions
    assert (3, 0, 4) in positions
    assert (2, 1, 3) in positions
    assert (2, 0, 4) not in positions


def test_build_orbit_mesh_combines_exterior_faces():
    mesh = build_orbit_mesh_from_context(_sample_ctx())

    assert isinstance(mesh, OrbitMeshData)
    assert mesh.vertex_count > 0
    assert len(mesh.positions) == mesh.vertex_count * 3
    assert len(mesh.colors) == mesh.vertex_count * 3
    assert mesh.bounds_radius >= 1.0


def test_build_orbit_mesh_empty_structure():
    ctx = _sample_ctx()
    ctx.layers = [{"index": 0, "cells": [[".", "."], [".", "."]]}]
    mesh = build_orbit_mesh_from_context(ctx)

    assert mesh.vertex_count == 0
    assert mesh.positions == ()


def test_mesh_build_worker_emits_finished():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")

    ctx = _sample_ctx()
    worker = MeshBuildWorker(ctx)
    results: list[OrbitMeshData] = []
    worker.finished.connect(results.append)

    worker.run()

    assert len(results) == 1
    assert results[0].vertex_count > 0


def test_orbit_preview_view_matrix_uses_qvector3d_lookat():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    widget._bounds_center = (1.0, 2.0, 3.0)
    widget._bounds_radius = 4.0
    widget._distance = 12.0

    matrix = widget._view_matrix()

    assert matrix.isIdentity() is False


def test_face_count_scales_with_surface_not_volume():
    wide_cells = [["A" for _ in range(8)] for _ in range(8)]

    wide_ctx = _sample_ctx()
    wide_ctx.layers = [{"index": 0, "cells": wide_cells}]
    wide_ctx.grid = {"site_size": 20, "offset_x": 0, "offset_z": 0}
    wide = build_orbit_mesh_from_context(wide_ctx)
    box = build_box_orbit_mesh_from_context(wide_ctx)

    assert wide.triangle_count == 12
    assert box.triangle_count > wide.triangle_count
    assert box.triangle_count < 8 * 8 * 6 * 2


def test_greedy_default_builder_uses_fewer_triangles_than_box_baseline():
    wide_cells = [["A" for _ in range(6)] for _ in range(6)]
    ctx = _sample_ctx()
    ctx.layers = [{"index": 0, "cells": wide_cells}]
    ctx.grid = {"site_size": 20, "offset_x": 0, "offset_z": 0}

    greedy = build_orbit_mesh_from_context(ctx)
    box = build_box_orbit_mesh_from_context(ctx)

    assert greedy.triangle_count < box.triangle_count
