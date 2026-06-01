from pathlib import Path

from helpers.block_catalog import (
    catalog_display_name,
    generate_block_catalog,
    lang_display_name,
    load_block_catalog,
    normalize_block_id,
    resolve_catalog_texture,
    save_block_catalog,
)


def test_lang_display_name_prefers_block_key():
    lang = {
        "block.minecraft.stone": "Stone",
        "item.minecraft.stone": "Stone Item",
    }

    assert lang_display_name(lang, "stone") == "Stone"


def test_lang_display_name_falls_back_to_item_key():
    lang = {"item.minecraft.oak_boat": "Oak Boat"}

    assert lang_display_name(lang, "oak_boat") == "Oak Boat"


def test_resolve_catalog_texture_prefers_block_png(tmp_path: Path):
    textures_dir = tmp_path / "textures" / "block"
    textures_dir.mkdir(parents=True)
    (textures_dir / "stone.png").write_bytes(b"png")

    assert resolve_catalog_texture(textures_dir, "stone") == "stone.png"


def test_resolve_catalog_texture_falls_back_to_top_texture(tmp_path: Path):
    textures_dir = tmp_path / "textures" / "block"
    textures_dir.mkdir(parents=True)
    (textures_dir / "grass_block_top.png").write_bytes(b"png")

    assert resolve_catalog_texture(textures_dir, "grass_block") == "grass_block_top.png"


def test_generate_block_catalog_from_assets(tmp_path: Path):
    assets_dir = tmp_path / "assets"
    (assets_dir / "blockstates").mkdir(parents=True)
    (assets_dir / "lang").mkdir()
    (assets_dir / "textures" / "block").mkdir(parents=True)

    (assets_dir / "blockstates" / "stone.json").write_text("{}", encoding="utf-8")
    (assets_dir / "blockstates" / "oak_planks.json").write_text("{}", encoding="utf-8")
    (assets_dir / "textures" / "block" / "stone.png").write_bytes(b"png")
    (assets_dir / "lang" / "en_us.json").write_text(
        '{"block.minecraft.stone":"Stone","block.minecraft.oak_planks":"Oak Planks"}',
        encoding="utf-8",
    )

    catalog = generate_block_catalog(assets_dir=assets_dir)

    assert catalog["minecraft:stone"] == {"display_name": "Stone", "texture": "stone.png"}
    assert catalog["minecraft:oak_planks"] == {"display_name": "Oak Planks"}


def test_save_and_load_block_catalog(tmp_path: Path):
    catalog = {"minecraft:stone": {"display_name": "Stone"}}

    path = save_block_catalog(catalog, path=tmp_path / "catalog.json")
    loaded = load_block_catalog(path=path)

    assert loaded == catalog
    assert catalog_display_name("minecraft:stone", catalog=loaded) == "Stone"


def test_normalize_block_id():
    assert normalize_block_id("stone") == "minecraft:stone"
    assert normalize_block_id("minecraft:stone") == "minecraft:stone"
