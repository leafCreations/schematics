"""Migrate legacy project-owned assets out of versioned Minecraft extracts."""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from helpers.minecraft_asset_manifest import discover_versioned_asset_roots
from helpers.paths import (
    ASSETS_ROOT,
    GENERATED_ASSETS_FOLDER,
    LEGACY_GENERATED_ASSETS_FOLDER,
    LEGACY_PROJECT_CUSTOM_FOLDER,
    PROJECT_CUSTOM_FOLDER,
)

LEGACY_CUSTOM_RELATIVE = Path("textures/block/custom")
LEGACY_GENERATED_NAME = "generated"


@dataclass(frozen=True)
class MigrationPlan:
    custom_sources: tuple[Path, ...]
    generated_sources: tuple[Path, ...]
    custom_files: tuple[Path, ...]
    generated_files: tuple[Path, ...]


def _iter_files(root: Path) -> Iterator[Path]:
    if not root.is_dir():
        return
    yield from (path for path in root.rglob("*") if path.is_file())


def plan_project_asset_migration(assets_root: Path = ASSETS_ROOT) -> MigrationPlan:
    custom_sources: list[Path] = []
    generated_sources: list[Path] = []
    custom_files: list[Path] = []
    generated_files: list[Path] = []

    for minecraft_root in discover_versioned_asset_roots(assets_root):
        legacy_custom = minecraft_root / LEGACY_CUSTOM_RELATIVE
        if legacy_custom.is_dir():
            custom_sources.append(legacy_custom)
            custom_files.extend(_iter_files(legacy_custom))

        legacy_generated = minecraft_root / LEGACY_GENERATED_NAME
        if legacy_generated.is_dir():
            generated_sources.append(legacy_generated)
            generated_files.extend(_iter_files(legacy_generated))

    if LEGACY_PROJECT_CUSTOM_FOLDER.is_dir() and LEGACY_PROJECT_CUSTOM_FOLDER not in custom_sources:
        custom_sources.append(LEGACY_PROJECT_CUSTOM_FOLDER)
        custom_files.extend(_iter_files(LEGACY_PROJECT_CUSTOM_FOLDER))

    if (
        LEGACY_GENERATED_ASSETS_FOLDER.is_dir()
        and LEGACY_GENERATED_ASSETS_FOLDER not in generated_sources
    ):
        generated_sources.append(LEGACY_GENERATED_ASSETS_FOLDER)
        generated_files.extend(_iter_files(LEGACY_GENERATED_ASSETS_FOLDER))

    return MigrationPlan(
        custom_sources=tuple(custom_sources),
        generated_sources=tuple(generated_sources),
        custom_files=tuple(custom_files),
        generated_files=tuple(generated_files),
    )


def _copy_tree_files(source_root: Path, target_root: Path) -> int:
    copied = 0
    for source in _iter_files(source_root):
        relative = source.relative_to(source_root)
        target = target_root / relative
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied += 1
    return copied


def apply_project_asset_migration(
    plan: MigrationPlan,
    *,
    remove_legacy: bool = True,
) -> tuple[int, int]:
    custom_copied = 0
    generated_copied = 0

    for source in plan.custom_sources:
        custom_copied += _copy_tree_files(source, PROJECT_CUSTOM_FOLDER)

    for source in plan.generated_sources:
        generated_copied += _copy_tree_files(source, GENERATED_ASSETS_FOLDER)

    if remove_legacy:
        for source in plan.custom_sources:
            shutil.rmtree(source, ignore_errors=True)
        for source in plan.generated_sources:
            shutil.rmtree(source, ignore_errors=True)

    return custom_copied, generated_copied
