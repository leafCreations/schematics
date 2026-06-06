"""Shared CRUD list panel layout for Groups and Layers (Structure tab, left column)."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ui.toolbar_icons import (
    layer_add_icon,
    layer_copy_icon,
    layer_delete_icon,
    layer_edit_icon,
    layer_move_down_icon,
    layer_move_up_icon,
    layer_paste_icon,
    panel_icon_size,
)
from ui.widgets.panel_header import PANEL_LIST_MAX_HEIGHT, create_titled_panel_layout
from ui.widgets.panel_tool_button import make_panel_tool_button
from ui.widgets.signal_utils import CallbackGate
from ui.widgets.visibility_list_row import VisibilityListRow


@dataclass(frozen=True)
class CrudTooltips:
    add: str
    edit: str
    delete: str
    copy: str
    paste: str


@dataclass(frozen=True)
class ReorderTooltips:
    up: str
    down: str


@dataclass
class CrudPanelButtons:
    add: QToolButton
    edit: QToolButton
    delete: QToolButton
    copy: QToolButton
    paste: QToolButton

    def header_widgets(self) -> list[QToolButton]:
        return [self.add, self.edit, self.delete, self.copy, self.paste]


@dataclass
class ReorderPanelButtons:
    up: QToolButton
    down: QToolButton


def make_crud_panel_buttons(
    *,
    add_clicked,
    edit_clicked,
    delete_clicked,
    copy_clicked,
    paste_clicked,
    tooltips: CrudTooltips,
    icon_px: int | None = None,
) -> CrudPanelButtons:
    """Build the five standard list-panel header action buttons."""
    px = icon_px if icon_px is not None else panel_icon_size().width()
    return CrudPanelButtons(
        add=make_panel_tool_button(layer_add_icon(size=px), tooltips.add, clicked=add_clicked),
        edit=make_panel_tool_button(layer_edit_icon(size=px), tooltips.edit, clicked=edit_clicked),
        delete=make_panel_tool_button(
            layer_delete_icon(size=px),
            tooltips.delete,
            clicked=delete_clicked,
        ),
        copy=make_panel_tool_button(layer_copy_icon(size=px), tooltips.copy, clicked=copy_clicked),
        paste=make_panel_tool_button(
            layer_paste_icon(size=px),
            tooltips.paste,
            clicked=paste_clicked,
        ),
    )


def make_reorder_panel_buttons(
    *,
    up_clicked,
    down_clicked,
    tooltips: ReorderTooltips,
    icon_px: int | None = None,
) -> ReorderPanelButtons:
    """Build up/down reorder buttons for a list panel footer."""
    px = icon_px if icon_px is not None else panel_icon_size().width()
    return ReorderPanelButtons(
        up=make_panel_tool_button(layer_move_up_icon(size=px), tooltips.up, clicked=up_clicked),
        down=make_panel_tool_button(
            layer_move_down_icon(size=px),
            tooltips.down,
            clicked=down_clicked,
        ),
    )


def add_reorder_row(layout: QVBoxLayout, reorder: ReorderPanelButtons) -> None:
    """Append a right-aligned up/down button row to a panel layout."""
    row = QHBoxLayout()
    row.addStretch(1)
    row.addWidget(reorder.up)
    row.addWidget(reorder.down)
    layout.addLayout(row)


def add_visibility_list_item(
    list_widget: QListWidget,
    *,
    row_key: object,
    row: VisibilityListRow,
) -> QListWidgetItem:
    """Add a custom row widget to a list, storing ``row_key`` in ``UserRole``."""
    item = QListWidgetItem()
    item.setData(Qt.ItemDataRole.UserRole, row_key)
    item.setSizeHint(row.sizeHint())
    list_widget.addItem(item)
    list_widget.setItemWidget(item, row)
    return item


class ManagedListPanel(QGroupBox):
    """List panel with CRUD header buttons, ``QListWidget``, and reorder footer."""

    add_requested = Signal()
    edit_requested = Signal()
    delete_requested = Signal()
    copy_requested = Signal()
    paste_requested = Signal()
    move_up_requested = Signal()
    move_down_requested = Signal()

    def __init__(
        self,
        title: str,
        *,
        crud_tooltips: CrudTooltips,
        reorder_tooltips: ReorderTooltips,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._callback_gate = CallbackGate()
        icon_px = panel_icon_size().width()

        self._crud = make_crud_panel_buttons(
            add_clicked=self.add_requested.emit,
            edit_clicked=self.edit_requested.emit,
            delete_clicked=self.delete_requested.emit,
            copy_clicked=self.copy_requested.emit,
            paste_clicked=self.paste_requested.emit,
            tooltips=crud_tooltips,
            icon_px=icon_px,
        )
        self._crud.paste.setEnabled(False)

        layout = create_titled_panel_layout(self, title, self._crud.header_widgets())

        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_list_row_changed)

        self._reorder = make_reorder_panel_buttons(
            up_clicked=self.move_up_requested.emit,
            down_clicked=self.move_down_requested.emit,
            tooltips=reorder_tooltips,
            icon_px=icon_px,
        )

        layout.addWidget(self._list, stretch=1)
        add_reorder_row(layout, self._reorder)
        self.setMaximumHeight(PANEL_LIST_MAX_HEIGHT)

    @property
    def callback_gate(self) -> CallbackGate:
        return self._callback_gate

    @property
    def list_widget(self) -> QListWidget:
        return self._list

    @property
    def crud_buttons(self) -> CrudPanelButtons:
        return self._crud

    @property
    def reorder_buttons(self) -> ReorderPanelButtons:
        return self._reorder

    def set_paste_enabled(self, enabled: bool) -> None:
        self._crud.paste.setEnabled(enabled)

    def set_edit_enabled(self, enabled: bool) -> None:
        self._crud.edit.setEnabled(enabled)

    def set_delete_enabled(self, enabled: bool) -> None:
        self._crud.delete.setEnabled(enabled)

    def set_copy_enabled(self, enabled: bool) -> None:
        self._crud.copy.setEnabled(enabled)

    def select_row_by_user_data(self, key: object) -> bool:
        """Select the first row whose ``UserRole`` equals ``key``."""
        for row in range(self._list.count()):
            item = self._list.item(row)

            if item is not None and item.data(Qt.ItemDataRole.UserRole) == key:
                self._list.setCurrentRow(row)
                return True

        return False

    def user_data_at_row(self, row: int) -> object | None:
        item = self._list.item(row)

        if item is None:
            return None

        return item.data(Qt.ItemDataRole.UserRole)

    def _on_list_row_changed(self, row: int) -> None:
        """Override to handle selection changes from keyboard or programmatic updates."""
