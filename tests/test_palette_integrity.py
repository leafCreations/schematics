from pathlib import Path

import pytest

from registries.loader import BLOCK_REGISTRY
from registries.validate import collect_palette_integrity_errors, validate_palettes


def test_palette_integrity_passes_for_repository_data():
    validate_palettes()


def test_collect_palette_integrity_errors_flags_unknown_token():
    palettes = {
        "test": {
            "label": "Test",
            "tokens": ["MISSING_TOKEN"],
            "blocks": [],
        }
    }

    errors = collect_palette_integrity_errors(block_palettes=palettes)

    assert any("unknown token 'MISSING_TOKEN'" in error for error in errors)


def test_collect_palette_integrity_errors_flags_unknown_catalog_block():
    palettes = {
        "test": {
            "label": "Test",
            "tokens": [],
            "blocks": ["minecraft:not_a_real_block"],
        }
    }

    errors = collect_palette_integrity_errors(
        block_palettes=palettes,
        catalog={"minecraft:stone": {"display_name": "Stone"}},
    )

    assert any("unknown catalog block" in error for error in errors)


def test_collect_palette_integrity_errors_flags_unknown_behavior_palette():
    registry = {
        "TEST": {
            "behavior": "solid",
            "ui": {"palette": "missing_palette"},
        }
    }

    errors = collect_palette_integrity_errors(block_registry=registry, block_palettes={})

    assert any("unknown palette 'missing_palette'" in error for error in errors)


def test_validate_palettes_raises_with_details():
    with pytest.raises(ValueError, match="Palette integrity check failed"):
        validate_palettes(
            block_registry=BLOCK_REGISTRY,
            block_palettes={"broken": {"tokens": ["NOT_A_TOKEN"], "blocks": []}},
        )


def test_collect_behavior_integrity_errors_flags_missing_minecraft():
    registry = {
        "BAD": {
            "behavior": "solid",
            "ui": {"palette": "terrain"},
        }
    }

    errors = collect_palette_integrity_errors(
        block_registry=registry,
        block_palettes={"terrain": {"tokens": ["BAD"], "blocks": []}},
        check_textures=False,
    )

    assert any("minecraft" in error for error in errors)


def test_collect_behavior_integrity_errors_flags_placeholder_mismatch():
    registry = {
        "BAD": {
            "behavior": "solid",
            "ui": {"palette": "terrain", "requires_material": True},
            "minecraft": {"block": "minecraft:stone"},
        }
    }

    errors = collect_palette_integrity_errors(
        block_registry=registry,
        block_palettes={"terrain": {"tokens": ["BAD"], "blocks": []}},
        check_textures=False,
    )

    assert any("requires_material" in error for error in errors)


def test_load_structure_module_emits_deprecation_warning(tmp_path: Path):
    import warnings

    module_path = tmp_path / "stage1_structure.py"
    module_path.write_text(
        "STRUCTURE_CONFIG = {\n"
        '  "structure": "test", "stage": 1, "name": "T", "output_folder": "out",\n'
        '  "grid": {"site_size": 5, "offset_x": 0, "offset_z": 0, "site_structure_layers": [0]},\n'
        '  "layers": [{"index": 0, "cells": [["."]]}],\n'
        "}\n",
        encoding="utf-8",
    )

    from helpers.structure_loader import load_structure_module

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        config = load_structure_module(module_path)

    assert config["structure"] == "test"
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
