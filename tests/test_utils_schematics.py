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


def test_build_texture_key_candidates_skips_default_when_material_set():
    parsed = ParsedToken(token="STAIRS", material="cobblestone", direction="north")
    entry = BLOCK_REGISTRY["STAIRS"]
    defaults = entry.get("defaults", {})
    render_textures = entry.get("render", {}).get("textures", {}).get("top", {})

    keys = schematics_utils._build_texture_key_candidates(
        "STAIRS:cobblestone@north",
        parsed,
        "STAIRS",
        defaults,
        render_textures,
        {},
        "top",
    )

    assert keys == ["STAIRS:cobblestone"]
    assert "STAIRS" not in keys
    assert "STAIRS#straight" not in keys


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
        stairs_behavior=True,
    )
    south = schematics_utils._prepare_topdown_texture(
        tex,
        "STAIRS",
        "S",
        0,
        stairs_behavior=True,
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
        stairs_behavior=True,
    )
    rotated = schematics_utils._prepare_topdown_texture(
        tex,
        "STAIRS",
        "S",
        90,
        stairs_behavior=True,
    )

    assert base.getpixel((0, 0)) == (255, 0, 0, 255)
    assert rotated.getpixel((0, 0)) == (0, 255, 0, 255)


def test_straight_stairs_still_rotate_with_direction(tmp_path):
    tex = Image.new("RGBA", (constants.BLOCK_PX, constants.BLOCK_PX), (0, 255, 0, 255))
    tex.putpixel((0, 0), (255, 0, 0, 255))
    save_cached("top", "STAIRS", tex, generated_root=tmp_path)

    entry = BLOCK_REGISTRY["STAIRS"]
    parsed = ParsedToken(token="STAIRS", material="oak", direction="south")
    assert schematics_utils._is_corner_stair_shape(parsed, entry) is False

    tex = load_cached("top", "STAIRS", generated_root=tmp_path)
    north = schematics_utils._prepare_topdown_texture(
        tex,
        "STAIRS",
        "N",
        0,
        stairs_behavior=True,
    )
    south = schematics_utils._prepare_topdown_texture(
        tex,
        "STAIRS",
        "S",
        0,
        stairs_behavior=True,
    )

    assert north.getpixel((0, 0)) == (0, 255, 0, 255)
    assert south.getpixel((0, 0)) == (255, 0, 0, 255)


def test_paste_straight_stair_matches_worldgen_facing():
    textures = compile_texture_set("top", str(BLOCK_TEXTURES_FOLDER), constants.BLOCK_PX)

    def riser_corner(token: str) -> str:
        img = Image.new("RGBA", (constants.BLOCK_PX, constants.BLOCK_PX), (0, 0, 0, 0))
        schematics_utils.paste_topdown_token(img, textures, token, (0, 0), constants.BLOCK_PX)
        corners = {(2, 2): "TL", (27, 2): "TR", (2, 27): "BL", (27, 27): "BR"}
        best_name = "?"
        best_alpha = 256
        for point, name in corners.items():
            alpha = img.getpixel(point)[3]
            if alpha < best_alpha:
                best_alpha = alpha
                best_name = name
        assert best_alpha < 255, f"{token}: expected riser ghost, got opaque corners"
        return best_name

    assert riser_corner("STAIRS:oak@south") == "TL"
    assert riser_corner("STAIRS:oak@north") == "BL"
    assert riser_corner("STAIRS:oak@east") == "TL"
    assert riser_corner("STAIRS:oak@west") == "TR"


def test_paste_corner_stair_matches_worldgen_facing():
    textures = compile_texture_set("top", str(BLOCK_TEXTURES_FOLDER), constants.BLOCK_PX)

    def riser_corner(token: str) -> str:
        img = Image.new("RGBA", (constants.BLOCK_PX, constants.BLOCK_PX), (0, 0, 0, 0))
        schematics_utils.paste_topdown_token(img, textures, token, (0, 0), constants.BLOCK_PX)
        corners = {(2, 2): "TL", (27, 2): "TR", (2, 27): "BL", (27, 27): "BR"}
        best_name = "?"
        best_alpha = 256
        for point, name in corners.items():
            alpha = img.getpixel(point)[3]
            if alpha < best_alpha:
                best_alpha = alpha
                best_name = name
        assert best_alpha < 255, f"{token}: expected riser ghost, got opaque corners"
        return best_name

    assert riser_corner("STAIRS:oak@south#outer_left") == "TL"
    assert riser_corner("STAIRS:oak@south#outer_right") == "TR"
    assert riser_corner("STAIRS:oak@north#outer_right") == "BL"
    assert riser_corner("STAIRS:oak@north#outer_left") == "BR"


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


def test_build_texture_key_candidates_bed_color_includes_default_fallbacks():
    parsed = ParsedToken(token="BED", material="blue", direction="north", variant="head")
    entry = BLOCK_REGISTRY["BED"]
    defaults = entry.get("defaults", {})
    render_textures = entry.get("render", {}).get("textures", {})

    keys = schematics_utils._build_texture_key_candidates(
        "BED:blue@north#head",
        parsed,
        "BED",
        defaults,
        render_textures,
        {},
        "top",
    )

    assert keys[:2] == ["BED:blue#head", "BED:blue"]
    assert "BED:red#head" in keys
    assert "BED#head" in keys
    assert keys[-1] == "BED"
