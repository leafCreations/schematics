from pathlib import Path

import pytest
import yaml

from helpers.layer_management import remove_layer_from_document
from ui.document import (
    StructureDocument,
    create_structure_stage_document,
    delete_structure_stage_document,
    load_structure_document,
    save_layer,
    save_structure_metadata,
    validate_structure_document,
)


def test_open_residence_stage1_structure():
    path = Path("structures/residence/stage1/stage.yaml")
    document = load_structure_document(path)

    validate_structure_document(document)
    assert document.metadata["structure"] == "residence"
    assert document.metadata["stage"] == 1
    assert document.metadata["output_folder"] == "stage1_residence"
    assert len(document.layers) == 6
    assert document.site_ground
    assert document.layers[0]["cells"]
    assert document.layer_files == [
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
    path = Path("structures/residence/stage2/stage.yaml")
    document = load_structure_document(path)

    assert document.metadata["stage"] == 2
    assert document.metadata["output_folder"] == "stage2_residence"
    assert len(document.layers) == 6
    assert document.site_ground


def test_create_structure_stage_document_writes_yaml_and_layer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr("ui.document.STRUCTURES_FOLDER", tmp_path / "structures")

    structure_path = create_structure_stage_document(
        structure="tower",
        stage=3,
        site_width=40,
        site_depth=32,
        structure_width=12,
        structure_depth=10,
    )

    assert structure_path == tmp_path / "structures" / "tower" / "stage3" / "stage.yaml"
    assert structure_path.is_file()
    assert (structure_path.parent / "layers" / "layer_00.yaml").is_file()

    document = load_structure_document(structure_path)
    assert document.metadata["structure"] == "tower"
    assert document.metadata["stage"] == 3
    assert document.metadata["dimension"] == "overworld"
    assert document.metadata["output_folder"] == "stage3_tower"
    assert document.metadata["grid"]["site_width"] == 40
    assert document.metadata["grid"]["site_depth"] == 32
    assert len(document.layers) == 1
    assert len(document.layers[0]["cells"]) == 10
    assert len(document.layers[0]["cells"][0]) == 12
    assert all(cell == "GRASS" for row in document.site_ground for cell in row)

    saved = yaml.safe_load(structure_path.read_text(encoding="utf-8"))
    assert "dimension" not in saved
    assert "grid" not in saved
    assert "output_folder" not in saved
    assert "site_ground" not in saved

    manifest_path = tmp_path / "structures" / "tower" / "structure.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert manifest["structure"] == "tower"
    assert manifest["stages"][0]["stage"] == 3
    assert manifest["stages"][0]["path"] == "stage3/stage.yaml"
    assert manifest["stages"][0]["dimension"] == "overworld"
    assert manifest["stages"][0]["output_folder"] == "stage3_tower"
    assert manifest["stages"][0]["grid"]["site_width"] == 40
    assert manifest["stages"][0]["grid"]["site_depth"] == 32
    assert all(cell == "GRASS" for row in manifest["site_ground"] for cell in row)


def test_create_structure_stage_document_rejects_taken_stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr("ui.document.STRUCTURES_FOLDER", tmp_path / "structures")

    create_structure_stage_document(
        structure="villa",
        stage=1,
        site_width=20,
        site_depth=20,
        structure_width=8,
        structure_depth=8,
    )

    with pytest.raises(FileExistsError, match="already exists"):
        create_structure_stage_document(
            structure="villa",
            stage=1,
            site_width=20,
            site_depth=20,
            structure_width=8,
            structure_depth=8,
        )


def test_create_structure_stage_document_allows_new_stage_for_existing_structure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr("ui.document.STRUCTURES_FOLDER", tmp_path / "structures")

    stage1 = create_structure_stage_document(
        structure="villa",
        stage=1,
        site_width=20,
        site_depth=20,
        structure_width=8,
        structure_depth=8,
    )
    stage2 = create_structure_stage_document(
        structure="villa",
        stage=2,
        site_width=20,
        site_depth=20,
        structure_width=10,
        structure_depth=10,
        dimension="nether",
    )

    assert stage1.is_file()
    assert stage2.is_file()

    stage2_document = load_structure_document(stage2)
    assert stage2_document.metadata["stage"] == 2
    assert stage2_document.metadata["dimension"] == "nether"

    manifest = yaml.safe_load((tmp_path / "structures" / "villa" / "structure.yaml").read_text())
    assert manifest["structure"] == "villa"
    assert [entry["stage"] for entry in manifest["stages"]] == [1, 2]
    assert manifest["stages"][0]["path"] == "stage1/stage.yaml"
    assert manifest["stages"][1]["path"] == "stage2/stage.yaml"
    assert manifest["stages"][0]["output_folder"] == "stage1_villa"
    assert manifest["stages"][1]["output_folder"] == "stage2_villa"
    assert all(cell == "GRASS" for row in manifest["site_ground"] for cell in row)


def test_delete_structure_stage_document_updates_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr("ui.document.STRUCTURES_FOLDER", tmp_path / "structures")

    create_structure_stage_document(
        structure="hall",
        stage=1,
        site_width=10,
        site_depth=10,
        structure_width=5,
        structure_depth=5,
    )
    create_structure_stage_document(
        structure="hall",
        stage=2,
        site_width=10,
        site_depth=10,
        structure_width=5,
        structure_depth=5,
    )

    delete_structure_stage_document(structure="hall", stage=1)

    assert not (tmp_path / "structures" / "hall" / "stage1").exists()
    assert (tmp_path / "structures" / "hall" / "stage2").exists()

    manifest = yaml.safe_load((tmp_path / "structures" / "hall" / "structure.yaml").read_text())
    assert [entry["stage"] for entry in manifest["stages"]] == [2]
    assert manifest["stages"][0]["path"] == "stage2/stage.yaml"


def test_create_structure_stage_document_rejects_structure_larger_than_site(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr("ui.document.STRUCTURES_FOLDER", tmp_path / "structures")

    with pytest.raises(ValueError, match="cannot be larger than site"):
        create_structure_stage_document(
            structure="barn",
            stage=1,
            site_width=8,
            site_depth=8,
            structure_width=12,
            structure_depth=6,
        )


def test_create_structure_stage_document_nether_ground(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr("ui.document.STRUCTURES_FOLDER", tmp_path / "structures")

    structure_path = create_structure_stage_document(
        structure="fortress",
        stage=1,
        site_width=6,
        site_depth=5,
        structure_width=4,
        structure_depth=3,
        dimension="nether",
    )

    document = load_structure_document(structure_path)
    assert document.metadata["dimension"] == "nether"
    assert all(cell == "minecraft:netherrack" for row in document.site_ground for cell in row)


def test_create_structure_stage_document_end_ground(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr("ui.document.STRUCTURES_FOLDER", tmp_path / "structures")

    structure_path = create_structure_stage_document(
        structure="island",
        stage=1,
        site_width=4,
        site_depth=4,
        structure_width=3,
        structure_depth=3,
        dimension="end",
    )

    document = load_structure_document(structure_path)
    assert document.metadata["dimension"] == "end"
    assert all(cell == "minecraft:end_stone" for row in document.site_ground for cell in row)


def test_existing_structure_without_dimension_defaults_and_persists(tmp_path: Path):
    structure_path = tmp_path / "structure.yaml"
    layers_dir = tmp_path / "layers"
    layers_dir.mkdir()
    (layers_dir / "layer_00.yaml").write_text(
        "index: 0\ngroup: Main\ncells:\n- - .\n",
        encoding="utf-8",
    )
    structure_path.write_text(
        "structure: test\nstage: 1\nname: Test\noutput_folder: test\n"
        "grid:\n  site_width: 2\n  site_depth: 2\n  offset_x: 0\n  offset_z: 0\n"
        "  site_structure_layers:\n  - 0\n"
        "layer_files:\n- layers/layer_00.yaml\n"
        "site_ground:\n- - GRASS\n  - GRASS\n- - GRASS\n  - GRASS\n",
        encoding="utf-8",
    )

    document = load_structure_document(structure_path)
    assert document.metadata["dimension"] == "overworld"

    save_structure_metadata(
        structure_path,
        document.metadata,
        layer_files=document.layer_files,
        site_ground=document.site_ground,
        document=document,
    )

    saved = yaml.safe_load(structure_path.read_text(encoding="utf-8"))
    assert saved["dimension"] == "overworld"
