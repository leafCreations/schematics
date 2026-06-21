from pathlib import Path

import pytest
from PIL import Image

from helpers import constants
from helpers.paths import BLOCK_TEXTURES_FOLDER
from helpers.sprite_baker.compose_stairs import compose_stairs, list_stairs_bake_keys
from helpers.sprite_baker.demo import SpriteBakeError
from helpers.sprite_baker.stair_shapes import build_stair_top_mask
from registries.loader import BLOCK_REGISTRY, build_registry_texture_mapping


def test_registry_mapping_includes_stair_shapes():
    mapping = build_registry_texture_mapping("top")
    assert mapping["STAIRS"] == "oak_planks.png"
    assert "STAIRS#outer_left" in mapping
    assert "STAIRS#top:outer_left" in mapping
    assert not any("#top:" in key for key in list_stairs_bake_keys("top"))


def test_list_stairs_bake_keys_are_canonical():
    keys = list_stairs_bake_keys("top")
    assert "STAIRS" in keys
    assert "STAIRS#outer_left" in keys
    assert "STAIRS#straight" not in keys
    assert "STAIRS#top:outer_left" not in keys


def test_list_stairs_bake_keys_expands_materials(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    Image.new("RGBA", (16, 16), (200, 100, 50, 255)).save(textures_dir / "oak_planks.png")
    Image.new("RGBA", (16, 16), (20, 20, 20, 255)).save(textures_dir / "spruce_planks.png")

    keys = list_stairs_bake_keys("top", textures_dir=textures_dir)
    assert "STAIRS:oak#outer_left" in keys
    assert "STAIRS:spruce" in keys


def test_stair_top_masks_differ_by_shape():
    size = 16
    straight = build_stair_top_mask(size, "straight")
    outer_left = build_stair_top_mask(size, "outer_left")
    assert straight.getpixel((4, 4)) == 0
    assert straight.getpixel((12, 4)) == 0
    assert outer_left.getpixel((4, 4)) == 0
    assert outer_left.getpixel((12, 4)) == 255


def test_compose_stairs_rejects_non_stairs(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()

    with pytest.raises(SpriteBakeError, match="not a stairs block"):
        compose_stairs(
            key="SLAB",
            view="top",
            size=constants.BLOCK_PX,
            textures_dir=textures_dir,
        )


def test_compose_stairs_shapes_differ(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()

    planks = Image.new("RGBA", (16, 16), (200, 100, 50, 255))
    planks.save(textures_dir / "oak_planks.png")

    straight = compose_stairs(
        key="STAIRS",
        view="top",
        size=16,
        textures_dir=textures_dir,
    )
    outer_left = compose_stairs(
        key="STAIRS#outer_left",
        view="top",
        size=16,
        textures_dir=textures_dir,
    )

    assert straight.getpixel((4, 4))[3] == 0
    assert straight.getpixel((12, 12))[3] == 255
    assert outer_left.getpixel((4, 4))[3] == 0


def test_compose_stairs_falls_back_to_base_material_texture(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()

    Image.new("RGBA", (16, 16), (80, 80, 80, 255)).save(textures_dir / "cobblestone.png")

    image = compose_stairs(
        key="STAIRS:cobblestone",
        view="top",
        size=16,
        textures_dir=textures_dir,
    )

    assert image.getpixel((8, 12))[3] == 255


@pytest.mark.requires_assets
def test_compose_stairs_uses_planks_texture():
    if not (BLOCK_TEXTURES_FOLDER / "oak_planks.png").exists():
        pytest.skip("oak_planks.png not available")

    image = compose_stairs(
        key="STAIRS",
        view="top",
        size=constants.BLOCK_PX,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )

    assert image.size == (constants.BLOCK_PX, constants.BLOCK_PX)
    assert image.getpixel((constants.BLOCK_PX // 2, constants.BLOCK_PX // 2))[3] == 255


@pytest.mark.requires_assets
def test_bake_stairs_integration(tmp_path: Path):
    if not (BLOCK_TEXTURES_FOLDER / "oak_planks.png").exists():
        pytest.skip("oak_planks.png not available")

    from sprite_baker_test_utils import compile_texture_tokens, generated_assets_root

    from helpers.sprite_baker.cache import load_or_bake

    generated_root = tmp_path / "generated"

    for bake_key in ("STAIRS", "STAIRS#outer_left"):
        load_or_bake(
            "top",
            bake_key,
            lambda key=bake_key: compose_stairs(
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
            ("STAIRS", "STAIRS#outer_left"),
        )

    assert textures["STAIRS"].getpixel((5, 20))[3] == 255
    assert textures["STAIRS"].getpixel((5, 5))[3] == 0
    assert textures["STAIRS#outer_left"].getpixel((5, 5))[3] == 0

    entry = BLOCK_REGISTRY["STAIRS"]
    assert entry.get("behavior") == "stairs"
