"""Selector brush hints for structure-layer editing."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QSizePolicy

from ui.widgets.panel_header import create_simple_titled_panel_layout


class LayerSelectorPanel(QGroupBox):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = create_simple_titled_panel_layout(self, "Selector")

        self._hint = QLabel(
            "Drag to select a region. Ctrl+click toggles cells.",
        )
        self._hint.setWordWrap(True)

        self._selection_range = QLabel("—")
        self._selection_range.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        form = QFormLayout()
        form.addRow("Selected cells", self._selection_range)

        layout.addWidget(self._hint)
        layout.addLayout(form)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

    def set_selection_range(self, text: str) -> None:
        self._selection_range.setText(text or "—")

    def set_hint_for_mode(self, *, rectangle: bool) -> None:
        if rectangle:
            self._hint.setText("Drag to select a region. Ctrl+click toggles cells.")
        else:
            self._hint.setText(
                "Click a block to select all cells of the same type. Ctrl+click toggles cells.",
            )
