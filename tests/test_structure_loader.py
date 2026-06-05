from pathlib import Path

import pytest
import yaml

from helpers.paths import STRUCTURES_FOLDER
from helpers.structure_loader import (
    load_structure_config,
    load_structure_yaml,
    resolve_structure_source,
    validate_layers_consistent_dimensions,
    validate_structure_config,
)


def _minimal_config(**overrides):
    config = {
        "structure": "test",
        "stage": 1,
        "name": "Test",
        "output_folder": "test_output",
        "grid": {
            "site_size": 10,
            "offset_x": 1,
            "offset_z": 2,
            "site_structure_layers": [0],
        },
        "layers": [
            {
                "index": 0,
                "group": "Floor 1",
                "cells": [["PLANKS:oak", "."], [".", "COBBLESTONE"]],
            }
        ],
    }
    config.update(overrides)
    return config


def test_validate_structure_config_accepts_minimal_config():
    validated = validate_structure_config(_minimal_config())

    assert validated["structure"] == "test"
    assert len(validated["layers"]) == 1


def test_validate_structure_config_rejects_missing_site_dimensions():
    config = _minimal_config()
    del config["grid"]["site_size"]

    with pytest.raises(ValueError, match="site_width"):
        validate_structure_config(config)


def test_validate_structure_config_accepts_rectangular_site():
    config = _minimal_config(
        grid={
            "site_width": 20,
            "site_depth": 10,
            "offset_x": 1,
            "offset_z": 2,
            "site_structure_layers": [0],
        }
    )

    validated = validate_structure_config(config)

    assert validated["grid"]["site_width"] == 20
    assert validated["grid"]["site_depth"] == 10


def test_validate_structure_config_rejects_non_rectangular_layer():
    config = _minimal_config(
        layers=[
            {
                "index": 0,
                "cells": [["A", "B"], ["C"]],
            }
        ]
    )

    with pytest.raises(ValueError, match="width"):
        validate_structure_config(config)


def test_validate_structure_config_rejects_invalid_site_structure_layers():
    config = _minimal_config(
        grid={
            "site_size": 10,
            "offset_x": 0,
            "offset_z": 0,
            "site_structure_layers": [3],
        }
    )

    with pytest.raises(ValueError, match="site_structure_layers"):
        validate_structure_config(config)


def test_load_structure_yaml_residence_stage1():
    path = STRUCTURES_FOLDER / "residence" / "stage1" / "structure.yaml"
    config = load_structure_yaml(path)

    assert config["structure"] == "residence"
    assert config["stage"] == 1
    assert len(config["layers"]) == 7
    assert config["grid"]["trim_block"] == "COBBLESTONE#mossy"
    floor_layer = next(layer for layer in config["layers"] if layer.get("index") == 0)
    assert floor_layer["cells"][0][2] == "COBBLESTONE#mossy"


def test_load_structure_yaml_residence_stage2():
    path = STRUCTURES_FOLDER / "residence" / "stage2" / "structure.yaml"
    config = load_structure_yaml(path)

    assert config["structure"] == "residence"
    assert config["stage"] == 2
    assert len(config["layers"]) == 6


def test_load_structure_yaml_discovers_layer_files(tmp_path: Path):
    import shutil

    src = STRUCTURES_FOLDER / "residence" / "stage1"
    dest = tmp_path / "stage"
    shutil.copytree(src / "layers", dest / "layers")
    structure_path = dest / "structure.yaml"
    data = yaml.safe_load((src / "structure.yaml").read_text(encoding="utf-8"))
    del data["layer_files"]
    structure_path.write_text(
        yaml.safe_dump(data, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    config = load_structure_yaml(structure_path)

    assert len(config["layers"]) == 7


def test_validate_structure_config_rejects_unknown_cell_token():
    config = _minimal_config(
        layers=[{"index": 0, "cells": [["NOT_A_REAL_TOKEN"]]}],
    )

    with pytest.raises(ValueError, match="unknown or invalid cell tokens"):
        validate_structure_config(config)


def test_resolve_structure_source_prefers_yaml():
    path = resolve_structure_source("residence", 1)

    assert path.name == "structure.yaml"


def test_load_structure_config_builds_context_from_yaml():
    ctx = load_structure_config("residence", 1)

    assert ctx.structure == "residence"
    assert ctx.stage == 1
    assert len(ctx.layers) == 7
    assert ctx.topdown_textures


def test_validate_structure_config_rejects_duplicate_layer_index():
    config = _minimal_config(
        layers=[
            {"index": 0, "cells": [["."]]},
            {"index": 0, "cells": [["."]]},
        ]
    )

    with pytest.raises(ValueError, match="Duplicate layer index"):
        validate_structure_config(config)


def test_validate_structure_config_rejects_mismatched_layer_dimensions():
    config = _minimal_config(
        layers=[
            {"index": 0, "cells": [[".", "."], [".", "."]]},
            {"index": 1, "cells": [["."]]},
        ]
    )

    with pytest.raises(ValueError, match="same width and depth"):
        validate_structure_config(config)


def test_validate_layers_consistent_dimensions_accepts_matching_layers():
    layers = [
        {"index": 0, "cells": [[".", "."], [".", "."]]},
        {"index": 1, "cells": [[".", "."], [".", "."]]},
    ]

    validate_layers_consistent_dimensions(layers)
