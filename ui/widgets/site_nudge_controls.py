from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SiteNudgeControls(QWidget):
    """Arrow buttons to move the selected structure on the site grid."""

    nudge_requested = Signal(int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        group = QGroupBox("Nudge placement")
        layout = QGridLayout(group)
        layout.setSpacing(4)

        north = QPushButton("↑ N")
        south = QPushButton("↓ S")
        west = QPushButton("← W")
        east = QPushButton("→ E")

        for button in (north, south, west, east):
            button.setToolTip("Move structure one block (select structure on grid first)")

        north.clicked.connect(lambda: self.nudge_requested.emit(0, -1))
        south.clicked.connect(lambda: self.nudge_requested.emit(0, 1))
        west.clicked.connect(lambda: self.nudge_requested.emit(-1, 0))
        east.clicked.connect(lambda: self.nudge_requested.emit(1, 0))

        layout.addWidget(north, 0, 1)
        layout.addWidget(west, 1, 0)
        layout.addWidget(east, 1, 2)
        layout.addWidget(south, 2, 1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(group)

    def set_enabled(self, enabled: bool) -> None:
        for child in self.findChildren(QPushButton):
            child.setEnabled(enabled)
