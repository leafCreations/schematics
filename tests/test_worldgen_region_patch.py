import struct
import zlib
from pathlib import Path

import amulet_nbt
from amulet_nbt import CompoundTag, IntTag, ListTag, NamedTag, StringTag

from helpers.structure_tokens import ParsedToken, parse_structure_token
from helpers.worldgen_multiblock import WorldgenPlacement, parsed_needs_deferred_placement
from helpers.worldgen_region_patch import (
    pack_post_processing_coord,
    patch_chunk_nbt_for_beds,
    post_processing_section_index,
)


def test_parsed_needs_deferred_placement_for_bed_and_door():
    assert parsed_needs_deferred_placement(parse_structure_token("BED:blue@north#head"))
    assert parsed_needs_deferred_placement(parse_structure_token("DOOR:oak@north#lower"))
    assert not parsed_needs_deferred_placement(parse_structure_token("CHEST@west#left"))


def test_pack_post_processing_coord_matches_minecraft_nibble_format():
    assert pack_post_processing_coord(1, 5, 1) == 337


def test_post_processing_section_index_for_negative_y():
    assert post_processing_section_index(-59) == 0


def test_patch_chunk_nbt_for_beds_adds_entities_ticks_and_post_processing():
    root = CompoundTag(
        {
            "block_entities": ListTag(),
            "block_ticks": ListTag(),
            "PostProcessing": ListTag([ListTag() for _ in range(24)]),
        }
    )
    placement = WorldgenPlacement(
        global_x=1,
        world_y=-59,
        global_z=1,
        block=None,
        parsed=parse_structure_token("BED:blue@north#head"),
    )

    patch_chunk_nbt_for_beds(root, [placement])

    assert len(root["block_entities"]) == 1
    assert str(root["block_entities"][0]["id"]) == "minecraft:bed"
    assert len(root["block_ticks"]) == 1
    assert str(root["block_ticks"][0]["i"]) == "minecraft:blue_bed"
    assert int(root["PostProcessing"][0][0]) == 337


def test_patch_world_bed_placements_writes_region_block_entities(tmp_path: Path):
    from helpers.worldgen_region_patch import _write_region_chunk, patch_world_bed_placements

    world_dir = tmp_path / "world"
    region_dir = world_dir / "dimensions/minecraft/overworld/region"
    region_dir.mkdir(parents=True)
    region_path = region_dir / "r.0.0.mca"

    root = CompoundTag(
        {
            "DataVersion": IntTag(4786),
            "xPos": IntTag(0),
            "zPos": IntTag(0),
            "yPos": IntTag(-4),
            "Status": StringTag("minecraft:full"),
            "sections": ListTag(),
            "block_entities": ListTag(),
            "block_ticks": ListTag(),
            "PostProcessing": ListTag([ListTag() for _ in range(24)]),
        }
    )
    _write_region_chunk(region_path, 0, 0, NamedTag(root).save_to(compressed=False))

    placement = WorldgenPlacement(
        global_x=1,
        world_y=-59,
        global_z=1,
        block=None,
        parsed=ParsedToken(token="BED", material="blue", direction="north", variant="head"),
    )
    patch_world_bed_placements(world_dir, [placement])

    with region_path.open("rb") as handle:
        offset = struct.unpack(">I", handle.read(4))[0] >> 8
        handle.seek(offset * 4096)
        length = struct.unpack(">I", handle.read(4))[0]
        handle.read(1)
        chunk_data = zlib.decompress(handle.read(length - 1))

    patched = amulet_nbt.load(chunk_data).compound
    assert len(patched["block_entities"]) == 1
    assert int(patched["block_entities"][0]["y"]) == -59
