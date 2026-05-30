from PIL import Image

from helpers.structure_loader import (
    build_schematic_context,
)
from helpers.structure_loader import (
    load_structure_config as _load_structure_config,
)
from helpers.types import BlockId

__all__ = [
    "build_schematic_context",
    "default_texture_name",
    "load_structure_config",
    "normalize_direction",
    "rotate_directional_texture",
    "split_block_id",
]


def load_structure_config(structure: str, stage: int):
    return _load_structure_config(structure, stage)


# --- REGISTRY-DRIVEN SCHEMATIC HELPERS ---
def split_block_id(block_id: BlockId) -> tuple[str, str]:
    """Return (namespace, block_name) from a Minecraft block id."""
    if ":" not in block_id:
        return "minecraft", block_id
    return block_id.split(":", 1)


def default_texture_name(block_id: BlockId) -> str:
    """Resolve minecraft:oak_planks -> oak_planks.png.

    This intentionally strips the namespace so future modded blocks can use
    their own asset folders while keeping the registry close to Minecraft syntax.
    Example: create:brass_block -> brass_block.png
    """
    _namespace, block_name = split_block_id(block_id)
    return f"{block_name}.png"


def normalize_direction(direction: str | None) -> str | None:
    if direction is None:
        return None

    direction = str(direction).strip().upper()

    direction_aliases = {
        "NORTH": "N",
        "EAST": "E",
        "SOUTH": "S",
        "WEST": "W",
        "N": "N",
        "E": "E",
        "S": "S",
        "W": "W",
    }

    return direction_aliases.get(direction)


def rotate_directional_texture(texture: Image.Image, direction: str | None) -> Image.Image:
    """Rotate a square top-down asset so token direction is visible in schematics.

    Assumption: source assets are drawn in NORTH orientation by default.
    Uses lossless right-angle transpose operations instead of Image.rotate()
    so pixel-art textures do not get resampled or visually blurred.
    """
    if direction is None or direction == "N":
        return texture.copy()
    if direction == "E":
        return texture.transpose(Image.Transpose.ROTATE_90)
    if direction == "S":
        return texture.transpose(Image.Transpose.ROTATE_180)
    if direction == "W":
        return texture.transpose(Image.Transpose.ROTATE_270)
    return texture.copy()
