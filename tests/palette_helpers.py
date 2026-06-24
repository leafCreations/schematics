"""Palette test helpers — avoid hard-coded block counts that change with catalog updates."""

from __future__ import annotations

from helpers.block_picker import resolve_palette
from helpers.minecraft_versions import DEFAULT_STRUCTURE_MINECRAFT_VERSION


def terrain_section_entry_counts(
    *,
    minecraft_version: str = DEFAULT_STRUCTURE_MINECRAFT_VERSION,
) -> dict[str, int]:
    """Return terrain palette entry counts keyed by dimension section."""
    return palette_section_entry_counts("terrain", minecraft_version=minecraft_version)


def palette_section_entry_counts(
    palette_name: str,
    *,
    minecraft_version: str = DEFAULT_STRUCTURE_MINECRAFT_VERSION,
) -> dict[str, int]:
    """Return palette entry counts keyed by dimension section."""
    palette = resolve_palette(palette_name, minecraft_version=minecraft_version)
    if palette is None:
        raise AssertionError(f"{palette_name} palette missing")

    return {
        section: sum(1 for entry in palette.entries if entry.section == section)
        for section in palette.sections
    }
