"""Compact tool buttons for left-column Structure panels."""

from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QToolButton

from ui.toolbar_icons import panel_icon_size

PANEL_BUTTON_STYLE = """
QToolButton {
    background: transparent;
    border: none;
    border-radius: 3px;
    padding: 2px;
    margin: 0px;
}
QToolButton:hover:!disabled {
    background: palette(midlight);
}
QToolButton:pressed:!disabled {
    background: palette(mid);
}
QToolButton:disabled {
    background: transparent;
}
"""


def make_panel_tool_button(
    icon: QIcon,
    tooltip: str,
    *,
    clicked,
) -> QToolButton:
    button = QToolButton()
    button.setIcon(icon)
    button.setIconSize(panel_icon_size())
    button.setFixedSize(panel_icon_size())
    button.setToolTip(tooltip)
    button.setAutoRaise(True)
    button.setStyleSheet(PANEL_BUTTON_STYLE)
    button.clicked.connect(clicked)
    return button
