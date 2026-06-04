"""Layer group filter, visibility, and management (Structure tab)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QToolButton,
    QWidget,
)

from ui.toolbar_icons import (
    layer_add_icon,
    layer_copy_icon,
    layer_delete_icon,
    layer_paste_icon,
    layer_visible_off_icon,
    panel_icon_size,
)
from ui.widgets.panel_header import create_titled_panel_layout
from ui.widgets.panel_tool_button import make_panel_tool_button

_ALL_FILTER = None
_ALL_ROW_KEY = "__all__"


class _GroupListRow(QWidget):
    row_clicked = Signal(object)
    visibility_clicked = Signal(str)

    def __init__(
        self,
        *,
        group_key: str | None,
        label_text: str,
        hidden: bool,
        show_visibility: bool,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._group_key = group_key
        panel_icon_size().width()

        self._label = QLabel(label_text)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 2, 2)
        layout.setSpacing(4)
        layout.addWidget(self._label, stretch=1)

        if show_visibility:
            self._visibility_button = QToolButton()
            self._visibility_button.setAutoRaise(True)
            self._visibility_button.setIconSize(panel_icon_size())
            self._visibility_button.setFixedSize(panel_icon_size())
            self._visibility_button.clicked.connect(self._on_visibility_clicked)
            self._set_hidden(hidden)
            layout.addWidget(self._visibility_button, alignment=Qt.AlignmentFlag.AlignRight)
        else:
            self._visibility_button = None

    def _set_hidden(self, hidden: bool) -> None:
        if self._visibility_button is None:
            return

        icon_px = panel_icon_size().width()

        if hidden:
            self._visibility_button.setIcon(layer_visible_off_icon(size=icon_px))
            self._visibility_button.setToolTip("Show group in renders")
        else:
            self._visibility_button.setIcon(QIcon())
            self._visibility_button.setToolTip("Hide group from renders")

    def _on_visibility_clicked(self) -> None:
        if self._group_key is not None:
            self.visibility_clicked.emit(self._group_key)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if self._visibility_button is not None and self._visibility_button.geometry().contains(
            event.position().toPoint()
        ):
            super().mousePressEvent(event)
            return

        self.row_clicked.emit(self._group_key)
        super().mousePressEvent(event)


class GroupsPanel(QGroupBox):
    """Filter the Layers list and manage layer groups."""

    group_selected = Signal(object)
    visibility_toggled = Signal(str)
    add_requested = Signal()
    delete_requested = Signal()
    copy_requested = Signal()
    paste_requested = Signal()
    group_renamed = Signal(str, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._block_signals = False
        self._selected_filter: str | None = _ALL_FILTER
        icon_px = panel_icon_size().width()

        self._add_button = make_panel_tool_button(
            layer_add_icon(size=icon_px),
            "Add a new empty group",
            clicked=self.add_requested.emit,
        )
        self._delete_button = make_panel_tool_button(
            layer_delete_icon(size=icon_px),
            "Remove the selected group",
            clicked=self.delete_requested.emit,
        )
        self._copy_button = make_panel_tool_button(
            layer_copy_icon(size=icon_px),
            "Copy the selected group (layers and cells)",
            clicked=self.copy_requested.emit,
        )
        self._paste_button = make_panel_tool_button(
            layer_paste_icon(size=icon_px),
            "Paste a copied group as new layers",
            clicked=self.paste_requested.emit,
        )
        self._paste_button.setEnabled(False)
        self._delete_button.setEnabled(False)
        self._copy_button.setEnabled(False)

        layout = create_titled_panel_layout(
            self,
            "Groups",
            [
                self._add_button,
                self._delete_button,
                self._copy_button,
                self._paste_button,
            ],
        )

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Group name")
        self._name_edit.setEnabled(False)
        self._name_edit.editingFinished.connect(self._emit_group_renamed)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Name"))
        name_row.addWidget(self._name_edit, stretch=1)

        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_row_changed)

        layout.addLayout(name_row)
        layout.addWidget(self._list, stretch=1)
        self.setMaximumHeight(180)

    def set_paste_enabled(self, enabled: bool) -> None:
        self._paste_button.setEnabled(enabled)

    def selected_group_filter(self) -> str | None:
        return self._selected_filter

    def selected_group_name(self) -> str | None:
        if self._selected_filter is _ALL_FILTER:
            return None

        return self._selected_filter

    def load_groups(
        self,
        groups: list[str],
        *,
        hidden_groups: set[str],
        selected_filter: str | None = None,
    ) -> None:
        self._block_signals = True
        self._list.clear()
        self._selected_filter = selected_filter

        all_item = QListWidgetItem()
        all_item.setData(Qt.ItemDataRole.UserRole, _ALL_ROW_KEY)
        all_row = _GroupListRow(
            group_key=_ALL_FILTER,
            label_text="All",
            hidden=False,
            show_visibility=False,
        )
        all_row.row_clicked.connect(self._on_row_clicked)
        all_item.setSizeHint(all_row.sizeHint())
        self._list.addItem(all_item)
        self._list.setItemWidget(all_item, all_row)

        for group in groups:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, group)
            row = _GroupListRow(
                group_key=group,
                label_text=group,
                hidden=group in hidden_groups,
                show_visibility=True,
            )
            row.row_clicked.connect(self._on_row_clicked)
            row.visibility_clicked.connect(self.visibility_toggled.emit)
            item.setSizeHint(row.sizeHint())
            self._list.addItem(item)
            self._list.setItemWidget(item, row)

        self._select_filter_row(selected_filter)
        self._update_action_buttons()
        self._block_signals = False

    def _select_filter_row(self, group_filter: str | None) -> None:
        target_key = _ALL_ROW_KEY if group_filter is None else group_filter

        for row in range(self._list.count()):
            item = self._list.item(row)

            if item is not None and item.data(Qt.ItemDataRole.UserRole) == target_key:
                self._list.setCurrentRow(row)
                self._sync_name_edit()
                return

        self._list.setCurrentRow(0)
        self._selected_filter = _ALL_FILTER
        self._sync_name_edit()

    def _sync_name_edit(self) -> None:
        self._block_signals = True
        name = self.selected_group_name()

        if name is None:
            self._name_edit.clear()
            self._name_edit.setEnabled(False)
        else:
            self._name_edit.setText(name)
            self._name_edit.setEnabled(True)

        self._update_action_buttons()
        self._block_signals = False

    def _update_action_buttons(self) -> None:
        has_group = self.selected_group_name() is not None
        self._delete_button.setEnabled(has_group)
        self._copy_button.setEnabled(has_group)

    def _emit_group_renamed(self) -> None:
        if self._block_signals:
            return

        old_name = self.selected_group_name()

        if old_name is None:
            return

        new_name = self._name_edit.text().strip()

        if not new_name or new_name == old_name:
            self._name_edit.setText(old_name)
            return

        self.group_renamed.emit(old_name, new_name)

    def _on_row_clicked(self, group_key: str | None) -> None:
        if self._block_signals:
            return

        self._selected_filter = group_key
        self._select_filter_row(group_key)
        self.group_selected.emit(group_key)

    def _on_row_changed(self, row: int) -> None:
        if self._block_signals or row < 0:
            return

        item = self._list.item(row)

        if item is None:
            return

        stored = item.data(Qt.ItemDataRole.UserRole)

        if stored == _ALL_ROW_KEY:
            self._selected_filter = _ALL_FILTER
            self._sync_name_edit()
            self.group_selected.emit(_ALL_FILTER)
            return

        if stored is not None:
            self._selected_filter = str(stored)
            self._sync_name_edit()
            self.group_selected.emit(str(stored))
