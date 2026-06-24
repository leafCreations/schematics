from helpers.minecraft_versions import (
    DEFAULT_STRUCTURE_MINECRAFT_VERSION,
    SUPPORTED_MINECRAFT_VERSIONS,
    compare_minecraft_versions,
    format_version_title_suffix,
    minecraft_version_at_least,
    normalize_minecraft_version,
)


def test_supported_versions():
    assert SUPPORTED_MINECRAFT_VERSIONS == ("26.1.2", "26.2")


def test_normalize_minecraft_version_defaults_unknown():
    assert normalize_minecraft_version(None) == DEFAULT_STRUCTURE_MINECRAFT_VERSION
    assert normalize_minecraft_version("bad") == DEFAULT_STRUCTURE_MINECRAFT_VERSION
    assert normalize_minecraft_version("26.2") == "26.2"


def test_compare_minecraft_versions():
    assert compare_minecraft_versions("26.1.2", "26.2") < 0
    assert compare_minecraft_versions("26.2", "26.1.2") > 0
    assert compare_minecraft_versions("26.1.2", "26.1.2") == 0


def test_minecraft_version_at_least():
    assert minecraft_version_at_least(structure_version="26.2", required_version="26.1.2")
    assert not minecraft_version_at_least(structure_version="26.1.2", required_version="26.2")


def test_format_version_title_suffix():
    assert format_version_title_suffix("26.1.2") == " (v26.1.2)"
