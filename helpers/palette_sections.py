"""Palette section keys and display labels (e.g. terrain dimensions)."""

from __future__ import annotations

PALETTE_SECTION_ALL = ""
PALETTE_SECTION_ORDER = ("overworld", "nether", "end")
PALETTE_SECTION_LABELS = {
    "overworld": "Overworld",
    "nether": "Nether",
    "end": "The End",
}


def palette_section_label(section_key: str) -> str:
    return PALETTE_SECTION_LABELS.get(section_key, section_key.replace("_", " ").title())


def normalize_palette_section_keys(sections: dict[str, object]) -> tuple[str, ...]:
    ordered: list[str] = []

    for section_key in PALETTE_SECTION_ORDER:
        if section_key in sections:
            ordered.append(section_key)

    for section_key in sections:
        if section_key not in ordered:
            ordered.append(str(section_key))

    return tuple(ordered)
