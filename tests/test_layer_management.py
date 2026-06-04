from pathlib import Path

from helpers.layer_management import (
    adjust_site_structure_layers_after_remove,
    append_layer_to_document,
    create_layer,
    move_layer_in_document,
    next_layer_relative_path,
    next_worldgen_index,
    remap_indices_after_swap,
    remap_site_structure_layers_after_swap,
    remove_layer_from_document,
)
from ui.document import StructureDocument


def test_next_worldgen_index_avoids_duplicates():
    layers = [{"index": 0}, {"index": 2}]
    assert next_worldgen_index(layers) == 3


def test_remap_site_structure_layers_after_swap():
    grid = {"site_structure_layers": [0, 2, 3]}
    remap_site_structure_layers_after_swap(grid, 1, 3)
    assert grid["site_structure_layers"] == [0, 2, 1]


def test_move_layer_and_remap_dirty_indices():
    from types import SimpleNamespace

    doc = SimpleNamespace(
        layers=[{"index": 0}, {"index": 1}, {"index": 2}],
        layer_files=["a.yaml", "b.yaml", "c.yaml"],
        layer_paths=[Path("a.yaml"), Path("b.yaml"), Path("c.yaml")],
        metadata={"grid": {"site_structure_layers": [0, 2]}},
    )
    assert move_layer_in_document(doc, 2, -1) == 1
    assert [layer["index"] for layer in doc.layers] == [0, 2, 1]
    assert doc.layer_files == ["a.yaml", "c.yaml", "b.yaml"]
    assert doc.metadata["grid"]["site_structure_layers"] == [0, 1]
    assert remap_indices_after_swap({0, 2}, 2, 1) == {0, 1}


def test_adjust_site_structure_layers_after_remove():
    grid = {"site_structure_layers": [0, 2, 3]}
    adjust_site_structure_layers_after_remove(grid, 1)
    assert grid["site_structure_layers"] == [0, 1, 2]


def test_append_and_remove_layer_on_document(tmp_path: Path):
    base = tmp_path / "structures" / "test" / "stage1"
    layers_dir = base / "layers"
    layers_dir.mkdir(parents=True)
    (layers_dir / "layer_00.yaml").write_text(
        "index: 0\ngroup: A\ncells:\n- - .\n",
        encoding="utf-8",
    )
    structure_path = base / "structure.yaml"
    structure_path.write_text(
        "structure: test\nstage: 1\nname: Test\noutput_folder: stage1_test\n"
        "grid:\n  site_width: 2\n  site_depth: 2\n  offset_x: 0\n  offset_z: 0\n"
        "  site_structure_layers:\n  - 0\n"
        "layer_files:\n- layers/layer_00.yaml\n",
        encoding="utf-8",
    )

    document = StructureDocument(
        structure_path=structure_path,
        metadata={
            "structure": "test",
            "stage": 1,
            "name": "Test",
            "output_folder": "stage1_test",
            "grid": {
                "site_width": 2,
                "site_depth": 2,
                "offset_x": 0,
                "offset_z": 0,
                "site_structure_layers": [0],
            },
        },
        layer_files=["layers/layer_00.yaml"],
        layer_paths=[layers_dir / "layer_00.yaml"],
        layers=[{"index": 0, "group": "A", "cells": [[".", "."], [".", "."]]}],
        site_ground=[[".", "."], [".", "."]],
    )

    new_layer = create_layer(width=2, depth=2, worldgen_index=1, group="B")
    rel = next_layer_relative_path(document.layer_paths)
    index = append_layer_to_document(document, new_layer, relative_path=rel)

    assert index == 1
    assert len(document.layers) == 2
    assert document.layer_files[-1] == rel

    removed = remove_layer_from_document(document, 1)
    assert removed is None
    assert len(document.layers) == 1
