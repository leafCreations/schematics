"""Add, remove, and copy structure layers in the editor."""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from helpers.grid_cells import empty_cells

_LAYER_FILE_RE = re.compile(r"layer_(\d+)\.yaml$")


def layer_label(layer: dict[str, Any], list_index: int) -> str:
    group = layer.get("group")
    if group:
        return str(group)
    return f"Layer {layer.get('index', list_index)}"


def next_layer_relative_path(existing_paths: list[Path]) -> str:
    """Return a new ``layers/layer_NN.yaml`` path not in *existing_paths*."""
    max_num = -1

    for path in existing_paths:
        match = _LAYER_FILE_RE.match(path.name)

        if match:
            max_num = max(max_num, int(match.group(1)))

    return f"layers/layer_{max_num + 1:02d}.yaml"


def next_worldgen_index(layers: list[dict[str, Any]]) -> int:
    """Return an unused worldgen ``index`` for a new layer."""
    used = {int(layer["index"]) for layer in layers if "index" in layer}
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
    cells: list[list[str]] | None = None,
) -> dict[str, Any]:
    return {
        "index": int(worldgen_index),
        "group": group,
        "cells": copy.deepcopy(cells) if cells is not None else empty_cells(width, depth),
    }


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


def swap_layers_in_document(document: Any, index_a: int, index_b: int) -> None:
    """Swap two layers and keep ``layer_files`` / ``site_structure_layers`` in sync."""
    layer_count = len(document.layers)

    if index_a < 0 or index_b < 0 or index_a >= layer_count or index_b >= layer_count:
        raise IndexError(f"layer list index out of range: {index_a}, {index_b}")

    if index_a == index_b:
        return

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

    grid = document.metadata.setdefault("grid", {})
    remap_site_structure_layers_after_swap(grid, index_a, index_b)


def move_layer_in_document(document: Any, list_index: int, delta: int) -> int | None:
    """Move a layer up (``delta=-1``) or down (``delta=1``); return its new list index."""
    new_index = list_index + delta

    if new_index < 0 or new_index >= len(document.layers):
        return None

    swap_layers_in_document(document, list_index, new_index)
    return new_index


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
