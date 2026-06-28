"""HUD Properties dialog for Viewer 3D orbit camera overlay."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QSlider,
    QWidget,
)

from ui.app_settings import clamp_orbit_camera_move_speed
from ui.dialog_layout import (
    DIALOG_FIELD_MIN_WIDTH,
    apply_dialog_field_style,
    create_dialog_button_box,
    create_dialog_form_layout,
    create_dialog_shell,
)

_PLACEMENT_CHOICES: tuple[tuple[str, str], ...] = (
    ("top_left", "Top Left"),
    ("top_center", "Top Center"),
    ("top_right", "Top Right"),
    ("middle_left", "Middle Left"),
    ("middle_right", "Middle Right"),
    ("bottom_left", "Bottom Left"),
    ("bottom_center", "Bottom Center"),
    ("bottom_right", "Bottom Right"),
)

_SPEED_SLIDER_MIN = 0
_SPEED_SLIDER_MAX = 16
_SPEED_SLIDER_STEP = 1


@dataclass(frozen=True)
class CameraHudSettingsResult:
    hud_visible: bool
    placement: str
    crosshair_visible: bool
    move_speed: float


def _speed_from_slider(value: int) -> float:
    return clamp_orbit_camera_move_speed(0.2 + value * 0.05)


def _slider_from_speed(speed: float) -> int:
    clamped = clamp_orbit_camera_move_speed(speed)
    return int(round((clamped - 0.2) / 0.05))


class CameraHudSettingsDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        hud_visible: bool,
        placement: str,
        crosshair_visible: bool,
        move_speed: float,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("HUD Properties")

        self._show_hud = QCheckBox()
        self._show_hud.setChecked(hud_visible)

        self._placement = QComboBox()
        for value, label in _PLACEMENT_CHOICES:
            self._placement.addItem(label, value)
        index = self._placement.findData(placement)
        if index >= 0:
            self._placement.setCurrentIndex(index)
        apply_dialog_field_style(self._placement, min_width=DIALOG_FIELD_MIN_WIDTH)

        self._show_crosshair = QCheckBox()
        self._show_crosshair.setChecked(crosshair_visible)

        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setRange(_SPEED_SLIDER_MIN, _SPEED_SLIDER_MAX)
        self._speed_slider.setSingleStep(_SPEED_SLIDER_STEP)
        self._speed_slider.setPageStep(_SPEED_SLIDER_STEP)
        self._speed_slider.setValue(_slider_from_speed(move_speed))
        apply_dialog_field_style(self._speed_slider, min_width=DIALOG_FIELD_MIN_WIDTH)

        self._speed_value = QLabel()
        self._speed_value.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        self._update_speed_label(self._speed_slider.value())
        self._speed_slider.valueChanged.connect(self._update_speed_label)

        speed_row = QWidget()
        speed_layout = QHBoxLayout(speed_row)
        speed_layout.setContentsMargins(0, 0, 0, 0)
        speed_layout.setSpacing(8)
        speed_layout.addWidget(self._speed_slider, stretch=1)
        speed_layout.addWidget(self._speed_value)

        form = create_dialog_form_layout()
        form.addRow("Show HUD panel", self._show_hud)
        form.addRow("Placement", self._placement)
        form.addRow("Show Crosshairs", self._show_crosshair)
        form.addRow("Movement Speed", speed_row)

        hint = QLabel("Changes are saved when you click OK.")
        hint.setWordWrap(True)

        layout = create_dialog_shell(self)
        layout.addLayout(form)
        layout.addWidget(hint)
        layout.addWidget(create_dialog_button_box(self))

    def _update_speed_label(self, slider_value: int) -> None:
        speed = _speed_from_slider(slider_value)
        self._speed_value.setText(f"{speed:.2f}×")

    def values(self) -> CameraHudSettingsResult:
        placement = self._placement.currentData()
        if not isinstance(placement, str):
            placement = "top_right"
        return CameraHudSettingsResult(
            hud_visible=self._show_hud.isChecked(),
            placement=placement,
            crosshair_visible=self._show_crosshair.isChecked(),
            move_speed=_speed_from_slider(self._speed_slider.value()),
        )
