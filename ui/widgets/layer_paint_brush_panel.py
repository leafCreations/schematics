"""Paint brush hints and options for structure-layer editing."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QSizePolicy,
)

from helpers.grid_brush import PaintBrushMode
from ui.widgets.panel_header import create_simple_titled_panel_layout


class LayerPaintBrushPanel(QGroupBox):
    brush_mode_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = create_simple_titled_panel_layout(self, "Paint brush")

        self._brush_type = QComboBox()
        self._brush_type.addItem("Fill", "fill")
        self._brush_type.addItem("Outline", "outline")
        self._brush_type.setToolTip(
            "Fill: all cells in the dragged rectangle. "
            "Outline: only the outer edge of the rectangle."
        )
        self._brush_type.currentIndexChanged.connect(self.brush_mode_changed.emit)

        form = QFormLayout()
        form.addRow("Brush type", self._brush_type)

        layout.addLayout(form)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

    def paint_brush_mode(self) -> PaintBrushMode:
        mode = self._brush_type.currentData()

        if mode in ("fill", "outline"):
            return mode

        return "fill"
