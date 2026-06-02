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
