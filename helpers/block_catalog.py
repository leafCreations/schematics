from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from helpers.minecraft_versions import (
    DEFAULT_STRUCTURE_MINECRAFT_VERSION,
    minecraft_version_at_least,
    normalize_minecraft_version,
)
from helpers.paths import ASSET_FOLDER, BASE_DIR, VERSIONS_ASSETS_FOLDER

CATALOG_PATH = BASE_DIR / "registries" / "generated" / "catalog.json"
SKIP_BLOCKSTATE_STEMS = frozenset({"_all", "_list"})

CatalogEntry = dict[str, Any]
BlockCatalog = dict[str, CatalogEntry]

_catalog_cache: BlockCatalog | None = None


def _title_block_name(block_name: str) -> str:
    return block_name.replace("_", " ").title()


def lang_display_name(lang: dict[str, str], block_name: str) -> str | None:
    for prefix in ("block.minecraft.", "item.minecraft."):
        value = lang.get(f"{prefix}{block_name}")

        if value:
            return value

    return None


def resolve_catalog_texture(textures_dir: Path, block_name: str) -> str | None:
    for filename in (f"{block_name}.png", f"{block_name}_top.png"):
        if (textures_dir / filename).exists():
            return filename

    return None


def _block_stem(block_id: str) -> str:
    return normalize_block_id(block_id).split(":", 1)[-1]


def infer_block_introduced_in(block_id: str, *, entry: CatalogEntry | None = None) -> str:
    """Return the Minecraft version that introduced *block_id*."""
    if entry is not None:
        introduced = entry.get("introduced_in")

        if isinstance(introduced, str) and introduced.strip():
            return normalize_minecraft_version(introduced)

    stem = _block_stem(block_id)

    if "cinnabar" in stem or "sulfur" in stem:
        return "26.2"

    return DEFAULT_STRUCTURE_MINECRAFT_VERSION


def catalog_entry_introduced_in(
    block_id: str,
    *,
    catalog: BlockCatalog | None = None,
) -> str:
    resolved_catalog = load_block_catalog() if catalog is None else catalog
    entry = resolved_catalog.get(normalize_block_id(block_id))
    return infer_block_introduced_in(block_id, entry=entry)


def block_available_in_version(
    block_id: str,
    minecraft_version: str,
    *,
    catalog: BlockCatalog | None = None,
) -> bool:
    """Return whether *block_id* exists in the active catalog for *minecraft_version*."""
    normalized = normalize_block_id(block_id)
    resolved_catalog = load_block_catalog() if catalog is None else catalog
    entry = resolved_catalog.get(normalized)

    if entry is None:
        return False

    introduced_in = catalog_entry_introduced_in(normalized, catalog=resolved_catalog)
    return minecraft_version_at_least(
        structure_version=normalize_minecraft_version(minecraft_version),
        required_version=introduced_in,
    )


def _generate_block_catalog_from_assets(assets_dir: Path) -> BlockCatalog:
    blockstates_dir = assets_dir / "blockstates"
    lang_path = assets_dir / "lang" / "en_us.json"
    textures_dir = assets_dir / "textures" / "block"

    if not blockstates_dir.is_dir():
        raise FileNotFoundError(f"Blockstates folder not found: {blockstates_dir}")

    if not lang_path.is_file():
        raise FileNotFoundError(f"Language file not found: {lang_path}")

    lang = json.loads(lang_path.read_text(encoding="utf-8"))
    catalog: BlockCatalog = {}

    for path in sorted(blockstates_dir.glob("*.json")):
        block_name = path.stem

        if block_name in SKIP_BLOCKSTATE_STEMS:
            continue

        block_id = f"minecraft:{block_name}"
        display_name = lang_display_name(lang, block_name) or _title_block_name(block_name)
        entry: CatalogEntry = {"display_name": display_name}

        texture = resolve_catalog_texture(textures_dir, block_name)

        if texture is not None:
            entry["texture"] = texture

        catalog[block_id] = entry

    return catalog


def _resolve_base_assets_dir() -> Path | None:
    versioned = VERSIONS_ASSETS_FOLDER / "26_1_2" / "minecraft"

    if versioned.is_dir():
        return versioned

    return None


def generate_block_catalog(*, assets_dir: Path = ASSET_FOLDER) -> BlockCatalog:
    base_assets_dir = _resolve_base_assets_dir()
    catalog = _generate_block_catalog_from_assets(assets_dir)

    if base_assets_dir is None or base_assets_dir.resolve() == assets_dir.resolve():
        for block_id, entry in catalog.items():
            entry.setdefault("introduced_in", infer_block_introduced_in(block_id, entry=entry))
        return catalog

    base_catalog = _generate_block_catalog_from_assets(base_assets_dir)

    for block_id, entry in catalog.items():
        if block_id not in base_catalog:
            entry["introduced_in"] = "26.2"
        else:
            entry.setdefault("introduced_in", DEFAULT_STRUCTURE_MINECRAFT_VERSION)

    return catalog


def save_block_catalog(
    catalog: BlockCatalog,
    path: Path = CATALOG_PATH,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(catalog, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def load_block_catalog(path: Path = CATALOG_PATH) -> BlockCatalog:
    global _catalog_cache

    if path == CATALOG_PATH and _catalog_cache is not None:
        return _catalog_cache

    if not path.is_file():
        return {}

    catalog = json.loads(path.read_text(encoding="utf-8"))

    if path == CATALOG_PATH:
        _catalog_cache = catalog

    return catalog


def normalize_block_id(block_id: str) -> str:
    if ":" in block_id:
        return block_id

    return f"minecraft:{block_id}"


def catalog_display_name(
    block_id: str,
    *,
    catalog: BlockCatalog | None = None,
) -> str | None:
    resolved_catalog = load_block_catalog() if catalog is None else catalog
    entry = resolved_catalog.get(normalize_block_id(block_id))

    if entry is None:
        return None

    display_name = entry.get("display_name")

    if isinstance(display_name, str) and display_name:
        return display_name

    return None
