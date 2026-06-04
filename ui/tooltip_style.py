"""Application-wide tooltip colors (readable on dark desktop themes)."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QObject
from PySide6.QtGui import QHelpEvent
from PySide6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QToolTip

_TOOLTIP_STYLE_MARKER = "/* structure-scripts-tooltips */"

_TOOLTIP_STYLE = """
QToolTip {
    color: #f0f0f0;
    background-color: #454545;
    border: 1px solid #666666;
    padding: 3px 3px;
    border-radius: 4px;
}
"""


def configure_ui_tooltips() -> None:
    app = QApplication.instance()

    if app is None:
        return

    existing = app.styleSheet() or ""

    if _TOOLTIP_STYLE_MARKER in existing:
        return

    app.setStyleSheet(f"{existing}\n{_TOOLTIP_STYLE_MARKER}\n{_TOOLTIP_STYLE}")


class TableViewportTooltipFilter(QObject):
    """Show cell tooltips via :meth:`QToolTip.showText` (avoids blank popups with delegates)."""

    def __init__(
        self,
        table: QTableWidget,
        *,
        tooltip_text: Callable[[QTableWidgetItem | None], str],
    ) -> None:
        super().__init__(table)
        self._table = table
        self._tooltip_text = tooltip_text

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.ToolTip and isinstance(event, QHelpEvent):
            item = self._table.itemAt(event.pos())
            text = self._tooltip_text(item)

            if text:
                # No widget parent — avoids inheriting table/cell colors on the popup.
                QToolTip.showText(event.globalPos(), text)

            return True

        return super().eventFilter(obj, event)


def install_table_viewport_tooltips(
    table: QTableWidget,
    *,
    tooltip_text: Callable[[QTableWidgetItem | None], str],
) -> TableViewportTooltipFilter:
    """Attach a viewport filter that renders *tooltip_text* with global ``QToolTip`` styling."""
    filter_ = TableViewportTooltipFilter(table, tooltip_text=tooltip_text)
    table.viewport().installEventFilter(filter_)
    return filter_
