from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from helpers.paths import ASSET_FOLDER, BASE_DIR

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


def generate_block_catalog(*, assets_dir: Path = ASSET_FOLDER) -> BlockCatalog:
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
