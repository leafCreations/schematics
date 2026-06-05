from pathlib import Path

import pytest
from PIL import Image

from helpers import constants
from helpers.paths import BLOCK_TEXTURES_FOLDER
from helpers.sprite_baker.compose_door import compose_door, list_door_bake_keys
from helpers.sprite_baker.demo import SpriteBakeError
from registries.loader import build_registry_texture_mapping


def test_registry_mapping_includes_door_halves():
    mapping = build_registry_texture_mapping("top")
    assert "DOOR" in mapping
    assert "DOOR#lower" in mapping
    assert "DOOR#upper" in mapping
    assert not any("#top:" in key for key in list_door_bake_keys("top"))


def test_list_door_bake_keys_are_canonical():
    keys = list_door_bake_keys("top")
    assert "DOOR" in keys
    assert "DOOR#lower" in keys
    assert "DOOR#upper" in keys
    assert "DOOR#top:lower" not in keys


def test_list_door_bake_keys_expands_materials(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    Image.new("RGBA", (16, 16), (200, 100, 50, 255)).save(textures_dir / "oak_door_bottom.png")
    Image.new("RGBA", (16, 16), (20, 20, 20, 255)).save(textures_dir / "spruce_door_bottom.png")

    keys = list_door_bake_keys("top", textures_dir=textures_dir)
    assert "DOOR:oak#lower" in keys
    assert "DOOR:spruce#upper" in keys


def test_list_door_bake_keys_inventory(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    Image.new("RGBA", (16, 16), (200, 100, 50, 255)).save(textures_dir / "oak_door_bottom.png")
    Image.new("RGBA", (16, 16), (20, 20, 20, 255)).save(textures_dir / "oak_door_top.png")

    keys = list_door_bake_keys("inventory", textures_dir=textures_dir)
    assert keys == ["DOOR", "DOOR:oak"]
    assert "DOOR:oak#lower" not in keys


def test_compose_door_inventory_stacks_halves(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()

    door_bottom = Image.new("RGBA", (16, 16), (200, 100, 50, 255))
    door_top = Image.new("RGBA", (16, 16), (20, 20, 20, 255))
    door_bottom.save(textures_dir / "oak_door_bottom.png")
    door_top.save(textures_dir / "oak_door_top.png")

    icon = compose_door(
        key="DOOR:oak",
        view="inventory",
        size=16,
        textures_dir=textures_dir,
    )
    lower = compose_door(key="DOOR:oak#lower", view="side", size=16, textures_dir=textures_dir)
    upper = compose_door(key="DOOR:oak#upper", view="side", size=16, textures_dir=textures_dir)

    assert icon.getpixel((8, 4)) == (20, 20, 20, 255)
    assert icon.getpixel((8, 12)) == (200, 100, 50, 255)
    assert icon.getpixel((8, 4)) == upper.getpixel((8, 4))
    assert icon.getpixel((8, 12)) == lower.getpixel((8, 12))


def test_compose_door_rejects_non_door(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()

    with pytest.raises(SpriteBakeError, match="not a door block"):
        compose_door(
            key="SLAB",
            view="top",
            size=constants.BLOCK_PX,
            textures_dir=textures_dir,
        )


def test_compose_door_top_is_north_edge_strip(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()

    door_bottom = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            door_bottom.putpixel((x, y), (200, 100, 50, 255))
    door_bottom.putpixel((0, 0), (20, 20, 20, 255))
    door_bottom.save(textures_dir / "oak_door_bottom.png")

    top = compose_door(
        key="DOOR",
        view="top",
        size=16,
        textures_dir=textures_dir,
    )

    assert top.getpixel((8, 0)) == (200, 100, 50, 255)
    assert top.getpixel((8, 3)) == (200, 100, 50, 255)
    assert top.getpixel((0, 0)) == (0, 0, 0, 0)
    assert top.getpixel((8, 5)) == (0, 0, 0, 0)


def test_compose_door_top_halves_match(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()

    door_bottom = Image.new("RGBA", (16, 16), (200, 100, 50, 255))
    door_top = Image.new("RGBA", (16, 16), (20, 20, 20, 255))
    door_bottom.save(textures_dir / "oak_door_bottom.png")
    door_top.save(textures_dir / "oak_door_top.png")

    lower = compose_door(key="DOOR#lower", view="top", size=16, textures_dir=textures_dir)
    upper = compose_door(key="DOOR#upper", view="top", size=16, textures_dir=textures_dir)

    assert lower.getpixel((8, 0)) == upper.getpixel((8, 0))
    assert lower.getpixel((8, 4)) == (0, 0, 0, 0)


def test_compose_door_side_halves_differ(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()

    door_bottom = Image.new("RGBA", (16, 16), (200, 100, 50, 255))
    door_top = Image.new("RGBA", (16, 16), (20, 20, 20, 255))
    door_bottom.save(textures_dir / "oak_door_bottom.png")
    door_top.save(textures_dir / "oak_door_top.png")

    lower = compose_door(key="DOOR#lower", view="side", size=16, textures_dir=textures_dir)
    upper = compose_door(key="DOOR#upper", view="side", size=16, textures_dir=textures_dir)

    assert lower.getpixel((8, 8)) == (200, 100, 50, 255)
    assert upper.getpixel((8, 8)) == (20, 20, 20, 255)


@pytest.mark.requires_assets
def test_compose_door_uses_vanilla_textures():
    if not (BLOCK_TEXTURES_FOLDER / "oak_door_bottom.png").exists():
        pytest.skip("oak_door_bottom.png not available")

    image = compose_door(
        key="DOOR:oak@north#lower",
        view="side",
        size=constants.BLOCK_PX,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )

    assert image.size == (constants.BLOCK_PX, constants.BLOCK_PX)
    assert image.getpixel((constants.BLOCK_PX // 2, constants.BLOCK_PX // 2))[3] == 255


@pytest.mark.requires_assets
def test_bake_door_integration(tmp_path: Path):
    if not (BLOCK_TEXTURES_FOLDER / "oak_door_bottom.png").exists():
        pytest.skip("oak_door_bottom.png not available")

    from sprite_baker_test_utils import compile_texture_tokens, generated_assets_root

    from helpers.sprite_baker.cache import load_or_bake

    generated_root = tmp_path / "generated"

    for bake_key in ("DOOR", "DOOR#lower", "DOOR#upper"):
        load_or_bake(
            "top",
            bake_key,
            lambda key=bake_key: compose_door(
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
            ("DOOR",),
        )

    door = textures["DOOR"]
    mid = constants.BLOCK_PX // 2

    assert door.getpixel((mid, 0))[3] == 255
    assert door.getpixel((mid, 3))[3] == 255
    assert door.getpixel((mid, 5))[3] == 0
