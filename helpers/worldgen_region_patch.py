"""Post-save region patches for blocks Amulet does not fully persist."""

from __future__ import annotations

import struct
import zlib
from collections import defaultdict
from pathlib import Path

import amulet_nbt
from amulet_nbt import CompoundTag, IntTag, ListTag, NamedTag, ShortTag, StringTag

from helpers.registry_blocks import resolve_minecraft_block_id
from helpers.registry_lookup import get_block_entry
from helpers.worldgen_multiblock import WorldgenPlacement

_MIN_SECTION_Y = -4
_POST_PROCESSING_SECTIONS = 24


def pack_post_processing_coord(local_x: int, local_y: int, local_z: int) -> int:
    """Pack a section-local coordinate into a PostProcessing short (0ZYX nibbles)."""
    return (local_z << 8) | (local_y << 4) | local_x


def post_processing_section_index(world_y: int, *, min_section_y: int = _MIN_SECTION_Y) -> int:
    return (world_y >> 4) - min_section_y


def local_coord_in_section(world_coord: int) -> int:
    return world_coord & 15


def _region_path(world_dir: Path, chunk_x: int, chunk_z: int) -> Path:
    region_root = world_dir / "dimensions/minecraft/overworld/region"
    if not region_root.is_dir():
        region_root = world_dir / "region"
    return region_root / f"r.{chunk_x >> 5}.{chunk_z >> 5}.mca"


def _read_region_chunk(region_path: Path, chunk_x: int, chunk_z: int) -> bytes | None:
    if not region_path.is_file():
        return None

    index = (chunk_x % 32) + (chunk_z % 32) * 32
    with region_path.open("rb") as handle:
        handle.seek(index * 4)
        location = struct.unpack(">I", handle.read(4))[0]
        if location == 0:
            return None

        offset = location >> 8
        handle.seek(offset * 4096)
        length = struct.unpack(">I", handle.read(4))[0]
        compression = handle.read(1)[0]
        if compression != 2:
            raise ValueError(f"unsupported chunk compression type {compression}")

        payload = handle.read(length - 1)
        if len(payload) != length - 1:
            raise ValueError("truncated chunk payload")

    return zlib.decompress(payload)


def _write_region_chunk(
    region_path: Path,
    chunk_x: int,
    chunk_z: int,
    chunk_data: bytes,
) -> None:
    region_path.parent.mkdir(parents=True, exist_ok=True)
    if not region_path.exists():
        region_path.write_bytes(b"\x00" * (32 * 32 * 4) + b"\x00" * (32 * 32 * 3))

    index = (chunk_x % 32) + (chunk_z % 32) * 32
    compressed = zlib.compress(chunk_data)
    payload = struct.pack("B", 2) + compressed
    total_length = 4 + len(payload)
    sector_count = (total_length + 4095) // 4096
    padded_length = sector_count * 4096

    with region_path.open("r+b") as handle:
        handle.seek(index * 4)
        old_location = struct.unpack(">I", handle.read(4))[0]
        old_sectors = old_location & 0xFF if old_location else 0

        handle.seek(0, 2)
        file_size = handle.tell()
        if old_location:
            new_offset = old_location >> 8
            if sector_count <= old_sectors:
                handle.seek(new_offset * 4096)
            else:
                new_offset = (file_size + 4095) // 4096
                handle.seek(new_offset * 4096)
        else:
            new_offset = (file_size + 4095) // 4096
            handle.seek(new_offset * 4096)

        handle.write(struct.pack(">I", len(payload) + 1))
        handle.write(payload)
        handle.write(b"\x00" * (padded_length - total_length))

        handle.seek(index * 4)
        handle.write(struct.pack(">I", (new_offset << 8) | sector_count))

        timestamp_index = (32 * 32 * 4) + (index * 4)
        handle.seek(timestamp_index)
        handle.write(struct.pack(">I", 0))


def _ensure_post_processing_lists(root: CompoundTag) -> ListTag:
    post_processing = root.get("PostProcessing")
    if not isinstance(post_processing, ListTag):
        post_processing = ListTag()

    while len(post_processing) < _POST_PROCESSING_SECTIONS:
        post_processing.append(ListTag())

    root["PostProcessing"] = post_processing
    return post_processing


def _append_post_processing(root: CompoundTag, world_x: int, world_y: int, world_z: int) -> None:
    section_index = post_processing_section_index(world_y)
    if not (0 <= section_index < _POST_PROCESSING_SECTIONS):
        return

    packed = pack_post_processing_coord(
        local_coord_in_section(world_x),
        local_coord_in_section(world_y),
        local_coord_in_section(world_z),
    )
    section_list = _ensure_post_processing_lists(root)[section_index]
    if not isinstance(section_list, ListTag):
        section_list = ListTag()
        _ensure_post_processing_lists(root)[section_index] = section_list

    for entry in section_list:
        if int(entry) == packed:
            return

    section_list.append(ShortTag(packed))


def _append_block_entity(root: CompoundTag, world_x: int, world_y: int, world_z: int) -> None:
    block_entities = root.get("block_entities")
    if not isinstance(block_entities, ListTag):
        block_entities = ListTag()
        root["block_entities"] = block_entities

    for entity in block_entities:
        if (
            int(entity.get("x")) == world_x
            and int(entity.get("y")) == world_y
            and int(entity.get("z")) == world_z
        ):
            return

    block_entities.append(
        CompoundTag(
            {
                "id": StringTag("minecraft:bed"),
                "x": IntTag(world_x),
                "y": IntTag(world_y),
                "z": IntTag(world_z),
            }
        )
    )


def _append_block_tick(
    root: CompoundTag,
    world_x: int,
    world_y: int,
    world_z: int,
    block_id: str,
) -> None:
    block_ticks = root.get("block_ticks")
    if not isinstance(block_ticks, ListTag):
        block_ticks = ListTag()
        root["block_ticks"] = block_ticks

    for tick in block_ticks:
        if (
            int(tick.get("x")) == world_x
            and int(tick.get("y")) == world_y
            and int(tick.get("z")) == world_z
        ):
            return

    block_ticks.append(
        CompoundTag(
            {
                "i": StringTag(block_id),
                "p": IntTag(0),
                "t": IntTag(0),
                "x": IntTag(world_x),
                "y": IntTag(world_y),
                "z": IntTag(world_z),
            }
        )
    )


def patch_chunk_nbt_for_beds(root: CompoundTag, placements: list[WorldgenPlacement]) -> None:
    for placement in placements:
        entry = get_block_entry(placement.parsed)
        if entry is not None:
            block_id = resolve_minecraft_block_id(entry, placement.parsed)
        else:
            block_id = "minecraft:bed"
        _append_block_entity(root, placement.global_x, placement.world_y, placement.global_z)
        _append_post_processing(root, placement.global_x, placement.world_y, placement.global_z)
        _append_block_tick(
            root,
            placement.global_x,
            placement.world_y,
            placement.global_z,
            block_id,
        )


def patch_world_bed_placements(world_dir: Path, placements: list[WorldgenPlacement]) -> None:
    """Inject bed block entities and post-load updates into saved region files."""
    if not placements:
        return

    by_region: dict[Path, dict[tuple[int, int], list[WorldgenPlacement]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for placement in placements:
        chunk_x = placement.global_x // 16
        chunk_z = placement.global_z // 16
        by_region[_region_path(world_dir, chunk_x, chunk_z)][(chunk_x, chunk_z)].append(placement)

    for region_path, chunks in by_region.items():
        for (chunk_x, chunk_z), chunk_placements in chunks.items():
            chunk_data = _read_region_chunk(region_path, chunk_x, chunk_z)
            if chunk_data is None:
                continue

            root = amulet_nbt.load(chunk_data).compound
            patch_chunk_nbt_for_beds(root, chunk_placements)
            chunk_bytes = NamedTag(root).save_to(compressed=False)
            _write_region_chunk(region_path, chunk_x, chunk_z, chunk_bytes)
