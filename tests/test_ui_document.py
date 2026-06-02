from pathlib import Path

import yaml

from ui.document import load_structure_document, save_layer


def test_open_residence_stage1_structure():
    path = Path("structures/residence/stage1/structure.yaml")
    document = load_structure_document(path)

    assert document.metadata["structure"] == "residence"
    assert document.metadata["stage"] == 1
    assert len(document.layers) == 6
    assert document.layers[0]["cells"]


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
