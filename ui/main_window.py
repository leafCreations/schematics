from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from ui.document import StructureDocument, open_structure, save_layer
from ui.platform import ensure_qt_platform
from ui.texture_cache import GridTextureCache
from ui.widgets.grid import LayerGridWidget
from ui.widgets.palette_panel import PalettePanel
from ui.widgets.properties_panel import PropertiesPanel


class MainWindow(QMainWindow):
    def __init__(self, document: StructureDocument, parent=None) -> None:
        super().__init__(parent)
        self._document = document
        self._current_layer_index = 0
        self._dirty_layers: set[int] = set()
        self._eraser_active = False
        self._structure_name = document.metadata.get("name", document.structure_path.stem)

        self._layer_selector = QComboBox()
        self._eraser_button = QPushButton("Eraser")
        self._eraser_button.setCheckable(True)
        self._save_button = QPushButton("Save Layer")
        self._status = QStatusBar()
        self._status.showMessage("Loading block textures...")
        QApplication.processEvents()
        self._texture_cache = GridTextureCache()
        self._grid = LayerGridWidget(self._texture_cache)
        self._palette_panel = PalettePanel()
        self._properties_panel = PropertiesPanel()

        self.setStatusBar(self._status)

        for index, layer in enumerate(document.layers):
            label = layer.get("group") or layer.get("name") or f"Layer {layer.get('index', index)}"
            self._layer_selector.addItem(f"{index}: {label}", index)

        self._layer_selector.currentIndexChanged.connect(self._on_layer_changed)
        self._eraser_button.toggled.connect(self._on_eraser_toggled)
        self._save_button.clicked.connect(self._save_current_layer)
        self._palette_panel.entry_selected.connect(self._on_palette_entry_selected)
        self._properties_panel.brush_changed.connect(self._update_window_title)
        self._grid.cell_selected.connect(self._on_grid_cell_selected)
        self._grid.cell_paint_requested.connect(self._on_cell_paint)
        self._grid.cell_erase_requested.connect(self._on_cell_erase)
        self._grid.itemSelectionChanged.connect(self._grid.highlight_selection)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.addWidget(QLabel("Layer"))
        header_layout.addWidget(self._layer_selector, stretch=1)
        header_layout.addWidget(self._eraser_button)
        header_layout.addWidget(self._save_button)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(header)
        center_layout.addWidget(self._grid, stretch=1)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._palette_panel)
        splitter.addWidget(center)
        splitter.addWidget(self._properties_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 1)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(splitter)
        self.setCentralWidget(container)

        self._show_layer(0)
        self._update_window_title()
        self.resize(1280, 800)
        self._status.showMessage("Left-click to paint, right-click to erase.", 5000)

    def _on_palette_entry_selected(self, entry) -> None:
        if self._eraser_active:
            self._eraser_button.setChecked(False)

        self._properties_panel.show_picker_entry(entry)

    def _on_eraser_toggled(self, active: bool) -> None:
        self._eraser_active = active

        if active:
            self._palette_panel.clear_selection()
            self._properties_panel.clear_picker_entry()
            self._status.showMessage("Eraser active — left-click or right-click cells to clear.")
        else:
            self._status.showMessage("Select a palette block to paint.", 3000)

        self._update_window_title()

    def _on_layer_changed(self, index: int) -> None:
        if index < 0:
            return

        if index == self._current_layer_index:
            return

        if not self._confirm_discard_layer_changes(self._current_layer_index):
            self._layer_selector.blockSignals(True)
            self._layer_selector.setCurrentIndex(self._current_layer_index)
            self._layer_selector.blockSignals(False)
            return

        self._show_layer(index)

    def _confirm_discard_layer_changes(self, layer_index: int) -> bool:
        if layer_index not in self._dirty_layers:
            return True

        layer_path = self._document.layer_paths[layer_index].name
        answer = QMessageBox.question(
            self,
            "Unsaved changes",
            f"Save changes to {layer_path} before switching layers?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

        if answer == QMessageBox.StandardButton.Cancel:
            return False

        return not (answer == QMessageBox.StandardButton.Save and not self._save_layer(layer_index))

    def _show_layer(self, index: int) -> None:
        layer = self._document.layers[index]
        self._current_layer_index = index
        self._grid.set_layer_cells(layer["cells"])
        layer_path = self._document.layer_paths[index]
        self._update_save_button()
        self._update_window_title()
        self._status.showMessage(f"Editing {layer_path.name}")

    def _on_grid_cell_selected(self, row: int, col: int, raw_token: str) -> None:
        self._properties_panel.show_grid_cell(row, col, raw_token)

    def _on_cell_paint(self, row: int, col: int) -> None:
        if self._eraser_active:
            self._set_cell(row, col, ".")
            return

        token = self._properties_panel.build_placement_token()

        if token is None:
            return

        self._set_cell(row, col, token)

    def _on_cell_erase(self, row: int, col: int) -> None:
        self._set_cell(row, col, ".")

    def _set_cell(self, row: int, col: int, raw_token: str) -> None:
        layer = self._document.layers[self._current_layer_index]
        cells = layer["cells"]

        if cells[row][col] == raw_token:
            return

        cells[row][col] = raw_token
        self._grid.update_cell(row, col, raw_token)
        self._mark_layer_dirty(self._current_layer_index)
        self._properties_panel.show_grid_cell(row, col, raw_token)

    def _mark_layer_dirty(self, layer_index: int) -> None:
        self._dirty_layers.add(layer_index)
        self._update_save_button()
        self._update_window_title()

    def _mark_layer_clean(self, layer_index: int) -> None:
        self._dirty_layers.discard(layer_index)
        self._update_save_button()
        self._update_window_title()

    def _update_save_button(self) -> None:
        suffix = " *" if self._current_layer_index in self._dirty_layers else ""
        self._save_button.setText(f"Save Layer{suffix}")

    def _update_window_title(self) -> None:
        dirty_marker = " *" if self._dirty_layers else ""
        self.setWindowTitle(f"Structure Editor — {self._structure_name}{dirty_marker}")

    def _save_current_layer(self) -> None:
        if self._save_layer(self._current_layer_index):
            path = self._document.layer_paths[self._current_layer_index]
            self._status.showMessage(f"Saved {path.name}", 3000)

    def _save_layer(self, layer_index: int) -> bool:
        layer = self._document.layers[layer_index]
        path = self._document.layer_paths[layer_index]

        try:
            save_layer(path, layer)
        except OSError as exc:
            QMessageBox.critical(self, "Save failed", str(exc))
            return False

        self._mark_layer_clean(layer_index)
        return True

    def closeEvent(self, event) -> None:
        if self._dirty_layers:
            answer = QMessageBox.question(
                self,
                "Unsaved changes",
                "Save unsaved layer changes before quitting?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )

            if answer == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return

            if answer == QMessageBox.StandardButton.Save:
                for layer_index in sorted(self._dirty_layers):
                    if not self._save_layer(layer_index):
                        event.ignore()
                        return

        event.accept()


def build_main_window(structure: str, stage: int) -> MainWindow:
    document = open_structure(structure, stage)
    return MainWindow(document)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Structure schematic editor")
    parser.add_argument("--structure", default="residence")
    parser.add_argument("--stage", type=int, default=1)
    args = parser.parse_args(argv)

    ensure_qt_platform()
    app = QApplication(sys.argv)
    window = build_main_window(args.structure, args.stage)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
