from pathlib import Path

import pytest
from PIL import Image

from helpers import constants
from helpers.paths import BLOCK_TEXTURES_FOLDER
from helpers.sprite_baker.compose_wall import compose_wall, list_wall_bake_keys
from helpers.sprite_baker.demo import SpriteBakeError
from registries.loader import build_registry_texture_mapping


def test_registry_mapping_includes_wall_variants():
    mapping = build_registry_texture_mapping("top")
    assert "WALL#post" in mapping
    assert mapping["WALL#post"] == "cobblestone.png"
    assert mapping["WALL#cross"] == "cobblestone.png"


def test_list_wall_bake_keys(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    Image.new("RGBA", (16, 16), (200, 100, 50, 255)).save(textures_dir / "cobblestone.png")

    keys = list_wall_bake_keys("top", textures_dir=textures_dir)
    assert "WALL#post" in keys
    assert "WALL:cobblestone#straight" in keys

    inventory_keys = list_wall_bake_keys("inventory", textures_dir=textures_dir)
    assert "WALL" in inventory_keys
    assert "WALL:cobblestone" in inventory_keys


def test_compose_wall_rejects_non_wall(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()

    with pytest.raises(SpriteBakeError, match="not a wall block"):
        compose_wall(
            key="CHEST",
            view="top",
            size=constants.BLOCK_PX,
            textures_dir=textures_dir,
        )


def test_compose_wall_variants_differ(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    Image.new("RGBA", (16, 16), (200, 100, 50, 255)).save(textures_dir / "teststone.png")

    post = compose_wall(
        key="WALL:teststone#post",
        view="top",
        size=16,
        textures_dir=textures_dir,
    )
    cross = compose_wall(
        key="WALL:teststone#cross",
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


@pytest.mark.requires_assets
def test_compose_wall_post_uses_inventory_model():
    post = compose_wall(
        key="WALL:cobblestone#post",
        view="top",
        size=16,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )
    inventory = compose_wall(
        key="WALL:cobblestone",
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
