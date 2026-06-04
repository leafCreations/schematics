from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
)

from helpers.block_picker import PickerEntry, PickerPalette, list_palettes
from ui.widgets.panel_header import create_simple_titled_panel_layout

_ENTRY_ROLE = 256


class PalettePanel(QGroupBox):
    entry_selected = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._palettes: list[PickerPalette] = list_palettes()
        self._palettes_by_name = {palette.name: palette for palette in self._palettes}

        layout = create_simple_titled_panel_layout(self, "Palettes")

        self._category_combo = QComboBox()
        self._block_list = QListWidget()
        self._block_list.currentItemChanged.connect(self._on_item_changed)

        for palette in self._palettes:
            self._category_combo.addItem(palette.label, palette.name)

        category_label = QLabel("Category")
        blocks_label = QLabel("Blocks")

        layout.addWidget(category_label)
        layout.addWidget(self._category_combo)
        layout.addWidget(blocks_label)
        layout.addWidget(self._block_list, stretch=1)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self._block_list.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self._category_combo.currentIndexChanged.connect(self._on_category_changed)

        if self._palettes:
            self._populate_block_list(self._palettes[0].name)

    def _on_category_changed(self, _index: int) -> None:
        palette_name = self._category_combo.currentData()

        if isinstance(palette_name, str):
            self._populate_block_list(palette_name)

    def _populate_block_list(self, palette_name: str) -> None:
        palette = self._palettes_by_name.get(palette_name)

        self._block_list.blockSignals(True)
        self._block_list.clear()

        if palette is not None:
            for entry in palette.entries:
                item = QListWidgetItem(entry.label)
                item.setData(_ENTRY_ROLE, entry)
                self._block_list.addItem(item)

        self._block_list.clearSelection()
        self._block_list.setCurrentRow(-1)
        self._block_list.blockSignals(False)

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
        palette_index = self._category_combo.findData(entry.palette)

        if palette_index < 0:
            return

        if self._category_combo.currentIndex() != palette_index:
            self._category_combo.setCurrentIndex(palette_index)
        else:
            self._populate_block_list(entry.palette)

        for row in range(self._block_list.count()):
            item = self._block_list.item(row)
            candidate = item.data(_ENTRY_ROLE)

            if candidate == entry:
                self._block_list.setCurrentItem(item)
                return

    def clear_selection(self) -> None:
        self._block_list.clearSelection()
        self._block_list.setCurrentRow(-1)
