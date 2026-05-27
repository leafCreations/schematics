from dataclasses import dataclass
from pathlib import Path

from helpers.types import BlockRegistryEntry, MappedTextureImages


@dataclass
class SchematicContext:
    # structure
    structure: str
    stage: int

    # dimensions
    data: dict[int, list[str]]
    site_size: int
    struct_w: int
    struct_h: int
    offset_x: int
    offset_z: int

    # metadata
    name: str
    floor_map: dict[str, list[int]]

    # registries
    block_registry: dict[str, BlockRegistryEntry]

    # paths
    assets_dir: Path
    worldgen_template_dir: Path
    output_schematics_dir: Path
    output_worldgen_dir: Path

    # textures
    topdown_textures: MappedTextureImages | None = None
    sideview_textures: MappedTextureImages | None = None
