"""Layer group filter, visibility, and management (Structure tab)."""

from __future__ import annotations

from PySide6.QtCore import Signal

from ui.widgets.list_panel_base import (
    CrudTooltips,
    ManagedListPanel,
    ReorderTooltips,
    add_visibility_list_item,
)
from ui.widgets.visibility_list_row import VisibilityListRow

_ALL_FILTER = None
_ALL_ROW_KEY = "__all__"

_GROUP_CRUD_TOOLTIPS = CrudTooltips(
    add="Add a new empty group",
    edit="Edit the selected group name",
    delete="Remove the selected group",
    copy="Copy the selected group (layers and cells)",
    paste="Paste a copied group as new layers",
)
_GROUP_REORDER_TOOLTIPS = ReorderTooltips(
    up="Move selected group up",
    down="Move selected group down",
)
_GROUP_HIDDEN_TOOLTIP = "Show group in renders"
_GROUP_VISIBLE_TOOLTIP = "Hide group from renders"


class GroupsPanel(ManagedListPanel):
    """Filter the Layers list and manage layer groups."""

    group_selected = Signal(object)
    visibility_toggled = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(
            "Groups",
            crud_tooltips=_GROUP_CRUD_TOOLTIPS,
            reorder_tooltips=_GROUP_REORDER_TOOLTIPS,
            parent=parent,
        )
        self._selected_filter: str | None = _ALL_FILTER
        self.crud_buttons.edit.setEnabled(False)
        self.crud_buttons.delete.setEnabled(False)
        self.crud_buttons.copy.setEnabled(False)
        self._update_reorder_buttons()

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
        with self.callback_gate.block():
            self.list_widget.clear()
            self._selected_filter = selected_filter

            all_row = VisibilityListRow(
                row_key=_ALL_FILTER,
                label_text="All",
                hidden=False,
                show_visibility=False,
            )
            all_row.row_clicked.connect(self._on_row_clicked)
            add_visibility_list_item(self.list_widget, row_key=_ALL_ROW_KEY, row=all_row)

            for group in groups:
                row = VisibilityListRow(
                    row_key=group,
                    label_text=group,
                    hidden=group in hidden_groups,
                    hidden_tooltip=_GROUP_HIDDEN_TOOLTIP,
                    visible_tooltip=_GROUP_VISIBLE_TOOLTIP,
                )
                row.row_clicked.connect(self._on_row_clicked)
                row.visibility_clicked.connect(self.visibility_toggled.emit)
                add_visibility_list_item(self.list_widget, row_key=group, row=row)

            self._select_filter_row(selected_filter)
            self._update_action_buttons()
            self._update_reorder_buttons()

    def _select_filter_row(self, group_filter: str | None) -> None:
        target_key = _ALL_ROW_KEY if group_filter is None else group_filter

        if self.select_row_by_user_data(target_key):
            self._update_action_buttons()
            return

        self.list_widget.setCurrentRow(0)
        self._selected_filter = _ALL_FILTER
        self._update_action_buttons()

    def _update_action_buttons(self) -> None:
        has_group = self.selected_group_name() is not None
        self.crud_buttons.edit.setEnabled(has_group)
        self.crud_buttons.delete.setEnabled(has_group)
        self.crud_buttons.copy.setEnabled(has_group)

    def _group_row_index(self) -> int:
        """Selected row index among groups (0 = first group, excluding All)."""
        row = self.list_widget.currentRow()

        if row <= 0:
            return -1

        return row - 1

    def _group_count(self) -> int:
        return max(0, self.list_widget.count() - 1)

    def _update_reorder_buttons(self) -> None:
        group_index = self._group_row_index()
        group_count = self._group_count()
        self.reorder_buttons.up.setEnabled(group_index > 0)
        self.reorder_buttons.down.setEnabled(0 <= group_index < group_count - 1)

    def _on_row_clicked(self, group_key: object) -> None:
        if self.callback_gate.blocked:
            return

        filter_value = group_key if isinstance(group_key, str) else None
        self._selected_filter = _ALL_FILTER if filter_value is None else filter_value
        self._select_filter_row(filter_value)
        self._update_reorder_buttons()
        self.group_selected.emit(group_key)

    def _on_list_row_changed(self, row: int) -> None:
        if self.callback_gate.blocked or row < 0:
            return

        stored = self.user_data_at_row(row)

        if stored == _ALL_ROW_KEY:
            self._selected_filter = _ALL_FILTER
            self._update_action_buttons()
            self._update_reorder_buttons()
            self.group_selected.emit(_ALL_FILTER)
            return

        if stored is not None:
            self._selected_filter = str(stored)
            self._update_action_buttons()
            self._update_reorder_buttons()
            self.group_selected.emit(str(stored))
