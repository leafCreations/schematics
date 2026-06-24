"""In-app schematic PNG preview for the Render tab."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QWidget,
)

import helpers.constants as constants
from renderers.registry import PREVIEW_RENDER_REGISTRY
from ui.editor_prefs import preview_zoom_percent, set_preview_zoom_percent
from ui.widgets.panel_header import create_simple_titled_panel_layout
from ui.widgets.preview_toolbar import PreviewToolbar

_PREVIEW_COMBO_MAX_WIDTH = 200
_THUMBNAIL_MAX_HEIGHT = 72
_ZOOM_MIN = 0.25
_ZOOM_MAX = 4.0
_ZOOM_WHEEL_FACTOR = 1.1
_DEFAULT_ZOOM = 1.0
_THUMBNAIL_BUTTON_STYLE = """
QPushButton {
    border: 2px solid transparent;
    border-radius: 3px;
    padding: 2px;
    background: transparent;
}
QPushButton:checked {
    border: 2px solid #0078d4;
    background-color: rgba(0, 120, 212, 0.12);
}
QPushButton:hover:!checked {
    border: 2px solid #c8c8c8;
}
"""


def clamp_zoom_factor(factor: float) -> float:
    return max(_ZOOM_MIN, min(_ZOOM_MAX, factor))


def zoom_percent(factor: float) -> int:
    return int(round(factor * 100))


class _PreviewScrollWheelFilter(QObject):
    def __init__(self, panel: PreviewPanel) -> None:
        super().__init__(panel)
        self._panel = panel

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Wheel and self._panel._source_pixmap is not None:
            wheel = event
            if isinstance(wheel, QWheelEvent):
                self._panel._on_preview_wheel(wheel)
                return True
        return super().eventFilter(watched, event)


class PreviewPanel(QGroupBox):
    preview_render_requested = Signal(str)
    preview_group_changed = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = create_simple_titled_panel_layout(self, "Preview")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._groups: list[str] = []
        self._image_paths: list[Path] = []
        self._current_index = -1
        self._source_pixmap: QPixmap | None = None
        self._zoom_factor = clamp_zoom_factor(preview_zoom_percent() / 100.0)

        self._render_combo = QComboBox()
        self._render_combo.setMaximumWidth(_PREVIEW_COMBO_MAX_WIDTH)
        self._render_combo.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self._render_combo.blockSignals(True)
        for render_name, label in PREVIEW_RENDER_REGISTRY.items():
            self._render_combo.addItem(label, render_name)
        self._render_combo.blockSignals(False)
        self._render_combo.currentIndexChanged.connect(self._on_render_selection_changed)

        self._group_combo = QComboBox()
        self._group_combo.setMaximumWidth(_PREVIEW_COMBO_MAX_WIDTH)
        self._group_combo.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self._group_combo.currentIndexChanged.connect(self._on_group_selection_changed)

        self._updated_label = QLabel()
        self._updated_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(8)
        toolbar_layout.addWidget(self._render_combo)
        toolbar_layout.addWidget(self._group_combo)
        toolbar_layout.addWidget(self._updated_label)
        toolbar_layout.addStretch(1)

        self._caption = QLabel("Select a render type to generate a preview.")
        self._caption.setWordWrap(True)

        self._preview_toolbar = PreviewToolbar()
        self._preview_toolbar.previous_clicked.connect(self._show_previous_image)
        self._preview_toolbar.next_clicked.connect(self._show_next_image)
        self._preview_toolbar.zoom_changed.connect(self._on_toolbar_zoom_changed)
        self._preview_toolbar.reset_clicked.connect(self.reset_zoom_to_default)

        self._thumbnail_buttons: list[QPushButton] = []
        self._thumbnail_group = QButtonGroup(self)
        self._thumbnail_group.setExclusive(True)
        self._thumbnail_group.idClicked.connect(self._on_thumbnail_clicked)

        self._thumbnail_strip = QWidget()
        self._thumbnail_layout = QHBoxLayout(self._thumbnail_strip)
        self._thumbnail_layout.setContentsMargins(0, 0, 0, 0)
        self._thumbnail_layout.setSpacing(6)

        self._thumbnail_scroll = QScrollArea()
        self._thumbnail_scroll.setWidget(self._thumbnail_strip)
        self._thumbnail_scroll.setWidgetResizable(True)
        self._thumbnail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._thumbnail_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._thumbnail_scroll.setFixedHeight(_THUMBNAIL_MAX_HEIGHT + 12)

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self._image_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self._scroll = QScrollArea()
        self._scroll.setWidget(self._image_label)
        self._scroll.setWidgetResizable(True)
        self._scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._scroll.viewport().installEventFilter(_PreviewScrollWheelFilter(self))

        layout.addWidget(toolbar)
        layout.addWidget(self._caption)
        layout.addWidget(self._thumbnail_scroll)
        layout.addWidget(self._preview_toolbar)
        layout.addWidget(self._scroll, stretch=1)

        self._group_combo.hide()
        self._update_group_combo_visibility()
        self._update_navigation_state()
        self._update_zoom_display()

    def zoom_factor(self) -> float:
        return self._zoom_factor

    def set_zoom_percent(self, percent: int) -> None:
        """Set preview zoom from an integer percent (25–400)."""
        self._set_zoom_factor(percent / 100.0)

    def restore_saved_zoom(self) -> None:
        """Apply the persisted preview zoom from editor settings."""
        self._set_zoom_factor(preview_zoom_percent() / 100.0, persist=False)

    def reset_zoom_to_default(self) -> None:
        """Reset zoom to 100% (tests and explicit reset)."""
        self._set_zoom_factor(_DEFAULT_ZOOM)

    def zoom_in(self) -> None:
        """Increase zoom by one wheel step (×1.1, clamped)."""
        self._set_zoom_factor(self._zoom_factor * _ZOOM_WHEEL_FACTOR)

    def zoom_out(self) -> None:
        """Decrease zoom by one wheel step (÷1.1, clamped)."""
        self._set_zoom_factor(self._zoom_factor / _ZOOM_WHEEL_FACTOR)

    def uses_group_selector(self) -> bool:
        return self.selected_render() == constants.RENDER_TOP_VIEW

    def _update_group_combo_visibility(self) -> None:
        if not self.uses_group_selector():
            self._group_combo.hide()
            return
        self._group_combo.setVisible(len(self._groups) > 1)

    def selected_render(self) -> str:
        render_name = self._render_combo.currentData()
        if not isinstance(render_name, str):
            raise RuntimeError("Preview render combo is missing render data.")
        return render_name

    def selected_group(self) -> str | None:
        if not self._groups:
            return None
        if len(self._groups) == 1:
            return self._groups[0]
        return self._group_combo.currentText() or None

    def set_groups(self, groups: list[str]) -> None:
        self._groups = list(groups)
        self._group_combo.blockSignals(True)
        self._group_combo.clear()
        for group in self._groups:
            self._group_combo.addItem(group)
        self._group_combo.blockSignals(False)
        self._update_group_combo_visibility()

    def set_render_busy(self, busy: bool) -> None:
        self._render_combo.setEnabled(not busy)
        if self.uses_group_selector():
            self._group_combo.setEnabled(not busy)
        self._preview_toolbar.set_previous_enabled(not busy and self._can_go_previous())
        self._preview_toolbar.set_next_enabled(not busy and self._can_go_next())

    def set_loading(self, message: str = "Rendering…") -> None:
        self._clear_gallery()
        self._updated_label.clear()
        self._caption.setText(message)
        self._caption.show()

    def clear(self, message: str = "Select a render type to generate a preview.") -> None:
        self._clear_gallery()
        self._updated_label.clear()
        self._caption.setText(message)
        self._caption.show()

    def set_gallery(self, image_paths: list[Path], *, select_index: int = 0) -> None:
        self._image_paths = list(image_paths)
        self._rebuild_thumbnails()

        if not self._image_paths:
            self._clear_image()
            self._current_index = -1
            self._update_navigation_state()
            return

        index = max(0, min(select_index, len(self._image_paths) - 1))
        self._show_image_at(index)

    def show_preview(self, image_path: Path) -> None:
        """Display a single image (legacy helper); prefer set_gallery for top-down previews."""
        self.set_gallery([image_path], select_index=0)

    def _on_render_selection_changed(self, _index: int) -> None:
        self._update_group_combo_visibility()
        self.preview_render_requested.emit(self.selected_render())

    def _on_group_selection_changed(self, _index: int) -> None:
        group_name = self.selected_group()
        if group_name:
            self.preview_group_changed.emit(group_name)

    def _on_thumbnail_clicked(self, index: int) -> None:
        if 0 <= index < len(self._image_paths):
            self._show_image_at(index)

    def _show_previous_image(self) -> None:
        if self._can_go_previous():
            self._show_image_at(self._current_index - 1)

    def _show_next_image(self) -> None:
        if self._can_go_next():
            self._show_image_at(self._current_index + 1)

    def _can_go_previous(self) -> bool:
        return self._current_index > 0

    def _can_go_next(self) -> bool:
        return 0 <= self._current_index < len(self._image_paths) - 1

    def _show_image_at(self, index: int) -> None:
        if not (0 <= index < len(self._image_paths)):
            return

        image_path = self._image_paths[index]
        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            self.clear("Could not load preview image.")
            return

        self._current_index = index
        self._source_pixmap = pixmap
        self._apply_zoom()

        modified = datetime.fromtimestamp(image_path.stat().st_mtime)
        self._updated_label.setText(f"Updated {modified:%Y-%m-%d %H:%M:%S}")
        self._caption.clear()
        self._caption.hide()

        if 0 <= index < len(self._thumbnail_buttons):
            self._sync_thumbnail_selection(index)

        self._update_navigation_state()

    def _on_preview_wheel(self, event: QWheelEvent) -> None:
        if self._source_pixmap is None or self._source_pixmap.isNull():
            return

        delta = event.angleDelta().y()
        if delta == 0:
            return

        factor = _ZOOM_WHEEL_FACTOR if delta > 0 else 1.0 / _ZOOM_WHEEL_FACTOR
        self._set_zoom_factor(self._zoom_factor * factor)

    def _on_toolbar_zoom_changed(self, percent: int) -> None:
        self._set_zoom_factor(percent / 100.0)

    def _set_zoom_factor(self, factor: float, *, persist: bool = True) -> None:
        self._zoom_factor = clamp_zoom_factor(factor)
        self._apply_zoom()
        if persist:
            set_preview_zoom_percent(zoom_percent(self._zoom_factor))

    def _apply_zoom(self) -> None:
        if self._source_pixmap is None or self._source_pixmap.isNull():
            self._image_label.clear()
            self._update_zoom_display()
            return

        width = max(1, int(self._source_pixmap.width() * self._zoom_factor))
        height = max(1, int(self._source_pixmap.height() * self._zoom_factor))
        scaled = self._source_pixmap.scaled(
            width,
            height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._scroll.setWidgetResizable(False)
        self._image_label.setPixmap(scaled)
        self._image_label.resize(scaled.size())
        self._update_zoom_display()

    def _update_zoom_display(self) -> None:
        self._preview_toolbar.set_zoom_percent(zoom_percent(self._zoom_factor))

    def _sync_thumbnail_selection(self, index: int) -> None:
        for button_index, button in enumerate(self._thumbnail_buttons):
            button.setChecked(button_index == index)

    def _rebuild_thumbnails(self) -> None:
        while self._thumbnail_layout.count():
            item = self._thumbnail_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._thumbnail_buttons.clear()
        for button in self._thumbnail_group.buttons():
            self._thumbnail_group.removeButton(button)

        for index, image_path in enumerate(self._image_paths):
            pixmap = QPixmap(str(image_path))
            button = QPushButton()
            button.setCheckable(True)
            button.setStyleSheet(_THUMBNAIL_BUTTON_STYLE)
            button.setToolTip(self._thumbnail_tooltip(image_path))

            if not pixmap.isNull():
                scaled = pixmap.scaledToHeight(
                    _THUMBNAIL_MAX_HEIGHT,
                    Qt.TransformationMode.SmoothTransformation,
                )
                button.setIcon(QIcon(scaled))
                button.setIconSize(scaled.size())

            self._thumbnail_group.addButton(button, index)
            self._thumbnail_layout.addWidget(button)
            self._thumbnail_buttons.append(button)

        self._thumbnail_layout.addStretch(1)
        self._thumbnail_scroll.setVisible(bool(self._image_paths))
        has_multiple = len(self._image_paths) > 1
        self._preview_toolbar.set_navigation_visible(has_multiple)

    def _thumbnail_tooltip(self, image_path: Path) -> str:
        stem = image_path.stem
        if "_facades_" in stem:
            direction = stem.rsplit("_facades_", 1)[-1]
            return f"Direction {direction}"
        if "_y" in stem:
            return f"Y={stem.rsplit('_y', 1)[-1]}"
        return stem

    def _update_navigation_state(self) -> None:
        has_multiple = len(self._image_paths) > 1
        self._preview_toolbar.set_previous_enabled(has_multiple and self._can_go_previous())
        self._preview_toolbar.set_next_enabled(has_multiple and self._can_go_next())

    def _clear_gallery(self) -> None:
        self._image_paths = []
        self._current_index = -1
        self._rebuild_thumbnails()
        self._clear_image()

    def _clear_image(self) -> None:
        self._source_pixmap = None
        self._image_label.clear()
        self._scroll.setWidgetResizable(True)
