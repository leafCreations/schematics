from dataclasses import dataclass
from pathlib import Path

@dataclass
class SchematicContext:
    # structure
    data: dict
    site_size: int
    struct_w: int
    struct_h: int
    offset_x: int
    offset_z: int
    
    # metadata
    name: str    
    output_folder: str
    floor_map: dict
    #registries
    block_registry: dict
    
    #paths
    assets_dir: Path
    output_dir: Path
    
    #textures
    topdown_textures: dict | None = None
    sideview_textures: dict | None = None
    
    
