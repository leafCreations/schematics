"""Render type selection and generate action for the structure editor."""

from __future__ import annotations

import importlib.util

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import helpers.constants as constants
from renderers.registry import RENDER_REGISTRY
from ui.widgets.panel_header import create_nested_group_layout


def worldgen_dependencies_available() -> bool:
    return importlib.util.find_spec("amulet") is not None


def resolve_selected_renders(
    *,
    select_all: bool,
    checked_by_name: dict[str, bool],
) -> list[str]:
    if select_all:
        return [constants.RENDER_ALL]

    selected = [name for name, checked in checked_by_name.items() if checked]

    if not selected:
        raise ValueError("Select at least one render type.")

    return selected


class RenderPanel(QWidget):
    generate_requested = Signal(list)
    open_output_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._render_checks: dict[str, QCheckBox] = {}
        self._worldgen_available = worldgen_dependencies_available()

        intro = QLabel(
            "Generate blueprint PNGs and optional Minecraft worlds using the same "
            "pipeline as render_main.py. Unsaved editor changes are not included "
            "unless you save first."
        )
        intro.setWordWrap(True)

        types_group = QGroupBox()
        types_layout = create_nested_group_layout(types_group, "Render types")

        self._select_all = QCheckBox("All render types")
        self._select_all.setChecked(True)
        self._select_all.toggled.connect(self._on_select_all_toggled)
        types_layout.addWidget(self._select_all)

        for render_name, (label, _render_fn) in RENDER_REGISTRY.items():
            checkbox = QCheckBox(label)
            checkbox.setProperty("render_name", render_name)
            checkbox.setChecked(True)

            if render_name == constants.RENDER_WORLDGEN and not self._worldgen_available:
                checkbox.setChecked(False)
                checkbox.setEnabled(False)
                checkbox.setToolTip(
                    "Install worldgen dependencies (see docs/worldgen.md): "
                    'pip install -e ".[worldgen]"'
                )

            checkbox.toggled.connect(self._on_render_type_toggled)
            self._render_checks[render_name] = checkbox
            types_layout.addWidget(checkbox)

        self._output_label = QLabel()
        self._output_label.setWordWrap(True)

        self._generate_button = QPushButton("Generate Renders")
        self._generate_button.clicked.connect(self._on_generate_clicked)

        self._open_output_button = QPushButton("Open schematic output folder")
        self._open_output_button.clicked.connect(self.open_output_requested.emit)

        layout = QVBoxLayout(self)
        layout.addWidget(intro)
        layout.addWidget(types_group)
        layout.addWidget(self._output_label)
        layout.addWidget(self._generate_button)
        layout.addWidget(self._open_output_button)
        layout.addStretch(1)

    def set_output_hint(self, output_folder: str | None) -> None:
        if not output_folder:
            self._output_label.setText("Output folder is set in structure.yaml (output_folder).")
            return

        self._output_label.setText(
            f"Schematics: output/schematics/{output_folder}/\n"
            f"Worlds: output/worlds/{output_folder}/"
        )

    def set_busy(self, busy: bool) -> None:
        self._generate_button.setEnabled(not busy)
        self._select_all.setEnabled(not busy)

        for checkbox in self._render_checks.values():
            if busy or (
                checkbox.property("render_name") == constants.RENDER_WORLDGEN
                and not self._worldgen_available
            ):
                checkbox.setEnabled(False)
            else:
                checkbox.setEnabled(True)

    def selected_renders(self) -> list[str]:
        return resolve_selected_renders(
            select_all=self._select_all.isChecked(),
            checked_by_name={
                render_name: checkbox.isChecked()
                for render_name, checkbox in self._render_checks.items()
            },
        )

    def _on_select_all_toggled(self, checked: bool) -> None:
        for checkbox in self._render_checks.values():
            if checkbox.isEnabled():
                checkbox.blockSignals(True)
                checkbox.setChecked(checked)
                checkbox.blockSignals(False)

    def _on_render_type_toggled(self, _checked: bool) -> None:
        enabled_boxes = [cb for cb in self._render_checks.values() if cb.isEnabled()]

        if not enabled_boxes:
            return

        all_checked = all(cb.isChecked() for cb in enabled_boxes)
        any_checked = any(cb.isChecked() for cb in enabled_boxes)

        self._select_all.blockSignals(True)
        self._select_all.setChecked(all_checked)
        self._select_all.setTristate(False)
        self._select_all.blockSignals(False)

        self._generate_button.setEnabled(any_checked or self._select_all.isChecked())

    def _on_generate_clicked(self) -> None:
        try:
            renders = self.selected_renders()
        except ValueError as exc:
            QMessageBox.warning(self, "Render", str(exc))
            return

        self.generate_requested.emit(renders)
