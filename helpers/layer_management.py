"""Add, remove, and copy structure layers in the editor."""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from helpers.grid_cells import empty_cells

_LAYER_FILE_RE = re.compile(r"layer_(\d+)\.yaml$")


def layer_worldgen_index(layer: dict[str, Any], list_index: int) -> int:
    return int(layer.get("index", list_index))


def layers_by_worldgen_index(layers: list[dict[str, Any]]) -> list[int]:
    """List indices sorted by ascending worldgen ``index`` (lowest Y first)."""
    return sorted(
        range(len(layers)),
        key=lambda list_index: (layer_worldgen_index(layers[list_index], list_index), list_index),
    )


def swap_worldgen_indices_between_layers(layer_a: dict[str, Any], layer_b: dict[str, Any]) -> None:
    index_a = int(layer_a["index"])
    index_b = int(layer_b["index"])
    layer_a["index"] = index_b
    layer_b["index"] = index_a


def layer_label(layer: dict[str, Any], list_index: int) -> str:
    group = layer.get("group")
    if group:
        return str(group)
    return f"Layer {layer_worldgen_index(layer, list_index)}"


def layer_display_label(layer: dict[str, Any], list_index: int) -> str:
    """User-facing layer title: ``description`` when set, otherwise ``group``."""
    description = layer.get("description")

    if isinstance(description, str) and description.strip():
        return description.strip()

    return layer_label(layer, list_index)


def set_layer_description(layer: dict[str, Any], description: str) -> None:
    normalized = description.strip()

    if normalized:
        layer["description"] = normalized
    else:
        layer.pop("description", None)


def next_layer_relative_path(existing_paths: list[Path]) -> str:
    """Return a new ``layers/layer_NN.yaml`` path not in *existing_paths*."""
    max_num = -1

    for path in existing_paths:
        match = _LAYER_FILE_RE.match(path.name)

        if match:
            max_num = max(max_num, int(match.group(1)))

    return f"layers/layer_{max_num + 1:02d}.yaml"


def used_worldgen_indices(layers: list[dict[str, Any]]) -> set[int]:
    return {int(layer["index"]) for layer in layers if "index" in layer}


def worldgen_index_in_use(
    layers: list[dict[str, Any]],
    index: int,
    *,
    except_layer_index: int | None = None,
) -> bool:
    target = int(index)

    for layer_index, layer in enumerate(layers):
        if except_layer_index is not None and layer_index == except_layer_index:
            continue

        if "index" in layer and int(layer["index"]) == target:
            return True

    return False


def next_worldgen_index(layers: list[dict[str, Any]]) -> int:
    """Return an unused worldgen ``index`` for a new layer."""
    used = used_worldgen_indices(layers)
    candidate = max(used, default=-1) + 1

    while candidate in used:
        candidate += 1

    return candidate


def create_layer(
    *,
    width: int,
    depth: int,
    worldgen_index: int,
    group: str,
    description: str = "",
    cells: list[list[str]] | None = None,
) -> dict[str, Any]:
    layer: dict[str, Any] = {
        "index": int(worldgen_index),
        "group": group,
        "cells": copy.deepcopy(cells) if cells is not None else empty_cells(width, depth),
    }
    set_layer_description(layer, description)
    return layer


def copy_layer_dict(layer: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(layer)


def adjust_site_structure_layers_after_remove(grid: dict[str, Any], removed_index: int) -> None:
    """Update ``site_structure_layers`` list indices after deleting a layer."""
    indices = grid.get("site_structure_layers")

    if not isinstance(indices, list):
        return

    adjusted: list[int] = []

    for layer_idx in indices:
        if not isinstance(layer_idx, int):
            continue

        if layer_idx == removed_index:
            continue

        adjusted.append(layer_idx - 1 if layer_idx > removed_index else layer_idx)

    if adjusted:
        grid["site_structure_layers"] = adjusted
    elif grid.get("site_structure_layers"):
        grid["site_structure_layers"] = [0]


def remap_site_structure_layers_after_swap(
    grid: dict[str, Any],
    index_a: int,
    index_b: int,
) -> None:
    """Swap entries in ``site_structure_layers`` when two layers trade positions."""
    indices = grid.get("site_structure_layers")

    if not isinstance(indices, list):
        return

    grid["site_structure_layers"] = [
        index_b if idx == index_a else index_a if idx == index_b else idx
        for idx in indices
        if isinstance(idx, int)
    ]


def remap_indices_after_permutation(indices: set[int], permutation: list[int]) -> set[int]:
    inverse = [0] * len(permutation)

    for new_index, old_index in enumerate(permutation):
        inverse[old_index] = new_index

    return {inverse[idx] for idx in indices if 0 <= idx < len(inverse)}


def remap_site_structure_layers_after_permutation(
    grid: dict[str, Any],
    permutation: list[int],
) -> None:
    """Remap ``site_structure_layers`` after layers are reordered."""
    indices = grid.get("site_structure_layers")

    if not isinstance(indices, list):
        return

    inverse = [0] * len(permutation)

    for new_index, old_index in enumerate(permutation):
        inverse[old_index] = new_index

    grid["site_structure_layers"] = [
        inverse[idx] for idx in indices if isinstance(idx, int) and 0 <= idx < len(inverse)
    ]


def reorder_layers_in_document(document: Any, permutation: list[int]) -> None:
    """Reorder layers using *permutation* where ``permutation[new_index]`` is the old index."""
    layer_count = len(document.layers)

    if len(permutation) != layer_count:
        raise ValueError("permutation length must match layer count")

    slot_indices = slot_worldgen_indices(document.layers)

    document.layers = [document.layers[old_index] for old_index in permutation]
    document.layer_files = [document.layer_files[old_index] for old_index in permutation]
    document.layer_paths = [document.layer_paths[old_index] for old_index in permutation]

    apply_slot_worldgen_indices(document.layers, slot_indices)

    grid = document.metadata.setdefault("grid", {})
    remap_site_structure_layers_after_permutation(grid, permutation)


def remap_indices_after_swap(indices: set[int], index_a: int, index_b: int) -> set[int]:
    remapped: set[int] = set()

    for idx in indices:
        if idx == index_a:
            remapped.add(index_b)
        elif idx == index_b:
            remapped.add(index_a)
        else:
            remapped.add(idx)

    return remapped


def slot_worldgen_indices(layers: list[dict[str, Any]]) -> list[int]:
    """Worldgen ``index`` at each list position (used to keep Y levels when reordering)."""
    return [int(layer.get("index", position)) for position, layer in enumerate(layers)]


def apply_slot_worldgen_indices(layers: list[dict[str, Any]], slot_indices: list[int]) -> None:
    for position, layer in enumerate(layers):
        layer["index"] = slot_indices[position]


def swap_layers_in_document(document: Any, index_a: int, index_b: int) -> None:
    """Swap two layers and keep ``layer_files`` / ``site_structure_layers`` in sync."""
    layer_count = len(document.layers)

    if index_a < 0 or index_b < 0 or index_a >= layer_count or index_b >= layer_count:
        raise IndexError(f"layer list index out of range: {index_a}, {index_b}")

    if index_a == index_b:
        return

    slot_indices = slot_worldgen_indices(document.layers)

    document.layers[index_a], document.layers[index_b] = (
        document.layers[index_b],
        document.layers[index_a],
    )
    document.layer_files[index_a], document.layer_files[index_b] = (
        document.layer_files[index_b],
        document.layer_files[index_a],
    )
    document.layer_paths[index_a], document.layer_paths[index_b] = (
        document.layer_paths[index_b],
        document.layer_paths[index_a],
    )

    apply_slot_worldgen_indices(document.layers, slot_indices)

    grid = document.metadata.setdefault("grid", {})
    remap_site_structure_layers_after_swap(grid, index_a, index_b)


def move_layer_in_document(document: Any, list_index: int, delta: int) -> int | None:
    """Move a layer up (``delta=-1``) or down (``delta=1``); return its new list index."""
    new_index = list_index + delta

    if new_index < 0 or new_index >= len(document.layers):
        return None

    swap_layers_in_document(document, list_index, new_index)
    return new_index


def move_layer_by_worldgen_delta(
    document: Any,
    list_index: int,
    delta: int,
) -> tuple[int, int] | None:
    """Swap worldgen ``index`` with the Y-adjacent layer (``delta=-1`` = lower Y)."""
    order = layers_by_worldgen_index(document.layers)

    try:
        rank = order.index(list_index)
    except ValueError:
        return None

    new_rank = rank + delta

    if new_rank < 0 or new_rank >= len(order):
        return None

    other_index = order[new_rank]
    swap_worldgen_indices_between_layers(
        document.layers[list_index],
        document.layers[other_index],
    )
    return list_index, other_index


def clamp_site_structure_layers(grid: dict[str, Any], layer_count: int) -> None:
    """Drop invalid entries from ``site_structure_layers``."""
    indices = grid.get("site_structure_layers")

    if not isinstance(indices, list):
        return

    valid = [int(idx) for idx in indices if isinstance(idx, int) and 0 <= idx < layer_count]
    grid["site_structure_layers"] = valid or ([0] if layer_count else [])


def append_layer_to_document(
    document: Any,
    layer: dict[str, Any],
    *,
    relative_path: str | None = None,
) -> int:
    """Append *layer* to a :class:`~ui.document.StructureDocument`; return list index."""
    base_dir = document.structure_path.parent
    rel = relative_path or next_layer_relative_path(document.layer_paths)
    path = base_dir / rel

    document.layers.append(layer)
    document.layer_files.append(rel)
    document.layer_paths.append(path)
    return len(document.layers) - 1


def remove_layer_from_document(document: Any, list_index: int) -> Path | None:
    """Remove layer at *list_index*; return removed file path if it existed on disk."""
    if list_index < 0 or list_index >= len(document.layers):
        raise IndexError(f"layer list index out of range: {list_index}")

    path = document.layer_paths.pop(list_index)
    document.layer_files.pop(list_index)
    document.layers.pop(list_index)

    grid = document.metadata.setdefault("grid", {})
    adjust_site_structure_layers_after_remove(grid, list_index)
    clamp_site_structure_layers(grid, len(document.layers))

    return path if path.is_file() else None
