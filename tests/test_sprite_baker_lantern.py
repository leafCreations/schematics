import pytest

from helpers import constants
from helpers.paths import BLOCK_TEXTURES_FOLDER
from helpers.sprite_baker.compose_lantern import compose_lantern, list_lantern_bake_keys
from helpers.sprite_baker.demo import SpriteBakeError
from registries.loader import BLOCK_REGISTRY, build_registry_texture_mapping


def test_registry_mapping_includes_lantern_variants():
    mapping = build_registry_texture_mapping("top")
    assert mapping["LANTERN"] == "lantern.png"
    assert mapping["LANTERN#soul"] == "soul_lantern.png"
    assert "LANTERN#normal" not in mapping


def test_list_lantern_bake_keys():
    keys = list_lantern_bake_keys("top")
    assert "LANTERN" in keys
    assert "LANTERN#soul" in keys
    assert "COPPER_LANTERN" in keys
    assert "COPPER_LANTERN#oxidized" in keys


def test_copper_lantern_registry():
    entry = BLOCK_REGISTRY["COPPER_LANTERN"]
    assert entry.get("behavior") == "lantern"
    variants = entry["minecraft"]["variants"]
    assert variants["normal"]["block"] == "minecraft:copper_lantern"
    assert variants["waxed_oxidized"]["block"] == "minecraft:waxed_oxidized_copper_lantern"
    assert all("hanging" in data.get("blockstates", {}) for data in variants.values())


def test_lantern_registry_behavior():
    entry = BLOCK_REGISTRY["LANTERN"]
    assert entry.get("behavior") == "lantern"


def test_compose_lantern_rejects_non_lantern():
    with pytest.raises(SpriteBakeError, match="not a lantern block"):
        compose_lantern(
            key="TORCH",
            view="top",
            size=constants.BLOCK_PX,
            textures_dir=BLOCK_TEXTURES_FOLDER,
        )


@pytest.mark.requires_assets
def test_compose_lantern_variants_differ():
    normal_top = compose_lantern(
        key="LANTERN",
        view="top",
        size=16,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )
    soul_top = compose_lantern(
        key="LANTERN#soul",
        view="top",
        size=16,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )
    normal_side = compose_lantern(
        key="LANTERN",
        view="side",
        size=16,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )
    soul_side = compose_lantern(
        key="LANTERN#soul",
        view="side",
        size=16,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )

    assert normal_top.getpixel((8, 8))[3] == 255
    assert soul_top.getpixel((8, 8))[3] == 255
    # Chain is composited above the cage (toward the supporting block).
    assert any(normal_top.getpixel((x, 2))[3] for x in range(16))
    assert any(soul_top.getpixel((x, 2))[3] for x in range(16))
    assert normal_side.getpixel((8, 8))[3] == 255
    assert soul_side.getpixel((8, 8))[3] == 255
    # Hanging lanterns share the same top-down silhouette; soul differs on side view.
    assert normal_side.tobytes() != soul_side.tobytes()


@pytest.mark.requires_assets
def test_compile_texture_set_loads_baked_lantern_variants(tmp_path):
    from sprite_baker_test_utils import compile_texture_tokens, generated_assets_root

    generated_root = tmp_path / "generated"
    lantern_tokens = ("LANTERN", "LANTERN#soul")

    with generated_assets_root(generated_root):
        textures = compile_texture_tokens(
            "top",
            str(BLOCK_TEXTURES_FOLDER),
            constants.BLOCK_PX,
            lantern_tokens,
        )
        side_textures = compile_texture_tokens(
            "side",
            str(BLOCK_TEXTURES_FOLDER),
            constants.BLOCK_PX,
            lantern_tokens,
        )

    assert "LANTERN" in textures
    assert "LANTERN#soul" in textures
    assert textures["LANTERN"].getpixel((15, 15))[3] == 255
    assert (generated_root / "top" / "LANTERN.png").exists()
    assert (generated_root / "top" / "LANTERN_soul.png").exists()
    assert side_textures["LANTERN"].tobytes() != side_textures["LANTERN#soul"].tobytes()
