from pathlib import Path

import pytest
from PIL import Image

from helpers import constants
from helpers.paths import BLOCK_TEXTURES_FOLDER
from helpers.sprite_baker.compose_simple import (
    compose_simple,
    is_simple_bakeable,
    list_planks_bake_keys,
    list_simple_bake_keys,
    parse_bake_key,
)
from helpers.sprite_baker.demo import SpriteBakeError
from registries.loader import BLOCK_REGISTRY


def test_parse_bake_key_variant():
    parsed = parse_bake_key("COBBLESTONE#mossy")
    assert parsed.token == "COBBLESTONE"
    assert parsed.variant == "mossy"


def test_parse_bake_key_material():
    parsed = parse_bake_key("PLANKS:spruce")
    assert parsed.token == "PLANKS"
    assert parsed.material == "spruce"


def test_is_simple_bakeable_solid_blocks():
    assert is_simple_bakeable(BLOCK_REGISTRY["GRASS"]) is True
    assert is_simple_bakeable(BLOCK_REGISTRY["PLANKS"]) is True
    assert is_simple_bakeable(BLOCK_REGISTRY["FURNACE"]) is True
    assert is_simple_bakeable(BLOCK_REGISTRY["STAIRS"]) is False
    assert is_simple_bakeable(BLOCK_REGISTRY["FENCE"]) is False


def test_list_simple_bake_keys_includes_terrain_blocks():
    keys = list_simple_bake_keys("top")
    assert "GRASS" in keys
    assert "DIRT" in keys
    assert "COBBLESTONE#mossy" in keys
    assert "COBBLESTONE#normal" not in keys
    assert "FURNACE" in keys
    assert "STAIRS#outer_left" not in keys


def test_list_planks_bake_keys_expands_materials(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    Image.new("RGBA", (16, 16), (200, 100, 50, 255)).save(textures_dir / "oak_planks.png")
    Image.new("RGBA", (16, 16), (20, 20, 20, 255)).save(textures_dir / "spruce_planks.png")

    keys = list_planks_bake_keys(textures_dir=textures_dir)
    assert keys == ["PLANKS", "PLANKS:oak", "PLANKS:spruce"]


def test_registry_mapping_skips_default_variant():
    from registries.loader import build_registry_texture_mapping

    mapping = build_registry_texture_mapping("top")
    assert "COBBLESTONE" in mapping
    assert "COBBLESTONE#mossy" in mapping
    assert "COBBLESTONE#normal" not in mapping
    assert "GRASS" in mapping
    assert "GRASS#top" not in mapping
    assert mapping["GRASS"] == "grass_block_top.png"
    assert "CRAFTING_TABLE" in mapping
    assert "CRAFTING_TABLE#top" not in mapping
    assert mapping["CRAFTING_TABLE"] == "crafting_table_top.png"
    assert "FURNACE" in mapping
    assert mapping["FURNACE"] == "furnace_front.png"
    assert "TORCH#soul" in mapping
    assert "TORCH#normal" not in mapping
    assert "CHEST#left" in mapping


def test_compose_simple_rejects_non_simple_block(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()

    with pytest.raises(SpriteBakeError, match="not a flat texture block"):
        compose_simple(
            key="STAIRS",
            view="top",
            size=constants.BLOCK_PX,
            textures_dir=textures_dir,
        )


@pytest.mark.requires_assets
def test_compose_simple_grass_uses_top_texture_and_tint():
    if not (BLOCK_TEXTURES_FOLDER / "grass_block_top.png").exists():
        pytest.skip("grass_block_top.png not available")

    image = compose_simple(
        key="GRASS",
        view="top",
        size=constants.BLOCK_PX,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )

    plain_top = Image.open(BLOCK_TEXTURES_FOLDER / "grass_block_top.png").convert("RGBA")
    plain_top = plain_top.resize((constants.BLOCK_PX, constants.BLOCK_PX), Image.Resampling.NEAREST)

    assert image.size == (constants.BLOCK_PX, constants.BLOCK_PX)
    assert image.getpixel((0, 0)) != plain_top.getpixel((0, 0))


@pytest.mark.requires_assets
def test_compose_simple_planks_uses_oak_planks():
    if not (BLOCK_TEXTURES_FOLDER / "oak_planks.png").exists():
        pytest.skip("oak_planks.png not available")

    image = compose_simple(
        key="PLANKS",
        view="top",
        size=constants.BLOCK_PX,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )
    expected = Image.open(BLOCK_TEXTURES_FOLDER / "oak_planks.png").convert("RGBA")
    expected = expected.resize((constants.BLOCK_PX, constants.BLOCK_PX), Image.Resampling.NEAREST)

    assert image.getpixel((0, 0)) == expected.getpixel((0, 0))


@pytest.mark.requires_assets
def test_compose_simple_cobblestone_mossy_variant():
    if not (BLOCK_TEXTURES_FOLDER / "mossy_cobblestone.png").exists():
        pytest.skip("mossy_cobblestone.png not available")

    image = compose_simple(
        key="COBBLESTONE#mossy",
        view="top",
        size=constants.BLOCK_PX,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )
    expected = Image.open(BLOCK_TEXTURES_FOLDER / "mossy_cobblestone.png").convert("RGBA")
    expected = expected.resize((constants.BLOCK_PX, constants.BLOCK_PX), Image.Resampling.NEAREST)

    assert image.getpixel((0, 0)) == expected.getpixel((0, 0))


@pytest.mark.requires_assets
def test_compose_simple_furnace_uses_front_texture():
    if not (BLOCK_TEXTURES_FOLDER / "furnace_front.png").exists():
        pytest.skip("furnace_front.png not available")

    image = compose_simple(
        key="FURNACE",
        view="top",
        size=constants.BLOCK_PX,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )
    expected = Image.open(BLOCK_TEXTURES_FOLDER / "furnace_front.png").convert("RGBA")
    expected = expected.resize((constants.BLOCK_PX, constants.BLOCK_PX), Image.Resampling.NEAREST)

    assert image.getpixel((0, 0)) == expected.getpixel((0, 0))


@pytest.mark.requires_assets
def test_bake_simple_grass_integration(tmp_path: Path):
    if not (BLOCK_TEXTURES_FOLDER / "grass_block_top.png").exists():
        pytest.skip("grass_block_top.png not available")

    from helpers.sprite_baker.cache import load_or_bake
    from registries.loader import compile_texture_set

    generated_root = tmp_path / "generated"

    load_or_bake(
        "top",
        "GRASS",
        lambda: compose_simple(
            key="GRASS",
            view="top",
            size=constants.BLOCK_PX,
            textures_dir=BLOCK_TEXTURES_FOLDER,
        ),
        generated_root=generated_root,
        force=True,
    )

    import registries.loader as loader_module

    previous_root = loader_module.GENERATED_ASSETS_FOLDER
    loader_module.GENERATED_ASSETS_FOLDER = generated_root

    try:
        textures = compile_texture_set(
            "top",
            str(BLOCK_TEXTURES_FOLDER),
            block_px=constants.BLOCK_PX,
        )
    finally:
        loader_module.GENERATED_ASSETS_FOLDER = previous_root

    grass = textures["GRASS"]
    planks = textures["PLANKS"]
    assert grass.getpixel((0, 0)) != planks.getpixel((0, 0))
