from helpers.campfire_state import (
    DEFAULT_CAMPFIRE_FACING,
    DEFAULT_CAMPFIRE_LIT,
    campfire_block_entry,
    explicit_lit,
    is_campfire_block_id,
    resolve_campfire_facing,
    resolve_campfire_lit,
    with_campfire_lit,
)
from helpers.registry_blocks import resolve_minecraft_blockstates
from helpers.structure_tokens import parse_structure_token


def test_is_campfire_block_id():
    assert is_campfire_block_id("minecraft:campfire")
    assert is_campfire_block_id("minecraft:soul_campfire")
    assert not is_campfire_block_id("minecraft:stone")


def test_parse_campfire_token_with_facing_and_lit():
    parsed = parse_structure_token("minecraft:campfire@west;lit=false")

    assert parsed is not None
    assert resolve_campfire_facing(parsed) == "west"
    assert resolve_campfire_lit(parsed) is False


def test_campfire_defaults():
    parsed = parse_structure_token("minecraft:campfire")

    assert parsed is not None
    assert resolve_campfire_facing(parsed) == DEFAULT_CAMPFIRE_FACING
    assert resolve_campfire_lit(parsed) is DEFAULT_CAMPFIRE_LIT
    assert explicit_lit(parsed) is None


def test_with_campfire_lit_replaces_state():
    updated = with_campfire_lit("minecraft:campfire@north;lit=true", False)

    assert updated == "minecraft:campfire@north;lit=false"


def test_worldgen_blockstates_for_campfire():
    parsed = parse_structure_token("minecraft:soul_campfire@east;lit=false")
    entry = campfire_block_entry("minecraft:soul_campfire")

    blockstates = resolve_minecraft_blockstates(
        entry,
        parsed,
        entry["minecraft"]["blockstates"],
    )

    assert blockstates == {"facing": "east", "lit": "false"}
