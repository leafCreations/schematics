"""Layer stack list with reorder controls (Structure tab, left column)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QToolButton,
    QWidget,
)

from helpers.layer_groups import layer_matches_group_filter
from helpers.layer_management import (
    layer_display_label,
    layer_worldgen_index,
    layers_by_worldgen_index,
)
from helpers.layer_visibility import is_layer_visible
from ui.toolbar_icons import (
    layer_add_icon,
    layer_copy_icon,
    layer_delete_icon,
    layer_edit_icon,
    layer_move_down_icon,
    layer_move_up_icon,
    layer_paste_icon,
    layer_visible_off_icon,
    panel_icon_size,
)
from ui.widgets.panel_header import create_titled_panel_layout
from ui.widgets.panel_tool_button import make_panel_tool_button


class _LayerListRow(QWidget):
    row_clicked = Signal(int)
    visibility_clicked = Signal(int)

    def __init__(
        self,
        *,
        list_index: int,
        label_text: str,
        hidden: bool,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._list_index = list_index

        self._label = QLabel(label_text)
        self._label.setWordWrap(False)

        self._visibility_button = QToolButton()
        self._visibility_button.setAutoRaise(True)
        self._visibility_button.setIconSize(panel_icon_size())
        self._visibility_button.setFixedSize(panel_icon_size())
        self._visibility_button.setToolTip(
            "Show layer in renders" if hidden else "Hide layer from renders"
        )
        self._visibility_button.clicked.connect(self._on_visibility_clicked)
        self._set_hidden(hidden)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 2, 2)
        layout.setSpacing(4)
        layout.addWidget(self._label, stretch=1)
        layout.addWidget(self._visibility_button, alignment=Qt.AlignmentFlag.AlignRight)

    def _set_hidden(self, hidden: bool) -> None:
        icon_px = panel_icon_size().width()

        if hidden:
            self._visibility_button.setIcon(layer_visible_off_icon(size=icon_px))
        else:
            self._visibility_button.setIcon(QIcon())

    def _on_visibility_clicked(self) -> None:
        self.visibility_clicked.emit(self._list_index)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if not self._visibility_button.geometry().contains(event.position().toPoint()):
            self.row_clicked.emit(self._list_index)

        super().mousePressEvent(event)


class LayerListPanel(QGroupBox):
    layer_selected = Signal(int)
    move_up_requested = Signal()
    move_down_requested = Signal()
    visibility_toggled = Signal(int)
    add_requested = Signal()
    edit_requested = Signal()
    delete_requested = Signal()
    copy_requested = Signal()
    paste_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._block_signals = False
        self._y_order: list[int] = []
        icon_px = panel_icon_size().width()

        self._add_button = make_panel_tool_button(
            layer_add_icon(size=icon_px),
            "Add a new empty layer (Y level and group)",
            clicked=self.add_requested.emit,
        )
        self._edit_button = make_panel_tool_button(
            layer_edit_icon(size=icon_px),
            "Edit the current layer Y level and group",
            clicked=self.edit_requested.emit,
        )
        self._delete_button = make_panel_tool_button(
            layer_delete_icon(size=icon_px),
            "Remove the current layer",
            clicked=self.delete_requested.emit,
        )
        self._copy_button = make_panel_tool_button(
            layer_copy_icon(size=icon_px),
            "Copy the current layer to the clipboard",
            clicked=self.copy_requested.emit,
        )
        self._paste_button = make_panel_tool_button(
            layer_paste_icon(size=icon_px),
            "Paste a copied layer as a new layer",
            clicked=self.paste_requested.emit,
        )
        self._paste_button.setEnabled(False)

        layout = create_titled_panel_layout(
            self,
            "Layers",
            [
                self._add_button,
                self._edit_button,
                self._delete_button,
                self._copy_button,
                self._paste_button,
            ],
        )

        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_row_changed)

        self._up_button = make_panel_tool_button(
            layer_move_up_icon(size=icon_px),
            "Move selected layer up in Y order",
            clicked=self.move_up_requested.emit,
        )
        self._down_button = make_panel_tool_button(
            layer_move_down_icon(size=icon_px),
            "Move selected layer down in Y order",
            clicked=self.move_down_requested.emit,
        )

        reorder_row = QHBoxLayout()
        reorder_row.addStretch(1)
        reorder_row.addWidget(self._up_button)
        reorder_row.addWidget(self._down_button)

        layout.addWidget(self._list, stretch=1)
        layout.addLayout(reorder_row)

        self.setMaximumHeight(220)

    def set_paste_enabled(self, enabled: bool) -> None:
        self._paste_button.setEnabled(enabled)

    def set_delete_enabled(self, enabled: bool) -> None:
        self._delete_button.setEnabled(enabled)

    def set_edit_enabled(self, enabled: bool) -> None:
        self._edit_button.setEnabled(enabled)

    def set_copy_enabled(self, enabled: bool) -> None:
        self._copy_button.setEnabled(enabled)

    def load_layers(
        self,
        layers: list[dict[str, Any]],
        layer_paths: list[Path],
        *,
        current_index: int,
        dirty_layers: set[int] | None = None,
        group_filter: str | None = None,
    ) -> None:
        self._block_signals = True
        self._list.clear()
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
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, index)

            row = _LayerListRow(
                list_index=index,
                label_text=self._row_label(layer, index, dirty),
                hidden=not is_layer_visible(layer),
            )
            row.row_clicked.connect(self._on_row_clicked)
            row.visibility_clicked.connect(self.visibility_toggled.emit)
            item.setSizeHint(row.sizeHint())
            self._list.addItem(item)
            self._list.setItemWidget(item, row)

        if visible_indices:
            select_index = current_index if current_index in visible_indices else visible_indices[0]

            for row in range(self._list.count()):
                item = self._list.item(row)

                if item is not None and item.data(Qt.ItemDataRole.UserRole) == select_index:
                    self._list.setCurrentRow(row)
                    break

        active = current_index if current_index in visible_indices else -1
        self._update_reorder_buttons(active)
        self._block_signals = False

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

        self._block_signals = True

        for row in range(self._list.count()):
            item = self._list.item(row)

            if item is not None and item.data(Qt.ItemDataRole.UserRole) == index:
                self._list.setCurrentRow(row)
                self._update_reorder_buttons(index)
                self._block_signals = False
                return

        self._update_reorder_buttons(index)
        self._block_signals = False

    def current_index(self) -> int:
        row = self._list.currentRow()

        if row < 0:
            return -1

        item = self._list.item(row)

        if item is None:
            return row

        stored = item.data(Qt.ItemDataRole.UserRole)

        return int(stored) if stored is not None else row

    def _on_row_clicked(self, index: int) -> None:
        if self._block_signals:
            return

        for row in range(self._list.count()):
            item = self._list.item(row)

            if item is not None and item.data(Qt.ItemDataRole.UserRole) == index:
                self._block_signals = True
                self._list.setCurrentRow(row)
                self._block_signals = False
                self._update_reorder_buttons(index)
                self.layer_selected.emit(index)
                return

    def _on_row_changed(self, row: int) -> None:
        if self._block_signals or row < 0:
            return

        item = self._list.item(row)

        if item is None:
            return

        index = item.data(Qt.ItemDataRole.UserRole)

        if index is not None:
            self._update_reorder_buttons(int(index))
            self.layer_selected.emit(int(index))

    def _update_reorder_buttons(self, list_index: int) -> None:
        if list_index < 0 or not self._y_order:
            self._up_button.setEnabled(False)
            self._down_button.setEnabled(False)
            return

        try:
            rank = self._y_order.index(list_index)
        except ValueError:
            self._up_button.setEnabled(False)
            self._down_button.setEnabled(False)
            return

        layer_count = len(self._y_order)
        self._up_button.setEnabled(layer_count > 1 and rank > 0)
        self._down_button.setEnabled(layer_count > 1 and rank < layer_count - 1)
