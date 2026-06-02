from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QTabWidget, QVBoxLayout, QWidget

from helpers.block_picker import PickerEntry, list_palettes

_ENTRY_ROLE = 256


class PalettePanel(QWidget):
    entry_selected = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._tabs = QTabWidget(self)
        self._lists: dict[str, QListWidget] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tabs)

        for palette in list_palettes():
            list_widget = QListWidget(self._tabs)
            list_widget.currentItemChanged.connect(self._on_item_changed)

            for entry in palette.entries:
                item = QListWidgetItem(entry.label)
                item.setData(_ENTRY_ROLE, entry)
                list_widget.addItem(item)

            self._lists[palette.name] = list_widget
            self._tabs.addTab(list_widget, palette.label)

    def _on_item_changed(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            return

        entry = current.data(_ENTRY_ROLE)

        if isinstance(entry, PickerEntry):
            self.entry_selected.emit(entry)

    def select_entry(self, entry: PickerEntry) -> None:
        list_widget = self._lists.get(entry.palette)

        if list_widget is None:
            return

        for row in range(list_widget.count()):
            item = list_widget.item(row)
            candidate = item.data(_ENTRY_ROLE)

            if candidate == entry:
                list_widget.setCurrentItem(item)
                return

    def clear_selection(self) -> None:
        current = self._tabs.currentWidget()

        if isinstance(current, QListWidget):
            current.clearSelection()
            current.setCurrentRow(-1)
