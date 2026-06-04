"""Application-wide popup menu styling for the structure editor."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication, QMenu

_MENU_STYLE_MARKER = "/* structure-scripts-menus */"

EDITOR_MENU_STYLE = """
QMenu {
    padding: 6px 0px;
}
QMenu::item {
    min-height: 18px;
    padding: 3px 24px 3px 16px;
    font-size: 13px;
}
QMenu::item:selected {
    background: #4e4e4e;
    color: #e8e8e8;
}
QMenu::icon {
    padding-left: 14px;
}
"""


def configure_ui_menus() -> None:
    """Apply editor menu styling to all ``QMenu`` instances (menu bar, context menus, toolbar)."""
    app = QApplication.instance()

    if app is None:
        return

    existing = app.styleSheet() or ""

    if _MENU_STYLE_MARKER in existing:
        return

    app.setStyleSheet(f"{existing}\n{_MENU_STYLE_MARKER}\n{EDITOR_MENU_STYLE}")


def style_editor_popup_menu(menu: QMenu) -> None:
    """No-op; menus use :func:`configure_ui_menus` at application startup."""


def style_layer_tool_menu(menu: QMenu) -> None:
    """No-op; kept for call-site compatibility."""
