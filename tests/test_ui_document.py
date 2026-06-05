from pathlib import Path

import pytest
import yaml

from helpers.layer_management import remove_layer_from_document
from ui.document import (
    StructureDocument,
    load_structure_document,
    save_layer,
    save_structure_metadata,
    validate_structure_document,
)


def test_open_residence_stage1_structure():
    path = Path("structures/residence/stage1/structure.yaml")
    document = load_structure_document(path)

    validate_structure_document(document)
    assert document.metadata["structure"] == "residence"
    assert document.metadata["stage"] == 1
    assert len(document.layers) == 7
    assert document.layers[0]["cells"]
    assert document.layer_files == [
        "layers/layer_06.yaml",
        "layers/layer_00.yaml",
        "layers/layer_01.yaml",
        "layers/layer_02.yaml",
        "layers/layer_03.yaml",
        "layers/layer_04.yaml",
        "layers/layer_05.yaml",
    ]


def test_remove_layer_and_save_structure_metadata_updates_layer_files(tmp_path: Path):
    structure_path = tmp_path / "structure.yaml"
    layers_dir = tmp_path / "layers"
    layers_dir.mkdir()
    (layers_dir / "layer_00.yaml").write_text(
        "index: 0\ngroup: Floor\ncells:\n- - .\n",
        encoding="utf-8",
    )
    (layers_dir / "layer_01.yaml").write_text(
        "index: 1\ngroup: Roof\ncells:\n- - .\n",
        encoding="utf-8",
    )
    structure_path.write_text(
        "structure: test\nstage: 1\nname: Test\noutput_folder: test_out\n"
        "grid:\n  site_width: 10\n  site_depth: 10\n  offset_x: 0\n  offset_z: 0\n"
        "  site_structure_layers:\n  - 0\n"
        "layer_files:\n- layers/layer_00.yaml\n- layers/layer_01.yaml\n",
        encoding="utf-8",
    )

    document = StructureDocument(
        structure_path=structure_path,
        metadata=yaml.safe_load(structure_path.read_text(encoding="utf-8")),
        layer_files=["layers/layer_00.yaml", "layers/layer_01.yaml"],
        layer_paths=[layers_dir / "layer_00.yaml", layers_dir / "layer_01.yaml"],
        layers=[
            {"index": 0, "group": "Floor", "cells": [["."]]},
            {"index": 1, "group": "Roof", "cells": [["."]]},
        ],
        site_ground=[["."] * 10 for _ in range(10)],
    )

    removed_path = remove_layer_from_document(document, 1)
    assert removed_path == layers_dir / "layer_01.yaml"
    removed_path.unlink()

    save_structure_metadata(
        structure_path,
        document.metadata,
        layer_files=document.layer_files,
        site_ground=document.site_ground,
        document=document,
    )

    saved = yaml.safe_load(structure_path.read_text(encoding="utf-8"))
    assert saved["layer_files"] == ["layers/layer_00.yaml"]
    reloaded = load_structure_document(structure_path)
    assert len(reloaded.layers) == 1


def test_save_structure_metadata_preserves_layer_files(tmp_path: Path):
    structure_path = tmp_path / "structure.yaml"
    layers_dir = tmp_path / "layers"
    layers_dir.mkdir()
    (layers_dir / "layer_00.yaml").write_text(
        "index: 0\ngroup: Floor\ncells:\n- - .\n",
        encoding="utf-8",
    )
    structure_path.write_text(
        "structure: test\nstage: 1\nname: Test\noutput_folder: test_out\n"
        "grid:\n  site_width: 10\n  site_depth: 10\n  offset_x: 0\n  offset_z: 0\n"
        "  site_structure_layers:\n  - 0\n"
        "layer_files:\n- layers/layer_00.yaml\n",
        encoding="utf-8",
    )

    document = load_structure_document(structure_path)
    document.metadata["grid"]["offset_x"] = 3
    save_structure_metadata(
        structure_path,
        document.metadata,
        layer_files=document.layer_files,
        site_ground=document.site_ground,
        document=document,
    )

    saved = yaml.safe_load(structure_path.read_text(encoding="utf-8"))
    assert saved["layer_files"] == ["layers/layer_00.yaml"]
    assert saved["grid"]["offset_x"] == 3


def test_save_layer_roundtrip(tmp_path: Path):
    layer = {
        "index": 0,
        "group": "Test",
        "cells": [[".", "GRASS"], [".", "."]],
    }
    path = tmp_path / "layer_test.yaml"

    save_layer(path, layer)
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert loaded == layer


def test_save_layer_rejects_invalid_document(tmp_path: Path):
    structure_path = tmp_path / "structure.yaml"
    layers_dir = tmp_path / "layers"
    layers_dir.mkdir()
    layer_path = layers_dir / "layer_00.yaml"
    layer_path.write_text("index: 0\ncells:\n- - .\n", encoding="utf-8")
    (layers_dir / "layer_01.yaml").write_text("index: 0\ncells:\n- - .\n", encoding="utf-8")
    structure_path.write_text(
        "structure: test\nstage: 1\nname: Test\noutput_folder: test_out\n"
        "grid:\n  site_width: 10\n  site_depth: 10\n  offset_x: 0\n  offset_z: 0\n"
        "layer_files:\n- layers/layer_00.yaml\n- layers/layer_01.yaml\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate layer index"):
        load_structure_document(structure_path)


def test_editor_save_layer_roundtrip_passes_validation(tmp_path: Path):
    structure_path = tmp_path / "structure.yaml"
    layers_dir = tmp_path / "layers"
    layers_dir.mkdir()
    (layers_dir / "layer_00.yaml").write_text(
        "index: 0\ngroup: Floor\ncells:\n- - COBBLESTONE\n",
        encoding="utf-8",
    )
    structure_path.write_text(
        "structure: test\nstage: 1\nname: Test\noutput_folder: test_out\n"
        "grid:\n  site_width: 10\n  site_depth: 10\n  offset_x: 0\n  offset_z: 0\n"
        "  site_structure_layers:\n  - 0\n"
        "layer_files:\n- layers/layer_00.yaml\n",
        encoding="utf-8",
    )

    document = load_structure_document(structure_path)
    document.layers[0]["cells"][0][0] = "GRASS"
    save_layer(
        document.layer_paths[0],
        document.layers[0],
        document=document,
    )

    reloaded = load_structure_document(structure_path)
    assert reloaded.layers[0]["cells"][0][0] == "GRASS"


def test_open_residence_stage2_structure():
    path = Path("structures/residence/stage2/structure.yaml")
    document = load_structure_document(path)

    assert document.metadata["stage"] == 2
    assert len(document.layers) == 6
