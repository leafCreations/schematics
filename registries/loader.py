import os
import yaml
from pathlib import Path
import helpers.utils as utils
from PIL import Image

REGISTRY_PATH = Path(__file__).parent / "blocks.yaml"

with open(REGISTRY_PATH, "r") as f:
    BLOCK_REGISTRY = yaml.safe_load(f)
    
def _resolve_registry_texture(entry, texture_type="top"):
    """Resolve a texture from registry data.

    Priority:
    1. schematic top_texture / side_texture override
    2. minecraft block-name fallback, e.g. minecraft:oak_planks -> oak_planks.png
    """
    schematic = entry.get("schematic", {})
    minecraft = entry.get("minecraft", {})
    explicit_key = f"{texture_type}_texture"

    if schematic.get(explicit_key):
        return schematic[explicit_key]

    block_id = minecraft.get("block")
    if not block_id:
        return None

    return utils.default_texture_name(block_id)

def _build_registry_texture_mapping(texture_type="top"):
    mapping = {}

    for raw_token, entry in BLOCK_REGISTRY.items():
        schematic = entry.get("schematic", {})
        texture_name = _resolve_registry_texture(entry, texture_type)

        if texture_name:
            mapping[raw_token] = texture_name

    return mapping

def compile_texture_set(texture_type, assets_dir, block_px):
    mapping = _build_registry_texture_mapping(texture_type)
    loaded = {}

    for token, filename in mapping.items():
        for folder in [
            assets_dir,
            os.path.join(assets_dir, "block_assets"),
            os.path.join(assets_dir, "item_assets")
        ]:
            normalized_filename = filename.lstrip("/\\")
            path = os.path.join(folder, normalized_filename)

            if os.path.exists(path):
                img = (
                    Image.open(path)
                    .convert("RGBA")
                    .resize((block_px, block_px), Image.Resampling.NEAREST)
                )

                loaded[token] = img
                break

    return loaded