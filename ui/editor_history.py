"""Undo/redo snapshots for structure editor layout changes."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path

from ui.document import StructureDocument

MAX_UNDO_LEVELS = 100


@dataclass(frozen=True)
class EditorHistoryState:
    metadata: dict
    layers: list[dict]
    layer_files: list[str]
    layer_paths: list[str]
    site_ground: list[list[str]]
    dirty_layers: frozenset[int]
    dirty_structure: bool


def capture_history_state(
    document: StructureDocument,
    *,
    dirty_layers: set[int],
    dirty_structure: bool,
) -> EditorHistoryState:
    return EditorHistoryState(
        metadata=copy.deepcopy(document.metadata),
        layers=copy.deepcopy(document.layers),
        layer_files=list(document.layer_files),
        layer_paths=[str(path) for path in document.layer_paths],
        site_ground=copy.deepcopy(document.site_ground),
        dirty_layers=frozenset(dirty_layers),
        dirty_structure=dirty_structure,
    )


def apply_history_state(
    document: StructureDocument,
    state: EditorHistoryState,
    *,
    dirty_layers: set[int],
    dirty_structure_holder: list[bool],
) -> None:
    """Restore document layout; ``dirty_structure_holder`` is a one-element list for out-param."""
    document.metadata.clear()
    document.metadata.update(copy.deepcopy(state.metadata))

    document.layers = copy.deepcopy(state.layers)
    document.layer_files = list(state.layer_files)
    document.layer_paths = [Path(path) for path in state.layer_paths]
    document.site_ground = copy.deepcopy(state.site_ground)

    dirty_layers.clear()
    dirty_layers.update(state.dirty_layers)
    dirty_structure_holder[0] = state.dirty_structure
