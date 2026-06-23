from pathlib import Path

from helpers.context import SchematicContext

BASE_DIR = Path(__file__).resolve().parent.parent

ASSETS_ROOT = BASE_DIR / "assets"
MINECRAFT_ASSETS_FOLDER = ASSETS_ROOT / "minecraft"
VERSIONS_ASSETS_FOLDER = ASSETS_ROOT / "versions"
PROJECT_ASSETS_FOLDER = ASSETS_ROOT / "project"
PROJECT_CUSTOM_FOLDER = PROJECT_ASSETS_FOLDER / "custom"
GENERATED_ASSETS_FOLDER = PROJECT_ASSETS_FOLDER / "generated"
UI_ICONS_FOLDER = ASSETS_ROOT / "icons"
UI_ASSETS_FOLDER = ASSETS_ROOT / "ui"

DEFAULT_MINECRAFT_VERSION = "26.2"
DEFAULT_WORLGEN_VERSION = "26.1.2"

# Minecraft resource root (blockstates, lang, models, textures).
ASSET_FOLDER = MINECRAFT_ASSETS_FOLDER
BLOCK_TEXTURES_FOLDER = MINECRAFT_ASSETS_FOLDER / "textures" / "block"
ITEM_TEXTURES_FOLDER = MINECRAFT_ASSETS_FOLDER / "textures" / "item"
ENTITY_BED_TEXTURES_FOLDER = MINECRAFT_ASSETS_FOLDER / "textures" / "entity" / "bed"
ENTITY_CHEST_TEXTURES_FOLDER = MINECRAFT_ASSETS_FOLDER / "textures" / "entity" / "chest"
OUTPUT_SCHEMATICS_FOLDER = BASE_DIR / "output/schematics"
OUTPUT_WORLDS_FOLDER = BASE_DIR / "output/worlds"
STRUCTURES_FOLDER = BASE_DIR / "structures"
WORLGEN_TEMPLATES_FOLDER = BASE_DIR / "worldgen_templates"
LEGACY_TEMPLATE_FOLDER = BASE_DIR / "template"
# Deprecated: use resolve_worldgen_template_dir().
TEMPLATE_FOLDER = LEGACY_TEMPLATE_FOLDER

LEGACY_GENERATED_ASSETS_FOLDER = MINECRAFT_ASSETS_FOLDER / "generated"
LEGACY_PROJECT_CUSTOM_FOLDER = MINECRAFT_ASSETS_FOLDER / "textures" / "block" / "custom"


def minecraft_version_dir_name(version: str) -> str:
    return version.replace(".", "_")


def resolve_minecraft_assets_folder(*, version: str | None = None) -> Path:
    """Return the active vanilla resource root."""
    if MINECRAFT_ASSETS_FOLDER.is_dir():
        return MINECRAFT_ASSETS_FOLDER

    version_name = minecraft_version_dir_name(version or DEFAULT_MINECRAFT_VERSION)
    versioned = ASSETS_ROOT / f"minecraft_{version_name}"
    if versioned.is_dir():
        return versioned

    raise FileNotFoundError(
        "Minecraft assets not found. Create assets/minecraft/ or assets/"
        f"minecraft_{version_name}/ — see docs/assets.md."
    )


def resolve_generated_assets_folder() -> Path:
    """Return the sprite bake cache directory, falling back to legacy paths."""
    if GENERATED_ASSETS_FOLDER.is_dir():
        return GENERATED_ASSETS_FOLDER

    if LEGACY_GENERATED_ASSETS_FOLDER.is_dir():
        return LEGACY_GENERATED_ASSETS_FOLDER

    return GENERATED_ASSETS_FOLDER


def resolve_project_custom_folder() -> Path:
    """Return project schematic templates, falling back to legacy custom paths."""
    if PROJECT_CUSTOM_FOLDER.is_dir():
        return PROJECT_CUSTOM_FOLDER

    if LEGACY_PROJECT_CUSTOM_FOLDER.is_dir():
        return LEGACY_PROJECT_CUSTOM_FOLDER

    return PROJECT_CUSTOM_FOLDER


def worldgen_version_from_template_dir_name(dir_name: str) -> str:
    """Convert a worldgen_templates folder name (e.g. ``v26_1_2``) to a version string."""
    if not dir_name.startswith("v"):
        raise ValueError(f"Not a versioned worldgen template folder: {dir_name!r}")
    return dir_name[1:].replace("_", ".")


def list_worldgen_template_versions() -> list[str]:
    """Return Minecraft version strings that have an existing worldgen template folder."""
    if not WORLGEN_TEMPLATES_FOLDER.is_dir():
        return []

    versions: list[str] = []
    for path in sorted(WORLGEN_TEMPLATES_FOLDER.iterdir()):
        if path.is_dir() and path.name.startswith("v"):
            versions.append(worldgen_version_from_template_dir_name(path.name))
    return versions


def resolve_worldgen_template_dir(*, version: str | None = None) -> Path:
    """Return the world template directory for worldgen (versioned under worldgen_templates/)."""
    version_name = minecraft_version_dir_name(version or DEFAULT_WORLGEN_VERSION)
    versioned = WORLGEN_TEMPLATES_FOLDER / f"v{version_name}"

    if versioned.is_dir():
        return versioned

    if LEGACY_TEMPLATE_FOLDER.is_dir():
        return LEGACY_TEMPLATE_FOLDER

    raise FileNotFoundError(
        "Worldgen template not found. Create "
        f"{WORLGEN_TEMPLATES_FOLDER / f'v{version_name}'}/ from a Minecraft world "
        f"(see docs/worldgen.md), or restore legacy {LEGACY_TEMPLATE_FOLDER}/."
    )


def resolve_worldgen_output_dir(output_folder: str, *, version: str | None = None) -> Path:
    """Return the generated world directory (versioned under output/worlds/)."""
    version_name = minecraft_version_dir_name(version or DEFAULT_WORLGEN_VERSION)
    return OUTPUT_WORLDS_FOLDER / output_folder / f"v{version_name}"


def name_slug(name: str) -> str:
    return name.lower().replace(" ", "_")


def schematic_output_path(ctx: SchematicContext, suffix: str) -> Path:
    return ctx.output_schematics_dir / f"{name_slug(ctx.name)}_{suffix}"


def schematic_output_file(ctx: SchematicContext, filename: str) -> Path:
    return ctx.output_schematics_dir / filename
