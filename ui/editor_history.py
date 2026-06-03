"""Undo/redo snapshots for structure editor layout changes."""

from __future__ import annotations

import copy
from dataclasses import dataclass

from ui.document import StructureDocument

MAX_UNDO_LEVELS = 100


@dataclass(frozen=True)
class EditorHistoryState:
    metadata: dict
    layers_cells: list[list[list[str]]]
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
        layers_cells=[copy.deepcopy(layer["cells"]) for layer in document.layers],
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

    for layer, cells in zip(document.layers, state.layers_cells, strict=True):
        layer["cells"] = copy.deepcopy(cells)

    document.site_ground = copy.deepcopy(state.site_ground)

    dirty_layers.clear()
    dirty_layers.update(state.dirty_layers)
    dirty_structure_holder[0] = state.dirty_structure
