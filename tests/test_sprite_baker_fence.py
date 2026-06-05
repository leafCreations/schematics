from pathlib import Path

import pytest
from PIL import Image

from helpers import constants
from helpers.paths import BLOCK_TEXTURES_FOLDER
from helpers.sprite_baker.compose_fence import compose_fence, list_fence_bake_keys
from helpers.sprite_baker.demo import SpriteBakeError
from registries.loader import build_registry_texture_mapping


def test_registry_mapping_includes_fence_variants():
    mapping = build_registry_texture_mapping("top")
    assert "FENCE#post" in mapping
    assert mapping["FENCE#post"] == "oak_fence_inventory.png"
    assert mapping["FENCE#straight"] == "oak_fence_inventory.png"
    assert mapping["FENCE#cross"] == "oak_fence_cross.png"


def test_list_fence_bake_keys(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    Image.new("RGBA", (16, 16), (200, 100, 50, 255)).save(textures_dir / "oak_planks.png")

    keys = list_fence_bake_keys("top", textures_dir=textures_dir)
    assert "FENCE#post" in keys
    assert "FENCE:oak#straight" in keys

    inventory_keys = list_fence_bake_keys("inventory", textures_dir=textures_dir)
    assert inventory_keys == ["FENCE", "FENCE:oak"]


def test_compose_fence_rejects_non_fence(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()

    with pytest.raises(SpriteBakeError, match="not a fence block"):
        compose_fence(
            key="CHEST",
            view="top",
            size=constants.BLOCK_PX,
            textures_dir=textures_dir,
        )


def test_compose_fence_variants_differ(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    planks = Image.new("RGBA", (16, 16), (200, 100, 50, 255))
    planks.save(textures_dir / "testwood_planks.png")

    post = compose_fence(
        key="FENCE:testwood#post",
        view="top",
        size=16,
        textures_dir=textures_dir,
    )
    cross = compose_fence(
        key="FENCE:testwood#cross",
        view="top",
        size=16,
        textures_dir=textures_dir,
    )

    assert post.size == (16, 16)
    assert cross.size == (16, 16)
    assert post.getpixel((8, 8)) != (0, 0, 0, 0)
    assert cross.getpixel((8, 8)) != (0, 0, 0, 0)
    assert post.getpixel((0, 2)) == (0, 0, 0, 0)
    assert cross.getpixel((0, 2)) != (0, 0, 0, 0)


def test_compose_fence_straight_falls_back_to_mask_without_model(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    Image.new("RGBA", (16, 16), (200, 100, 50, 255)).save(textures_dir / "testwood_planks.png")

    straight = compose_fence(
        key="FENCE:testwood#straight",
        view="top",
        size=16,
        textures_dir=textures_dir,
    )

    assert straight.getpixel((8, 0))[3] == 255
    assert straight.getpixel((8, 15))[3] == 255
    assert straight.getpixel((0, 2)) == (0, 0, 0, 0)


@pytest.mark.requires_assets
def test_compose_fence_post_uses_inventory_model():
    post = compose_fence(
        key="FENCE:oak#post",
        view="top",
        size=16,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )
    inventory = compose_fence(
        key="FENCE:oak",
        view="inventory",
        size=16,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )

    assert post.size == (16, 16)
    assert inventory.size == (16, 16)
    assert post.tobytes() != inventory.tobytes()
    assert post.getpixel((8, 8))[3] == 255
    assert inventory.getpixel((8, 8))[3] == 255
    assert post.getpixel((0, 2)) == (0, 0, 0, 0)


@pytest.mark.requires_assets
def test_bake_fence_integration(tmp_path: Path):
    from sprite_baker_test_utils import compile_texture_tokens, generated_assets_root

    from helpers.sprite_baker.cache import load_or_bake

    generated_root = tmp_path / "generated"

    for bake_key in ("FENCE:oak#post", "FENCE:oak#cross"):
        load_or_bake(
            "top",
            bake_key,
            lambda key=bake_key: compose_fence(
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
            ("FENCE:oak#post", "FENCE:oak#cross"),
        )

    assert "FENCE:oak#post" in textures
    assert "FENCE:oak#cross" in textures
