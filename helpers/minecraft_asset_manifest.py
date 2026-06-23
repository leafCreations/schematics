"""Allowlist for pruned Minecraft client resource extracts.

Only paths listed here are kept by ``scripts/prune_minecraft_assets.py``.
See ``docs/assets.md`` for rationale and setup.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

# Directories kept in full (relative to the assets root).
KEEP_DIR_PREFIXES: tuple[str, ...] = (
    "blockstates",
    "models/block",
    "textures/block",
    "textures/item",
    "textures/entity/bed",
    "textures/entity/chest",
)

# Individual files kept outside the directory prefixes above.
KEEP_FILES: frozenset[str] = frozenset({"lang/en_us.json"})


def is_under(relative_posix: str, prefix: str) -> bool:
    return relative_posix == prefix or relative_posix.startswith(f"{prefix}/")


def should_keep_file(
    relative_posix: str,
    *,
    preserve_generated: bool = True,
) -> bool:
    del preserve_generated
    if relative_posix in KEEP_FILES:
        return True

    return any(is_under(relative_posix, prefix) for prefix in KEEP_DIR_PREFIXES)


@dataclass(frozen=True)
class PrunePlan:
    assets_root: Path
    remove_files: tuple[Path, ...]
    keep_files: tuple[Path, ...]
    bytes_removed: int

    @property
    def remove_count(self) -> int:
        return len(self.remove_files)

    @property
    def keep_count(self) -> int:
        return len(self.keep_files)


def plan_prune(
    assets_root: Path,
    *,
    preserve_generated: bool = True,
) -> PrunePlan:
    if not assets_root.is_dir():
        raise FileNotFoundError(f"Assets root not found: {assets_root}")

    remove_files: list[Path] = []
    keep_files: list[Path] = []
    bytes_removed = 0

    for path in sorted(assets_root.rglob("*")):
        if not path.is_file():
            continue

        relative_posix = path.relative_to(assets_root).as_posix()
        if should_keep_file(relative_posix, preserve_generated=preserve_generated):
            keep_files.append(path)
            continue

        remove_files.append(path)
        bytes_removed += path.stat().st_size

    return PrunePlan(
        assets_root=assets_root,
        remove_files=tuple(remove_files),
        keep_files=tuple(keep_files),
        bytes_removed=bytes_removed,
    )


def apply_prune(plan: PrunePlan) -> None:
    for path in plan.remove_files:
        path.unlink(missing_ok=True)

    _remove_empty_dirs(plan.assets_root)


def _remove_empty_dirs(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def discover_versioned_asset_roots(assets_root: Path) -> list[Path]:
    if not assets_root.is_dir():
        return []

    versioned = sorted(
        path
        for path in assets_root.iterdir()
        if path.is_dir() and path.name.startswith("minecraft_")
    )
    active = assets_root / "minecraft"
    if active.is_dir() and active not in versioned:
        versioned.insert(0, active)

    return versioned


def iter_default_prune_targets(assets_root: Path) -> Iterator[Path]:
    yield from discover_versioned_asset_roots(assets_root)
