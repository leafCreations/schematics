"""UI-facing block picker resolution.

Turns the raw ``BLOCK_PALETTES`` / ``BLOCK_REGISTRY`` data into structured
entries a block picker can render: resolved labels, the cell token to write,
behavior/property requirements, and the list of valid materials for templated
tokens (derived from the generated catalog).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from helpers.block_catalog import (
    block_available_in_version,
    catalog_display_name,
    load_block_catalog,
    normalize_block_id,
)
from helpers.campfire_state import is_campfire_block_id
from helpers.minecraft_versions import normalize_minecraft_version
from helpers.palette_sections import normalize_palette_section_keys
from helpers.registry_lookup import is_minecraft_block_token, minecraft_block_id
from helpers.structure_tokens import BlockStates, format_block_states, parse_structure_token
from helpers.terrain_tokens import legacy_terrain_block_id, migrate_terrain_token
from registries.loader import BLOCK_PALETTES, BLOCK_REGISTRY

_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


@dataclass(frozen=True)
class PickerEntry:
    """A single selectable block in a palette tab."""

    token: str
    label: str
    behavior: str
    palette: str
    block_template: str | None = None
    material_field: str | None = None
    material_default: str | None = None
    requires_material: bool = False
    requires_direction: bool = False
    requires_variant: bool = False
    variants: tuple[str, ...] = ()
    materials: tuple[str, ...] = ()
    is_catalog_block: bool = False
    variant_blocks: tuple[tuple[str, str], ...] = ()
    section: str | None = None


@dataclass(frozen=True)
class PickerPalette:
    """A palette tab with its resolved entries."""

    name: str
    label: str
    entries: tuple[PickerEntry, ...] = field(default_factory=tuple)
    sections: tuple[str, ...] = ()


def _placeholder_field(template: str | None) -> str | None:
    if not template:
        return None

    match = _PLACEHOLDER_RE.search(template)

    return match.group(1) if match else None


def _default_block_template(entry: dict[str, Any]) -> str | None:
    minecraft = entry.get("minecraft", {})

    block = minecraft.get("block")
    if isinstance(block, str):
        return block

    variants = minecraft.get("variants", {})
    for variant in variants.values():
        block = variant.get("block")
        if isinstance(block, str):
            return block

    return None


def enumerate_token_materials(
    block_template: str | None,
    *,
    catalog: dict[str, Any] | None = None,
    minecraft_version: str | None = None,
) -> tuple[str, ...]:
    """Return materials/colors that produce a real catalog block for a template.

    Example: ``minecraft:{material}_planks`` -> ``("acacia", "birch", "oak", ...)``.
    """
    if not block_template or _placeholder_field(block_template) is None:
        return ()

    resolved_catalog = load_block_catalog() if catalog is None else catalog
    placeholder = _PLACEHOLDER_RE.search(block_template).group(0)
    prefix, _, suffix = block_template.partition(placeholder)

    materials: set[str] = set()

    for block_id in resolved_catalog:
        if not block_id.startswith(prefix) or not block_id.endswith(suffix):
            continue

        if len(block_id) <= len(prefix) + len(suffix):
            continue

        material = block_id[len(prefix) : len(block_id) - len(suffix) if suffix else None]

        if material:
            materials.add(material)

    resolved = tuple(sorted(materials))

    if minecraft_version is None:
        return resolved

    version = normalize_minecraft_version(minecraft_version)
    filtered: list[str] = []

    for material in resolved:
        block_id = block_template.format(material=material, color=material)

        if block_available_in_version(block_id, version, catalog=resolved_catalog):
            filtered.append(material)

    return tuple(filtered)


def _resolve_list_label(token: str, entry: dict[str, Any]) -> str:
    """Short palette list label without material/color (chosen in the paint brush)."""
    ui = entry.get("ui", {})
    label_template = ui.get("label", "")

    if _PLACEHOLDER_RE.search(label_template):
        stripped = _PLACEHOLDER_RE.sub("", label_template).strip()

        if stripped:
            return stripped

    if label_template and "{" not in label_template:
        return label_template

    return token.replace("_", " ").title()


def _resolve_label(entry: dict[str, Any], material: str | None) -> str:
    ui = entry.get("ui", {})
    label_template = ui.get("label", "")

    if material is not None:
        block_template = _default_block_template(entry)
        if block_template:
            block_id = block_template.format(material=material, color=material)
            display = catalog_display_name(block_id)
            if display:
                return display

        if "{" in label_template:
            return label_template.format(material=material, color=material)

    if "{" in label_template:
        return label_template

    return label_template or entry.get("behavior", "block")


def picker_entry_for_token(
    token: str,
    *,
    catalog: dict[str, Any] | None = None,
    minecraft_version: str | None = None,
) -> PickerEntry | None:
    """Build a :class:`PickerEntry` for a semantic registry token."""
    entry = BLOCK_REGISTRY.get(token)

    if entry is None:
        return None

    ui = entry.get("ui", {})
    block_template = _default_block_template(entry)
    material_field = _placeholder_field(block_template)
    requires_material = bool(ui.get("requires_material", False))

    material_default = entry.get("material_default") or entry.get("color_default")

    materials = ()

    if requires_material:
        if token == "LOG":
            from helpers.log_materials import enumerate_log_materials

            materials = enumerate_log_materials(catalog=catalog)
        else:
            materials = enumerate_token_materials(
                block_template,
                catalog=catalog,
                minecraft_version=minecraft_version,
            )

    return PickerEntry(
        token=token,
        label=_resolve_list_label(token, entry),
        behavior=entry.get("behavior", "solid"),
        palette=ui.get("palette", ""),
        block_template=block_template,
        material_field=material_field,
        material_default=material_default,
        requires_material=requires_material,
        requires_direction=bool(ui.get("requires_direction", False)),
        requires_variant=bool(ui.get("requires_variant", False)),
        variants=tuple(ui.get("variants", []) or ()),
        materials=materials,
    )


_picker_by_registry_token: dict[str, PickerEntry] | None = None
_picker_by_block_id: dict[str, PickerEntry] | None = None


def clear_picker_entry_cache() -> None:
    global _picker_by_registry_token, _picker_by_block_id
    _picker_by_registry_token = None
    _picker_by_block_id = None


def _ensure_picker_entry_indexes(*, catalog: dict[str, Any] | None = None) -> None:
    global _picker_by_registry_token, _picker_by_block_id

    if _picker_by_registry_token is not None and _picker_by_block_id is not None:
        return

    by_registry: dict[str, PickerEntry] = {}
    by_block: dict[str, PickerEntry] = {}

    for palette in list_palettes(catalog=catalog):
        for entry in palette.entries:
            if entry.is_catalog_block:
                for block_id in catalog_block_ids(entry):
                    by_block[block_id] = entry
            else:
                by_registry[entry.token] = entry

    _picker_by_registry_token = by_registry
    _picker_by_block_id = by_block


def homogeneous_picker_entry_for_positions(
    cells: list[list[str]],
    positions: list[tuple[int, int]],
) -> PickerEntry | None:
    """Return a palette entry when every *positions* cell is the same block type.

    Cells must be non-empty and resolve to the same registry token or catalog
    block id (e.g. ``PLANKS:oak`` and ``PLANKS:spruce`` both match ``PLANKS``).
    """
    if not positions:
        return None

    entry: PickerEntry | None = None

    for row, col in positions:
        try:
            raw = cells[row][col]
        except IndexError:
            return None

        if raw == ".":
            return None

        cell_entry = picker_entry_for_cell(raw)

        if cell_entry is None:
            return None

        if entry is None:
            entry = cell_entry
        elif cell_entry.token != entry.token:
            return None

    return entry


def cell_positions_with_same_block_type(
    cells: list[list[str]],
    reference_token: str,
) -> list[tuple[int, int]]:
    """Return every non-empty cell matching *reference_token*'s palette block type.

    Registry entries match on entry token and variant (e.g. ``PLANKS:oak`` and
    ``PLANKS:spruce`` match each other, but ``COBBLESTONE`` and
    ``COBBLESTONE#mossy`` do not).
    When the reference does not resolve to a palette entry, falls back to exact
    token string equality.
    """
    if reference_token == ".":
        return []

    entry = picker_entry_for_cell(reference_token)
    ref_parsed = parse_structure_token(reference_token)
    ref_variant = ref_parsed.variant if ref_parsed else None
    positions: list[tuple[int, int]] = []

    for row, line in enumerate(cells):
        for col, token in enumerate(line):
            if token == ".":
                continue

            if entry is not None:
                if entry.is_catalog_block:
                    if migrate_terrain_token(token) == migrate_terrain_token(reference_token):
                        positions.append((row, col))
                    continue

                cell_entry = picker_entry_for_cell(token)
                cell_parsed = parse_structure_token(token)
                cell_variant = cell_parsed.variant if cell_parsed else None

                if (
                    cell_entry is not None
                    and cell_entry.token == entry.token
                    and cell_variant == ref_variant
                ):
                    positions.append((row, col))
            elif token == reference_token:
                positions.append((row, col))

    return positions


def picker_entry_for_cell(raw_token: str) -> PickerEntry | None:
    """Return the palette entry that matches a structure-layer cell token."""
    parsed = parse_structure_token(raw_token)

    if parsed is None:
        return None

    _ensure_picker_entry_indexes()

    if is_minecraft_block_token(parsed):
        block_id = minecraft_block_id(parsed)
        assert _picker_by_block_id is not None
        return _picker_by_block_id.get(block_id) or picker_entry_for_block_id(block_id)

    legacy_block_id = legacy_terrain_block_id(parsed)

    if legacy_block_id is not None:
        assert _picker_by_block_id is not None
        return _picker_by_block_id.get(legacy_block_id) or picker_entry_for_block_id(
            legacy_block_id,
            palette="terrain",
        )

    assert _picker_by_registry_token is not None
    return _picker_by_registry_token.get(parsed.token) or picker_entry_for_token(parsed.token)


def catalog_block_ids(entry: PickerEntry) -> frozenset[str]:
    ids = {entry.token}

    for _variant_key, block_id in entry.variant_blocks:
        ids.add(block_id)

    return frozenset(ids)


def variant_key_for_catalog_block(entry: PickerEntry, block_id: str) -> str | None:
    normalized = normalize_block_id(block_id)

    for variant_key, variant_block_id in entry.variant_blocks:
        if normalize_block_id(variant_block_id) == normalized:
            return variant_key

    return None


def picker_entry_for_block_id(
    block_id: str,
    *,
    palette: str = "",
    catalog: dict[str, Any] | None = None,
    variants: dict[str, str] | None = None,
    section: str | None = None,
) -> PickerEntry:
    """Build a :class:`PickerEntry` for a raw ``minecraft:`` catalog block."""
    normalized = normalize_block_id(block_id)
    display = catalog_display_name(normalized, catalog=catalog)
    variant_items = tuple(
        (str(variant_key), normalize_block_id(variant_block_id))
        for variant_key, variant_block_id in sorted((variants or {}).items())
    )

    is_campfire = is_campfire_block_id(normalized)

    return PickerEntry(
        token=normalized,
        label=display or normalized.split(":", 1)[-1].replace("_", " ").title(),
        behavior="campfire" if is_campfire else "solid",
        palette=palette,
        is_catalog_block=True,
        requires_direction=is_campfire,
        variants=tuple(variant_key for variant_key, _block_id in variant_items),
        variant_blocks=variant_items,
        section=section,
    )


def _parse_palette_block_spec(
    block_spec: str | dict[str, Any],
) -> tuple[str, dict[str, str]]:
    if isinstance(block_spec, str):
        return normalize_block_id(block_spec), {}

    if not isinstance(block_spec, dict):
        raise ValueError(
            f"Palette block entry must be a string or mapping, got {type(block_spec)!r}"
        )

    block_id = block_spec.get("id")

    if not isinstance(block_id, str) or not block_id.strip():
        raise ValueError(f"Palette block entry missing string 'id': {block_spec!r}")

    raw_variants = block_spec.get("variants") or {}
    variants: dict[str, str] = {}

    if not isinstance(raw_variants, dict):
        raise ValueError(f"Palette block variants must be a mapping: {block_spec!r}")

    for variant_key, variant_block_id in raw_variants.items():
        if not isinstance(variant_key, str) or not isinstance(variant_block_id, str):
            raise ValueError(
                f"Palette block variant keys and values must be strings: {block_spec!r}"
            )

        variants[variant_key] = normalize_block_id(variant_block_id)

    return normalize_block_id(block_id), variants


def picker_entry_for_palette_block(
    block_spec: str | dict[str, Any],
    *,
    palette: str,
    catalog: dict[str, Any] | None = None,
    section: str | None = None,
) -> PickerEntry:
    block_id, variants = _parse_palette_block_spec(block_spec)
    return picker_entry_for_block_id(
        block_id,
        palette=palette,
        catalog=catalog,
        variants=variants,
        section=section,
    )


PaletteBlockSpec = tuple[str | None, str | dict[str, Any]]


def _collect_palette_block_specs(palette: dict[str, Any]) -> list[PaletteBlockSpec]:
    specs: list[PaletteBlockSpec] = []

    sections = palette.get("sections")
    if isinstance(sections, dict):
        for section_key in normalize_palette_section_keys(sections):
            section_blocks = sections.get(section_key) or []
            if not isinstance(section_blocks, list):
                raise ValueError(
                    f"Palette section {section_key!r} must be a list, got {type(section_blocks)!r}"
                )

            for block_spec in section_blocks:
                specs.append((section_key, block_spec))

        return specs

    for block_spec in palette.get("blocks", []) or ():
        specs.append((None, block_spec))

    return specs


def cell_token(
    entry: PickerEntry,
    material: str | None = None,
    *,
    direction: str | None = None,
    variant: str | None = None,
    states: BlockStates | None = None,
) -> str:
    """Return the structure-layer cell string for a picker selection."""
    if entry.is_catalog_block:
        block_id = entry.token

        if variant:
            for variant_key, variant_block_id in entry.variant_blocks:
                if variant_key == variant:
                    block_id = variant_block_id
                    break

        token = block_id

        if entry.requires_direction:
            token = f"{token}@{direction or 'north'}"

        if states:
            token = f"{token};{format_block_states(states)}"
        elif entry.behavior == "campfire":
            token = f"{token};lit=true"

        return token

    token = entry.token

    if entry.requires_material:
        chosen = material or entry.material_default

        if chosen:
            token = f"{token}:{chosen}"

    if direction and entry.requires_direction:
        token = f"{token}@{direction}"

    if variant:
        token = f"{token}#{variant}"

    if states:
        token = f"{token};{format_block_states(states)}"

    return token


def format_entry_label(
    entry: PickerEntry,
    material: str | None = None,
    *,
    catalog: dict[str, Any] | None = None,
) -> str:
    """Resolve a display label for a picker entry at a chosen material."""
    if not entry.requires_material or material is None:
        return entry.label

    if entry.behavior == "log":
        from helpers.log_materials import resolve_log_block_id

        block_id = resolve_log_block_id(material, catalog=catalog)
    elif entry.block_template:
        block_id = entry.block_template.format(material=material, color=material)
    else:
        return entry.label

    display = catalog_display_name(block_id, catalog=catalog)

    return display or f"{material} {entry.label}".strip()


def _picker_entry_available_for_version(
    entry: PickerEntry,
    *,
    catalog: dict[str, Any] | None,
    minecraft_version: str | None,
) -> bool:
    if minecraft_version is None:
        return True

    version = normalize_minecraft_version(minecraft_version)
    resolved_catalog = load_block_catalog() if catalog is None else catalog

    if entry.is_catalog_block:
        return any(
            block_available_in_version(block_id, version, catalog=resolved_catalog)
            for block_id in catalog_block_ids(entry)
        )

    if entry.requires_material:
        return bool(entry.materials)

    return True


def resolve_palette(
    name: str,
    *,
    catalog: dict[str, Any] | None = None,
    minecraft_version: str | None = None,
) -> PickerPalette | None:
    """Resolve a single palette tab into structured picker entries."""
    palette = BLOCK_PALETTES.get(name)

    if palette is None:
        return None

    entries: list[PickerEntry] = []
    section_keys: tuple[str, ...] = ()

    for token in palette.get("tokens", []) or ():
        token_entry = picker_entry_for_token(
            token,
            catalog=catalog,
            minecraft_version=minecraft_version,
        )

        if token_entry is not None and _picker_entry_available_for_version(
            token_entry,
            catalog=catalog,
            minecraft_version=minecraft_version,
        ):
            entries.append(token_entry)

    sections = palette.get("sections")
    if isinstance(sections, dict):
        section_keys = normalize_palette_section_keys(sections)

    for section_key, block_spec in _collect_palette_block_specs(palette):
        block_entry = picker_entry_for_palette_block(
            block_spec,
            palette=name,
            catalog=catalog,
            section=section_key,
        )

        if _picker_entry_available_for_version(
            block_entry,
            catalog=catalog,
            minecraft_version=minecraft_version,
        ):
            entries.append(block_entry)

    return PickerPalette(
        name=name,
        label=palette.get("label", name.title()),
        entries=tuple(entries),
        sections=section_keys,
    )


def picker_entry_search_terms(entry: PickerEntry) -> tuple[str, ...]:
    """Lowercase strings used to match palette search queries."""
    terms: list[str] = [
        entry.label,
        entry.token,
        entry.behavior,
        entry.palette,
    ]

    if entry.section:
        terms.append(entry.section)

    for variant_key in entry.variants:
        terms.append(variant_key)

    for variant_key, block_id in entry.variant_blocks:
        terms.append(variant_key)
        terms.append(block_id)

        block_name = block_id.split(":", 1)[-1]
        terms.append(block_name)
        terms.append(block_name.replace("_", " "))

    for material in entry.materials:
        terms.append(material)

    return tuple(term.casefold() for term in terms if term)


def entry_matches_search(entry: PickerEntry, query: str) -> bool:
    """Return whether ``query`` matches a palette entry's searchable fields."""
    normalized = query.strip().casefold()

    if not normalized:
        return True

    query_variants = {
        normalized,
        normalized.replace(" ", "_"),
        normalized.replace("_", " "),
    }

    for term in picker_entry_search_terms(entry):
        for query_variant in query_variants:
            if query_variant in term:
                return True

    return False


def search_picker_entries(
    palettes: list[PickerPalette],
    query: str,
) -> list[PickerEntry]:
    """Return palette entries matching ``query`` across every palette tab."""
    normalized = query.strip()

    if not normalized:
        return []

    results: list[PickerEntry] = []

    for palette in palettes:
        for entry in palette.entries:
            if entry_matches_search(entry, query):
                results.append(entry)

    return results


def list_palettes(
    *,
    catalog: dict[str, Any] | None = None,
    minecraft_version: str | None = None,
) -> list[PickerPalette]:
    """Resolve every palette tab into structured picker entries."""
    resolved: list[PickerPalette] = []

    for name in sorted(BLOCK_PALETTES):
        palette = resolve_palette(name, catalog=catalog, minecraft_version=minecraft_version)

        if palette is not None:
            resolved.append(palette)

    return resolved
