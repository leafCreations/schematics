from pathlib import Path

from helpers.migrate_project_assets import (
    apply_project_asset_migration,
    plan_project_asset_migration,
)
from helpers.minecraft_asset_dedupe import build_version_overlays, materialize_version
from helpers.minecraft_asset_manifest import plan_prune, should_keep_file


def _touch(path: Path, content: bytes = b"x" * 4) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def test_should_keep_file_matches_manifest():
    assert should_keep_file("blockstates/stone.json")
    assert should_keep_file("lang/en_us.json")
    assert should_keep_file("textures/block/stone.png")
    assert not should_keep_file("generated/top/STAIRS_oak.png")
    assert should_keep_file("textures/block/custom/red_bed.png")


def test_plan_prune_reports_removable_files(tmp_path: Path):
    _touch(tmp_path / "blockstates/stone.json")
    _touch(tmp_path / "lang/en_us.json")
    _touch(tmp_path / "lang/fr_fr.json")
    _touch(tmp_path / "sounds/dig/stone1.ogg")
    _touch(tmp_path / "textures/block/stone.png")
    _touch(tmp_path / "generated/top/STAIRS_oak.png")

    plan = plan_prune(tmp_path)

    assert plan.keep_count == 3
    assert plan.remove_count == 3


def test_project_asset_migration_moves_custom_and_generated(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("helpers.migrate_project_assets.ASSETS_ROOT", tmp_path)
    monkeypatch.setattr(
        "helpers.migrate_project_assets.PROJECT_CUSTOM_FOLDER",
        tmp_path / "project" / "custom",
    )
    monkeypatch.setattr(
        "helpers.migrate_project_assets.GENERATED_ASSETS_FOLDER",
        tmp_path / "project" / "generated",
    )

    source = tmp_path / "minecraft_26_1_2"
    _touch(source / "textures/block/custom/red_bed.png", b"bed")
    _touch(source / "generated/top/STAIRS_oak.png", b"sprite")

    plan = plan_project_asset_migration(tmp_path)
    custom_copied, generated_copied = apply_project_asset_migration(plan)

    assert custom_copied == 1
    assert generated_copied == 1
    assert (tmp_path / "project/custom/red_bed.png").read_bytes() == b"bed"
    assert (tmp_path / "project/generated/top/STAIRS_oak.png").read_bytes() == b"sprite"
    assert not (source / "textures/block/custom").exists()
    assert not (source / "generated").exists()


def test_build_version_overlays_splits_shared_and_unique(tmp_path: Path):
    left = tmp_path / "left"
    right = tmp_path / "right"
    output = tmp_path / "versions"

    _touch(left / "blockstates/stone.json", b"shared")
    _touch(right / "blockstates/stone.json", b"shared")
    _touch(left / "lang/en_us.json", b"left-lang")
    _touch(right / "lang/en_us.json", b"right-lang")
    _touch(left / "textures/block/only_left.png", b"left-only")

    stats = build_version_overlays({"26.1.2": left, "26.2": right}, output)

    assert stats.base_files == 1
    assert stats.overlay_files["26.1.2"] == 2
    assert stats.overlay_files["26.2"] == 1
    assert (output / "base/blockstates/stone.json").read_bytes() == b"shared"
    assert (output / "26_1_2/lang/en_us.json").read_bytes() == b"left-lang"
    assert (output / "26_2/lang/en_us.json").read_bytes() == b"right-lang"


def test_materialize_version_merges_base_and_overlay(tmp_path: Path):
    versions = tmp_path / "versions"
    _touch(versions / "base/blockstates/stone.json", b"shared")
    _touch(versions / "26_2/lang/en_us.json", b"english")

    target = tmp_path / "minecraft"
    linked = materialize_version(versions, "26.2", target)

    assert linked == 2
    assert (target / "blockstates/stone.json").read_bytes() == b"shared"
    assert (target / "lang/en_us.json").read_bytes() == b"english"
