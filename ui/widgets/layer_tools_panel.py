"""Structure-layer action toolbar (eraser, save)."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, Qt, Signal
from PySide6.QtGui import QAction, QActionGroup, QHelpEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMenu,
    QToolBar,
    QToolButton,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from ui.selector_mode import SelectorMode
from ui.toolbar_icons import (
    layer_copy_icon,
    layer_eraser_icon,
    layer_move_selection_icon,
    layer_paint_brush_icon,
    layer_painting_grid_icon,
    layer_paste_icon,
    layer_rotate_left_icon,
    layer_rotate_right_icon,
    layer_selector_rectangle_icon,
    layer_selector_same_block_icon,
    toolbar_icon_size,
)

_FLAT_TOOLBAR_STYLE = """
QToolBar {
    background: transparent;
    border: none;
    spacing: 2px;
    padding: 0px;
}
QToolButton {
    background: transparent;
    border: none;
    border-radius: 4px;
    padding: 5px;
    margin: 0px;
}
QToolButton:hover:!disabled {
    background: palette(midlight);
}
QToolButton:pressed:!disabled {
    background: palette(mid);
}
QToolButton:checked:!disabled {
    background: palette(highlight);
}
QToolButton:disabled {
    background: transparent;
}
"""

_ERASER_TOGGLE_STYLE = """
QToolButton#layerEraserToggle {
    background: transparent;
    border: none;
    border-top-left-radius: 4px;
    border-bottom-left-radius: 4px;
    padding: 5px;
    margin: 0px;
}
QToolButton#layerEraserToggle:hover:!disabled {
    background: palette(midlight);
}
QToolButton#layerEraserToggle:pressed:!disabled {
    background: palette(mid);
}
QToolButton#layerEraserToggle:checked:!disabled {
    background: palette(highlight);
}
"""

_SELECTOR_TOGGLE_STYLE = """
QToolButton#layerSelectorToggle {
    background: transparent;
    border: none;
    border-top-left-radius: 4px;
    border-bottom-left-radius: 4px;
    padding: 5px;
    margin: 0px;
}
QToolButton#layerSelectorToggle:hover:!disabled {
    background: palette(midlight);
}
QToolButton#layerSelectorToggle:pressed:!disabled {
    background: palette(mid);
}
QToolButton#layerSelectorToggle:checked:!disabled {
    background: palette(highlight);
}
"""

_SELECTOR_MENU_BUTTON_STYLE = """
QToolButton#layerSelectorMenu {
    background: transparent;
    border: none;
    border-left: 1px solid palette(mid);
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
    padding: 4px 2px;
    margin: 0px;
    min-width: 10px;
}
QToolButton#layerSelectorMenu:hover:!disabled {
    background: palette(midlight);
}
QToolButton#layerSelectorMenu:pressed:!disabled {
    background: palette(mid);
}
"""

_ERASER_MENU_BUTTON_STYLE = """
QToolButton#layerEraserMenu {
    background: transparent;
    border: none;
    border-left: 1px solid palette(mid);
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
    padding: 4px 2px;
    margin: 0px;
    min-width: 10px;
}
QToolButton#layerEraserMenu:hover:!disabled {
    background: palette(midlight);
}
QToolButton#layerEraserMenu:pressed:!disabled {
    background: palette(mid);
}
"""


_PAINT_BRUSH_TOOLTIP = "Toggle paint mode (drag to select region, release to place)"
_SELECTOR_TOOLTIP = "Selection Tool"
_MOVE_TOOLTIP = "Toggle move (drag to select, then drag to place)"
_ERASER_TOOLTIP = "Toggle erase mode (left-click clears cells)"


class _SuppressTooltips(QObject):
    """Drop tooltip events (used for the eraser menu arrow and container)."""

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.ToolTip:
            return True

        return super().eventFilter(obj, event)


class _PaintBrushTooltipFilter(QObject):
    """Show a readable tooltip for the paint brush toggle."""

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.ToolTip and isinstance(event, QHelpEvent):
            QToolTip.showText(event.globalPos(), _PAINT_BRUSH_TOOLTIP, obj)
            return True

        return super().eventFilter(obj, event)


class _SelectorTooltipFilter(QObject):
    """Show a readable tooltip for the selector toggle."""

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.ToolTip and isinstance(event, QHelpEvent):
            QToolTip.showText(event.globalPos(), _SELECTOR_TOOLTIP, obj)
            return True

        return super().eventFilter(obj, event)


class _MoveTooltipFilter(QObject):
    """Show a readable tooltip for the move toggle."""

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.ToolTip and isinstance(event, QHelpEvent):
            QToolTip.showText(event.globalPos(), _MOVE_TOOLTIP, obj)
            return True

        return super().eventFilter(obj, event)


class _EraserTooltipFilter(QObject):
    """Show a readable tooltip for the eraser toggle (avoids broken theme defaults)."""

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.ToolTip and isinstance(event, QHelpEvent):
            QToolTip.showText(event.globalPos(), _ERASER_TOOLTIP, obj)
            return True

        return super().eventFilter(obj, event)


class LayerActionToolbar(QToolBar):
    """Icon toolbar: Selector | Move | Paint | Eraser | Copy | Paste | Rotate | Painting grid."""

    paint_brush_toggled = Signal(bool)
    selector_toggled = Signal(bool)
    selector_mode_changed = Signal(SelectorMode)
    move_toggled = Signal(bool)
    eraser_toggled = Signal(bool)
    clear_entire_layer_requested = Signal()
    copy_requested = Signal()
    paste_requested = Signal()
    rotate_left_requested = Signal()
    rotate_right_requested = Signal()
    painting_grid_toggled = Signal(bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMovable(False)
        self.setFloatable(False)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setIconSize(toolbar_icon_size())
        self.setStyleSheet(_FLAT_TOOLBAR_STYLE)

        self._selector_tooltip_filter = _SelectorTooltipFilter(self)
        self._no_tooltip_filter = _SuppressTooltips(self)
        self._make_selector_control()

        self._move_tooltip_filter = _MoveTooltipFilter(self)
        self._move_action = QAction(layer_move_selection_icon(), "Move", self)
        self._move_action.setCheckable(True)
        self._move_action.toggled.connect(self.move_toggled.emit)
        move_toggle = QToolButton(self)
        move_toggle.setDefaultAction(self._move_action)
        move_toggle.setAutoRaise(True)
        move_toggle.installEventFilter(self._move_tooltip_filter)
        self.addWidget(move_toggle)

        self.addSeparator()

        self._paint_brush_tooltip_filter = _PaintBrushTooltipFilter(self)
        self._paint_brush_action = QAction(layer_paint_brush_icon(), "Paint brush", self)
        self._paint_brush_action.setCheckable(True)
        self._paint_brush_action.setChecked(True)
        self._paint_brush_action.toggled.connect(self.paint_brush_toggled.emit)
        paint_toggle = QToolButton(self)
        paint_toggle.setDefaultAction(self._paint_brush_action)
        paint_toggle.setAutoRaise(True)
        paint_toggle.installEventFilter(self._paint_brush_tooltip_filter)
        self.addWidget(paint_toggle)

        self.addSeparator()

        self._eraser_tooltip_filter = _EraserTooltipFilter(self)
        self._make_eraser_control()

        self.addSeparator()

        self._copy_action = self._make_action(
            layer_copy_icon(),
            "Copy",
            "Copy selected cells (use Selector tool or Ctrl+click)",
            self.copy_requested.emit,
        )
        self._copy_action.setEnabled(False)

        self._paste_action = self._make_action(
            layer_paste_icon(),
            "Paste",
            "Paste copied cells starting at the selection anchor",
            self.paste_requested.emit,
        )
        self._paste_action.setEnabled(False)

        self.addSeparator()

        self._make_action(
            layer_rotate_left_icon(),
            "Rotate left",
            "Rotate all layers 90° counter-clockwise",
            self.rotate_left_requested.emit,
        )

        self._make_action(
            layer_rotate_right_icon(),
            "Rotate right",
            "Rotate all layers 90° clockwise",
            self.rotate_right_requested.emit,
        )

        self.addSeparator()

        self._painting_grid_action = QAction(layer_painting_grid_icon(), "Painting Grid", self)
        self._painting_grid_action.setCheckable(True)
        self._painting_grid_action.setChecked(True)
        self._painting_grid_action.setToolTip("Show or hide cell grid borders")
        self._painting_grid_action.toggled.connect(self.painting_grid_toggled.emit)
        self.addAction(self._painting_grid_action)

    def _make_action(
        self,
        icon,
        text: str,
        tooltip: str,
        triggered,
    ) -> QAction:
        action = QAction(icon, text, self)
        action.setToolTip(tooltip)

        if triggered is not None:
            action.triggered.connect(triggered)

        self.addAction(action)
        return action

    def _make_selector_control(self) -> None:
        self._selector_mode = SelectorMode.RECTANGLE

        self._rectangle_mode_action = QAction(
            layer_selector_rectangle_icon(),
            "Rectangle",
            self,
        )
        self._same_block_mode_action = QAction(
            layer_selector_same_block_icon(),
            "Same Block",
            self,
        )
        self._rectangle_mode_action.setCheckable(True)
        self._same_block_mode_action.setCheckable(True)
        self._rectangle_mode_action.setChecked(True)

        mode_group = QActionGroup(self)
        mode_group.setExclusive(True)
        mode_group.addAction(self._rectangle_mode_action)
        mode_group.addAction(self._same_block_mode_action)

        menu = QMenu(self)
        menu.addAction(self._rectangle_mode_action)
        menu.addAction(self._same_block_mode_action)

        self._rectangle_mode_action.triggered.connect(
            lambda: self._choose_selector_mode_from_menu(SelectorMode.RECTANGLE),
        )
        self._same_block_mode_action.triggered.connect(
            lambda: self._choose_selector_mode_from_menu(SelectorMode.SAME_BLOCK),
        )

        icon_size = toolbar_icon_size()

        container = QWidget(self)
        container.setStyleSheet("background: transparent;")
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        self._selector_action = QAction(
            layer_selector_rectangle_icon(),
            "Selection Tool",
            self,
        )
        self._selector_action.setCheckable(True)

        toggle = QToolButton(container)
        toggle.setObjectName("layerSelectorToggle")
        toggle.setDefaultAction(self._selector_action)
        toggle.setIconSize(icon_size)
        toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        toggle.setAutoRaise(True)
        toggle.setStyleSheet(_SELECTOR_TOGGLE_STYLE)
        toggle.installEventFilter(self._selector_tooltip_filter)
        self._selector_action.toggled.connect(self.selector_toggled.emit)

        container.installEventFilter(self._no_tooltip_filter)

        menu_button = QToolButton(container)
        menu_button.setObjectName("layerSelectorMenu")
        menu_button.setArrowType(Qt.ArrowType.DownArrow)
        menu_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        menu_button.setAutoRaise(True)
        menu_button.setStyleSheet(_SELECTOR_MENU_BUTTON_STYLE)
        menu_button.setFixedWidth(11)
        menu_button.installEventFilter(self._no_tooltip_filter)
        menu_button.clicked.connect(
            lambda: menu.popup(container.mapToGlobal(QPoint(0, container.height()))),
        )

        row.addWidget(toggle)
        row.addWidget(menu_button)
        self.addWidget(container)

    def _choose_selector_mode_from_menu(self, mode: SelectorMode) -> None:
        self.set_selector_mode(mode)

        if not self._selector_action.isChecked():
            self._selector_action.setChecked(True)

    def _set_selector_mode(self, mode: SelectorMode) -> None:
        if mode == self._selector_mode:
            return

        self._selector_mode = mode
        icon = (
            layer_selector_rectangle_icon()
            if mode is SelectorMode.RECTANGLE
            else layer_selector_same_block_icon()
        )
        self._selector_action.setIcon(icon)
        self.selector_mode_changed.emit(mode)

    def selector_mode(self) -> SelectorMode:
        return self._selector_mode

    def set_selector_mode(self, mode: SelectorMode) -> None:
        if mode is SelectorMode.RECTANGLE:
            self._rectangle_mode_action.setChecked(True)
        else:
            self._same_block_mode_action.setChecked(True)

        self._set_selector_mode(mode)

    def _make_eraser_control(self) -> None:
        clear_action = QAction("Clear entire layer", self)
        clear_action.setToolTip("Set every cell in the current layer to empty (.)")
        clear_action.triggered.connect(self.clear_entire_layer_requested.emit)

        menu = QMenu(self)
        menu.addAction(clear_action)

        icon_size = toolbar_icon_size()

        container = QWidget(self)
        container.setStyleSheet("background: transparent;")
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        self._eraser_action = QAction(layer_eraser_icon(), "Eraser", self)
        self._eraser_action.setCheckable(True)

        toggle = QToolButton(container)
        toggle.setObjectName("layerEraserToggle")
        toggle.setDefaultAction(self._eraser_action)
        toggle.setIconSize(icon_size)
        toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        toggle.setAutoRaise(True)
        toggle.setStyleSheet(_ERASER_TOGGLE_STYLE)
        toggle.installEventFilter(self._eraser_tooltip_filter)
        self._eraser_action.toggled.connect(self.eraser_toggled.emit)

        container.installEventFilter(self._no_tooltip_filter)

        menu_button = QToolButton(container)
        menu_button.setObjectName("layerEraserMenu")
        menu_button.setArrowType(Qt.ArrowType.DownArrow)
        menu_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        menu_button.setAutoRaise(True)
        menu_button.setStyleSheet(_ERASER_MENU_BUTTON_STYLE)
        menu_button.setFixedWidth(11)
        menu_button.installEventFilter(self._no_tooltip_filter)
        menu_button.clicked.connect(
            lambda: menu.popup(container.mapToGlobal(QPoint(0, container.height()))),
        )

        row.addWidget(toggle)
        row.addWidget(menu_button)
        self.addWidget(container)

    def set_copy_enabled(self, enabled: bool) -> None:
        self._copy_action.setEnabled(enabled)

    def set_paste_enabled(self, enabled: bool) -> None:
        self._paste_action.setEnabled(enabled)

    def set_painting_grid_checked(self, checked: bool) -> None:
        self._painting_grid_action.blockSignals(True)
        self._painting_grid_action.setChecked(checked)
        self._painting_grid_action.blockSignals(False)

    def set_paint_brush_checked(self, checked: bool) -> None:
        self._paint_brush_action.blockSignals(True)
        self._paint_brush_action.setChecked(checked)
        self._paint_brush_action.blockSignals(False)

    def set_selector_checked(self, checked: bool) -> None:
        self._selector_action.blockSignals(True)
        self._selector_action.setChecked(checked)
        self._selector_action.blockSignals(False)

    def set_move_checked(self, checked: bool) -> None:
        self._move_action.blockSignals(True)
        self._move_action.setChecked(checked)
        self._move_action.blockSignals(False)

    def set_eraser_checked(self, checked: bool) -> None:
        self._eraser_action.blockSignals(True)
        self._eraser_action.setChecked(checked)
        self._eraser_action.blockSignals(False)


class LayerToolsPanel(QWidget):
    paint_brush_toggled = Signal(bool)
    selector_toggled = Signal(bool)
    selector_mode_changed = Signal(SelectorMode)
    move_toggled = Signal(bool)
    eraser_toggled = Signal(bool)
    clear_entire_layer_requested = Signal()
    copy_requested = Signal()
    paste_requested = Signal()
    rotate_left_requested = Signal()
    rotate_right_requested = Signal()
    painting_grid_toggled = Signal(bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._toolbar = LayerActionToolbar()
        self._toolbar.paint_brush_toggled.connect(self.paint_brush_toggled.emit)
        self._toolbar.selector_toggled.connect(self.selector_toggled.emit)
        self._toolbar.selector_mode_changed.connect(self.selector_mode_changed.emit)
        self._toolbar.move_toggled.connect(self.move_toggled.emit)
        self._toolbar.eraser_toggled.connect(self.eraser_toggled.emit)
        self._toolbar.clear_entire_layer_requested.connect(self.clear_entire_layer_requested.emit)
        self._toolbar.copy_requested.connect(self.copy_requested.emit)
        self._toolbar.paste_requested.connect(self.paste_requested.emit)
        self._toolbar.rotate_left_requested.connect(self.rotate_left_requested.emit)
        self._toolbar.rotate_right_requested.connect(self.rotate_right_requested.emit)
        self._toolbar.painting_grid_toggled.connect(self.painting_grid_toggled.emit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._toolbar)

    def set_copy_enabled(self, enabled: bool) -> None:
        self._toolbar.set_copy_enabled(enabled)

    def set_paste_enabled(self, enabled: bool) -> None:
        self._toolbar.set_paste_enabled(enabled)

    def set_painting_grid_checked(self, checked: bool) -> None:
        self._toolbar.set_painting_grid_checked(checked)

    def set_paint_brush_checked(self, checked: bool) -> None:
        self._toolbar.set_paint_brush_checked(checked)

    def set_selector_checked(self, checked: bool) -> None:
        self._toolbar.set_selector_checked(checked)

    def selector_mode(self) -> SelectorMode:
        return self._toolbar.selector_mode()

    def set_selector_mode(self, mode: SelectorMode) -> None:
        self._toolbar.set_selector_mode(mode)

    def set_move_checked(self, checked: bool) -> None:
        self._toolbar.set_move_checked(checked)

    def set_eraser_checked(self, checked: bool) -> None:
        self._toolbar.set_eraser_checked(checked)
