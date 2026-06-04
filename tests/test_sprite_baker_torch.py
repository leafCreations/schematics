from pathlib import Path

import pytest

from helpers import constants
from helpers.paths import BLOCK_TEXTURES_FOLDER
from helpers.sprite_baker.compose_torch import compose_torch, list_torch_bake_keys
from helpers.sprite_baker.demo import SpriteBakeError
from registries.loader import BLOCK_REGISTRY, build_registry_texture_mapping, compile_texture_set


def test_registry_mapping_includes_torch_variants():
    mapping = build_registry_texture_mapping("top")
    assert mapping["TORCH"] == "torch.png"
    assert mapping["TORCH#soul"] == "soul_torch.png"
    assert mapping["TORCH#wall"] == "wall_torch.png"
    assert "TORCH#normal" not in mapping


def test_list_torch_bake_keys():
    keys = list_torch_bake_keys("top")
    assert "TORCH" in keys
    assert "TORCH#soul" in keys
    assert "TORCH#wall" in keys

    inventory_keys = list_torch_bake_keys("inventory")
    assert inventory_keys == ["TORCH", "TORCH#soul", "TORCH#wall"]


def test_compose_torch_rejects_non_torch():
    with pytest.raises(SpriteBakeError, match="not a torch block"):
        compose_torch(
            key="FENCE",
            view="top",
            size=constants.BLOCK_PX,
            textures_dir=BLOCK_TEXTURES_FOLDER,
        )


@pytest.mark.requires_assets
def test_compose_torch_variants_differ():
    normal_top = compose_torch(
        key="TORCH",
        view="top",
        size=16,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )
    soul_top = compose_torch(
        key="TORCH#soul",
        view="top",
        size=16,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )
    wall_top = compose_torch(
        key="TORCH#wall",
        view="top",
        size=16,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )
    wall_side = compose_torch(
        key="TORCH#wall",
        view="side",
        size=16,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )
    soul_side = compose_torch(
        key="TORCH#soul",
        view="side",
        size=16,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )

    assert normal_top.getpixel((8, 8))[3] == 255
    assert soul_top.getpixel((8, 8))[3] == 255
    assert wall_top.getpixel((8, 8))[3] == 255
    assert wall_side.getpixel((8, 8))[3] == 255
    assert normal_top.tobytes() != soul_side.tobytes()
    assert wall_top.tobytes() != normal_top.tobytes()


@pytest.mark.requires_assets
def test_compose_torch_wall_top_uses_side_profile():
    normal_top = compose_torch(
        key="TORCH",
        view="top",
        size=16,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )
    wall_top = compose_torch(
        key="TORCH#wall",
        view="top",
        size=16,
        textures_dir=BLOCK_TEXTURES_FOLDER,
    )

    assert sum(normal_top.getpixel((x, y))[3] for x in range(16) for y in range(16)) < sum(
        wall_top.getpixel((x, y))[3] for x in range(16) for y in range(16)
    )


@pytest.mark.requires_assets
def test_bake_torch_integration(tmp_path: Path):
    from helpers.sprite_baker.cache import load_or_bake

    generated_root = tmp_path / "generated"

    for bake_key in ("TORCH", "TORCH#wall"):
        load_or_bake(
            "top",
            bake_key,
            lambda key=bake_key: compose_torch(
                key=key,
                view="top",
                size=constants.BLOCK_PX,
                textures_dir=BLOCK_TEXTURES_FOLDER,
            ),
            generated_root=generated_root,
            force=True,
        )

    import helpers.paths as paths_module
    import registries.loader as loader_module

    previous_paths_root = paths_module.GENERATED_ASSETS_FOLDER
    previous_loader_root = loader_module.GENERATED_ASSETS_FOLDER
    paths_module.GENERATED_ASSETS_FOLDER = generated_root
    loader_module.GENERATED_ASSETS_FOLDER = generated_root

    try:
        textures = compile_texture_set(
            "top",
            str(BLOCK_TEXTURES_FOLDER),
            block_px=constants.BLOCK_PX,
        )
    finally:
        paths_module.GENERATED_ASSETS_FOLDER = previous_paths_root
        loader_module.GENERATED_ASSETS_FOLDER = previous_loader_root

    assert "TORCH" in textures
    assert "TORCH#wall" in textures
    assert textures["TORCH"].getpixel((15, 15))[3] == 255


def test_torch_registry_behavior():
    assert BLOCK_REGISTRY["TORCH"]["behavior"] == "torch"
