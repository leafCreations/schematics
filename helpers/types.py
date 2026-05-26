# helpers/types.py

from typing import TypeAlias, TypedDict
from PIL import Image, ImageFont

# Simple Aliases
Token: TypeAlias = str
RawToken: TypeAlias = str
BlockId: TypeAlias = str

RenderList: TypeAlias = list[str]
TextureType: TypeAlias = str
MappedTextureNames: TypeAlias = dict[str, str]
MappedTextureImages: TypeAlias = dict[str, Image.Image]

BackgroundColor: TypeAlias = tuple[int, int, int]
ElevationRows: TypeAlias = list[str]
LayerElevations: TypeAlias = dict[int, ElevationRows]
SiteLayer: TypeAlias = list[list[str]]
SiteMap: TypeAlias = dict[int, SiteLayer]
Layers: TypeAlias = list[int]
Cell: TypeAlias = dict[str, object]
RawTokenMaterialsList: TypeAlias = list[RawToken]
MaterialsList: TypeAlias = list[tuple[str, int]]
MaterialsIconList: TypeAlias = list[dict[str, Token]]

# Structured Types
class FloorBlueprintLayout(TypedDict): 
    block_px: int
    padding: int
    layer_gap: int
    top_margin: int
    bottom_margin: int
    inventory_w: int
    panel_w: int
    panel_h: int
    layer_panel_w: int
    columns: int
    layer_pages: list[list[int]]
    
class FloorBlueprintPanel(TypedDict):
    sx: int
    sy: int
    block_px: int
    panel_w: int
    panel_h: int
    inventory_w: int
    
class PathLayout(TypedDict):
    block_px: int
    padding: int
    top_margin: int
    layers: list[int]
    panel_dim: int
    img_w: int
    img_h: int
    
class PathPanel(TypedDict):
    sx: int
    sy: int
    
class SiteFacadeLayout(TypedDict):
    block_px: int
    padding: int
    top_margin: int
    panel_w: int    
    img_w: int
    img_h: int
    view_keys: list[str]
    layer_keys: list[int]
    headings: dict[str, str]
    
class FacadeElevations(TypedDict):
    N: LayerElevations
    S: LayerElevations
    W: LayerElevations
    E: LayerElevations
    
class StructureFacadeLayout(TypedDict):
    block_px: int    
    top_margin: int
    panel_gap: int
    panel_w: int  
    panel_h: int      
    img_w: int
    img_h: int
    view_keys: list[str]
    layer_keys: list[int]
    headings: dict[str, str]

class MaterialsLayout(TypedDict):
    row_h: int
    heading_h: int
    footer_h: int
    padding: int
    img_w: int
    img_h: int
    
# Complex Types
Fonts: TypeAlias = dict[str, ImageFont.ImageFont]

