from pathlib import Path

import pytest

from helpers.structure_metadata import (
    apply_structure_identity,
    apply_structure_version,
    derive_output_folder,
    derive_structure_name,
    identity_from_structure_path,
    normalize_structure_slug,
    resolve_structure_version,
    validate_structure_slug,
)


def test_derive_output_folder():
    assert derive_output_folder("residence", 1) == "stage1_residence"
    assert derive_output_folder("My Barn", 2) == "stage2_mybarn"


def test_normalize_structure_slug():
    assert normalize_structure_slug("  Residence  ") == "residence"


def test_derive_structure_name():
    assert derive_structure_name("residence", 1) == "Residence Stage 1"
    assert derive_structure_name("mybarn", 2) == "Mybarn Stage 2"


def test_apply_structure_identity_sets_derived_name_and_output_folder():
    metadata = {"grid": {"offset_x": 0, "offset_z": 0, "site_width": 10, "site_depth": 10}}
    apply_structure_identity(metadata, structure="residence", stage=3)

    assert metadata["structure"] == "residence"
    assert metadata["stage"] == 3
    assert metadata["name"] == "Residence Stage 3"
    assert metadata["output_folder"] == "stage3_residence"


def test_identity_from_structure_path():
    path = Path("structures/residence/stage1/stage.yaml")
    assert identity_from_structure_path(path) == ("residence", 1)


def test_validate_structure_slug_rejects_uppercase():
    with pytest.raises(ValueError, match="lowercase"):
        validate_structure_slug("Residence")


def test_validate_structure_slug_accepts_letters_only():
    validate_structure_slug("residence")


def test_resolve_structure_version_defaults_to_26_1_2():
    assert resolve_structure_version({}) == "26.1.2"
    assert resolve_structure_version({"version": "26.2"}) == "26.2"


def test_apply_structure_version_normalizes_value():
    metadata: dict[str, str] = {}
    assert apply_structure_version(metadata, version="26.2") == "26.2"
    assert metadata["version"] == "26.2"


def test_validate_structure_slug_rejects_digits_and_underscores():
    with pytest.raises(ValueError, match="a-z only"):
        validate_structure_slug("my_barn")

    with pytest.raises(ValueError, match="a-z only"):
        validate_structure_slug("barn2")
