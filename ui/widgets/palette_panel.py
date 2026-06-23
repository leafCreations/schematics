from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
)

from helpers.block_picker import (
    PickerEntry,
    PickerPalette,
    entry_matches_search,
    list_palettes,
    search_picker_entries,
)
from helpers.palette_sections import PALETTE_SECTION_ALL, palette_section_label
from ui.widgets.panel_header import create_simple_titled_panel_layout

_ENTRY_ROLE = 256


class PalettePanel(QGroupBox):
    entry_selected = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._palettes: list[PickerPalette] = list_palettes()
        self._palettes_by_name = {palette.name: palette for palette in self._palettes}
        self._site_dimension = "overworld"

        layout = create_simple_titled_panel_layout(self, "Palettes")

        self._category_combo = QComboBox()
        self._dimension_combo = QComboBox()
        self._dimension_label = QLabel("Dimension")
        self._category_label = QLabel("Category")
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search all blocks…")
        self._search_edit.setClearButtonEnabled(True)
        self._block_list = QListWidget()
        self._block_list.currentItemChanged.connect(self._on_item_changed)

        for palette in self._palettes:
            self._category_combo.addItem(palette.label, palette.name)

        blocks_label = QLabel("Blocks")
        search_label = QLabel("Search")

        layout.addWidget(search_label)
        layout.addWidget(self._search_edit)
        layout.addWidget(self._category_label)
        layout.addWidget(self._category_combo)
        layout.addWidget(self._dimension_label)
        layout.addWidget(self._dimension_combo)
        layout.addWidget(blocks_label)
        layout.addWidget(self._block_list, stretch=1)

        self._dimension_label.hide()
        self._dimension_combo.hide()
        self._dimension_combo.currentIndexChanged.connect(self._on_dimension_changed)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self._block_list.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self._category_combo.currentIndexChanged.connect(self._on_category_changed)
        self._search_edit.textChanged.connect(self._on_search_changed)

        if self._palettes:
            self._populate_block_list(self._palettes[0].name)

    def _on_category_changed(self, _index: int) -> None:
        if self._is_searching():
            return

        palette_name = self._category_combo.currentData()

        if isinstance(palette_name, str):
            self._configure_dimension_filter(palette_name)
            self._populate_block_list(palette_name)

    def _on_dimension_changed(self, _index: int) -> None:
        if self._is_searching():
            return

        self._refresh_block_list()

    def _on_search_changed(self, _text: str) -> None:
        self._refresh_block_list()

    def _current_palette_name(self) -> str | None:
        palette_name = self._category_combo.currentData()
        return palette_name if isinstance(palette_name, str) else None

    def _is_searching(self) -> bool:
        return bool(self._search_query().strip())

    def _refresh_block_list(self) -> None:
        self._update_search_mode_ui()

        if self._is_searching():
            self._populate_search_results(self._search_query())
            return

        palette_name = self._current_palette_name()

        if palette_name is not None:
            self._populate_block_list(palette_name)

    def _update_search_mode_ui(self) -> None:
        searching = self._is_searching()

        self._category_label.setHidden(searching)
        self._category_combo.setHidden(searching)

        if searching:
            self._dimension_label.hide()
            self._dimension_combo.hide()
            return

        palette_name = self._current_palette_name()
        palette = self._palettes_by_name.get(palette_name or "")
        has_sections = palette is not None and bool(palette.sections)

        if has_sections:
            self._dimension_label.show()
            self._dimension_combo.show()
        else:
            self._dimension_label.hide()
            self._dimension_combo.hide()

    def set_site_dimension(self, dimension: str | None) -> None:
        normalized = str(dimension or "overworld").strip().lower()

        if normalized not in {"overworld", "nether", "end"}:
            normalized = "overworld"

        self._site_dimension = normalized
        self._apply_site_dimension_to_filter()

    def _apply_site_dimension_to_filter(self) -> None:
        if self._is_searching():
            return

        palette_name = self._current_palette_name()

        if palette_name is None or self._dimension_combo.count() == 0:
            return

        palette = self._palettes_by_name.get(palette_name)
        if palette is None or not palette.sections:
            return

        section_index = self._dimension_combo.findData(self._site_dimension)

        if section_index < 0:
            return

        if self._dimension_combo.currentIndex() == section_index:
            return

        self._dimension_combo.blockSignals(True)
        self._dimension_combo.setCurrentIndex(section_index)
        self._dimension_combo.blockSignals(False)
        self._populate_block_list(palette_name)

    def _configure_dimension_filter(self, palette_name: str) -> None:
        palette = self._palettes_by_name.get(palette_name)
        has_sections = palette is not None and bool(palette.sections)

        self._dimension_combo.blockSignals(True)
        self._dimension_combo.clear()

        if has_sections:
            self._dimension_label.show()
            self._dimension_combo.show()
            self._dimension_combo.addItem("All", PALETTE_SECTION_ALL)

            for section_key in palette.sections:
                self._dimension_combo.addItem(palette_section_label(section_key), section_key)

            self._apply_site_dimension_to_filter()
        else:
            self._dimension_label.hide()
            self._dimension_combo.hide()

        self._dimension_combo.blockSignals(False)

    def _selected_section_filter(self) -> str | None:
        if self._dimension_combo.count() == 0:
            return None

        section = self._dimension_combo.currentData()

        if section == PALETTE_SECTION_ALL:
            return None

        return section if isinstance(section, str) else None

    def _search_query(self) -> str:
        return self._search_edit.text()

    def _clear_search(self) -> None:
        if not self._search_query():
            return

        self._search_edit.blockSignals(True)
        self._search_edit.clear()
        self._search_edit.blockSignals(False)

    def _list_label_for_entry(self, entry: PickerEntry, *, show_palette: bool) -> str:
        if not show_palette:
            return entry.label

        palette = self._palettes_by_name.get(entry.palette)
        palette_label = palette.label if palette is not None else entry.palette.title()

        return f"{entry.label} — {palette_label}"

    def _populate_search_results(self, query: str) -> None:
        self._block_list.blockSignals(True)
        self._block_list.clear()

        for entry in search_picker_entries(self._palettes, query):
            item = QListWidgetItem(self._list_label_for_entry(entry, show_palette=True))
            item.setData(_ENTRY_ROLE, entry)
            self._block_list.addItem(item)

        self._block_list.clearSelection()
        self._block_list.setCurrentRow(-1)
        self._block_list.blockSignals(False)

    def _populate_block_list(self, palette_name: str) -> None:
        palette = self._palettes_by_name.get(palette_name)
        section_filter = self._selected_section_filter()

        self._block_list.blockSignals(True)
        self._block_list.clear()

        if palette is not None:
            entries = [
                entry
                for entry in palette.entries
                if section_filter is None or entry.section == section_filter
            ]

            for entry in sorted(entries, key=lambda candidate: candidate.label.casefold()):
                item = QListWidgetItem(self._list_label_for_entry(entry, show_palette=False))
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
        if self._is_searching() and not entry_matches_search(entry, self._search_query()):
            self._clear_search()

        palette_index = self._category_combo.findData(entry.palette)

        if palette_index < 0:
            return

        if self._category_combo.currentIndex() != palette_index:
            self._category_combo.setCurrentIndex(palette_index)
        elif not self._is_searching():
            self._configure_dimension_filter(entry.palette)
            self._populate_block_list(entry.palette)

        if not self._is_searching() and entry.section and self._dimension_combo.count() > 0:
            section_index = self._dimension_combo.findData(entry.section)

            if section_index >= 0:
                self._dimension_combo.blockSignals(True)
                self._dimension_combo.setCurrentIndex(section_index)
                self._dimension_combo.blockSignals(False)
                self._populate_block_list(entry.palette)

        if self._is_searching():
            self._block_list.blockSignals(True)
            try:
                for row in range(self._block_list.count()):
                    item = self._block_list.item(row)
                    candidate = item.data(_ENTRY_ROLE)

                    if candidate == entry:
                        self._block_list.setCurrentItem(item)
                        return
            finally:
                self._block_list.blockSignals(False)
            return

        self._block_list.blockSignals(True)
        try:
            for row in range(self._block_list.count()):
                item = self._block_list.item(row)
                candidate = item.data(_ENTRY_ROLE)

                if candidate == entry:
                    self._block_list.setCurrentItem(item)
                    return
        finally:
            self._block_list.blockSignals(False)

    def clear_selection(self) -> None:
        self._block_list.clearSelection()
        self._block_list.setCurrentRow(-1)
