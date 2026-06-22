from helpers.paths import BLOCK_TEXTURES_FOLDER
from helpers.sprite_baker.compose_campfire import (
    compose_campfire,
    is_campfire_bake_key,
    list_campfire_bake_keys,
)


def test_list_campfire_bake_keys_includes_facing_and_lit_variants():
    keys = list_campfire_bake_keys("top")

    assert "minecraft:campfire@north;lit=true" in keys
    assert "minecraft:campfire@west;lit=false" in keys
    assert "minecraft:soul_campfire@south;lit=true" in keys
    assert len(keys) == 16


def test_is_campfire_bake_key():
    assert is_campfire_bake_key("minecraft:campfire@north;lit=true")
    assert is_campfire_bake_key("minecraft:soul_campfire@west;lit=false")
    assert not is_campfire_bake_key("minecraft:stone")


def test_compose_campfire_top_view_lit_and_unlit():
    lit = compose_campfire(
        key="minecraft:campfire@north;lit=true",
        view="top",
        size=30,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )
    unlit = compose_campfire(
        key="minecraft:campfire@north;lit=false",
        view="top",
        size=30,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )

    assert lit.size == (30, 30)
    assert unlit.size == (30, 30)
    assert lit.getbbox() is not None
    assert unlit.getbbox() is not None
    assert lit.tobytes() != unlit.tobytes()
