from helpers.registry_lookup import get_block_entry
from helpers.structure_tokens import parse_structure_token
from helpers.worldgen_block_entities import (
    normalize_block_for_worldgen_export,
    resolve_worldgen_export_block_id,
)
from renderers import worldgen


def test_generate_bed_uses_unified_block_and_color():
    worldgen.BLOCK_CACHE.clear()

    block = worldgen.generate_block(parse_structure_token("BED:red@north#head"))

    assert block.base_name == "bed"
    assert str(block.properties["color"]) == "red"
    assert str(block.properties["facing"]) == "north"
    assert str(block.properties["part"]) == "head"


def test_generate_bed_foot_part():
    worldgen.BLOCK_CACHE.clear()

    block = worldgen.generate_block(parse_structure_token("BED:red@north#foot"))

    assert block.base_name == "bed"
    assert str(block.properties["color"]) == "red"
    assert str(block.properties["part"]) == "foot"


def test_worldgen_export_normalizes_bed_to_colored_block():
    worldgen.BLOCK_CACHE.clear()

    parsed = parse_structure_token("BED:red@north#head")
    entry = get_block_entry(parsed)
    assert entry is not None

    editor_block = worldgen.generate_block(parsed)
    export_block = normalize_block_for_worldgen_export(editor_block, entry, parsed)

    assert export_block.base_name == "red_bed"
    assert resolve_worldgen_export_block_id(entry, parsed) == "minecraft:red_bed"
