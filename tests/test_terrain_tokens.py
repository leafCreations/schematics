from helpers.registry_lookup import get_block_entry
from helpers.structure_tokens import parse_structure_token
from helpers.terrain_tokens import (
    GRASS_BLOCK,
    migrate_terrain_token,
    terrain_tokens_equivalent,
)


def test_migrate_legacy_terrain_tokens():
    assert migrate_terrain_token("GRASS") == GRASS_BLOCK
    assert migrate_terrain_token("COBBLESTONE#mossy") == "minecraft:mossy_cobblestone"
    assert migrate_terrain_token("PLANKS:oak") == "PLANKS:oak"


def test_legacy_and_catalog_tokens_equivalent():
    assert terrain_tokens_equivalent("GRASS", GRASS_BLOCK)
    assert terrain_tokens_equivalent("COBBLESTONE#mossy", "minecraft:mossy_cobblestone")
    assert not terrain_tokens_equivalent("COBBLESTONE", "minecraft:mossy_cobblestone")


def test_get_block_entry_resolves_legacy_grass_via_catalog():
    parsed = parse_structure_token("GRASS")
    assert parsed is not None

    entry = get_block_entry(parsed)
    assert entry is not None
    assert entry["minecraft"]["block"] == GRASS_BLOCK


def test_get_block_entry_resolves_legacy_mossy_cobblestone():
    parsed = parse_structure_token("COBBLESTONE#mossy")
    assert parsed is not None

    entry = get_block_entry(parsed)
    assert entry is not None
    assert entry["minecraft"]["block"] == "minecraft:mossy_cobblestone"
