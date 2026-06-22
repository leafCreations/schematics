from amulet.api.chunk import Chunk

from helpers.structure_tokens import parse_structure_token
from helpers.worldgen_block_updates import (
    behavior_needs_block_update,
    place_worldgen_block,
    schedule_block_update,
)
from helpers.worldgen_multiblock import parsed_needs_deferred_placement
from renderers import worldgen


def test_parsed_needs_deferred_placement_for_bed():
    assert parsed_needs_deferred_placement(parse_structure_token("BED:blue@north#head"))


def test_behavior_needs_block_update_for_bed():
    assert behavior_needs_block_update("bed")
    assert not behavior_needs_block_update("chest")


def test_schedule_block_update_stores_zero_delay_tick():
    chunk = Chunk(0, 0)

    schedule_block_update(chunk, 1, -59, 1, "minecraft:blue_bed")

    assert chunk.misc["block_ticks"][(1, -59, 1)] == ("minecraft:blue_bed", 0, 0)


def test_place_worldgen_block_schedules_bed_update():
    worldgen.BLOCK_CACHE.clear()
    chunk = Chunk(0, 0)
    parsed = parse_structure_token("BED:blue@north#head")
    block = worldgen.generate_block(parsed)

    place_worldgen_block(
        chunk,
        local_x=1,
        world_y=-59,
        local_z=1,
        world_x=1,
        world_z=1,
        block=block,
        parsed=parsed,
    )

    assert chunk.get_block(1, -59, 1).base_name == "blue_bed"
    assert chunk.misc["block_ticks"][(1, -59, 1)] == ("minecraft:blue_bed", 0, 0)


def test_place_worldgen_block_skips_chest_update():
    worldgen.BLOCK_CACHE.clear()
    chunk = Chunk(0, 0)
    parsed = parse_structure_token("CHEST@west#left")
    block = worldgen.generate_block(parsed)

    place_worldgen_block(
        chunk,
        local_x=7,
        world_y=-59,
        local_z=7,
        world_x=7,
        world_z=7,
        block=block,
        parsed=parsed,
    )

    assert "block_ticks" not in chunk.misc
