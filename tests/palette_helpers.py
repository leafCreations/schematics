"""Palette test helpers — avoid hard-coded block counts that change with catalog updates."""

from __future__ import annotations

from helpers.block_picker import resolve_palette


def terrain_section_entry_counts() -> dict[str, int]:
    """Return terrain palette entry counts keyed by dimension section."""
    return palette_section_entry_counts("terrain")


def palette_section_entry_counts(palette_name: str) -> dict[str, int]:
    """Return palette entry counts keyed by dimension section."""
    palette = resolve_palette(palette_name)
    if palette is None:
        raise AssertionError(f"{palette_name} palette missing")

    return {
        section: sum(1 for entry in palette.entries if entry.section == section)
        for section in palette.sections
    }
