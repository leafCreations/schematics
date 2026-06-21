from pathlib import Path

import pytest
from PIL import Image

from helpers import constants
from helpers.paths import BLOCK_TEXTURES_FOLDER
from helpers.sprite_baker.compose_trapdoor import compose_trapdoor, list_trapdoor_bake_keys
from helpers.sprite_baker.demo import SpriteBakeError
from registries.loader import build_registry_texture_mapping


def test_registry_mapping_includes_trapdoor_variants():
    mapping = build_registry_texture_mapping("top")
    assert "TRAPDOOR" in mapping
    assert "TRAPDOOR#top" in mapping


def test_list_trapdoor_bake_keys_expands_materials(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    Image.new("RGBA", (16, 16), (200, 100, 50, 255)).save(textures_dir / "oak_trapdoor.png")
    Image.new("RGBA", (16, 16), (20, 20, 20, 255)).save(textures_dir / "spruce_trapdoor.png")

    keys = list_trapdoor_bake_keys("top", textures_dir=textures_dir)
    assert "TRAPDOOR:oak" in keys
    assert "TRAPDOOR:spruce#top" in keys


def test_list_trapdoor_bake_keys_inventory(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    Image.new("RGBA", (16, 16), (200, 100, 50, 255)).save(textures_dir / "oak_trapdoor.png")

    keys = list_trapdoor_bake_keys("inventory", textures_dir=textures_dir)
    assert "TRAPDOOR" in keys
    assert "TRAPDOOR:oak" in keys
    assert "TRAPDOOR:oak#top" not in keys


def test_compose_trapdoor_top_bottom_halves(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    texture = Image.new("RGBA", (16, 16), (200, 100, 50, 255))
    texture.save(textures_dir / "oak_trapdoor.png")

    bottom = compose_trapdoor(key="TRAPDOOR:oak", view="top", size=16, textures_dir=textures_dir)
    top = compose_trapdoor(key="TRAPDOOR:oak#top", view="top", size=16, textures_dir=textures_dir)

    assert bottom.getpixel((8, 12)) == (200, 100, 50, 255)
    assert bottom.getpixel((8, 4)) == (0, 0, 0, 0)
    assert top.getpixel((8, 4)) == (200, 100, 50, 255)
    assert top.getpixel((8, 12)) == (0, 0, 0, 0)


def test_compose_trapdoor_inventory_is_flat(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    texture = Image.new("RGBA", (16, 16), (200, 100, 50, 255))
    texture.save(textures_dir / "oak_trapdoor.png")

    icon = compose_trapdoor(
        key="TRAPDOOR:oak",
        view="inventory",
        size=16,
        textures_dir=textures_dir,
    )

    assert icon.getpixel((8, 8)) == (200, 100, 50, 255)


def test_compose_trapdoor_waxed_copper_uses_unwaxed_textures(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()

    texture = Image.new("RGBA", (16, 16), (180, 120, 90, 255))
    texture.save(textures_dir / "exposed_copper_trapdoor.png")

    side = compose_trapdoor(
        key="TRAPDOOR:waxed_exposed_copper",
        view="side",
        size=16,
        textures_dir=textures_dir,
    )

    assert side.getpixel((8, 12)) == (180, 120, 90, 255)


def test_list_trapdoor_bake_keys_includes_waxed_copper_materials():
    keys = list_trapdoor_bake_keys("top", textures_dir=Path("/nonexistent"))
    assert "TRAPDOOR:waxed_exposed_copper#top" in keys


def test_compose_trapdoor_rejects_non_trapdoor(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()

    with pytest.raises(SpriteBakeError, match="not a trapdoor block"):
        compose_trapdoor(
            key="SLAB",
            view="top",
            size=constants.BLOCK_PX,
            textures_dir=textures_dir,
        )


@pytest.mark.requires_assets
def test_compose_trapdoor_uses_vanilla_textures():
    if not (BLOCK_TEXTURES_FOLDER / "oak_trapdoor.png").exists():
        pytest.skip("oak_trapdoor.png not available")

    image = compose_trapdoor(
        key="TRAPDOOR:oak@north",
        view="inventory",
        size=constants.BLOCK_PX,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )

    assert image.size == (constants.BLOCK_PX, constants.BLOCK_PX)
    assert image.getpixel((constants.BLOCK_PX // 2, constants.BLOCK_PX // 2))[3] == 255
