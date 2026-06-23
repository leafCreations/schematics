from helpers.paths import (
    ASSET_FOLDER,
    ASSETS_ROOT,
    BLOCK_TEXTURES_FOLDER,
    GENERATED_ASSETS_FOLDER,
    LEGACY_TEMPLATE_FOLDER,
    MINECRAFT_ASSETS_FOLDER,
    OUTPUT_WORLDS_FOLDER,
    PROJECT_ASSETS_FOLDER,
    PROJECT_CUSTOM_FOLDER,
    UI_ICONS_FOLDER,
    VERSIONS_ASSETS_FOLDER,
    WORLGEN_TEMPLATES_FOLDER,
    list_worldgen_template_versions,
    resolve_worldgen_output_dir,
    resolve_worldgen_template_dir,
    worldgen_version_from_template_dir_name,
)


def test_minecraft_assets_under_assets_root():
    assert MINECRAFT_ASSETS_FOLDER == ASSETS_ROOT / "minecraft"
    assert ASSET_FOLDER == MINECRAFT_ASSETS_FOLDER
    assert BLOCK_TEXTURES_FOLDER == MINECRAFT_ASSETS_FOLDER / "textures" / "block"
    assert PROJECT_ASSETS_FOLDER == ASSETS_ROOT / "project"
    assert PROJECT_CUSTOM_FOLDER == PROJECT_ASSETS_FOLDER / "custom"
    assert GENERATED_ASSETS_FOLDER == PROJECT_ASSETS_FOLDER / "generated"
    assert VERSIONS_ASSETS_FOLDER == ASSETS_ROOT / "versions"


def test_ui_icons_sibling_to_minecraft():
    assert UI_ICONS_FOLDER == ASSETS_ROOT / "icons"


def test_worldgen_templates_layout():
    assert ASSETS_ROOT.parent / "worldgen_templates" == WORLGEN_TEMPLATES_FOLDER
    assert ASSETS_ROOT.parent / "template" == LEGACY_TEMPLATE_FOLDER


def test_resolve_worldgen_template_dir_prefers_versioned_folder():
    resolved = resolve_worldgen_template_dir()
    assert resolved == WORLGEN_TEMPLATES_FOLDER / "v26_1_2"
    assert resolved.is_dir()


def test_resolve_worldgen_template_dir_accepts_explicit_version():
    resolved = resolve_worldgen_template_dir(version="26.2")
    assert resolved == WORLGEN_TEMPLATES_FOLDER / "v26_2"
    assert resolved.is_dir()


def test_worldgen_version_from_template_dir_name():
    assert worldgen_version_from_template_dir_name("v26_1_2") == "26.1.2"
    assert worldgen_version_from_template_dir_name("v26_2") == "26.2"


def test_list_worldgen_template_versions_includes_installed_templates():
    versions = list_worldgen_template_versions()
    assert "26.1.2" in versions
    assert "26.2" in versions


def test_resolve_worldgen_output_dir_includes_version():
    assert resolve_worldgen_output_dir("residence") == (OUTPUT_WORLDS_FOLDER / "residence/v26_1_2")
    assert resolve_worldgen_output_dir("residence", version="26.2") == (
        OUTPUT_WORLDS_FOLDER / "residence/v26_2"
    )
