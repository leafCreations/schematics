"""Selector brush hints for structure-layer editing."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QSizePolicy

from ui.widgets.panel_header import create_simple_titled_panel_layout


class LayerSelectorPanel(QGroupBox):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = create_simple_titled_panel_layout(self, "Selector")

        hint = QLabel(
            "Drag to select. Ctrl+click toggles cells. Same block type: edit in Selected Block."
        )
        hint.setWordWrap(True)

        self._selection_range = QLabel("—")
        self._selection_range.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        form = QFormLayout()
        form.addRow("Selected cells", self._selection_range)

        layout.addWidget(hint)
        layout.addLayout(form)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

    def set_selection_range(self, text: str) -> None:
        self._selection_range.setText(text or "—")
