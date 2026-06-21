from pathlib import Path

import pytest
from PIL import Image

from helpers import constants
from helpers.paths import BLOCK_TEXTURES_FOLDER
from helpers.sprite_baker.compose_slab import compose_slab, list_slab_bake_keys
from helpers.sprite_baker.demo import SpriteBakeError
from registries.loader import build_registry_texture_mapping


def test_registry_mapping_includes_slab_top_variant():
    mapping = build_registry_texture_mapping("top")
    assert "SLAB" in mapping
    assert "SLAB#top" in mapping
    assert "SLAB#side" not in mapping


def test_list_slab_bake_keys():
    keys = list_slab_bake_keys("top")
    assert "SLAB" in keys
    assert "SLAB#top" in keys


def test_list_slab_bake_keys_expands_materials(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    Image.new("RGBA", (16, 16), (200, 100, 50, 255)).save(textures_dir / "oak_planks.png")
    Image.new("RGBA", (16, 16), (20, 20, 20, 255)).save(textures_dir / "birch_planks.png")

    keys = list_slab_bake_keys("top", textures_dir=textures_dir)
    assert "SLAB:oak#top" in keys
    assert "SLAB:birch" in keys


def test_list_slab_bake_keys_includes_cobblestone():
    keys = list_slab_bake_keys("top", textures_dir=BLOCK_TEXTURES_FOLDER)
    assert "SLAB:cobblestone" in keys


def test_compose_slab_rejects_non_slab(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()

    with pytest.raises(SpriteBakeError, match="not a slab block"):
        compose_slab(
            key="PLANKS",
            view="top",
            size=constants.BLOCK_PX,
            textures_dir=textures_dir,
        )


def test_compose_slab_bottom_and_top_differ(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()

    planks = Image.new("RGBA", (16, 16), (200, 100, 50, 255))
    planks.save(textures_dir / "oak_planks.png")

    bottom = compose_slab(
        key="SLAB",
        view="top",
        size=16,
        textures_dir=textures_dir,
    )
    top = compose_slab(
        key="SLAB#top",
        view="top",
        size=16,
        textures_dir=textures_dir,
    )

    assert bottom.getpixel((8, 4)) == (0, 0, 0, 0)
    assert bottom.getpixel((8, 12)) == (200, 100, 50, 255)
    assert top.getpixel((8, 4)) == (200, 100, 50, 255)
    assert top.getpixel((8, 12)) == (0, 0, 0, 0)


def test_compose_slab_falls_back_to_base_material_texture(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()

    Image.new("RGBA", (16, 16), (90, 90, 90, 255)).save(textures_dir / "cobblestone.png")

    image = compose_slab(
        key="SLAB:cobblestone",
        view="top",
        size=16,
        textures_dir=textures_dir,
    )

    assert image.getpixel((8, 12))[3] == 255


@pytest.mark.requires_assets
def test_compose_slab_uses_planks_texture():
    if not (BLOCK_TEXTURES_FOLDER / "oak_planks.png").exists():
        pytest.skip("oak_planks.png not available")

    image = compose_slab(
        key="SLAB",
        view="top",
        size=constants.BLOCK_PX,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )

    assert image.size == (constants.BLOCK_PX, constants.BLOCK_PX)
    assert image.getpixel((constants.BLOCK_PX // 2, constants.BLOCK_PX - 1))[3] == 255


@pytest.mark.requires_assets
def test_bake_slab_integration(tmp_path: Path):
    if not (BLOCK_TEXTURES_FOLDER / "oak_planks.png").exists():
        pytest.skip("oak_planks.png not available")

    from sprite_baker_test_utils import compile_texture_tokens, generated_assets_root

    from helpers.sprite_baker.cache import load_or_bake

    generated_root = tmp_path / "generated"

    for bake_key in ("SLAB", "SLAB#top"):
        load_or_bake(
            "top",
            bake_key,
            lambda key=bake_key: compose_slab(
                key=key,
                view="top",
                size=constants.BLOCK_PX,
                textures_dir=BLOCK_TEXTURES_FOLDER,
            ),
            generated_root=generated_root,
            force=True,
        )

    with generated_assets_root(generated_root):
        textures = compile_texture_tokens(
            "top",
            str(BLOCK_TEXTURES_FOLDER),
            constants.BLOCK_PX,
            ("SLAB", "SLAB#top"),
        )

    bottom = textures["SLAB"]
    top = textures["SLAB#top"]
    mid = constants.BLOCK_PX // 2

    assert bottom.getpixel((mid, 10))[3] == 0
    assert bottom.getpixel((mid, constants.BLOCK_PX - 5))[3] == 255
    assert top.getpixel((mid, 5))[3] == 255
    assert top.getpixel((mid, constants.BLOCK_PX - 10))[3] == 0
