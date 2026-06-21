from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from helpers.block_picker import PickerEntry, cell_token
from helpers.grid_labels import grid_axis_position, grid_axis_selection_range
from helpers.lantern_placement import HANGING_STATE, explicit_hanging
from helpers.structure_tokens import BlockStates, parse_structure_token
from helpers.trapdoor_state import OPEN_STATE, explicit_open
from ui.texture_cache import DEFAULT_ICON_SIZE, GridTextureCache
from ui.widgets.panel_header import create_nested_group_layout

_DEFAULT_VARIANT_LABEL = "(default)"
_BRUSH_PREVIEW_ICON_SIZE = DEFAULT_ICON_SIZE


class PropertiesPanel(QWidget):
    brush_changed = Signal()
    brush_blockstate_changed = Signal()
    active_cell_changed = Signal(int, int)
    active_cell_cleared = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._title = QLabel("")
        self._brush_preview = QLabel()
        self._brush_preview.setFixedSize(
            _BRUSH_PREVIEW_ICON_SIZE,
            _BRUSH_PREVIEW_ICON_SIZE,
        )
        self._texture_cache: GridTextureCache | None = None
        self._material_combo = QComboBox()
        self._direction_combo = QComboBox()
        self._variant_combo = QComboBox()
        self._hanging_combo = QComboBox()
        self._open_combo = QComboBox()
        self._active_entry: PickerEntry | None = None
        self._selected_cell: tuple[int, int] | None = None

        self._material_combo.currentTextChanged.connect(self._on_brush_option_changed)
        self._direction_combo.currentTextChanged.connect(self._on_brush_option_changed)
        self._variant_combo.currentTextChanged.connect(self._on_brush_option_changed)
        self._hanging_combo.currentTextChanged.connect(self._on_blockstate_option_changed)
        self._open_combo.currentTextChanged.connect(self._on_blockstate_option_changed)

        for direction in ("north", "south", "east", "west"):
            self._direction_combo.addItem(direction)

        picker_group = QGroupBox()
        picker_layout = create_nested_group_layout(picker_group, "Selected Block")
        picker_form = QFormLayout()
        picker_layout.addLayout(picker_form)
        picker_form.addRow("Label", self._title)
        picker_form.addRow("Material", self._material_combo)
        picker_form.addRow("Direction", self._direction_combo)
        self._variant_label = QLabel("Variant")
        picker_form.addRow(self._variant_label, self._variant_combo)
        self._hanging_label = QLabel("Hanging")
        picker_form.addRow(self._hanging_label, self._hanging_combo)
        self._open_label = QLabel("Open")
        picker_form.addRow(self._open_label, self._open_combo)
        picker_form.addRow("Preview", self._brush_preview)

        cell_group = QGroupBox()
        cell_layout = create_nested_group_layout(cell_group, "Grid cell")
        self._cell_info = QLabel("No cell selected.")
        cell_layout.addWidget(self._cell_info)

        layout = QVBoxLayout(self)
        layout.addWidget(picker_group)
        layout.addWidget(cell_group)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        self._picker_group = picker_group
        self._cell_group = cell_group
        self._reset_picker_fields()

    def set_picker_group_visible(self, visible: bool) -> None:
        self._picker_group.setVisible(visible)

    def active_entry(self) -> PickerEntry | None:
        return self._active_entry

    def selected_trapdoor_open(self) -> bool:
        return self._open_combo.currentText().lower() == "true"

    def set_texture_cache(self, texture_cache: GridTextureCache | None) -> None:
        self._texture_cache = texture_cache

    def build_placement_token(self) -> str | None:
        entry = self._active_entry

        if entry is None:
            return None

        material = self._selected_material()
        direction = self._selected_direction()
        variant = self._selected_variant()
        states = self._selected_block_states()

        return cell_token(entry, material, direction=direction, variant=variant, states=states)

    def show_picker_entry(
        self,
        entry: PickerEntry,
        *,
        emit_brush: bool = True,
        brush_token: str | None = None,
    ) -> None:
        self._active_entry = entry
        self._picker_group.setEnabled(True)
        self._title.setText(entry.label)

        self._material_combo.blockSignals(True)
        self._direction_combo.blockSignals(True)
        self._variant_combo.blockSignals(True)
        self._hanging_combo.blockSignals(True)
        self._open_combo.blockSignals(True)
        try:
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

            self._direction_combo.setEnabled(entry.requires_direction)

            if entry.requires_direction:
                self._direction_combo.setCurrentText("north")

            self._variant_combo.clear()
            self._variant_combo.setEnabled(bool(entry.variants))

            if entry.behavior == "bed" and set(entry.variants) == {"head", "foot"}:
                self._variant_label.setText("Part")
                self._variant_combo.addItems(["head", "foot"])
                self._variant_combo.setCurrentText("head")
            elif entry.behavior == "door" and set(entry.variants) == {"lower", "upper"}:
                self._variant_label.setText("Half")
                self._variant_combo.addItems(["lower", "upper"])
                self._variant_combo.setCurrentText("lower")
            elif entry.behavior == "trapdoor" and set(entry.variants) == {"top"}:
                self._variant_label.setText("Half")
                self._variant_combo.addItem(_DEFAULT_VARIANT_LABEL)
                self._variant_combo.addItem("top")
            elif entry.variants:
                self._variant_label.setText("Variant")
                self._variant_combo.addItem(_DEFAULT_VARIANT_LABEL)
                self._variant_combo.addItems(entry.variants)
            else:
                self._variant_label.setText("Variant")
                self._variant_combo.addItem("—")

            self._hanging_combo.clear()

            if entry.behavior == "lantern":
                self._hanging_label.setVisible(True)
                self._hanging_combo.setVisible(True)
                self._hanging_combo.setEnabled(True)
                self._hanging_combo.addItems(["Auto", "Hanging", "Standing"])
                self._hanging_combo.setCurrentText("Auto")
            else:
                self._hanging_label.setVisible(False)
                self._hanging_combo.setVisible(False)
                self._hanging_combo.setEnabled(False)
                self._hanging_combo.addItem("—")

            self._open_combo.clear()

            if entry.behavior == "trapdoor":
                self._open_label.setVisible(True)
                self._open_combo.setVisible(True)
                self._open_combo.setEnabled(True)
                self._open_combo.addItems(["false", "true"])
                self._open_combo.setCurrentText("false")
            else:
                self._open_label.setVisible(False)
                self._open_combo.setVisible(False)
                self._open_combo.setEnabled(False)
                self._open_combo.addItem("—")
        finally:
            self._material_combo.blockSignals(False)
            self._direction_combo.blockSignals(False)
            self._variant_combo.blockSignals(False)
            self._hanging_combo.blockSignals(False)
            self._open_combo.blockSignals(False)

        if brush_token:
            self.sync_brush_from_cell(brush_token)
        else:
            self._refresh_entry_preview()

        if emit_brush:
            self.brush_changed.emit()

    def clear_picker_entry(self, *, emit_brush: bool = True) -> None:
        self._reset_picker_fields()

        if emit_brush:
            self.brush_changed.emit()

    def show_selection_summary(
        self,
        positions: list[tuple[int, int]],
        *,
        entry_label: str | None = None,
        sample_token: str | None = None,
    ) -> None:
        """Read-only grid-cell panel text for a multi-cell selector selection."""
        self._selected_cell = None
        lines = [
            f"Selected cells: {grid_axis_selection_range(positions)}",
            f"Count: {len(positions)}",
        ]

        if entry_label:
            lines.append(f"Block type: {entry_label}")

        if sample_token and sample_token != ".":
            parsed = parse_structure_token(sample_token)

            if parsed is not None:
                lines.extend(
                    [
                        f"Sample token: {parsed.token}",
                        f"Material: {parsed.material or '—'}",
                        f"Direction: {parsed.direction or '—'}",
                        f"Variant: {parsed.variant or '—'}",
                    ]
                )

        self._cell_info.setText("\n".join(lines))
        self._cell_group.setEnabled(True)
        self.active_cell_cleared.emit()

    def show_grid_cell(self, row: int, col: int, raw_token: str) -> None:
        self._selected_cell = (row, col)
        parsed = parse_structure_token(raw_token)
        lines = [f"Position: {grid_axis_position(row, col)}", f"Raw: {raw_token or '.'}"]

        if parsed is not None:
            lines.extend(
                [
                    f"Token: {parsed.token}",
                    f"Material: {parsed.material or '—'}",
                    f"Direction: {parsed.direction or '—'}",
                    f"Variant: {parsed.variant or '—'}",
                    f"Hanging: {self._format_hanging_display(parsed)}",
                    f"Open: {self._format_open_display(parsed)}",
                ]
            )

        self._cell_info.setText("\n".join(lines))
        self._cell_group.setEnabled(True)
        self.active_cell_changed.emit(row, col)

    def clear_grid_cell(self) -> None:
        self._selected_cell = None
        self._cell_info.setText("No cell selected.")
        self._cell_group.setEnabled(False)
        self.active_cell_cleared.emit()

    def selected_cell(self) -> tuple[int, int] | None:
        return self._selected_cell

    def sync_brush_from_cell(self, raw_token: str) -> None:
        """Load brush combos from a grid cell when it matches the active palette token."""
        if self._active_entry is None or raw_token == ".":
            return

        parsed = parse_structure_token(raw_token)

        if parsed is None:
            return

        if self._active_entry.is_catalog_block:
            if raw_token != self._active_entry.token:
                return
        elif parsed.token != self._active_entry.token:
            return

        self._material_combo.blockSignals(True)
        self._direction_combo.blockSignals(True)
        self._variant_combo.blockSignals(True)

        if parsed.material and self._material_combo.isEnabled():
            material_index = self._material_combo.findText(parsed.material)

            if material_index >= 0:
                self._material_combo.setCurrentIndex(material_index)

        if parsed.direction and self._direction_combo.isEnabled():
            direction_index = self._direction_combo.findText(parsed.direction)

            if direction_index >= 0:
                self._direction_combo.setCurrentIndex(direction_index)

        if parsed.variant and self._variant_combo.isEnabled():
            variant_index = self._variant_combo.findText(parsed.variant)

            if variant_index >= 0:
                self._variant_combo.setCurrentIndex(variant_index)

        self._material_combo.blockSignals(False)
        self._direction_combo.blockSignals(False)
        if self._active_entry is not None and self._active_entry.behavior == "lantern":
            self._hanging_combo.blockSignals(True)
            hanging = explicit_hanging(parsed)

            if hanging is None:
                self._hanging_combo.setCurrentText("Auto")
            elif hanging:
                self._hanging_combo.setCurrentText("Hanging")
            else:
                self._hanging_combo.setCurrentText("Standing")

            self._hanging_combo.blockSignals(False)

        if self._active_entry is not None and self._active_entry.behavior == "trapdoor":
            self._open_combo.blockSignals(True)
            open_state = explicit_open(parsed)

            if open_state:
                self._open_combo.setCurrentText("true")
            else:
                self._open_combo.setCurrentText("false")

            self._open_combo.blockSignals(False)

        self._variant_combo.blockSignals(False)
        self._refresh_entry_preview()

    def _on_brush_option_changed(self, _value: str) -> None:
        self._refresh_entry_preview()
        self.brush_changed.emit()

    def _on_blockstate_option_changed(self, _value: str) -> None:
        self._refresh_entry_preview()
        self.brush_changed.emit()
        self.brush_blockstate_changed.emit()

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
        if self._active_entry is None or not self._variant_combo.isEnabled():
            return None

        variant = self._variant_combo.currentText()

        if variant in {_DEFAULT_VARIANT_LABEL, "—"}:
            return None

        return variant

    def _selected_block_states(self) -> BlockStates:
        if self._active_entry is None:
            return ()

        if self._active_entry.behavior == "lantern":
            mode = self._hanging_combo.currentText()

            if mode == "Hanging":
                return ((HANGING_STATE, True),)

            if mode == "Standing":
                return ((HANGING_STATE, False),)

            return ()

        if self._active_entry.behavior == "trapdoor":
            open_value = self._open_combo.currentText().lower()

            if open_value == "true":
                return ((OPEN_STATE, True),)

            if open_value == "false":
                return ((OPEN_STATE, False),)

            return ()

        return ()

    @staticmethod
    def _format_hanging_display(parsed) -> str:
        hanging = explicit_hanging(parsed)

        if hanging is None:
            return "auto"

        return "true" if hanging else "false"

    @staticmethod
    def _format_open_display(parsed) -> str:
        open_state = explicit_open(parsed)

        if open_state is None:
            return "false"

        return "true" if open_state else "false"

    def _refresh_entry_preview(self) -> None:
        token = self.build_placement_token()

        if token is None or self._active_entry is None:
            self._brush_preview.clear()
            return

        self._refresh_brush_preview(token)

    def _refresh_brush_preview(self, token: str) -> None:
        if self._texture_cache is None:
            self._brush_preview.clear()
            return

        self._texture_cache.invalidate_token(token)
        icon = self._texture_cache.icon_for_cell(
            token,
            size=_BRUSH_PREVIEW_ICON_SIZE,
        )

        if icon is None:
            self._brush_preview.clear()
            return

        pixmap = icon.pixmap(QSize(_BRUSH_PREVIEW_ICON_SIZE, _BRUSH_PREVIEW_ICON_SIZE))
        scaled = pixmap.scaled(
            QSize(_BRUSH_PREVIEW_ICON_SIZE, _BRUSH_PREVIEW_ICON_SIZE),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        self._brush_preview.setPixmap(scaled)

    def _reset_picker_fields(self) -> None:
        self._active_entry = None
        self._picker_group.setEnabled(False)
        self._cell_group.setEnabled(False)
        self._hanging_label.setVisible(False)
        self._hanging_combo.setVisible(False)
        self._open_label.setVisible(False)
        self._open_combo.setVisible(False)
        self._title.setText("—")
        self._brush_preview.clear()
        self._cell_info.setText("No cell selected.")
