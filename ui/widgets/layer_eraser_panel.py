"""Eraser settings for structure-layer editing."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QSizePolicy,
    QSpinBox,
)

from ui.widgets.panel_header import create_simple_titled_panel_layout


class LayerEraserPanel(QGroupBox):
    eraser_size_changed = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = create_simple_titled_panel_layout(self, "Eraser")

        hint = QLabel(
            "Drag to select a region (light red overlay), then release to erase. "
            "Hover shows eraser size for right-click. "
            "Middle-click a block to erase all matching cells on this layer."
        )
        hint.setWordWrap(True)

        self._size = QSpinBox()
        self._size.setRange(1, 1)
        self._size.setValue(1)
        self._size.setToolTip(
            "Square brush: 1 clears one cell, 3 clears a 3×3 area, etc. "
            "Hover the grid to preview affected cells."
        )
        self._size.valueChanged.connect(self.eraser_size_changed.emit)

        form = QFormLayout()
        form.addRow("Eraser size", self._size)

        layout.addWidget(hint)
        layout.addLayout(form)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

    def eraser_size(self) -> int:
        return self._size.value()

    def set_eraser_size(self, size: int) -> None:
        size = max(1, min(self._size.maximum(), size))
        self._size.setValue(size)

    def set_grid_bounds(self, *, width: int, depth: int) -> None:
        """Clamp the spinbox maximum to the current layer dimensions."""
        max_size = max(1, min(width, depth))
        current = self._size.value()
        self._size.blockSignals(True)

        try:
            self._size.setMaximum(max_size)

            if current > max_size:
                self._size.setValue(max_size)
        finally:
            self._size.blockSignals(False)
