from helpers.block_picker import picker_entry_for_token
from helpers.log_materials import (
    enumerate_log_materials,
    log_block_suffix,
    resolve_log_block_id,
)
from helpers.registry_blocks import resolve_minecraft_block_id
from helpers.structure_tokens import parse_structure_token


def test_enumerate_log_materials_includes_overworld_and_nether_wood():
    materials = enumerate_log_materials()

    assert "oak" in materials
    assert "spruce" in materials
    assert "crimson" in materials
    assert "warped" in materials


def test_enumerate_log_materials_excludes_non_wood_stems():
    materials = enumerate_log_materials()

    for unexpected in (
        "mushroom",
        "melon",
        "pumpkin",
        "big_dripleaf",
        "attached_melon",
        "attached_pumpkin",
    ):
        assert unexpected not in materials


def test_log_block_suffix_uses_stem_for_nether_wood():
    assert log_block_suffix("oak") == "log"
    assert log_block_suffix("crimson") == "stem"
    assert log_block_suffix("warped") == "stem"


def test_resolve_log_block_id_for_nether_wood():
    assert resolve_log_block_id("oak") == "minecraft:oak_log"
    assert resolve_log_block_id("crimson") == "minecraft:crimson_stem"
    assert resolve_log_block_id("warped") == "minecraft:warped_stem"


def test_picker_entry_for_log_includes_crimson_and_warped():
    entry = picker_entry_for_token("LOG")

    assert entry is not None
    assert "crimson" in entry.materials
    assert "warped" in entry.materials


def test_resolve_minecraft_block_id_for_crimson_log():
    entry = picker_entry_for_token("LOG")
    assert entry is not None

    parsed = parse_structure_token("LOG:crimson")
    assert parsed is not None

    from registries.loader import BLOCK_REGISTRY

    block_id = resolve_minecraft_block_id(BLOCK_REGISTRY["LOG"], parsed)
    assert block_id == "minecraft:crimson_stem"
