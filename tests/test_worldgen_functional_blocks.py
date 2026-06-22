import struct
import tempfile
import zlib
from pathlib import Path

import amulet_nbt as anbt

from helpers.structure_loader import load_structure_config
from renderers import worldgen


def _load_chunk_root(world_dir: Path):
    mca = world_dir / "dimensions/minecraft/overworld/region/r.0.0.mca"
    data = mca.read_bytes()
    loc_sectors = struct.unpack(">I", data[0:4])[0]
    start = (loc_sectors >> 8) * 4096
    length = struct.unpack(">I", data[start : start + 4])[0]
    raw = zlib.decompress(data[start + 5 : start + 4 + length])
    return anbt.load(raw).tag


def _palette_names(root, section_y: int) -> list[str]:
    names: list[str] = []

    for sec in root["sections"]:
        if int(sec["Y"]) != section_y:
            continue

        for entry in sec["block_states"]["palette"]:
            names.append(str(entry.get("Name", entry)))

    return names


def test_worldgen_writes_chest_block_entities_to_chunk_nbt():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "world"
        ctx = load_structure_config("well", 1)
        ctx = ctx.__class__(**{**ctx.__dict__, "output_worldgen_dir": out})
        worldgen.generate_minecraft_world(ctx)

        root = _load_chunk_root(out)
        block_entities = list(root.get("block_entities", []))

        assert len(block_entities) >= 2
        assert all("chest" in str(entity.get("id", "")) for entity in block_entities)


def test_worldgen_writes_bed_blocks_to_chunk_palette():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "world"
        ctx = load_structure_config("well", 2)
        ctx = ctx.__class__(**{**ctx.__dict__, "output_worldgen_dir": out})
        worldgen.generate_minecraft_world(ctx)

        root = _load_chunk_root(out)
        palette = _palette_names(root, section_y=-4)

        assert any(name == "minecraft:red_bed" for name in palette)

        bed_palette_count = sum(
            1
            for sec in root["sections"]
            if int(sec["Y"]) == -4
            for entry in sec["block_states"]["palette"]
            if str(entry.get("Name", entry)) == "minecraft:red_bed"
        )
        assert bed_palette_count >= 1


def test_worldgen_writes_bed_block_entities_to_chunk_nbt():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "world"
        ctx = load_structure_config("well", 2)
        ctx = ctx.__class__(**{**ctx.__dict__, "output_worldgen_dir": out})
        worldgen.generate_minecraft_world(ctx)

        root = _load_chunk_root(out)
        bed_entities = [
            entity
            for entity in root.get("block_entities", [])
            if "bed" in str(entity.get("id", ""))
        ]

        assert len(bed_entities) >= 2
        assert {int(entity["y"]) for entity in bed_entities} >= {-60}
