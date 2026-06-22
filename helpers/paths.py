from pathlib import Path

from helpers.context import SchematicContext

BASE_DIR = Path(__file__).resolve().parent.parent

ASSETS_ROOT = BASE_DIR / "assets"
MINECRAFT_ASSETS_FOLDER = ASSETS_ROOT / "minecraft"
UI_ICONS_FOLDER = ASSETS_ROOT / "icons"
UI_ASSETS_FOLDER = ASSETS_ROOT / "ui"

# Minecraft resource root (blockstates, lang, models, textures, generated).
ASSET_FOLDER = MINECRAFT_ASSETS_FOLDER
GENERATED_ASSETS_FOLDER = MINECRAFT_ASSETS_FOLDER / "generated"
BLOCK_TEXTURES_FOLDER = MINECRAFT_ASSETS_FOLDER / "textures" / "block"
ITEM_TEXTURES_FOLDER = MINECRAFT_ASSETS_FOLDER / "textures" / "item"
ENTITY_BED_TEXTURES_FOLDER = MINECRAFT_ASSETS_FOLDER / "textures" / "entity" / "bed"
ENTITY_CHEST_TEXTURES_FOLDER = MINECRAFT_ASSETS_FOLDER / "textures" / "entity" / "chest"
OUTPUT_SCHEMATICS_FOLDER = BASE_DIR / "output/schematics"
OUTPUT_WORLDS_FOLDER = BASE_DIR / "output/worlds"
STRUCTURES_FOLDER = BASE_DIR / "structures"
TEMPLATE_FOLDER = BASE_DIR / "template"


def name_slug(name: str) -> str:
    return name.lower().replace(" ", "_")


def schematic_output_path(ctx: SchematicContext, suffix: str) -> Path:
    return ctx.output_schematics_dir / f"{name_slug(ctx.name)}_{suffix}"


def schematic_output_file(ctx: SchematicContext, filename: str) -> Path:
    return ctx.output_schematics_dir / filename
