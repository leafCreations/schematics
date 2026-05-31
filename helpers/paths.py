from pathlib import Path

from helpers.context import SchematicContext

BASE_DIR = Path(__file__).resolve().parent.parent

ASSET_FOLDER = BASE_DIR / "assets"
GENERATED_ASSETS_FOLDER = ASSET_FOLDER / "generated"
BLOCK_TEXTURES_FOLDER = ASSET_FOLDER / "textures" / "block"
ENTITY_BED_TEXTURES_FOLDER = ASSET_FOLDER / "textures" / "entity" / "bed"
ENTITY_CHEST_TEXTURES_FOLDER = ASSET_FOLDER / "textures" / "entity" / "chest"
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
