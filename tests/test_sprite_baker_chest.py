from pathlib import Path

import pytest

from helpers import constants
from helpers.paths import (
    BLOCK_TEXTURES_FOLDER,
    ENTITY_CHEST_TEXTURES_FOLDER,
    GENERATED_ASSETS_FOLDER,
)
from helpers.sprite_baker.chest_schematic import CHEST_SINGLE_TEMPLATE_PATH
from helpers.sprite_baker.compose_chest import compose_chest, list_chest_bake_keys
from helpers.sprite_baker.demo import SpriteBakeError
from registries.loader import build_registry_texture_mapping


def test_registry_mapping_includes_chest_parts():
    mapping = build_registry_texture_mapping("top")
    assert "CHEST" in mapping
    assert mapping["CHEST#single"] == "chest_single.png"
    assert mapping["CHEST#left"] == "chest_left.png"
    assert mapping["CHEST#right"] == "chest_right.png"


def test_list_chest_bake_keys():
    keys = list_chest_bake_keys("top")
    assert "CHEST" in keys
    assert "CHEST#single" in keys
    assert "CHEST#left" in keys
    assert "CHEST#right" in keys

    inventory_keys = list_chest_bake_keys("inventory")
    assert inventory_keys == ["CHEST", "CHEST#single"]


def test_compose_chest_rejects_non_chest(tmp_path: Path):
    with pytest.raises(SpriteBakeError, match="not a chest block"):
        compose_chest(
            key="DOOR",
            view="top",
            size=constants.BLOCK_PX,
            textures_dir=tmp_path,
            chest_textures_dir=tmp_path,
        )


def test_compose_chest_top_parts_differ():
    if not CHEST_SINGLE_TEMPLATE_PATH.exists():
        pytest.skip("chest templates not available")

    single = compose_chest(
        key="CHEST#single",
        view="top",
        size=16,
        textures_dir=Path("."),
        chest_textures_dir=ENTITY_CHEST_TEXTURES_FOLDER,
    )
    left = compose_chest(
        key="CHEST#left",
        view="top",
        size=16,
        textures_dir=Path("."),
        chest_textures_dir=ENTITY_CHEST_TEXTURES_FOLDER,
    )
    right = compose_chest(
        key="CHEST#right",
        view="top",
        size=16,
        textures_dir=Path("."),
        chest_textures_dir=ENTITY_CHEST_TEXTURES_FOLDER,
    )

    assert single.size == (16, 16)
    assert left.size == (16, 16)
    assert right.size == (16, 16)
    assert single.getpixel((8, 8)) != left.getpixel((8, 8))
    assert left.getpixel((8, 8)) != right.getpixel((8, 8))


def test_compose_chest_fills_cell():
    if not CHEST_SINGLE_TEMPLATE_PATH.exists():
        pytest.skip("chest templates not available")

    for part in ("single", "left", "right"):
        image = compose_chest(
            key=f"CHEST#{part}",
            view="top",
            size=16,
            textures_dir=Path("."),
            chest_textures_dir=ENTITY_CHEST_TEXTURES_FOLDER,
        )

        for x in (0, 15):
            for y in range(16):
                _, _, _, alpha = image.getpixel((x, y))
                assert alpha == 255, (part, x, y)


def test_compose_chest_side_parts_differ():
    if not (ENTITY_CHEST_TEXTURES_FOLDER / "normal.png").exists():
        pytest.skip("chest entity textures not available")

    single = compose_chest(
        key="CHEST#single",
        view="side",
        size=16,
        textures_dir=Path("."),
        chest_textures_dir=ENTITY_CHEST_TEXTURES_FOLDER,
    )
    left = compose_chest(
        key="CHEST#left",
        view="side",
        size=16,
        textures_dir=Path("."),
        chest_textures_dir=ENTITY_CHEST_TEXTURES_FOLDER,
    )

    assert single.getpixel((8, 8)) != left.getpixel((8, 8))


def test_compose_chest_west_faces_left():
    if not CHEST_SINGLE_TEMPLATE_PATH.exists():
        pytest.skip("chest templates not available")

    from helpers import utils

    single = compose_chest(
        key="CHEST#single",
        view="top",
        size=30,
        textures_dir=Path("."),
        chest_textures_dir=ENTITY_CHEST_TEXTURES_FOLDER,
    )
    west = utils.rotate_directional_texture(single, "W")

    latch_pixels = [
        (x, y)
        for y in range(west.size[1])
        for x in range(west.size[0])
        if west.getpixel((x, y))[3] > 128
        and 100 < max(west.getpixel((x, y))[:3]) < 200
        and min(west.getpixel((x, y))[:3]) > 80
    ]

    assert latch_pixels
    latch_x = sum(point[0] for point in latch_pixels) / len(latch_pixels)
    assert latch_x < west.size[0] / 2


def test_compose_chest_inventory_matches_single():
    if not CHEST_SINGLE_TEMPLATE_PATH.exists():
        pytest.skip("chest templates not available")

    single = compose_chest(
        key="CHEST#single",
        view="top",
        size=16,
        textures_dir=Path("."),
        chest_textures_dir=ENTITY_CHEST_TEXTURES_FOLDER,
    )
    icon = compose_chest(
        key="CHEST",
        view="inventory",
        size=16,
        textures_dir=Path("."),
        chest_textures_dir=ENTITY_CHEST_TEXTURES_FOLDER,
    )

    assert icon.size == single.size
    assert icon.getpixel((8, 8)) == single.getpixel((8, 8))


@pytest.mark.requires_assets
def test_bake_chest_integration(tmp_path: Path):
    if not CHEST_SINGLE_TEMPLATE_PATH.exists():
        pytest.skip("chest templates not available")

    from sprite_baker_test_utils import compile_texture_tokens, generated_assets_root

    from helpers.sprite_baker.cache import load_or_bake

    generated_root = tmp_path / "generated"

    for bake_key in ("CHEST", "CHEST#single", "CHEST#left", "CHEST#right"):
        load_or_bake(
            "top",
            bake_key,
            lambda key=bake_key: compose_chest(
                key=key,
                view="top",
                size=constants.BLOCK_PX,
                textures_dir=Path("."),
                chest_textures_dir=ENTITY_CHEST_TEXTURES_FOLDER,
            ),
            generated_root=generated_root,
            force=True,
        )

    with generated_assets_root(generated_root):
        textures = compile_texture_tokens(
            "top",
            str(Path(".")),
            constants.BLOCK_PX,
            ("CHEST#left", "CHEST#right"),
        )

    mid = constants.BLOCK_PX // 2

    assert textures["CHEST#left"].getpixel((mid, mid))[3] == 255
    assert textures["CHEST#right"].getpixel((mid, mid))[3] == 255
    assert textures["CHEST#left"] is not textures["CHEST#right"]


@pytest.mark.requires_assets
def test_compile_texture_set_loads_baked_chest_variants():
    if not (GENERATED_ASSETS_FOLDER / "top" / "CHEST_left.png").exists():
        pytest.skip("baked chest sprites not available")

    from sprite_baker_test_utils import compile_texture_tokens

    textures = compile_texture_tokens(
        "top",
        str(BLOCK_TEXTURES_FOLDER),
        constants.BLOCK_PX,
        ("CHEST#left", "CHEST#right", "CHEST#single"),
    )

    assert "CHEST#left" in textures
    assert "CHEST#right" in textures
    assert textures["CHEST#left"] is not textures["CHEST#single"]
