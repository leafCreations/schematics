"""Layer stack list with reorder controls (Structure tab, left column)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Signal

from helpers.layer_groups import layer_matches_group_filter
from helpers.layer_management import (
    layer_display_label,
    layer_worldgen_index,
    layers_by_worldgen_index,
)
from helpers.layer_visibility import is_layer_visible
from ui.widgets.list_panel_base import (
    CrudTooltips,
    ManagedListPanel,
    ReorderTooltips,
    add_visibility_list_item,
)
from ui.widgets.visibility_list_row import VisibilityListRow

_LAYER_CRUD_TOOLTIPS = CrudTooltips(
    add="Add a new empty layer (Y level and group)",
    edit="Edit the current layer Y level and group",
    delete="Remove the current layer",
    copy="Copy the current layer to the clipboard",
    paste="Paste a copied layer as a new layer",
)
_LAYER_REORDER_TOOLTIPS = ReorderTooltips(
    up="Move selected layer up in Y order",
    down="Move selected layer down in Y order",
)
_LAYER_HIDDEN_TOOLTIP = "Show layer in renders"
_LAYER_VISIBLE_TOOLTIP = "Hide layer from renders"


class LayerListPanel(ManagedListPanel):
    layer_selected = Signal(int)
    visibility_toggled = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(
            "Layers",
            crud_tooltips=_LAYER_CRUD_TOOLTIPS,
            reorder_tooltips=_LAYER_REORDER_TOOLTIPS,
            parent=parent,
        )
        self._y_order: list[int] = []

    def load_layers(
        self,
        layers: list[dict[str, Any]],
        layer_paths: list[Path],
        *,
        current_index: int,
        dirty_layers: set[int] | None = None,
        group_filter: str | None = None,
    ) -> None:
        with self.callback_gate.block():
            self.list_widget.clear()
            dirty = dirty_layers or set()
            visible_indices: list[int] = []
            self._y_order = layers_by_worldgen_index(layers)

            visible_entries = [
                (index, layer)
                for index, layer in enumerate(layers)
                if layer_matches_group_filter(layer, index, group_filter)
            ]
            visible_entries.sort(
                key=lambda entry: (
                    layer_worldgen_index(entry[1], entry[0]),
                    entry[0],
                )
            )

            for index, layer in visible_entries:
                visible_indices.append(index)
                row = VisibilityListRow(
                    row_key=index,
                    label_text=self._row_label(layer, index, dirty),
                    hidden=not is_layer_visible(layer),
                    hidden_tooltip=_LAYER_HIDDEN_TOOLTIP,
                    visible_tooltip=_LAYER_VISIBLE_TOOLTIP,
                )
                row.row_clicked.connect(self._on_row_clicked)
                row.visibility_clicked.connect(self.visibility_toggled.emit)
                add_visibility_list_item(self.list_widget, row_key=index, row=row)

            if visible_indices:
                select_index = (
                    current_index if current_index in visible_indices else visible_indices[0]
                )
                self.select_row_by_user_data(select_index)

            active = current_index if current_index in visible_indices else -1
            self._update_reorder_buttons(active)

    @staticmethod
    def _row_label(
        layer: dict[str, Any],
        index: int,
        dirty: set[int],
    ) -> str:
        label = layer_display_label(layer, index)
        y_level = layer_worldgen_index(layer, index)
        suffix = " *" if index in dirty else ""
        return f"Y {y_level}: {label}{suffix}"

    def set_current_index(self, index: int) -> None:
        if index < 0:
            self._update_reorder_buttons(index)
            return

        with self.callback_gate.block():
            if self.select_row_by_user_data(index):
                self._update_reorder_buttons(index)
                return

        self._update_reorder_buttons(index)

    def current_index(self) -> int:
        row = self.list_widget.currentRow()

        if row < 0:
            return -1

        stored = self.user_data_at_row(row)

        return int(stored) if stored is not None else row

    def _on_row_clicked(self, index: object) -> None:
        if self.callback_gate.blocked or not isinstance(index, int):
            return

        with self.callback_gate.block():
            if not self.select_row_by_user_data(index):
                return

        self._update_reorder_buttons(index)
        self.layer_selected.emit(index)

    def _on_list_row_changed(self, row: int) -> None:
        if self.callback_gate.blocked or row < 0:
            return

        index = self.user_data_at_row(row)

        if index is not None:
            self._update_reorder_buttons(int(index))
            self.layer_selected.emit(int(index))

    def _update_reorder_buttons(self, list_index: int) -> None:
        if list_index < 0 or not self._y_order:
            self.reorder_buttons.up.setEnabled(False)
            self.reorder_buttons.down.setEnabled(False)
            return

        try:
            rank = self._y_order.index(list_index)
        except ValueError:
            self.reorder_buttons.up.setEnabled(False)
            self.reorder_buttons.down.setEnabled(False)
            return

        layer_count = len(self._y_order)
        self.reorder_buttons.up.setEnabled(layer_count > 1 and rank > 0)
        self.reorder_buttons.down.setEnabled(layer_count > 1 and rank < layer_count - 1)
