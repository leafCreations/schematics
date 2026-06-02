from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from helpers.block_picker import PickerEntry, cell_token, format_entry_label
from helpers.structure_tokens import parse_structure_token

_DEFAULT_VARIANT_LABEL = "(default)"


class PropertiesPanel(QWidget):
    brush_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._mode_label = QLabel("Select a palette block to paint, or enable Eraser.")
        self._title = QLabel("")
        self._cell_preview = QLabel("")
        self._material_combo = QComboBox()
        self._direction_combo = QComboBox()
        self._variant_combo = QComboBox()
        self._active_entry: PickerEntry | None = None

        self._material_combo.currentTextChanged.connect(self._on_brush_option_changed)
        self._direction_combo.currentTextChanged.connect(self._on_brush_option_changed)
        self._variant_combo.currentTextChanged.connect(self._on_brush_option_changed)

        for direction in ("north", "south", "east", "west"):
            self._direction_combo.addItem(direction)

        picker_group = QGroupBox("Paint brush")
        picker_form = QFormLayout(picker_group)
        picker_form.addRow("Label", self._title)
        picker_form.addRow("Material", self._material_combo)
        picker_form.addRow("Direction", self._direction_combo)
        picker_form.addRow("Variant", self._variant_combo)
        picker_form.addRow("Cell token", self._cell_preview)

        cell_group = QGroupBox("Grid cell")
        cell_layout = QVBoxLayout(cell_group)
        self._cell_info = QLabel("No cell selected.")
        cell_layout.addWidget(self._cell_info)

        layout = QVBoxLayout(self)
        layout.addWidget(self._mode_label)
        layout.addWidget(picker_group)
        layout.addWidget(cell_group)
        layout.addStretch(1)

        self._picker_group = picker_group
        self._cell_group = cell_group
        self._reset_picker_fields()

    def active_entry(self) -> PickerEntry | None:
        return self._active_entry

    def build_placement_token(self) -> str | None:
        entry = self._active_entry

        if entry is None:
            return None

        material = self._selected_material()
        direction = self._selected_direction()
        variant = self._selected_variant()

        return cell_token(entry, material, direction=direction, variant=variant)

    def show_picker_entry(self, entry: PickerEntry) -> None:
        self._active_entry = entry
        self._mode_label.setText("Paint brush active — left-click grid cells to place.")
        self._picker_group.setEnabled(True)
        self._title.setText(entry.label)

        self._material_combo.blockSignals(True)
        self._material_combo.clear()

        if entry.requires_material:
            self._material_combo.setEnabled(True)
            self._material_combo.addItems(entry.materials)

            if entry.material_default and entry.material_default in entry.materials:
                self._material_combo.setCurrentText(entry.material_default)
            elif entry.materials:
                self._material_combo.setCurrentIndex(0)
        else:
            self._material_combo.setEnabled(False)
            self._material_combo.addItem("—")

        self._material_combo.blockSignals(False)

        self._direction_combo.setEnabled(entry.requires_direction)

        if entry.requires_direction:
            self._direction_combo.setCurrentText("north")

        self._variant_combo.blockSignals(True)
        self._variant_combo.clear()
        self._variant_combo.setEnabled(bool(entry.variants))

        if entry.variants:
            self._variant_combo.addItem(_DEFAULT_VARIANT_LABEL)
            self._variant_combo.addItems(entry.variants)
        else:
            self._variant_combo.addItem("—")

        self._variant_combo.blockSignals(False)
        self._refresh_entry_preview()
        self.brush_changed.emit()

    def clear_picker_entry(self) -> None:
        self._reset_picker_fields()
        self.brush_changed.emit()

    def show_grid_cell(self, row: int, col: int, raw_token: str) -> None:
        parsed = parse_structure_token(raw_token)
        lines = [f"Position: row {row}, col {col}", f"Raw: {raw_token or '.'}"]

        if parsed is not None:
            lines.extend(
                [
                    f"Token: {parsed.token}",
                    f"Material: {parsed.material or '—'}",
                    f"Direction: {parsed.direction or '—'}",
                    f"Variant: {parsed.variant or '—'}",
                ]
            )

        self._cell_info.setText("\n".join(lines))
        self._cell_group.setEnabled(True)

    def clear_grid_cell(self) -> None:
        self._cell_info.setText("No cell selected.")
        self._cell_group.setEnabled(False)

    def _on_brush_option_changed(self, _value: str) -> None:
        self._refresh_entry_preview()
        self.brush_changed.emit()

    def _selected_material(self) -> str | None:
        if self._active_entry is None or not self._active_entry.requires_material:
            return None

        material = self._material_combo.currentText()

        if material == "—":
            return self._active_entry.material_default

        return material or self._active_entry.material_default

    def _selected_direction(self) -> str | None:
        if self._active_entry is None or not self._active_entry.requires_direction:
            return None

        return self._direction_combo.currentText()

    def _selected_variant(self) -> str | None:
        if self._active_entry is None or not self._active_entry.variants:
            return None

        variant = self._variant_combo.currentText()

        if variant in {_DEFAULT_VARIANT_LABEL, "—"}:
            return None

        return variant

    def _refresh_entry_preview(self) -> None:
        token = self.build_placement_token()

        if token is None or self._active_entry is None:
            self._cell_preview.setText("—")
            return

        label = format_entry_label(self._active_entry, self._selected_material())
        self._cell_preview.setText(f"{token}\n({label})")

    def _reset_picker_fields(self) -> None:
        self._active_entry = None
        self._picker_group.setEnabled(False)
        self._cell_group.setEnabled(False)
        self._mode_label.setText("Select a palette block to paint, or enable Eraser.")
        self._title.setText("—")
        self._cell_preview.setText("—")
        self._cell_info.setText("No cell selected.")
