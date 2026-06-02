"""Registry integrity checks for palettes, behaviors, and the block catalog."""

from __future__ import annotations

from typing import Any

from helpers.block_catalog import load_block_catalog, normalize_block_id
from registries.loader import BLOCK_PALETTES, BLOCK_REGISTRY


def collect_palette_integrity_errors(
    *,
    block_registry: dict[str, Any] | None = None,
    block_palettes: dict[str, dict[str, Any]] | None = None,
    catalog: dict[str, Any] | None = None,
) -> list[str]:
    """Return human-readable integrity violations, or an empty list when valid."""
    registry = BLOCK_REGISTRY if block_registry is None else block_registry
    palettes = BLOCK_PALETTES if block_palettes is None else block_palettes
    resolved_catalog = load_block_catalog() if catalog is None else catalog

    errors: list[str] = []

    for palette_name, palette in palettes.items():
        if not isinstance(palette, dict):
            errors.append(f"palettes/{palette_name}.yaml must contain a mapping")
            continue

        for token in palette.get("tokens", []) or []:
            if token not in registry:
                errors.append(f"palettes/{palette_name}.yaml references unknown token {token!r}")

        for block_id in palette.get("blocks", []) or []:
            normalized = normalize_block_id(block_id)

            if normalized not in resolved_catalog:
                errors.append(
                    f"palettes/{palette_name}.yaml references unknown catalog block {block_id!r}"
                )

    for token, entry in registry.items():
        ui = entry.get("ui", {})
        palette_name = ui.get("palette")

        if palette_name and palette_name not in palettes:
            errors.append(f"behaviors token {token!r} references unknown palette {palette_name!r}")

    return errors


def validate_palettes(
    *,
    block_registry: dict[str, Any] | None = None,
    block_palettes: dict[str, dict[str, Any]] | None = None,
    catalog: dict[str, Any] | None = None,
) -> None:
    """Raise ``ValueError`` when palette/behavior/catalog references are inconsistent."""
    errors = collect_palette_integrity_errors(
        block_registry=block_registry,
        block_palettes=block_palettes,
        catalog=catalog,
    )

    if errors:
        joined = "\n".join(f"  - {error}" for error in errors)
        raise ValueError(f"Palette integrity check failed:\n{joined}")
