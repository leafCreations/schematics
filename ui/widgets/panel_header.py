"""Title row for QGroupBox panels (title left, actions right)."""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

PANEL_MARGINS = (8, 4, 8, 8)
PANEL_NESTED_MARGINS = (8, 8, 8, 8)
PANEL_LIST_MAX_HEIGHT = 220
PANEL_COMPASS_MAX_HEIGHT = 150


def add_panel_title_row(
    layout: QVBoxLayout,
    title: str,
    trailing_widgets: Iterable[QWidget],
) -> None:
    """Insert a bold title with trailing controls on one row."""
    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(2)

    title_label = QLabel(title)
    title_font = title_label.font()
    title_font.setBold(True)
    title_label.setFont(title_font)
    row.addWidget(title_label)
    row.addStretch(1)

    for widget in trailing_widgets:
        row.addWidget(widget)

    layout.addLayout(row)


def create_titled_panel_layout(
    panel: QGroupBox,
    title: str,
    trailing_widgets: Iterable[QWidget],
    *,
    margins: tuple[int, int, int, int] = PANEL_MARGINS,
) -> QVBoxLayout:
    """Use a custom title row instead of ``QGroupBox``'s built-in title."""
    panel.setTitle("")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(*margins)
    add_panel_title_row(layout, title, trailing_widgets)
    return layout


def create_simple_titled_panel_layout(
    panel: QGroupBox,
    title: str,
    *,
    margins: tuple[int, int, int, int] = PANEL_MARGINS,
) -> QVBoxLayout:
    """Bold title row for panels without header action buttons."""
    return create_titled_panel_layout(panel, title, (), margins=margins)


def create_nested_group_layout(
    group: QGroupBox,
    title: str,
    *,
    margins: tuple[int, int, int, int] = PANEL_NESTED_MARGINS,
) -> QVBoxLayout:
    """Bold title row for nested ``QGroupBox`` sections inside a panel."""
    return create_simple_titled_panel_layout(group, title, margins=margins)
