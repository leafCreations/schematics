from helpers.catalog_texture_exceptions import (
    catalog_block_background_color,
    catalog_block_texture_name,
    is_catalog_block_texture_exception,
)


def test_water_and_lava_are_render_overrides():
    assert is_catalog_block_texture_exception("minecraft:water")
    assert is_catalog_block_texture_exception("minecraft:lava")
    assert is_catalog_block_texture_exception("minecraft:grass_block")
    assert not is_catalog_block_texture_exception("minecraft:stone")


def test_catalog_block_texture_name():
    assert catalog_block_texture_name("minecraft:water") == "water_still.png"
    assert catalog_block_texture_name("minecraft:lava") == "lava_still.png"
    assert catalog_block_texture_name("minecraft:grass_block") is None
    assert catalog_block_texture_name("minecraft:stone") is None


def test_catalog_block_background_color():
    assert catalog_block_background_color("minecraft:grass_block") == (85, 255, 85)
    assert catalog_block_background_color("minecraft:water") == (63, 118, 228)
    assert catalog_block_background_color("minecraft:lava") == (207, 92, 15)
    assert catalog_block_background_color("minecraft:stone") is None
