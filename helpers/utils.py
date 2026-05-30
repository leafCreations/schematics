import importlib.util
from pathlib import Path

from PIL import Image

import helpers.constants as constants
from helpers.context import SchematicContext
from helpers.paths import (
    ASSET_FOLDER,
    OUTPUT_SCHEMATICS_FOLDER,
    OUTPUT_WORLDS_FOLDER,
    TEMPLATE_FOLDER,
)
from helpers.types import BlockId
from registries.loader import BLOCK_REGISTRY, compile_inventory_texture_set, compile_texture_set


def load_structure_config(structure: str, stage: int) -> SchematicContext:
    structure_file = f"structures/{structure}/stage{stage}_structure.py"

    structure_path = Path(structure_file).resolve()

    if not structure_path.exists():
        raise FileNotFoundError(f"Structure file not found: {structure_path}")

    module_name = structure_path.stem

    spec = importlib.util.spec_from_file_location(module_name, structure_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load structure module: {structure_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "STRUCTURE_CONFIG"):
        raise AttributeError(f"{structure_path} must define STRUCTURE_CONFIG")

    ctx = SchematicContext(
        structure=module.STRUCTURE_CONFIG["structure"],
        stage=module.STRUCTURE_CONFIG["stage"],
        layers=module.STRUCTURE_CONFIG["layers"],
        grid=module.STRUCTURE_CONFIG["grid"],
        name=module.STRUCTURE_CONFIG["name"],
        block_registry=BLOCK_REGISTRY,
        assets_dir=ASSET_FOLDER / "textures/block",
        output_schematics_dir=OUTPUT_SCHEMATICS_FOLDER / module.STRUCTURE_CONFIG["output_folder"],
        output_worldgen_dir=OUTPUT_WORLDS_FOLDER / module.STRUCTURE_CONFIG["output_folder"],
        worldgen_template_dir=TEMPLATE_FOLDER,
    )

    ctx.topdown_textures = compile_texture_set(
        constants.TEXTURE_TOP, ctx.assets_dir, block_px=constants.BLOCK_PX
    )
    ctx.sideview_textures = compile_texture_set(
        constants.TEXTURE_SIDE, ctx.assets_dir, block_px=constants.BLOCK_PX
    )
    ctx.inventory_textures = compile_inventory_texture_set(
        ctx.assets_dir, block_px=constants.BLOCK_PX
    )

    return ctx


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
