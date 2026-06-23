"""Build versioned base + overlay trees from pruned Minecraft extracts."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from helpers.paths import minecraft_version_dir_name


@dataclass(frozen=True)
class DedupeStats:
    base_files: int
    overlay_files: dict[str, int]
    bytes_in_base: int
    bytes_in_overlays: int


def _iter_relative_files(root: Path) -> dict[str, Path]:
    return {path.relative_to(root).as_posix(): path for path in root.rglob("*") if path.is_file()}


def _same_file(left: Path, right: Path) -> bool:
    if left.stat().st_size != right.stat().st_size:
        return False
    return left.read_bytes() == right.read_bytes()


def plan_dedupe_sources(sources: dict[str, Path]) -> tuple[set[str], dict[str, set[str]]]:
    """Return all relative paths and which versions contain each path."""
    all_paths: set[str] = set()
    versions_by_path: dict[str, set[str]] = {}

    for version, root in sources.items():
        for relative in _iter_relative_files(root):
            all_paths.add(relative)
            versions_by_path.setdefault(relative, set()).add(version)

    return all_paths, versions_by_path


def build_version_overlays(
    sources: dict[str, Path],
    output_root: Path,
    *,
    clean_output: bool = False,
) -> DedupeStats:
    if clean_output and output_root.exists():
        shutil.rmtree(output_root)

    base_dir = output_root / "base"
    overlay_dirs = {
        version: output_root / minecraft_version_dir_name(version) for version in sources
    }
    base_dir.mkdir(parents=True, exist_ok=True)

    for overlay_dir in overlay_dirs.values():
        overlay_dir.mkdir(parents=True, exist_ok=True)

    source_files = {version: _iter_relative_files(root) for version, root in sources.items()}
    all_paths, versions_by_path = plan_dedupe_sources(sources)

    base_files = 0
    bytes_in_base = 0
    overlay_counts = dict.fromkeys(sources, 0)
    bytes_in_overlays = 0

    for relative in sorted(all_paths):
        present_versions = sorted(versions_by_path[relative])
        paths = [source_files[version][relative] for version in present_versions]

        if len(paths) == 1:
            version = present_versions[0]
            target = overlay_dirs[version] / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(paths[0], target)
            overlay_counts[version] += 1
            bytes_in_overlays += paths[0].stat().st_size
            continue

        if all(_same_file(paths[0], path) for path in paths[1:]):
            target = base_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(paths[0], target)
            base_files += 1
            bytes_in_base += paths[0].stat().st_size
            continue

        for version in present_versions:
            source = source_files[version][relative]
            target = overlay_dirs[version] / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            overlay_counts[version] += 1
            bytes_in_overlays += source.stat().st_size

    return DedupeStats(
        base_files=base_files,
        overlay_files=overlay_counts,
        bytes_in_base=bytes_in_base,
        bytes_in_overlays=bytes_in_overlays,
    )


def materialize_version(
    versions_root: Path,
    version: str,
    target_root: Path,
    *,
    clean_target: bool = True,
) -> int:
    """Hardlink base + overlay into a merged resource tree."""
    base_dir = versions_root / "base"
    overlay_dir = versions_root / minecraft_version_dir_name(version)

    if clean_target and target_root.exists():
        shutil.rmtree(target_root)

    target_root.mkdir(parents=True, exist_ok=True)

    linked = 0
    for source_root in (base_dir, overlay_dir):
        if not source_root.is_dir():
            continue

        for source in source_root.rglob("*"):
            if not source.is_file():
                continue

            relative = source.relative_to(source_root)
            target = target_root / relative
            if target.exists():
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(source, target)
            except OSError:
                shutil.copy2(source, target)
            linked += 1

    return linked
