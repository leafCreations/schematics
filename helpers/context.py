from dataclasses import dataclass
from pathlib import Path

from helpers.types import MappedTextureImages

@dataclass
class SchematicContext:
    # structure
    data: dict[int, list[str]]
    site_size: int
    struct_w: int
    struct_h: int
    offset_x: int
    offset_z: int
    
    # metadata
    name: str    
    output_folder: str
    floor_map: dict[str, list[int]]
    #registries
    block_registry: dict
    
    #paths
    assets_dir: Path
    output_dir: Path
    
    #textures
    topdown_textures: MappedTextureImages | None = None
    sideview_textures: MappedTextureImages | None = None
    
    
