"""Structure footprint width/depth controls for the Structure tab."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class StructureSizePanel(QWidget):
    resize_requested = Signal(int, int)
    block_tooltips_changed = Signal(bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._block_signals = False

        self._width = QSpinBox()
        self._width.setRange(1, 512)
        self._width.setSuffix(" x")

        self._depth = QSpinBox()
        self._depth.setRange(1, 512)
        self._depth.setSuffix(" z")

        self._site_limit_label = QLabel()
        self._site_limit_label.setWordWrap(True)

        self._resize_button = QPushButton("Resize grid")
        self._resize_button.clicked.connect(self._on_resize_clicked)

        self._block_tooltips = QCheckBox("Show block tooltips on hover")
        self._block_tooltips.setToolTip(
            "When enabled, hovering a grid cell shows its block token (e.g. PLANKS, STAIRS)."
        )
        self._block_tooltips.toggled.connect(self.block_tooltips_changed.emit)

        form = QFormLayout()
        form.addRow("Width (x)", self._width)
        form.addRow("Depth (z)", self._depth)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(form)
        layout.addWidget(self._site_limit_label)
        layout.addWidget(self._block_tooltips)
        layout.addWidget(self._resize_button)

    def set_structure_size(self, width: int, depth: int) -> None:
        self._block_signals = True
        self._width.setValue(width)
        self._depth.setValue(depth)
        self._block_signals = False

    def set_site_limits(self, site_width: int, site_depth: int) -> None:
        self._width.setMaximum(site_width)
        self._depth.setMaximum(site_depth)
        self._site_limit_label.setText(
            f"Cannot exceed site grid ({site_width} × {site_depth}). "
            "Shrinking removes blocks from the east and south."
        )

    def current_size(self) -> tuple[int, int]:
        return self._width.value(), self._depth.value()

    def _on_resize_clicked(self) -> None:
        if self._block_signals:
            return

        self.resize_requested.emit(self._width.value(), self._depth.value())

    def set_block_tooltips_enabled(self, enabled: bool) -> None:
        self._block_tooltips.blockSignals(True)
        self._block_tooltips.setChecked(enabled)
        self._block_tooltips.blockSignals(False)

    def block_tooltips_enabled(self) -> bool:
        return self._block_tooltips.isChecked()
