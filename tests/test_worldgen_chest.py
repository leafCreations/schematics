from helpers.structure_tokens import parse_structure_token
from renderers import worldgen


def test_generate_chest_includes_facing():
    worldgen.BLOCK_CACHE.clear()

    block = worldgen.generate_block(parse_structure_token("CHEST@west#left"))

    assert block.base_name == "chest"
    assert str(block.properties["type"]) == "left"
    assert str(block.properties["facing"]) == "west"


def test_generate_double_chest_halves_share_facing():
    worldgen.BLOCK_CACHE.clear()

    left = worldgen.generate_block(parse_structure_token("CHEST@west#left"))
    right = worldgen.generate_block(parse_structure_token("CHEST@west#right"))

    assert str(left.properties["facing"]) == str(right.properties["facing"]) == "west"
    assert str(left.properties["type"]) == "left"
    assert str(right.properties["type"]) == "right"
