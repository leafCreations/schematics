"""Registry integrity checks for palettes, behaviors, and the block catalog."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from helpers.block_catalog import load_block_catalog
from helpers.block_picker import _parse_palette_block_spec
from helpers.paths import BLOCK_TEXTURES_FOLDER, GENERATED_ASSETS_FOLDER
from registries.loader import (
    BLOCK_PALETTES,
    BLOCK_REGISTRY,
    find_block_texture_path,
    resolve_registry_texture_filename,
)

_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")
_MATERIAL_PLACEHOLDERS = frozenset({"material", "color"})
_DIRECTION_PLACEHOLDERS = frozenset({"direction", "north", "south", "east", "west", "axis"})


def _placeholders_in_value(value: Any) -> set[str]:
    if not isinstance(value, str):
        return set()

    return set(_PLACEHOLDER_RE.findall(value))


def _behavior_block_template(entry: dict[str, Any]) -> str | None:
    minecraft = entry.get("minecraft", {})

    block = minecraft.get("block")
    if isinstance(block, str):
        return block

    for variant in (minecraft.get("variants") or {}).values():
        if isinstance(variant, dict):
            variant_block = variant.get("block")
            if isinstance(variant_block, str):
                return variant_block

    return None


def _collect_behavior_placeholders(entry: dict[str, Any]) -> set[str]:
    placeholders: set[str] = set()
    minecraft = entry.get("minecraft", {})

    template = _behavior_block_template(entry)
    if template:
        placeholders |= _placeholders_in_value(template)

    for value in (minecraft.get("blockstates") or {}).values():
        placeholders |= _placeholders_in_value(value)

    for variant in (minecraft.get("variants") or {}).values():
        if not isinstance(variant, dict):
            continue

        placeholders |= _placeholders_in_value(variant.get("block"))

        for value in (variant.get("blockstates") or {}).values():
            placeholders |= _placeholders_in_value(value)

    return placeholders


def collect_behavior_integrity_errors(
    *,
    block_registry: dict[str, Any] | None = None,
) -> list[str]:
    """Validate behavior YAML shape, minecraft blocks, and UI placeholder consistency."""
    registry = BLOCK_REGISTRY if block_registry is None else block_registry
    errors: list[str] = []

    for token, entry in registry.items():
        if not isinstance(entry, dict):
            errors.append(f"behaviors: token {token!r} must be a mapping")
            continue

        if not entry.get("behavior"):
            errors.append(f"behaviors: token {token!r} missing 'behavior'")

        minecraft = entry.get("minecraft")
        if not isinstance(minecraft, dict):
            errors.append(f"behaviors: token {token!r} missing 'minecraft'")
            continue

        has_block = isinstance(minecraft.get("block"), str)
        has_variants = bool(minecraft.get("variants"))

        if not has_block and not has_variants:
            errors.append(f"behaviors: token {token!r} needs minecraft.block or minecraft.variants")

        ui = entry.get("ui", {})
        placeholders = _collect_behavior_placeholders(entry)

        if ui.get("requires_material") and not placeholders.intersection(_MATERIAL_PLACEHOLDERS):
            errors.append(
                f"behaviors: token {token!r} requires_material but no "
                "{{material}} or {{color}} in minecraft templates"
            )

        if ui.get("requires_direction") and not placeholders.intersection(_DIRECTION_PLACEHOLDERS):
            errors.append(
                f"behaviors: token {token!r} requires_direction but no direction/axis "
                "placeholders in minecraft templates or blockstates"
            )

        if ui.get("requires_variant") and not has_variants:
            errors.append(
                f"behaviors: token {token!r} requires_variant but minecraft.variants is missing"
            )

    return errors


def _assets_available_for_texture_checks(assets_dir: Path) -> bool:
    if not assets_dir.is_dir():
        return False

    return any(assets_dir.rglob("*.png"))


def _texture_exists(
    texture_name: str,
    *,
    assets_dir: Path,
    generated_dir: Path,
) -> bool:
    if find_block_texture_path(assets_dir, texture_name) is not None:
        return True

    generated_path = generated_dir / texture_name
    return generated_path.is_file()


def collect_behavior_texture_errors(
    *,
    block_registry: dict[str, Any] | None = None,
    assets_dir: Path | None = None,
    generated_dir: Path | None = None,
) -> list[str]:
    """Flag missing top-view texture files when local assets are present."""
    registry = BLOCK_REGISTRY if block_registry is None else block_registry
    resolved_assets = BLOCK_TEXTURES_FOLDER if assets_dir is None else assets_dir
    resolved_generated = GENERATED_ASSETS_FOLDER if generated_dir is None else generated_dir

    if not _assets_available_for_texture_checks(resolved_assets):
        return []

    errors: list[str] = []
    seen: set[tuple[str, str]] = set()

    for token, entry in registry.items():
        if not isinstance(entry, dict):
            continue

        behavior = entry.get("behavior")
        render_textures = entry.get("render", {}).get("textures", {})

        if behavior in {"fence", "wall"} or isinstance(render_textures.get("top"), dict):
            continue

        if "top" not in render_textures:
            continue

        texture_name = resolve_registry_texture_filename(entry, "top")

        if not texture_name or "{" in texture_name:
            continue

        cache_key = (token, texture_name)
        if cache_key in seen:
            continue

        seen.add(cache_key)

        if not _texture_exists(
            texture_name,
            assets_dir=resolved_assets,
            generated_dir=resolved_generated,
        ):
            errors.append(
                f"behaviors: token {token!r} top texture {texture_name!r} not found under "
                f"assets or generated sprites"
            )

    return errors


def collect_palette_integrity_errors(
    *,
    block_registry: dict[str, Any] | None = None,
    block_palettes: dict[str, dict[str, Any]] | None = None,
    catalog: dict[str, Any] | None = None,
    check_textures: bool = True,
) -> list[str]:
    """Return human-readable integrity violations, or an empty list when valid."""
    registry = BLOCK_REGISTRY if block_registry is None else block_registry
    palettes = BLOCK_PALETTES if block_palettes is None else block_palettes
    resolved_catalog = load_block_catalog() if catalog is None else catalog

    errors: list[str] = []
    errors.extend(collect_behavior_integrity_errors(block_registry=registry))

    if check_textures:
        errors.extend(collect_behavior_texture_errors(block_registry=registry))

    for palette_name, palette in palettes.items():
        if not isinstance(palette, dict):
            errors.append(f"palettes/{palette_name}.yaml must contain a mapping")
            continue

        for token in palette.get("tokens", []) or []:
            if token not in registry:
                errors.append(f"palettes/{palette_name}.yaml references unknown token {token!r}")

        for block_spec in palette.get("blocks", []) or []:
            try:
                block_id, variants = _parse_palette_block_spec(block_spec)
            except ValueError as exc:
                errors.append(f"palettes/{palette_name}.yaml has invalid block entry: {exc}")
                continue

            block_ids = [block_id, *variants.values()]

            for catalog_block_id in block_ids:
                if catalog_block_id not in resolved_catalog:
                    errors.append(
                        "palettes/"
                        f"{palette_name}.yaml references unknown catalog block "
                        f"{catalog_block_id!r}"
                    )

        sections = palette.get("sections")
        if isinstance(sections, dict):
            for section_key, section_blocks in sections.items():
                if not isinstance(section_blocks, list):
                    errors.append(
                        f"palettes/{palette_name}.yaml section {section_key!r} must be a list"
                    )
                    continue

                for block_spec in section_blocks:
                    try:
                        block_id, variants = _parse_palette_block_spec(block_spec)
                    except ValueError as exc:
                        errors.append(
                            f"palettes/{palette_name}.yaml section {section_key!r} "
                            f"has invalid block entry: {exc}"
                        )
                        continue

                    block_ids = [block_id, *variants.values()]

                    for catalog_block_id in block_ids:
                        if catalog_block_id not in resolved_catalog:
                            errors.append(
                                "palettes/"
                                f"{palette_name}.yaml section {section_key!r} "
                                f"references unknown catalog block {catalog_block_id!r}"
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
    check_textures: bool = True,
) -> None:
    """Raise ``ValueError`` when registry references or behavior entries are inconsistent."""
    errors = collect_palette_integrity_errors(
        block_registry=block_registry,
        block_palettes=block_palettes,
        catalog=catalog,
        check_textures=check_textures,
    )

    if errors:
        joined = "\n".join(f"  - {error}" for error in errors)
        raise ValueError(f"Palette integrity check failed:\n{joined}")
