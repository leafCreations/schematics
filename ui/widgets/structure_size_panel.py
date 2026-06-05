"""Structure footprint width/depth controls for the Structure tab."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

_RESIZE_TOOLTIP = (
    "Apply width and depth to every layer. Shrinking removes blocks from the east and south edges."
)


class StructureSizePanel(QWidget):
    resize_requested = Signal(int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._block_signals = False

        self._width = QSpinBox()
        self._width.setRange(1, 512)
        self._width.setSuffix(" x")

        self._depth = QSpinBox()
        self._depth.setRange(1, 512)
        self._depth.setSuffix(" z")

        self._site_max_label = QLabel()
        self._site_max_label.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
        )

        self._resize_button = QPushButton("Resize grid")
        self._resize_button.setToolTip(_RESIZE_TOOLTIP)
        self._resize_button.clicked.connect(self._on_resize_clicked)

        form = QFormLayout()
        form.addRow("Width (x)", self._width)
        form.addRow("Depth (z)", self._depth)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(form)
        layout.addWidget(self._site_max_label)
        layout.addWidget(self._resize_button)

    def set_structure_size(self, width: int, depth: int) -> None:
        self._block_signals = True
        self._width.setValue(width)
        self._depth.setValue(depth)
        self._block_signals = False

    def set_site_limits(self, site_width: int, site_depth: int) -> None:
        self._width.setMaximum(site_width)
        self._depth.setMaximum(site_depth)
        self._width.setToolTip(f"Structure width (x). Site maximum is {site_width}.")
        self._depth.setToolTip(f"Structure depth (z). Site maximum is {site_depth}.")
        self._site_max_label.setText(f"Site maximum: {site_width} × {site_depth}")

    def current_size(self) -> tuple[int, int]:
        return self._width.value(), self._depth.value()

    def _on_resize_clicked(self) -> None:
        if self._block_signals:
            return

        self.resize_requested.emit(self._width.value(), self._depth.value())
