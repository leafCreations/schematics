from pathlib import Path

import pytest

from helpers import materials as material_utils
from helpers.block_catalog import save_block_catalog
from helpers.paths import BLOCK_TEXTURES_FOLDER
from helpers.structure_tokens import ParsedToken


class _RegistryEntry(dict):
    pass


def _ctx_with_registry(block_registry: dict):
    from pathlib import Path

    from helpers.context import SchematicContext

    return SchematicContext(
        structure="test",
        stage=1,
        name="Test",
        layers=[],
        grid={},
        block_registry=block_registry,
        assets_dir=Path("."),
        worldgen_template_dir=Path("."),
        output_schematics_dir=Path("."),
        output_worldgen_dir=Path("."),
    )


def _build_inventory_with_catalog(raw_tokens, ctx, catalog_path):
    import helpers.block_catalog as block_catalog_module

    original_path = block_catalog_module.CATALOG_PATH
    block_catalog_module.CATALOG_PATH = catalog_path
    block_catalog_module._catalog_cache = None

    try:
        return material_utils.build_material_inventory_from_raw_tokens(raw_tokens, ctx)
    finally:
        block_catalog_module.CATALOG_PATH = original_path
        block_catalog_module._catalog_cache = None


def _build_inventory_with_catalog_parsed(parsed_tokens, ctx, catalog_path):
    import helpers.block_catalog as block_catalog_module

    original_path = block_catalog_module.CATALOG_PATH
    block_catalog_module.CATALOG_PATH = catalog_path
    block_catalog_module._catalog_cache = None

    try:
        return material_utils.build_material_inventory(parsed_tokens, ctx)
    finally:
        block_catalog_module.CATALOG_PATH = original_path
        block_catalog_module._catalog_cache = None


def test_build_material_inventory_from_raw_tokens(tmp_path: Path):
    catalog_path = tmp_path / "catalog.json"
    save_block_catalog(
        {
            "minecraft:oak_planks": {"display_name": "Oak Planks"},
        },
        path=catalog_path,
    )

    ctx = _ctx_with_registry(
        {
            "PLANKS": {
                "behavior": "solid",
                "minecraft": {"block": "minecraft:{material}_planks"},
            },
        }
    )

    inventory, icons = _build_inventory_with_catalog(
        ["PLANKS:oak", "PLANKS:oak", "."],
        ctx,
        catalog_path,
    )[:2]

    assert inventory == [("Oak Planks", 2)]
    assert "Oak Planks" in icons


def test_build_material_inventory_matches_raw_token_wrapper(tmp_path: Path):
    catalog_path = tmp_path / "catalog.json"
    save_block_catalog(
        {"minecraft:oak_planks": {"display_name": "Oak Planks"}},
        path=catalog_path,
    )

    ctx = _ctx_with_registry(
        {
            "PLANKS": {
                "behavior": "solid",
                "minecraft": {"block": "minecraft:{material}_planks"},
            },
        }
    )
    parsed = [ParsedToken(token="PLANKS", material="oak")]

    from_raw = _build_inventory_with_catalog(["PLANKS:oak"], ctx, catalog_path)[:2]
    from_parsed = _build_inventory_with_catalog_parsed(parsed, ctx, catalog_path)[:2]

    assert from_raw == from_parsed


def test_resolve_material_texture_name_handles_nested_stair_textures():
    ctx = _ctx_with_registry(
        {
            "STAIRS": {
                "behavior": "stairs",
                "material_default": "oak",
                "defaults": {"shape": "straight"},
                "minecraft": {"block": "minecraft:{material}_stairs"},
                "render": {
                    "textures": {
                        "top": {
                            "straight": "{material}_planks.png",
                            "outer_left": "{material}_planks.png",
                        }
                    }
                },
            },
        }
    )

    straight = material_utils.resolve_material_texture_name(
        ParsedToken(token="STAIRS", material="oak"),
        ctx,
    )
    outer_left = material_utils.resolve_material_texture_name(
        ParsedToken(token="STAIRS", material="oak", variant="outer_left"),
        ctx,
    )

    assert straight == "oak_planks.png"
    assert outer_left == "oak_planks.png"


def test_resolve_material_inventory_icon_prefers_generated_sprites(tmp_path):
    from PIL import Image

    from helpers import materials as material_utils
    from helpers.paths import GENERATED_ASSETS_FOLDER
    from helpers.sprite_baker.cache import save_cached

    ctx = _ctx_with_registry(
        {
            "SLAB": {
                "behavior": "slab",
                "material_default": "oak",
                "defaults": {"type": "bottom"},
                "minecraft": {"block": "minecraft:{material}_slab"},
                "render": {"top": "{material}_planks.png"},
            },
            "STAIRS": {
                "behavior": "stairs",
                "material_default": "oak",
                "defaults": {"shape": "straight"},
                "minecraft": {"block": "minecraft:{material}_stairs"},
                "render": {"textures": {"top": {"straight": "{material}_planks.png"}}},
            },
        }
    )

    save_cached(
        "top",
        "SLAB:oak",
        Image.new("RGBA", (16, 16), (1, 2, 3, 255)),
        generated_root=tmp_path,
    )
    save_cached(
        "top",
        "STAIRS:oak",
        Image.new("RGBA", (16, 16), (4, 5, 6, 255)),
        generated_root=tmp_path,
    )

    original_root = GENERATED_ASSETS_FOLDER
    material_utils.GENERATED_ASSETS_FOLDER = tmp_path

    try:
        slab_icon = material_utils.resolve_material_inventory_icon(
            ParsedToken(token="SLAB", material="oak"),
            ctx,
        )
        stairs_icon = material_utils.resolve_material_inventory_icon(
            ParsedToken(token="STAIRS", material="oak"),
            ctx,
        )
    finally:
        material_utils.GENERATED_ASSETS_FOLDER = original_root

    assert slab_icon == "generated:SLAB:oak"
    assert stairs_icon == "generated:STAIRS:oak"


def test_resolve_material_sprite_key_for_stair_shapes():
    ctx = _ctx_with_registry(
        {
            "STAIRS": {
                "behavior": "stairs",
                "defaults": {"shape": "straight"},
                "minecraft": {"block": "minecraft:{material}_stairs"},
            },
        }
    )

    straight = material_utils.resolve_material_sprite_key(
        ParsedToken(token="STAIRS", material="oak"),
        ctx,
    )
    outer_left = material_utils.resolve_material_sprite_key(
        ParsedToken(token="STAIRS", material="oak", variant="outer_left"),
        ctx,
    )

    assert straight == "STAIRS:oak"
    assert outer_left == "STAIRS:oak#outer_left"


def test_build_material_inventory_prefers_generated_stair_shape(tmp_path):
    from PIL import Image

    from helpers import materials as material_utils
    from helpers.paths import GENERATED_ASSETS_FOLDER
    from helpers.sprite_baker.cache import save_cached

    ctx = _ctx_with_registry(
        {
            "STAIRS": {
                "behavior": "stairs",
                "material_default": "oak",
                "defaults": {"shape": "straight"},
                "minecraft": {"block": "minecraft:{material}_stairs"},
                "render": {"top": "{material}_planks.png"},
            },
        }
    )

    save_cached(
        "top",
        "STAIRS:oak",
        Image.new("RGBA", (16, 16), (1, 1, 1, 255)),
        generated_root=tmp_path,
    )
    save_cached(
        "top",
        "STAIRS:oak#outer_left",
        Image.new("RGBA", (16, 16), (2, 2, 2, 255)),
        generated_root=tmp_path,
    )

    original_root = GENERATED_ASSETS_FOLDER
    material_utils.GENERATED_ASSETS_FOLDER = tmp_path

    try:
        parsed = [
            ParsedToken(token="STAIRS", material="oak", direction="south"),
            ParsedToken(token="STAIRS", material="oak", direction="south", variant="outer_left"),
        ]
        _, icons, icon_tokens = material_utils.build_material_inventory(parsed, ctx)
    finally:
        material_utils.GENERATED_ASSETS_FOLDER = original_root

    assert icons["Oak Stairs"] == "generated:STAIRS:oak#outer_left"
    assert icon_tokens["Oak Stairs"].variant == "outer_left"


def test_resolve_material_sprite_key_for_fence_material():
    ctx = _ctx_with_registry(
        {
            "FENCE": {
                "behavior": "fence",
                "material_default": "oak",
                "minecraft": {"block": "minecraft:{material}_fence"},
            },
        }
    )

    key = material_utils.resolve_material_sprite_key(
        ParsedToken(token="FENCE", material="oak"),
        ctx,
    )

    assert key == "FENCE:oak"


def test_resolve_material_inventory_icon_uses_fence_inventory_view(tmp_path):
    from PIL import Image

    from helpers.paths import GENERATED_ASSETS_FOLDER
    from helpers.sprite_baker.cache import save_cached

    ctx = _ctx_with_registry(
        {
            "FENCE": {
                "behavior": "fence",
                "material_default": "oak",
                "minecraft": {"block": "minecraft:{material}_fence"},
                "render": {"inventory_image": "{material}_fence_inventory.png"},
            },
        }
    )

    save_cached(
        "inventory",
        "FENCE:oak",
        Image.new("RGBA", (16, 16), (10, 20, 30, 255)),
        generated_root=tmp_path,
    )
    save_cached(
        "top",
        "FENCE:oak",
        Image.new("RGBA", (16, 16), (99, 88, 77, 255)),
        generated_root=tmp_path,
    )

    original_root = GENERATED_ASSETS_FOLDER
    material_utils.GENERATED_ASSETS_FOLDER = tmp_path

    try:
        icon = material_utils.resolve_material_inventory_icon(
            ParsedToken(token="FENCE", material="oak"),
            ctx,
        )
    finally:
        material_utils.GENERATED_ASSETS_FOLDER = original_root

    assert icon == "generated:FENCE:oak"


@pytest.mark.requires_assets
def test_draw_inventory_icon_uses_inventory_view_without_parsed():

    from PIL import Image, ImageDraw

    from helpers.materials import draw_inventory_icon
    from helpers.sprite_baker.cache import load_generated_sprite

    ctx = _ctx_with_registry(
        {
            "FENCE": {
                "behavior": "fence",
                "material_default": "oak",
                "minecraft": {"block": "minecraft:{material}_fence"},
            },
        }
    )
    ctx.assets_dir = BLOCK_TEXTURES_FOLDER

    inv_ref = load_generated_sprite("inventory", "FENCE:oak", 25)

    img = Image.new("RGBA", (25, 25), (0, 0, 0, 0))
    draw_inventory_icon(
        img,
        ImageDraw.Draw(img),
        ctx,
        "generated:FENCE:oak",
        0,
        0,
        25,
        parsed=None,
    )

    assert img.tobytes() == inv_ref.tobytes()


@pytest.mark.requires_assets
def test_resolve_material_inventory_icon_defers_fence_bake_to_draw(tmp_path):

    from helpers import materials as material_utils
    from helpers.sprite_baker import runtime_bake as runtime_bake_module

    ctx = _ctx_with_registry(
        {
            "FENCE": {
                "behavior": "fence",
                "material_default": "oak",
                "minecraft": {"block": "minecraft:{material}_fence"},
                "render": {"inventory_image": "{material}_fence_inventory.png"},
            },
        }
    )
    ctx.assets_dir = BLOCK_TEXTURES_FOLDER

    original_materials_root = material_utils.GENERATED_ASSETS_FOLDER
    original_runtime_root = runtime_bake_module.GENERATED_ASSETS_FOLDER
    material_utils.GENERATED_ASSETS_FOLDER = tmp_path
    runtime_bake_module.GENERATED_ASSETS_FOLDER = tmp_path

    try:
        icon = material_utils.resolve_material_inventory_icon(
            ParsedToken(token="FENCE", material="oak"),
            ctx,
        )
        baked_path = tmp_path / "inventory" / "FENCE_oak.png"
    finally:
        material_utils.GENERATED_ASSETS_FOLDER = original_materials_root
        runtime_bake_module.GENERATED_ASSETS_FOLDER = original_runtime_root

    assert icon == "generated:FENCE:oak"
    assert not baked_path.exists()


@pytest.mark.requires_assets
def test_draw_inventory_icon_uses_side_view_for_stairs():

    from PIL import Image, ImageDraw

    from helpers.materials import draw_inventory_icon
    from helpers.sprite_baker.cache import load_generated_sprite

    ctx = _ctx_with_registry(
        {
            "STAIRS": {
                "behavior": "stairs",
                "material_default": "oak",
                "defaults": {"shape": "straight"},
                "minecraft": {"block": "minecraft:{material}_stairs"},
                "render": {"textures": {"top": {"straight": "{material}_planks.png"}}},
            },
        }
    )
    ctx.assets_dir = BLOCK_TEXTURES_FOLDER

    side_ref = load_generated_sprite("side", "STAIRS:oak", 25)
    top_ref = load_generated_sprite("top", "STAIRS:oak", 25)
    if side_ref is None or top_ref is None:
        pytest.skip("baked STAIRS:oak side/top sprites not available")

    img = Image.new("RGBA", (25, 25), (0, 0, 0, 0))
    draw_inventory_icon(
        img,
        ImageDraw.Draw(img),
        ctx,
        "generated:STAIRS:oak",
        0,
        0,
        25,
        parsed=ParsedToken(token="STAIRS", material="oak"),
    )

    assert img.tobytes() == side_ref.tobytes()
    assert img.tobytes() != top_ref.tobytes()


def test_resolve_material_inventory_icon_defers_stairs_bake_to_draw(tmp_path):

    from helpers import materials as material_utils
    from helpers.sprite_baker import runtime_bake as runtime_bake_module

    ctx = _ctx_with_registry(
        {
            "STAIRS": {
                "behavior": "stairs",
                "material_default": "oak",
                "defaults": {"shape": "straight"},
                "minecraft": {"block": "minecraft:{material}_stairs"},
                "render": {"textures": {"top": {"straight": "{material}_planks.png"}}},
            },
        }
    )
    ctx.assets_dir = BLOCK_TEXTURES_FOLDER

    original_materials_root = material_utils.GENERATED_ASSETS_FOLDER
    original_runtime_root = runtime_bake_module.GENERATED_ASSETS_FOLDER
    material_utils.GENERATED_ASSETS_FOLDER = tmp_path
    runtime_bake_module.GENERATED_ASSETS_FOLDER = tmp_path

    try:
        icon = material_utils.resolve_material_inventory_icon(
            ParsedToken(token="STAIRS", material="oak"),
            ctx,
        )
        baked_path = tmp_path / "side" / "STAIRS_oak.png"
    finally:
        material_utils.GENERATED_ASSETS_FOLDER = original_materials_root
        runtime_bake_module.GENERATED_ASSETS_FOLDER = original_runtime_root

    assert icon == "generated:STAIRS:oak"
    assert not baked_path.exists()


def test_resolve_material_display_name_uses_catalog(tmp_path: Path):
    catalog_path = tmp_path / "catalog.json"
    save_block_catalog(
        {
            "minecraft:oak_door": {"display_name": "Oak Door"},
            "minecraft:blue_bed": {"display_name": "Blue Bed"},
            "minecraft:grass_block": {"display_name": "Grass Block"},
        },
        path=catalog_path,
    )

    import helpers.block_catalog as block_catalog_module

    original_path = block_catalog_module.CATALOG_PATH
    block_catalog_module.CATALOG_PATH = catalog_path
    block_catalog_module._catalog_cache = None

    ctx = _ctx_with_registry(
        {
            "DOOR": {
                "behavior": "door",
                "material_default": "oak",
                "minecraft": {"block": "minecraft:{material}_door"},
            },
            "BED": {
                "behavior": "bed",
                "color_default": "red",
                "minecraft": {"block": "minecraft:{color}_bed"},
            },
            "GRASS": {
                "behavior": "solid",
                "minecraft": {"block": "minecraft:grass_block"},
            },
        }
    )

    try:
        assert (
            material_utils.resolve_material_display_name(
                ParsedToken(token="DOOR", material="oak"),
                ctx,
            )
            == "Oak Door"
        )
        assert (
            material_utils.resolve_material_display_name(
                ParsedToken(token="BED", material="blue"),
                ctx,
            )
            == "Blue Bed"
        )
        assert (
            material_utils.resolve_material_display_name(ParsedToken(token="GRASS"), ctx)
            == "Grass Block"
        )
    finally:
        block_catalog_module.CATALOG_PATH = original_path
        block_catalog_module._catalog_cache = None


def test_resolve_material_display_name_falls_back_to_block_name():
    ctx = _ctx_with_registry(
        {
            "PLANKS": {
                "behavior": "solid",
                "minecraft": {"block": "minecraft:dark_oak_planks"},
            },
        }
    )

    assert (
        material_utils.resolve_material_display_name(
            ParsedToken(token="PLANKS", material="dark_oak"),
            ctx,
        )
        == "Dark Oak Planks"
    )


def test_should_count_material_skips_door_upper():
    ctx = _ctx_with_registry(
        {"DOOR": {"behavior": "door", "minecraft": {"block": "minecraft:oak_door"}}}
    )
    parsed = ParsedToken(token="DOOR", material="oak", variant="upper")

    assert material_utils.should_count_material(parsed, ctx) is False


def test_resolve_material_sprite_key_for_door_material():
    ctx = _ctx_with_registry(
        {
            "DOOR": {
                "behavior": "door",
                "material_default": "oak",
                "minecraft": {"block": "minecraft:{material}_door"},
            },
        }
    )

    key = material_utils.resolve_material_sprite_key(
        ParsedToken(token="DOOR", material="oak", variant="lower"),
        ctx,
    )

    assert key == "DOOR:oak"


def test_resolve_material_inventory_icon_uses_generated_door(tmp_path):
    from PIL import Image

    from helpers import materials as material_utils
    from helpers.paths import GENERATED_ASSETS_FOLDER
    from helpers.sprite_baker.cache import save_cached

    ctx = _ctx_with_registry(
        {
            "DOOR": {
                "behavior": "door",
                "material_default": "oak",
                "minecraft": {"block": "minecraft:{material}_door"},
                "render": {
                    "textures": {
                        "upper": "{material}_door_top.png",
                        "lower": "{material}_door_bottom.png",
                    },
                },
            },
        }
    )

    save_cached(
        "inventory",
        "DOOR:oak",
        Image.new("RGBA", (16, 16), (4, 5, 6, 255)),
        generated_root=tmp_path,
    )

    original_root = GENERATED_ASSETS_FOLDER
    material_utils.GENERATED_ASSETS_FOLDER = tmp_path

    try:
        icon = material_utils.resolve_material_inventory_icon(
            ParsedToken(token="DOOR", material="oak", variant="lower"),
            ctx,
        )
    finally:
        material_utils.GENERATED_ASSETS_FOLDER = original_root

    assert icon == "generated:DOOR:oak"


def test_resolve_material_inventory_icon_defers_door_bake_to_draw(tmp_path):

    from helpers import materials as material_utils
    from helpers.sprite_baker import runtime_bake as runtime_bake_module

    ctx = _ctx_with_registry(
        {
            "DOOR": {
                "behavior": "door",
                "material_default": "oak",
                "minecraft": {"block": "minecraft:{material}_door"},
                "render": {
                    "textures": {
                        "upper": "{material}_door_top.png",
                        "lower": "{material}_door_bottom.png",
                    },
                },
            },
        }
    )
    ctx.assets_dir = BLOCK_TEXTURES_FOLDER

    original_materials_root = material_utils.GENERATED_ASSETS_FOLDER
    original_runtime_root = runtime_bake_module.GENERATED_ASSETS_FOLDER
    material_utils.GENERATED_ASSETS_FOLDER = tmp_path
    runtime_bake_module.GENERATED_ASSETS_FOLDER = tmp_path

    try:
        icon = material_utils.resolve_material_inventory_icon(
            ParsedToken(token="DOOR", material="oak", variant="lower"),
            ctx,
        )
        baked_path = tmp_path / "inventory" / "DOOR_oak.png"
    finally:
        material_utils.GENERATED_ASSETS_FOLDER = original_materials_root
        runtime_bake_module.GENERATED_ASSETS_FOLDER = original_runtime_root

    assert icon == "generated:DOOR:oak"
    assert not baked_path.exists()


def test_should_count_material_skips_bed_foot():
    ctx = _ctx_with_registry(
        {
            "BED": {
                "behavior": "bed",
                "color_default": "red",
                "minecraft": {"block": "minecraft:{color}_bed"},
            }
        }
    )
    parsed = ParsedToken(token="BED", material="black", variant="foot")

    assert material_utils.should_count_material(parsed, ctx) is False


def test_should_count_material_counts_normal_blocks():
    ctx = _ctx_with_registry(
        {"PLANKS": {"behavior": "solid", "minecraft": {"block": "minecraft:oak_planks"}}}
    )
    parsed = ParsedToken(token="PLANKS", material="oak")

    assert material_utils.should_count_material(parsed, ctx) is True


def test_draw_inventory_icon_uses_catalog_fallback_for_minecraft_block(monkeypatch):
    from PIL import Image, ImageDraw

    from helpers.materials import draw_inventory_icon
    from helpers.structure_tokens import parse_structure_token

    catalog_tex = Image.new("RGBA", (16, 16), (10, 20, 30, 255))

    def fake_load_catalog_texture_image(parsed, view, size):
        return catalog_tex.resize((size, size))

    monkeypatch.setattr(
        material_utils,
        "load_catalog_texture_image",
        fake_load_catalog_texture_image,
    )

    img = Image.new("RGBA", (25, 25), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    ctx = _ctx_with_registry({})
    parsed = parse_structure_token("minecraft:stone")

    draw_inventory_icon(
        img,
        draw,
        ctx,
        texture_name="missing_stone.png",
        x=0,
        y=0,
        size=25,
        parsed=parsed,
    )

    assert img.getpixel((0, 0))[:3] == (10, 20, 30)


@pytest.mark.requires_assets
def test_draw_inventory_icon_applies_schematic_tint_for_grass_and_water():
    from PIL import Image, ImageDraw

    from helpers.materials import draw_inventory_icon, resolve_material_inventory_icon
    from helpers.structure_tokens import parse_structure_token

    if not (BLOCK_TEXTURES_FOLDER / "grass_block_top.png").is_file():
        pytest.skip("grass_block_top.png not available")
    if not (BLOCK_TEXTURES_FOLDER / "water_still.png").is_file():
        pytest.skip("water_still.png not available")

    ctx = _ctx_with_registry({})
    ctx.assets_dir = BLOCK_TEXTURES_FOLDER

    for raw_token in ("minecraft:grass_block", "minecraft:water"):
        parsed = parse_structure_token(raw_token)
        assert parsed is not None
        texture_name = resolve_material_inventory_icon(parsed, ctx)
        img = Image.new("RGBA", (25, 25), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        plain = (
            Image.open(BLOCK_TEXTURES_FOLDER / texture_name)
            .convert("RGBA")
            .resize(
                (25, 25),
                resample=Image.Resampling.NEAREST,
            )
        )

        draw_inventory_icon(
            img,
            draw,
            ctx,
            texture_name=texture_name,
            x=0,
            y=0,
            size=25,
            parsed=parsed,
            raw_token=raw_token,
        )

        assert img.getpixel((12, 12)) != plain.getpixel((12, 12))


def test_draw_inventory_icon_gray_placeholder_without_catalog_fallback():
    from PIL import Image, ImageDraw

    from helpers.materials import draw_inventory_icon
    from helpers.structure_tokens import ParsedToken

    img = Image.new("RGBA", (25, 25), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    ctx = _ctx_with_registry({})
    parsed = ParsedToken(token="UNKNOWN")

    draw_inventory_icon(
        img,
        draw,
        ctx,
        texture_name="missing.png",
        x=0,
        y=0,
        size=25,
        parsed=parsed,
    )

    assert img.getpixel((12, 12))[:3] == (230, 230, 230)
