from helpers.block_catalog import (
    block_available_in_version,
    catalog_entry_introduced_in,
    infer_block_introduced_in,
)


def test_infer_block_introduced_in_marks_26_2_blocks():
    assert infer_block_introduced_in("minecraft:cinnabar") == "26.2"
    assert infer_block_introduced_in("minecraft:sulfur_spike") == "26.2"
    assert infer_block_introduced_in("minecraft:cobblestone") == "26.1.2"


def test_block_available_in_version_filters_26_2_blocks():
    assert block_available_in_version("minecraft:cobblestone", "26.1.2")
    assert block_available_in_version("minecraft:cinnabar", "26.2")
    assert not block_available_in_version("minecraft:cinnabar", "26.1.2")
    assert not block_available_in_version("minecraft:sulfur", "26.1.2")


def test_catalog_entry_introduced_in_uses_catalog_metadata():
    entry = {"display_name": "Test", "introduced_in": "26.2"}
    catalog = {"minecraft:custom_block": entry}
    assert catalog_entry_introduced_in("minecraft:custom_block", catalog=catalog) == "26.2"
