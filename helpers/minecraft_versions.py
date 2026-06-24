"""Supported Minecraft Java versions for structure packages."""

from __future__ import annotations

SUPPORTED_MINECRAFT_VERSIONS: tuple[str, ...] = ("26.1.2", "26.2")

DEFAULT_STRUCTURE_MINECRAFT_VERSION = "26.1.2"


def normalize_minecraft_version(value: object) -> str:
    """Return a supported version string or the default."""
    version = str(value or "").strip()

    if version in SUPPORTED_MINECRAFT_VERSIONS:
        return version

    return DEFAULT_STRUCTURE_MINECRAFT_VERSION


def _version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def compare_minecraft_versions(left: str, right: str) -> int:
    """Compare two version strings. Returns -1, 0, or 1."""
    left_tuple = _version_tuple(normalize_minecraft_version(left))
    right_tuple = _version_tuple(normalize_minecraft_version(right))

    if left_tuple < right_tuple:
        return -1

    if left_tuple > right_tuple:
        return 1

    return 0


def minecraft_version_at_least(*, structure_version: str, required_version: str) -> bool:
    """Return whether *structure_version* is >= *required_version*."""
    return compare_minecraft_versions(structure_version, required_version) >= 0


def format_version_title_suffix(version: object) -> str:
    """Return a title-bar suffix such as `` (v26.1.2)``."""
    normalized = normalize_minecraft_version(version)
    return f" (v{normalized})"
