from dataclasses import dataclass, field
from pathlib import Path

from helpers.types import BlockRegistryEntry, GridConfig, LayerConfig, MappedTextureImages


@dataclass
class SchematicContext:
    structure: str
    stage: int
    name: str

    layers: list[LayerConfig]
    grid: GridConfig

    block_registry: dict[str, BlockRegistryEntry]

    assets_dir: Path
    worldgen_template_dir: Path
    output_schematics_dir: Path
    output_worldgen_dir: Path

    topdown_textures: MappedTextureImages | None = None
    sideview_textures: MappedTextureImages | None = None
    inventory_textures: MappedTextureImages = field(default_factory=dict)
    site_ground: list[list[str]] | None = None
