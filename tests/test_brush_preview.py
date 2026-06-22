import pytest
from PIL import Image

from helpers.brush_preview import clear_brush_preview_cache, load_brush_preview_image
from helpers.paths import BLOCK_TEXTURES_FOLDER, ITEM_TEXTURES_FOLDER
from helpers.utils_schematics import resolve_cell_texture
from registries.loader import compile_texture_set


@pytest.mark.requires_assets
def test_brush_preview_uses_item_texture_for_campfire():
    if not (ITEM_TEXTURES_FOLDER / "campfire.png").is_file():
        pytest.skip("campfire item texture not available")

    clear_brush_preview_cache()
    preview = load_brush_preview_image("minecraft:campfire@north;lit=true", 48)
    item = (
        Image.open(ITEM_TEXTURES_FOLDER / "campfire.png")
        .convert("RGBA")
        .resize(
            (48, 48),
            Image.Resampling.NEAREST,
        )
    )

    assert preview is not None
    assert preview.tobytes() == item.tobytes()


@pytest.mark.requires_assets
def test_brush_preview_differs_from_grid_baked_sprite_for_campfire():
    if not (ITEM_TEXTURES_FOLDER / "campfire.png").is_file():
        pytest.skip("campfire item texture not available")

    clear_brush_preview_cache()
    token = "minecraft:campfire@north;lit=true"
    preview = load_brush_preview_image(token, 48)
    textures = compile_texture_set("top", str(BLOCK_TEXTURES_FOLDER), 48)
    grid = resolve_cell_texture(token, textures, view="top", size=48)

    assert preview is not None
    assert grid is not None
    assert preview.tobytes() != grid.tobytes()


@pytest.mark.requires_assets
def test_brush_preview_soul_campfire_uses_item_texture():
    if not (ITEM_TEXTURES_FOLDER / "soul_campfire.png").is_file():
        pytest.skip("soul_campfire item texture not available")

    clear_brush_preview_cache()
    preview = load_brush_preview_image("minecraft:soul_campfire@north;lit=true", 48)
    item = (
        Image.open(ITEM_TEXTURES_FOLDER / "soul_campfire.png")
        .convert("RGBA")
        .resize(
            (48, 48),
            Image.Resampling.NEAREST,
        )
    )

    assert preview is not None
    assert preview.tobytes() == item.tobytes()


@pytest.mark.requires_assets
def test_brush_preview_falls_back_to_block_texture_for_stone():
    if not (BLOCK_TEXTURES_FOLDER / "stone.png").is_file():
        pytest.skip("stone block texture not available")

    clear_brush_preview_cache()
    preview = load_brush_preview_image("minecraft:stone", 48)

    assert preview is not None
    assert preview.getbbox() is not None


@pytest.mark.requires_assets
def test_brush_preview_uses_block_texture_for_water_and_lava():
    if not (BLOCK_TEXTURES_FOLDER / "water_still.png").is_file():
        pytest.skip("water_still block texture not available")
    if not (BLOCK_TEXTURES_FOLDER / "lava_still.png").is_file():
        pytest.skip("lava_still block texture not available")

    clear_brush_preview_cache()

    for token, texture_name, _tint in (
        ("minecraft:water", "water_still.png", (63, 118, 228)),
        ("minecraft:lava", "lava_still.png", (207, 92, 15)),
    ):
        preview = load_brush_preview_image(token, 48)
        plain = (
            Image.open(BLOCK_TEXTURES_FOLDER / texture_name)
            .convert("RGBA")
            .resize(
                (48, 48),
                Image.Resampling.NEAREST,
            )
        )

        assert preview is not None
        assert preview.tobytes() != plain.tobytes()
        assert preview.getpixel((24, 24)) != plain.getpixel((24, 24))


@pytest.mark.requires_assets
def test_brush_preview_grass_has_green_tint():
    if not (BLOCK_TEXTURES_FOLDER / "grass_block_top.png").is_file():
        pytest.skip("grass_block_top.png not available")

    clear_brush_preview_cache()
    preview = load_brush_preview_image("minecraft:grass_block", 48)
    plain = (
        Image.open(BLOCK_TEXTURES_FOLDER / "grass_block_top.png")
        .convert("RGBA")
        .resize(
            (48, 48),
            Image.Resampling.NEAREST,
        )
    )

    assert preview is not None
    assert preview.tobytes() != plain.tobytes()


@pytest.mark.requires_assets
def test_grid_cell_texture_for_water_and_lava():
    if not (BLOCK_TEXTURES_FOLDER / "water_still.png").is_file():
        pytest.skip("water_still block texture not available")

    textures = compile_texture_set("top", str(BLOCK_TEXTURES_FOLDER), 48)

    for token, texture_name in (
        ("minecraft:water", "water_still.png"),
        ("minecraft:lava", "lava_still.png"),
    ):
        grid = resolve_cell_texture(token, textures, view="top", size=48)
        plain = (
            Image.open(BLOCK_TEXTURES_FOLDER / texture_name)
            .convert("RGBA")
            .resize(
                (48, 48),
                Image.Resampling.NEAREST,
            )
        )

        assert grid is not None
        assert grid.getbbox() is not None
        assert grid.tobytes() != plain.tobytes()


@pytest.mark.requires_assets
def test_grid_cell_texture_grass_has_green_tint():
    if not (BLOCK_TEXTURES_FOLDER / "grass_block_top.png").is_file():
        pytest.skip("grass_block_top.png not available")

    textures = compile_texture_set("top", str(BLOCK_TEXTURES_FOLDER), 48)
    grid = resolve_cell_texture("minecraft:grass_block", textures, view="top", size=48)
    plain = (
        Image.open(BLOCK_TEXTURES_FOLDER / "grass_block_top.png")
        .convert("RGBA")
        .resize(
            (48, 48),
            Image.Resampling.NEAREST,
        )
    )

    assert grid is not None
    assert grid.tobytes() != plain.tobytes()
