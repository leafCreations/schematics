"""List row with label and optional render-visibility toggle (Groups / Layers panels)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget

from ui.toolbar_icons import layer_visible_off_icon, panel_icon_size
from ui.widgets.panel_tool_button import PANEL_BUTTON_STYLE


class VisibilityListRow(QWidget):
    """One row in a managed list: label click selects; optional eye toggles visibility."""

    row_clicked = Signal(object)
    visibility_clicked = Signal(object)

    def __init__(
        self,
        *,
        row_key: object,
        label_text: str,
        hidden: bool,
        show_visibility: bool = True,
        hidden_tooltip: str = "Show in renders",
        visible_tooltip: str = "Hide from renders",
        word_wrap: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._row_key = row_key
        self._hidden_tooltip = hidden_tooltip
        self._visible_tooltip = visible_tooltip

        self._label = QLabel(label_text)
        self._label.setWordWrap(word_wrap)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 2, 2)
        layout.setSpacing(4)
        layout.addWidget(self._label, stretch=1)

        if show_visibility:
            self._visibility_button = QToolButton()
            self._visibility_button.setAutoRaise(True)
            self._visibility_button.setIconSize(panel_icon_size())
            self._visibility_button.setFixedSize(panel_icon_size())
            self._visibility_button.setStyleSheet(PANEL_BUTTON_STYLE)
            self._visibility_button.clicked.connect(self._on_visibility_clicked)
            self._set_hidden(hidden)
            layout.addWidget(self._visibility_button, alignment=Qt.AlignmentFlag.AlignRight)
        else:
            self._visibility_button = None

    def _set_hidden(self, hidden: bool) -> None:
        if self._visibility_button is None:
            return

        icon_px = panel_icon_size().width()

        if hidden:
            self._visibility_button.setIcon(layer_visible_off_icon(size=icon_px))
            self._visibility_button.setToolTip(self._hidden_tooltip)
        else:
            self._visibility_button.setIcon(QIcon())
            self._visibility_button.setToolTip(self._visible_tooltip)

    def _on_visibility_clicked(self) -> None:
        self.visibility_clicked.emit(self._row_key)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if self._visibility_button is not None and self._visibility_button.geometry().contains(
            event.position().toPoint()
        ):
            super().mousePressEvent(event)
            return

        self.row_clicked.emit(self._row_key)
        super().mousePressEvent(event)
