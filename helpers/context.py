from dataclasses import dataclass, field
from pathlib import Path

from helpers.types import BlockRegistryEntry, MappedTextureImages


@dataclass
class SchematicContext:
    structure: str
    stage: int
    name: str

    layers: list[dict]
    grid: dict

    block_registry: dict[str, BlockRegistryEntry]

    assets_dir: Path
    worldgen_template_dir: Path
    output_schematics_dir: Path
    output_worldgen_dir: Path

    topdown_textures: MappedTextureImages | None = None
    sideview_textures: MappedTextureImages | None = None
    inventory_textures: dict = field(default_factory=dict)
