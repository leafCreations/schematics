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

from helpers.block_catalog import catalog_display_name, load_block_catalog, normalize_block_id
from helpers.registry_lookup import is_minecraft_block_token, minecraft_block_id
from helpers.structure_tokens import BlockStates, format_block_states, parse_structure_token
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


@dataclass(frozen=True)
class PickerPalette:
    """A palette tab with its resolved entries."""

    name: str
    label: str
    entries: tuple[PickerEntry, ...] = field(default_factory=tuple)


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

    return tuple(sorted(materials))


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

    materials = (
        enumerate_token_materials(block_template, catalog=catalog) if requires_material else ()
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


def picker_entry_for_cell(raw_token: str) -> PickerEntry | None:
    """Return the palette entry that matches a structure-layer cell token."""
    parsed = parse_structure_token(raw_token)

    if parsed is None:
        return None

    if is_minecraft_block_token(parsed):
        block_id = minecraft_block_id(parsed)

        for palette in list_palettes():
            for entry in palette.entries:
                if entry.token == block_id:
                    return entry

        return picker_entry_for_block_id(block_id)

    for palette in list_palettes():
        for entry in palette.entries:
            if not entry.is_catalog_block and entry.token == parsed.token:
                return entry

    return picker_entry_for_token(parsed.token)


def picker_entry_for_block_id(
    block_id: str,
    *,
    palette: str = "",
    catalog: dict[str, Any] | None = None,
) -> PickerEntry:
    """Build a :class:`PickerEntry` for a raw ``minecraft:`` catalog block."""
    normalized = normalize_block_id(block_id)
    display = catalog_display_name(normalized, catalog=catalog)

    return PickerEntry(
        token=normalized,
        label=display or normalized.split(":", 1)[-1].replace("_", " ").title(),
        behavior="solid",
        palette=palette,
        is_catalog_block=True,
    )


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
        return entry.token

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
    if not entry.requires_material or material is None or not entry.block_template:
        return entry.label

    block_id = entry.block_template.format(material=material, color=material)
    display = catalog_display_name(block_id, catalog=catalog)

    return display or f"{material} {entry.label}".strip()


def resolve_palette(name: str, *, catalog: dict[str, Any] | None = None) -> PickerPalette | None:
    """Resolve a single palette tab into structured picker entries."""
    palette = BLOCK_PALETTES.get(name)

    if palette is None:
        return None

    entries: list[PickerEntry] = []

    for token in palette.get("tokens", []) or ():
        token_entry = picker_entry_for_token(token, catalog=catalog)

        if token_entry is not None:
            entries.append(token_entry)

    for block_id in palette.get("blocks", []) or ():
        entries.append(picker_entry_for_block_id(block_id, palette=name, catalog=catalog))

    return PickerPalette(
        name=name,
        label=palette.get("label", name.title()),
        entries=tuple(entries),
    )


def list_palettes(*, catalog: dict[str, Any] | None = None) -> list[PickerPalette]:
    """Resolve every palette tab into structured picker entries."""
    resolved: list[PickerPalette] = []

    for name in sorted(BLOCK_PALETTES):
        palette = resolve_palette(name, catalog=catalog)

        if palette is not None:
            resolved.append(palette)

    return resolved
