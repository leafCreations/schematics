from helpers.paths import (
    ASSET_FOLDER,
    ASSETS_ROOT,
    BLOCK_TEXTURES_FOLDER,
    GENERATED_ASSETS_FOLDER,
    MINECRAFT_ASSETS_FOLDER,
    UI_ICONS_FOLDER,
)


def test_minecraft_assets_under_assets_root():
    assert MINECRAFT_ASSETS_FOLDER == ASSETS_ROOT / "minecraft"
    assert ASSET_FOLDER == MINECRAFT_ASSETS_FOLDER
    assert BLOCK_TEXTURES_FOLDER == MINECRAFT_ASSETS_FOLDER / "textures" / "block"
    assert GENERATED_ASSETS_FOLDER == MINECRAFT_ASSETS_FOLDER / "generated"


def test_ui_icons_sibling_to_minecraft():
    assert UI_ICONS_FOLDER == ASSETS_ROOT / "icons"
