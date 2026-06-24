"""Preview gallery navigation and zoom display for the Viewer tab."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSlider, QWidget

_ZOOM_SLIDER_MIN = 25
_ZOOM_SLIDER_MAX = 400
_DEFAULT_ZOOM_PERCENT = 100


class PreviewToolbar(QWidget):
    """Previous/Next gallery controls, zoom slider, and zoom level (far right)."""

    previous_clicked = Signal()
    next_clicked = Signal()
    zoom_changed = Signal(int)
    reset_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._prev_button = QPushButton("Previous")
        self._prev_button.clicked.connect(self.previous_clicked.emit)
        self._next_button = QPushButton("Next")
        self._next_button.clicked.connect(self.next_clicked.emit)

        self._zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self._zoom_slider.setRange(_ZOOM_SLIDER_MIN, _ZOOM_SLIDER_MAX)
        self._zoom_slider.setValue(_DEFAULT_ZOOM_PERCENT)
        self._zoom_slider.setSingleStep(1)
        self._zoom_slider.setPageStep(10)
        self._zoom_slider.setFixedWidth(140)
        self._zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)

        self._reset_button = QPushButton("Reset")
        self._reset_button.clicked.connect(self.reset_clicked.emit)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._zoom_label.setMinimumWidth(48)

        layout.addWidget(self._prev_button)
        layout.addWidget(self._next_button)
        layout.addStretch(1)
        layout.addWidget(self._zoom_slider)
        layout.addWidget(self._reset_button)
        layout.addWidget(self._zoom_label)

    def _on_zoom_slider_changed(self, value: int) -> None:
        self._zoom_label.setText(f"{value}%")
        self.zoom_changed.emit(value)

    def set_zoom_percent(self, percent: int) -> None:
        clamped = max(_ZOOM_SLIDER_MIN, min(_ZOOM_SLIDER_MAX, int(percent)))
        self._zoom_label.setText(f"{clamped}%")
        self._zoom_slider.blockSignals(True)
        self._zoom_slider.setValue(clamped)
        self._zoom_slider.blockSignals(False)

    def set_previous_enabled(self, enabled: bool) -> None:
        self._prev_button.setEnabled(enabled)

    def set_next_enabled(self, enabled: bool) -> None:
        self._next_button.setEnabled(enabled)

    def set_navigation_visible(self, visible: bool) -> None:
        self._prev_button.setVisible(visible)
        self._next_button.setVisible(visible)
