from helpers.registry_lookup import (
    get_block_entry,
    is_minecraft_block_token,
    minecraft_block_id,
    registry_lookup_token,
    solid_entry_for_block_id,
)
from helpers.structure_tokens import ParsedToken, parse_structure_token
from registries.loader import BEHAVIORS_DIR, BLOCK_PALETTES, BLOCK_REGISTRY, PALETTES_DIR


def test_behavior_registry_loads_from_split_files():
    assert BEHAVIORS_DIR.is_dir()
    assert "STAIRS" in BLOCK_REGISTRY
    assert "GRASS" not in BLOCK_REGISTRY


def test_legacy_grass_resolves_through_catalog():
    parsed = parse_structure_token("GRASS")
    assert parsed is not None

    entry = get_block_entry(parsed)
    assert entry is not None
    assert entry["behavior"] == "solid"
    assert entry["minecraft"]["block"] == "minecraft:grass_block"


def test_block_palettes_load():
    assert PALETTES_DIR.is_dir()
    assert "terrain" in BLOCK_PALETTES
    assert "PLANKS" in BLOCK_PALETTES["wood"]["tokens"]
    assert BLOCK_PALETTES["terrain"]["sections"]["overworld"][0]["id"] == "minecraft:dirt"


def test_minecraft_block_token_parsing():
    parsed = parse_structure_token("minecraft:stone")

    assert parsed is not None
    assert is_minecraft_block_token(parsed)
    assert minecraft_block_id(parsed) == "minecraft:stone"
    assert registry_lookup_token(parsed) == "minecraft:stone"


def test_get_block_entry_for_minecraft_cell():
    parsed = parse_structure_token("minecraft:grass_block")

    assert parsed is not None

    entry = get_block_entry(parsed)

    assert entry is not None
    assert entry["behavior"] == "solid"
    assert entry["minecraft"]["block"] == "minecraft:grass_block"


def test_solid_entry_uses_catalog_texture():
    entry = solid_entry_for_block_id("minecraft:stone")

    assert entry["render"]["top"] == "stone.png"


def test_semantic_token_still_uses_behavior_registry():
    parsed = ParsedToken(token="FURNACE")

    entry = get_block_entry(parsed)

    assert entry is not None
    assert entry["behavior"] == "facing_block"
