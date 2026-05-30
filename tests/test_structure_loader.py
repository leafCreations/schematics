import pytest

from helpers.structure_loader import validate_structure_config


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


def test_validate_structure_config_rejects_missing_grid_key():
    config = _minimal_config()
    del config["grid"]["site_size"]

    with pytest.raises(ValueError, match="site_size"):
        validate_structure_config(config)


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
