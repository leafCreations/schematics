import pytest
from PIL import Image

import helpers.constants as constants
import helpers.utils_schematics as schematics_utils
from helpers.paths import BLOCK_TEXTURES_FOLDER
from helpers.sprite_baker.cache import load_cached, save_cached
from helpers.structure_tokens import ParsedToken
from registries.loader import BLOCK_REGISTRY, compile_texture_set


def test_show_interior_view_defaults_to_true():
    assert schematics_utils.show_interior_view("COBBLESTONE") is True


def test_show_interior_view_respects_registry_false():
    assert schematics_utils.show_interior_view("FURNACE") is False
    assert schematics_utils.show_interior_view("CRAFTING_TABLE") is False


def test_show_interior_view_empty_cell():
    assert schematics_utils.show_interior_view(".") is False


def test_corner_stair_facing_rotation_offsets():
    assert schematics_utils._corner_stair_facing_rotation("S") == 0
    assert schematics_utils._corner_stair_facing_rotation("N") == 180
    assert schematics_utils._corner_stair_facing_rotation("E") == 270
    assert schematics_utils._corner_stair_facing_rotation("W") == 90


def test_corner_stairs_rotate_by_facing(tmp_path):
    tex = Image.new("RGBA", (constants.BLOCK_PX, constants.BLOCK_PX), (0, 255, 0, 255))
    tex.putpixel((0, 0), (255, 0, 0, 255))
    save_cached("top", "STAIRS#outer_left", tex, generated_root=tmp_path)

    entry = BLOCK_REGISTRY["STAIRS"]
    parsed = ParsedToken(token="STAIRS", material="oak", direction="south", variant="outer_left")
    assert schematics_utils._is_corner_stair_shape(parsed, entry) is True

    tex = load_cached("top", "STAIRS#outer_left", generated_root=tmp_path)
    north = schematics_utils._prepare_topdown_texture(
        tex,
        "STAIRS",
        "N",
        0,
        corner_stair_shape=True,
    )
    south = schematics_utils._prepare_topdown_texture(
        tex,
        "STAIRS",
        "S",
        0,
        corner_stair_shape=True,
    )

    assert north.getpixel((0, 0)) == (0, 255, 0, 255)
    assert south.getpixel((0, 0)) == (255, 0, 0, 255)


def test_corner_stairs_apply_custom_rotation(tmp_path):
    tex = Image.new("RGBA", (constants.BLOCK_PX, constants.BLOCK_PX), (0, 255, 0, 255))
    tex.putpixel((0, 0), (255, 0, 0, 255))
    save_cached("top", "STAIRS#outer_right", tex, generated_root=tmp_path)

    tex = load_cached("top", "STAIRS#outer_right", generated_root=tmp_path)
    base = schematics_utils._prepare_topdown_texture(
        tex,
        "STAIRS",
        "S",
        0,
        corner_stair_shape=True,
    )
    rotated = schematics_utils._prepare_topdown_texture(
        tex,
        "STAIRS",
        "S",
        90,
        corner_stair_shape=True,
    )

    assert base.getpixel((0, 0)) == (255, 0, 0, 255)
    assert rotated.getpixel((0, 0)) == (0, 255, 0, 255)


def test_straight_stairs_still_rotate_with_direction(tmp_path):
    save_cached(
        "top",
        "STAIRS",
        Image.new("RGBA", (constants.BLOCK_PX, constants.BLOCK_PX), (0, 0, 255, 255)),
        generated_root=tmp_path,
    )

    entry = BLOCK_REGISTRY["STAIRS"]
    parsed = ParsedToken(token="STAIRS", material="oak", direction="south")
    assert schematics_utils._is_corner_stair_shape(parsed, entry) is False

    tex = load_cached("top", "STAIRS", generated_root=tmp_path)
    north = schematics_utils._prepare_topdown_texture(tex, "STAIRS", "N", 0)
    south = schematics_utils._prepare_topdown_texture(tex, "STAIRS", "S", 0)

    assert north.getpixel((0, 0)) == south.getpixel((0, 0))


def test_paste_corner_stair_matches_worldgen_facing():
    textures = compile_texture_set("top", str(BLOCK_TEXTURES_FOLDER), constants.BLOCK_PX)

    def cutout_corner(token: str) -> str:
        img = Image.new("RGBA", (constants.BLOCK_PX, constants.BLOCK_PX), (0, 0, 0, 0))
        schematics_utils.paste_topdown_token(img, textures, token, (0, 0), constants.BLOCK_PX)
        corners = {(2, 2): "TL", (27, 2): "TR", (2, 27): "BL", (27, 27): "BR"}
        for point, name in corners.items():
            if img.getpixel(point)[3] == 0:
                return name
        return "?"

    assert cutout_corner("STAIRS:oak@south#outer_left") == "TL"
    assert cutout_corner("STAIRS:oak@south#outer_right") == "TR"
    assert cutout_corner("STAIRS:oak@north#outer_right") == "BL"
    assert cutout_corner("STAIRS:oak@north#outer_left") == "BR"


@pytest.mark.requires_assets
def test_resolve_cell_texture_returns_planks_image():
    textures = compile_texture_set("top", str(BLOCK_TEXTURES_FOLDER), constants.BLOCK_PX)
    image = schematics_utils.resolve_cell_texture("PLANKS:oak", textures, size=constants.BLOCK_PX)

    assert image is not None
    assert image.size == (constants.BLOCK_PX, constants.BLOCK_PX)
    assert image.getpixel((0, 0))[3] == 255


@pytest.mark.requires_assets
def test_resolve_cell_texture_grass_registry_token_uses_catalog_fallback():
    image = schematics_utils.resolve_cell_texture("GRASS", {}, size=constants.BLOCK_PX)

    assert image is not None
    assert image.size == (constants.BLOCK_PX, constants.BLOCK_PX)
    assert image.getpixel((0, 0))[3] == 255
