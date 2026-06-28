from pathlib import Path

import pytest

from helpers import constants
from helpers.paths import (
    BLOCK_TEXTURES_FOLDER,
    ENTITY_BED_TEXTURES_FOLDER,
    GENERATED_ASSETS_FOLDER,
)
from helpers.sprite_baker.bed_schematic import BED_TOP_TEMPLATE_PATH
from helpers.sprite_baker.compose_bed import compose_bed, list_bed_bake_keys
from helpers.sprite_baker.demo import SpriteBakeError
from registries.loader import build_registry_texture_mapping


def test_registry_mapping_includes_bed_parts():
    mapping = build_registry_texture_mapping("top")
    assert "BED" in mapping
    assert "BED#head" in mapping
    assert "BED#foot" in mapping


def test_list_bed_bake_keys():
    keys = list_bed_bake_keys("top")
    assert "BED" in keys
    assert "BED#head" in keys
    assert "BED:red#head" in keys
    assert "BED:blue#head" in keys

    inventory_keys = list_bed_bake_keys("inventory")
    assert "BED" in inventory_keys
    assert "BED:red" in inventory_keys
    assert "BED:blue" in inventory_keys


def test_compose_bed_uses_token_color():
    if not BED_TOP_TEMPLATE_PATH.exists():
        pytest.skip("bed top template not available")
    if not (ENTITY_BED_TEXTURES_FOLDER / "black.png").exists():
        pytest.skip("black bed entity texture not available")
    if not (ENTITY_BED_TEXTURES_FOLDER / "red.png").exists():
        pytest.skip("red bed entity texture not available")

    black_head = compose_bed(
        key="BED:black#head",
        view="top",
        size=16,
        textures_dir=Path("."),
        bed_textures_dir=ENTITY_BED_TEXTURES_FOLDER,
    )
    red_head = compose_bed(
        key="BED:red#head",
        view="top",
        size=16,
        textures_dir=Path("."),
        bed_textures_dir=ENTITY_BED_TEXTURES_FOLDER,
    )

    assert black_head.getpixel((8, 12)) != red_head.getpixel((8, 12))


def test_compose_bed_fills_cell():
    if not BED_TOP_TEMPLATE_PATH.exists():
        pytest.skip("bed top template not available")
    if not (ENTITY_BED_TEXTURES_FOLDER / "black.png").exists():
        pytest.skip("black bed entity texture not available")

    for part in ("head", "foot"):
        image = compose_bed(
            key=f"BED:black#{part}",
            view="top",
            size=16,
            textures_dir=Path("."),
            bed_textures_dir=ENTITY_BED_TEXTURES_FOLDER,
        )

        for x in (0, 15):
            for y in range(16):
                _, _, _, alpha = image.getpixel((x, y))
                assert alpha == 255, (part, x, y)


def test_compose_bed_recolors_all_blanket_pixels():
    if not BED_TOP_TEMPLATE_PATH.exists():
        pytest.skip("bed top template not available")
    if not (ENTITY_BED_TEXTURES_FOLDER / "black.png").exists():
        pytest.skip("black bed entity texture not available")

    head = compose_bed(
        key="BED:black#head",
        view="top",
        size=16,
        textures_dir=Path("."),
        bed_textures_dir=ENTITY_BED_TEXTURES_FOLDER,
    )

    for y in range(16):
        for x in range(16):
            red, green, blue, alpha = head.getpixel((x, y))
            if alpha < 128:
                continue
            if red > 180 and green > 180 and blue > 180:
                continue
            assert not (red > 140 and green < 80 and blue < 80), (x, y, head.getpixel((x, y)))


def test_compose_bed_rejects_non_bed(tmp_path: Path):
    with pytest.raises(SpriteBakeError, match="not a bed block"):
        compose_bed(
            key="DOOR",
            view="top",
            size=constants.BLOCK_PX,
            textures_dir=tmp_path,
            bed_textures_dir=tmp_path,
        )


def test_compose_bed_top_parts_differ():
    if not BED_TOP_TEMPLATE_PATH.exists():
        pytest.skip("bed top template not available")
    if not (ENTITY_BED_TEXTURES_FOLDER / "red.png").exists():
        pytest.skip("red bed entity texture not available")

    head = compose_bed(
        key="BED#head",
        view="top",
        size=16,
        textures_dir=Path("."),
        bed_textures_dir=ENTITY_BED_TEXTURES_FOLDER,
    )
    foot = compose_bed(
        key="BED#foot",
        view="top",
        size=16,
        textures_dir=Path("."),
        bed_textures_dir=ENTITY_BED_TEXTURES_FOLDER,
    )

    assert head.getpixel((8, 4)) != foot.getpixel((8, 8))


def test_compose_bed_side_parts_differ():
    if not BED_TOP_TEMPLATE_PATH.exists():
        pytest.skip("bed templates not available")
    if not (ENTITY_BED_TEXTURES_FOLDER / "red.png").exists():
        pytest.skip("red bed entity texture not available")

    head = compose_bed(
        key="BED#head",
        view="side",
        size=16,
        textures_dir=Path("."),
        bed_textures_dir=ENTITY_BED_TEXTURES_FOLDER,
    )
    foot = compose_bed(
        key="BED#foot",
        view="side",
        size=16,
        textures_dir=Path("."),
        bed_textures_dir=ENTITY_BED_TEXTURES_FOLDER,
    )

    assert head.getpixel((8, 8)) != foot.getpixel((8, 8))


def test_compose_bed_inventory_stacks_halves():
    if not BED_TOP_TEMPLATE_PATH.exists():
        pytest.skip("bed top template not available")
    if not (ENTITY_BED_TEXTURES_FOLDER / "red.png").exists():
        pytest.skip("red bed entity texture not available")

    icon = compose_bed(
        key="BED:red",
        view="inventory",
        size=16,
        textures_dir=Path("."),
        bed_textures_dir=ENTITY_BED_TEXTURES_FOLDER,
    )
    head = compose_bed(
        key="BED:red#head",
        view="top",
        size=16,
        textures_dir=Path("."),
        bed_textures_dir=ENTITY_BED_TEXTURES_FOLDER,
    )

    assert icon.getpixel((8, 4))[3] == 255
    assert icon.getpixel((8, 12))[3] == 255
    assert icon.getpixel((8, 4)) == head.getpixel((8, 4))


@pytest.mark.requires_assets
def test_compose_bed_uses_entity_atlas():
    if not (ENTITY_BED_TEXTURES_FOLDER / "red.png").exists():
        pytest.skip("red bed entity texture not available")

    image = compose_bed(
        key="BED#head",
        view="top",
        size=constants.BLOCK_PX,
        textures_dir=Path("."),
        bed_textures_dir=ENTITY_BED_TEXTURES_FOLDER,
    )

    assert image.size == (constants.BLOCK_PX, constants.BLOCK_PX)
    assert image.getpixel((constants.BLOCK_PX // 2, constants.BLOCK_PX // 2))[3] == 255


@pytest.mark.requires_assets
def test_bake_bed_integration(tmp_path: Path):
    if not (ENTITY_BED_TEXTURES_FOLDER / "red.png").exists():
        pytest.skip("red bed entity texture not available")

    from sprite_baker_test_utils import compile_texture_tokens, generated_assets_root

    from helpers.sprite_baker.cache import load_or_bake

    generated_root = tmp_path / "generated"

    for bake_key in ("BED", "BED#head", "BED#foot"):
        load_or_bake(
            "top",
            bake_key,
            lambda key=bake_key: compose_bed(
                key=key,
                view="top",
                size=constants.BLOCK_PX,
                textures_dir=Path("."),
                bed_textures_dir=ENTITY_BED_TEXTURES_FOLDER,
            ),
            generated_root=generated_root,
            force=True,
        )

    with generated_assets_root(generated_root):
        textures = compile_texture_tokens(
            "top",
            str(Path(".")),
            constants.BLOCK_PX,
            ("BED#head", "BED#foot"),
        )

    mid = constants.BLOCK_PX // 2

    assert textures["BED#head"].getpixel((mid, mid))[3] == 255
    assert textures["BED#foot"].getpixel((mid, mid // 2))[3] == 255


@pytest.mark.requires_assets
def test_compile_texture_set_loads_bed_color_variants():
    if not (ENTITY_BED_TEXTURES_FOLDER / "black.png").exists():
        pytest.skip("black bed entity texture not available")
    if not (GENERATED_ASSETS_FOLDER / "top" / "BED_black_head.png").exists():
        pytest.skip("baked black bed sprite not available")

    from sprite_baker_test_utils import compile_texture_tokens

    textures = compile_texture_tokens(
        "top",
        str(BLOCK_TEXTURES_FOLDER),
        constants.BLOCK_PX,
        ("BED:black#head", "BED:black#foot", "BED#head"),
    )

    assert "BED:black#head" in textures
    assert "BED:black#foot" in textures
    assert textures["BED:black#head"] is not textures["BED#head"]
