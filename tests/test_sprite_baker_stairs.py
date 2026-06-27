from pathlib import Path

import pytest
from PIL import Image

from helpers import constants
from helpers.paths import BLOCK_TEXTURES_FOLDER
from helpers.sprite_baker.compose_slab import compose_slab
from helpers.sprite_baker.compose_stairs import compose_stairs, list_stairs_bake_keys
from helpers.sprite_baker.demo import SpriteBakeError
from helpers.sprite_baker.stair_shapes import (
    STAIR_RISER_GHOST_ALPHA,
    build_stair_top_mask,
)
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


def test_list_stairs_bake_keys_includes_cobblestone():
    keys = list_stairs_bake_keys("top", textures_dir=BLOCK_TEXTURES_FOLDER)
    assert "STAIRS:cobblestone" in keys


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

    assert straight.getpixel((4, 4))[3] == STAIR_RISER_GHOST_ALPHA
    assert straight.getpixel((12, 12))[3] == 255
    assert outer_left.getpixel((4, 4))[3] == STAIR_RISER_GHOST_ALPHA


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
    assert textures["STAIRS"].getpixel((5, 5))[3] == STAIR_RISER_GHOST_ALPHA
    assert textures["STAIRS#outer_left"].getpixel((5, 5))[3] == STAIR_RISER_GHOST_ALPHA

    entry = BLOCK_REGISTRY["STAIRS"]
    assert entry.get("behavior") == "stairs"


def _stairs_texture_dir(tmp_path: Path) -> Path:
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    Image.new("RGBA", (16, 16), (200, 100, 50, 255)).save(textures_dir / "oak_planks.png")
    return textures_dir


def test_compose_stairs_riser_ghost_alpha_between_void_and_tread(tmp_path: Path):
    textures_dir = _stairs_texture_dir(tmp_path)
    stair = compose_stairs(key="STAIRS", view="top", size=16, textures_dir=textures_dir)
    tread_alpha = stair.getpixel((12, 12))[3]
    riser_alpha = stair.getpixel((4, 4))[3]
    assert tread_alpha == 255
    assert 0 < riser_alpha < tread_alpha
    assert riser_alpha == STAIR_RISER_GHOST_ALPHA


def test_riser_ghost_lightened_brighter_than_unlightened(tmp_path: Path):
    from helpers.sprite_baker.stair_shapes import (
        STAIR_RISER_GHOST_LIGHTEN,
        apply_texture_mask_alpha,
        build_stair_riser_top_mask,
        lighten_texture_for_riser_ghost,
    )

    size = 16
    mask = build_stair_riser_top_mask(size, "straight")
    dark = Image.new("RGBA", (size, size), (100, 100, 100, 255))
    point = (4, 4)
    raw = apply_texture_mask_alpha(dark, mask, STAIR_RISER_GHOST_ALPHA).getpixel(point)
    lit = apply_texture_mask_alpha(
        lighten_texture_for_riser_ghost(dark, STAIR_RISER_GHOST_LIGHTEN),
        mask,
        STAIR_RISER_GHOST_ALPHA,
    ).getpixel(point)
    assert sum(lit[:3]) > sum(raw[:3])


def test_stair_riser_ghost_distinct_from_slab_void(tmp_path: Path):
    textures_dir = _stairs_texture_dir(tmp_path)
    size = 16
    half = size // 2
    stair = compose_stairs(key="STAIRS", view="top", size=size, textures_dir=textures_dir)
    slab = compose_slab(key="SLAB", view="top", size=size, textures_dir=textures_dir)
    # South-facing straight stair: north half is riser ghost; bottom slab void is transparent.
    assert stair.getpixel((4, 4))[3] == STAIR_RISER_GHOST_ALPHA
    assert slab.getpixel((4, 4))[3] == 0
    assert slab.getpixel((4, half + 2))[3] == 255


def test_compose_stairs_brick_material_uses_bricks_texture(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    Image.new("RGBA", (16, 16), (180, 80, 70, 255)).save(textures_dir / "bricks.png")

    image = compose_stairs(
        key="STAIRS:brick",
        view="top",
        size=16,
        textures_dir=textures_dir,
    )

    assert image.getpixel((12, 12))[3] == 255
    assert image.getpixel((4, 4))[3] == STAIR_RISER_GHOST_ALPHA


def test_compose_stairs_cinnabar_brick_uses_bricks_texture(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    Image.new("RGBA", (16, 16), (200, 50, 50, 255)).save(textures_dir / "cinnabar_bricks.png")

    image = compose_stairs(
        key="STAIRS:cinnabar_brick",
        view="top",
        size=16,
        textures_dir=textures_dir,
    )

    assert image.getpixel((12, 12))[3] == 255


def test_compose_stairs_purpur_uses_purpur_block_texture(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    Image.new("RGBA", (16, 16), (170, 90, 180, 255)).save(textures_dir / "purpur_block.png")

    image = compose_stairs(
        key="STAIRS:purpur",
        view="top",
        size=16,
        textures_dir=textures_dir,
    )

    assert image.getpixel((12, 12))[3] == 255
    assert image.getpixel((4, 4))[3] == STAIR_RISER_GHOST_ALPHA


def test_compose_stairs_quartz_uses_block_top_texture(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    Image.new("RGBA", (16, 16), (230, 225, 220, 255)).save(textures_dir / "quartz_block_top.png")

    image = compose_stairs(
        key="STAIRS:quartz",
        view="top",
        size=16,
        textures_dir=textures_dir,
    )

    assert image.getpixel((12, 12))[3] == 255


def test_compose_stairs_smooth_quartz_uses_bottom_texture(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    Image.new("RGBA", (16, 16), (220, 220, 215, 255)).save(textures_dir / "quartz_block_bottom.png")

    image = compose_stairs(
        key="STAIRS:smooth_quartz",
        view="top",
        size=16,
        textures_dir=textures_dir,
    )

    assert image.getpixel((12, 12))[3] == 255


def test_compose_stairs_waxed_cut_copper_uses_cut_copper_texture(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    Image.new("RGBA", (16, 16), (190, 120, 90, 255)).save(textures_dir / "cut_copper.png")

    image = compose_stairs(
        key="STAIRS:waxed_cut_copper",
        view="top",
        size=16,
        textures_dir=textures_dir,
    )

    assert image.getpixel((12, 12))[3] == 255
