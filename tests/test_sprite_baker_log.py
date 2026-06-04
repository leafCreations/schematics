from pathlib import Path

import pytest

from helpers import constants
from helpers.paths import BLOCK_TEXTURES_FOLDER
from helpers.sprite_baker.compose_log import compose_log, list_log_bake_keys
from helpers.sprite_baker.demo import SpriteBakeError
from registries.loader import compile_texture_set


def test_list_log_bake_keys(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    (textures_dir / "oak_log_top.png").write_bytes(b"png")
    (textures_dir / "oak_log.png").write_bytes(b"png")

    keys = list_log_bake_keys("top", textures_dir=textures_dir)

    assert "LOG:oak" in keys
    assert "LOG:oak#east_west" in keys
    assert "LOG#north_south" in keys


def test_compose_log_rejects_non_log():
    with pytest.raises(SpriteBakeError, match="not a log block"):
        compose_log(
            key="TORCH",
            view="top",
            size=constants.BLOCK_PX,
            textures_dir=BLOCK_TEXTURES_FOLDER,
        )


@pytest.mark.requires_assets
def test_compose_log_vertical_top_uses_log_top():
    image = compose_log(
        key="LOG:oak",
        view="top",
        size=16,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )
    horizontal = compose_log(
        key="LOG:oak#east_west",
        view="top",
        size=16,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )

    assert image.size == (16, 16)
    assert image.getpixel((8, 8))[3] == 255
    assert horizontal.tobytes() != image.tobytes()


@pytest.mark.requires_assets
def test_compose_log_side_uses_bark():
    image = compose_log(
        key="LOG:oak",
        view="side",
        size=16,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )

    assert image.getpixel((8, 8))[3] == 255


@pytest.mark.requires_assets
def test_bake_log_integration(tmp_path: Path):
    from helpers.sprite_baker.cache import load_or_bake

    generated_root = tmp_path / "generated"

    for bake_key in ("LOG:oak", "LOG:oak#east_west"):
        load_or_bake(
            "top",
            bake_key,
            lambda key=bake_key: compose_log(
                key=key,
                view="top",
                size=constants.BLOCK_PX,
                textures_dir=BLOCK_TEXTURES_FOLDER,
            ),
            generated_root=generated_root,
            force=True,
        )

    import helpers.paths as paths_module
    import registries.loader as loader_module

    previous_paths_root = paths_module.GENERATED_ASSETS_FOLDER
    previous_loader_root = loader_module.GENERATED_ASSETS_FOLDER
    paths_module.GENERATED_ASSETS_FOLDER = generated_root
    loader_module.GENERATED_ASSETS_FOLDER = generated_root

    try:
        textures = compile_texture_set(
            "top",
            str(BLOCK_TEXTURES_FOLDER),
            block_px=constants.BLOCK_PX,
        )
    finally:
        paths_module.GENERATED_ASSETS_FOLDER = previous_paths_root
        loader_module.GENERATED_ASSETS_FOLDER = previous_loader_root

    assert "LOG:oak" in textures
    assert "LOG:oak#east_west" in textures
    assert textures["LOG:oak"].getpixel((15, 15))[3] == 255
