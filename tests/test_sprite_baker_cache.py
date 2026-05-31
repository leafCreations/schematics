from pathlib import Path

import pytest
from PIL import Image

from helpers import constants
from helpers.paths import BLOCK_TEXTURES_FOLDER
from helpers.sprite_baker.cache import (
    cache_path,
    load_cached,
    load_generated_sprite,
    load_or_bake,
    sanitize_cache_key,
    save_cached,
)
from helpers.sprite_baker.demo import SpriteBakeError, bake_texture_file
from helpers.sprite_baker.registry import get_composer, register_composer


def test_sanitize_cache_key():
    assert sanitize_cache_key("STAIRS:oak@north#outer_left") == "STAIRS_oak_at_north_outer_left"


def test_cache_path_is_deterministic(tmp_path: Path):
    first = cache_path("top", "PLANKS", generated_root=tmp_path)
    second = cache_path("top", "PLANKS", generated_root=tmp_path)
    assert first == second
    assert first == tmp_path / "top" / "PLANKS.png"


def test_load_or_bake_writes_png_and_reuses(tmp_path: Path):
    calls = {"count": 0}

    def bake_fn() -> Image.Image:
        calls["count"] += 1
        return Image.new("RGBA", (constants.BLOCK_PX, constants.BLOCK_PX), (10, 20, 30, 255))

    first = load_or_bake("top", "PLANKS", bake_fn, generated_root=tmp_path)
    second = load_or_bake("top", "PLANKS", bake_fn, generated_root=tmp_path)

    assert calls["count"] == 1
    assert first.size == (constants.BLOCK_PX, constants.BLOCK_PX)
    assert first.mode == "RGBA"
    assert second.getpixel((0, 0)) == (10, 20, 30, 255)
    assert load_cached("top", "PLANKS", generated_root=tmp_path) is not None


def test_load_or_bake_force_rebakes(tmp_path: Path):
    calls = {"count": 0}

    def bake_fn() -> Image.Image:
        calls["count"] += 1
        color = (calls["count"] * 10, 0, 0, 255)
        return Image.new("RGBA", (constants.BLOCK_PX, constants.BLOCK_PX), color)

    load_or_bake("top", "PLANKS", bake_fn, generated_root=tmp_path)
    rebaked = load_or_bake("top", "PLANKS", bake_fn, generated_root=tmp_path, force=True)

    assert calls["count"] == 2
    assert rebaked.getpixel((0, 0)) == (20, 0, 0, 255)


def test_load_generated_sprite_resizes_when_needed(tmp_path: Path):
    grass = Image.new("RGBA", (16, 16), (0, 255, 0, 255))
    save_cached("top", "GRASS", grass, generated_root=tmp_path)

    sprite = load_generated_sprite(
        "top",
        "GRASS",
        block_px=constants.BLOCK_PX,
        generated_root=tmp_path,
    )

    assert sprite is not None
    assert sprite.size == (constants.BLOCK_PX, constants.BLOCK_PX)


def test_bake_texture_file_raises_for_missing_source(tmp_path: Path):
    with pytest.raises(SpriteBakeError, match="Texture source not found"):
        bake_texture_file(tmp_path / "missing.png", constants.BLOCK_PX)


def test_registry_composer_lookup():
    def composer(*, size: int, **_kwargs) -> Image.Image:
        return Image.new("RGBA", (size, size), (255, 0, 0, 255))

    register_composer("solid", composer)
    assert get_composer("solid") is composer
    assert get_composer("nonexistent_behavior") is None


@pytest.mark.requires_assets
def test_compile_texture_set_prefers_generated_sprite(tmp_path: Path):
    from registries.loader import compile_texture_set

    generated_root = tmp_path / "generated"
    assets_dir = tmp_path / "textures" / "block"
    assets_dir.mkdir(parents=True)

    vanilla = Image.new("RGBA", (16, 16), (0, 0, 255, 255))
    vanilla.save(assets_dir / "oak_planks.png")

    generated = Image.new("RGBA", (constants.BLOCK_PX, constants.BLOCK_PX), (255, 0, 0, 255))
    save_cached("top", "PLANKS", generated, generated_root=generated_root)

    import helpers.paths as paths_module
    import registries.loader as loader_module

    previous_paths_root = paths_module.GENERATED_ASSETS_FOLDER
    previous_loader_root = loader_module.GENERATED_ASSETS_FOLDER
    paths_module.GENERATED_ASSETS_FOLDER = generated_root
    loader_module.GENERATED_ASSETS_FOLDER = generated_root

    try:
        textures = compile_texture_set("top", str(assets_dir), block_px=constants.BLOCK_PX)
    finally:
        paths_module.GENERATED_ASSETS_FOLDER = previous_paths_root
        loader_module.GENERATED_ASSETS_FOLDER = previous_loader_root

    assert "PLANKS" in textures
    assert textures["PLANKS"].getpixel((0, 0)) == (255, 0, 0, 255)


@pytest.mark.requires_assets
def test_bake_demo_planks_integration(tmp_path: Path):
    if not (BLOCK_TEXTURES_FOLDER / "oak_planks.png").exists():
        pytest.skip("assets/textures/block/oak_planks.png not available")

    from registries.loader import compile_texture_set

    generated_root = tmp_path / "generated"
    image = load_or_bake(
        "top",
        "PLANKS",
        lambda: bake_texture_file(BLOCK_TEXTURES_FOLDER / "oak_planks.png", constants.BLOCK_PX),
        generated_root=generated_root,
    )

    assert image.size == (constants.BLOCK_PX, constants.BLOCK_PX)

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

    assert textures["PLANKS"].getpixel((0, 0)) == image.getpixel((0, 0))
