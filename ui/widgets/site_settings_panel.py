from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from helpers.grid import resolve_site_dimensions
from helpers.grid_placement import (
    PLACEMENT_LABELS,
    PLACEMENTS,
    Placement,
    apply_placement_to_grid,
    infer_placement,
    minimum_site_dimensions,
    offsets_for_placement,
    structure_dimensions_from_layers,
    structure_fits_site,
)
from ui.widgets.panel_header import create_nested_group_layout

_PLACEMENT_GRID = (
    ("top_left", 0, 0),
    ("top_center", 0, 1),
    ("top_right", 0, 2),
    ("middle_left", 1, 0),
    ("center", 1, 1),
    ("middle_right", 1, 2),
    ("bottom_left", 2, 0),
    ("bottom_center", 2, 1),
    ("bottom_right", 2, 2),
)


class SiteSettingsPanel(QWidget):
    settings_changed = Signal()
    block_tooltips_changed = Signal(bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._layers: list[dict] = []
        self._placement_buttons: dict[Placement, QPushButton] = {}
        self._block_signals = False

        self._site_width = QSpinBox()
        self._site_width.setRange(1, 512)
        self._site_width.valueChanged.connect(self._on_site_dimensions_changed)

        self._site_depth = QSpinBox()
        self._site_depth.setRange(1, 512)
        self._site_depth.valueChanged.connect(self._on_site_dimensions_changed)

        self._offset_label = QLabel("—")
        self._footprint_label = QLabel("—")

        self._block_tooltips = QCheckBox("Show block tooltips on hover")
        self._block_tooltips.setToolTip(
            "When enabled, hovering a site cell shows its block token (e.g. GRASS, DIRT_PATH)."
        )
        self._block_tooltips.toggled.connect(self.block_tooltips_changed.emit)

        placement_group = QGroupBox()
        placement_layout = create_nested_group_layout(placement_group, "Placement on site")
        placement_grid = QGridLayout()
        placement_layout.addLayout(placement_grid)
        placement_layout.setSpacing(4)

        for placement, row, col in _PLACEMENT_GRID:
            button = QPushButton(placement.replace("_", " ").title())
            button.setToolTip(PLACEMENT_LABELS[placement])
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked, value=placement: self._on_placement_clicked(value)
            )
            self._placement_buttons[placement] = button
            placement_grid.addWidget(button, row, col)

        site_group = QGroupBox()
        site_layout = create_nested_group_layout(site_group, "Site grid")
        site_form = QFormLayout()
        site_layout.addLayout(site_form)
        site_form.addRow("Site width (x)", self._site_width)
        site_form.addRow("Site depth (z)", self._site_depth)
        site_form.addRow("Structure", self._footprint_label)
        site_form.addRow("Offset (x, z)", self._offset_label)
        site_form.addRow(self._block_tooltips)

        layout = QVBoxLayout(self)
        layout.addWidget(site_group)
        layout.addWidget(placement_group)
        layout.addStretch(1)

    def load_from_metadata(self, metadata: dict, layers: list[dict]) -> None:
        self._layers = layers
        grid = metadata.get("grid", {})
        structure_width, structure_depth = structure_dimensions_from_layers(layers)
        site_width, site_depth = resolve_site_dimensions(grid)
        placement = grid.get("placement")

        if placement in PLACEMENTS:
            anchor: Placement = placement  # type: ignore[assignment]
        else:
            anchor = infer_placement(
                int(grid.get("offset_x", 0)),
                int(grid.get("offset_z", 0)),
                site_width,
                site_depth,
                structure_width,
                structure_depth,
            )

        min_width, min_depth = minimum_site_dimensions(structure_width, structure_depth)

        self._block_signals = True
        self._site_width.setMinimum(min_width)
        self._site_depth.setMinimum(min_depth)
        self._site_width.setValue(max(site_width, min_width))
        self._site_depth.setValue(max(site_depth, min_depth))
        self._set_placement_selection(anchor)
        self._block_signals = False
        self._refresh_labels()

    def apply_to_metadata(self, metadata: dict) -> bool:
        """Write site grid settings into metadata. Returns False if structure does not fit."""
        structure_width, structure_depth = structure_dimensions_from_layers(self._layers)
        site_width = self._site_width.value()
        site_depth = self._site_depth.value()
        placement = self._selected_placement()

        try:
            metadata["grid"] = apply_placement_to_grid(
                metadata.get("grid", {}),
                placement=placement,
                site_width=site_width,
                site_depth=site_depth,
                structure_width=structure_width,
                structure_depth=structure_depth,
            )
        except ValueError:
            return False

        return True

    def selected_placement(self) -> Placement:
        return self._selected_placement()

    def site_width(self) -> int:
        return self._site_width.value()

    def site_depth(self) -> int:
        return self._site_depth.value()

    def sync_offsets_from_grid(self, metadata: dict) -> None:
        """Refresh placement buttons and offset label after a nudge (grid already updated)."""
        grid = metadata.get("grid", {})
        structure_width, structure_depth = structure_dimensions_from_layers(self._layers)
        site_width, site_depth = resolve_site_dimensions(grid)
        placement = infer_placement(
            int(grid.get("offset_x", 0)),
            int(grid.get("offset_z", 0)),
            site_width,
            site_depth,
            structure_width,
            structure_depth,
        )

        self._block_signals = True
        self._set_placement_selection(placement)
        self._block_signals = False
        self._refresh_labels_from_grid(grid)

    def _refresh_labels_from_grid(self, grid: dict) -> None:
        structure_width, structure_depth = structure_dimensions_from_layers(self._layers)
        site_width, site_depth = resolve_site_dimensions(grid)
        self._offset_label.setText(f"{grid.get('offset_x', 0)}, {grid.get('offset_z', 0)}")
        self._footprint_label.setText(
            f"{structure_width} × {structure_depth} on {site_width} × {site_depth}",
        )

    def _selected_placement(self) -> Placement:
        for placement, button in self._placement_buttons.items():
            if button.isChecked():
                return placement

        return "center"

    def _set_placement_selection(self, placement: Placement) -> None:
        for name, button in self._placement_buttons.items():
            button.setChecked(name == placement)

    def _on_site_dimensions_changed(self, _value: int) -> None:
        if self._block_signals:
            return

        self._emit_settings_changed()

    def _on_placement_clicked(self, placement: Placement) -> None:
        if self._block_signals:
            return

        self._set_placement_selection(placement)
        self._emit_settings_changed()

    def _emit_settings_changed(self) -> None:
        structure_width, structure_depth = structure_dimensions_from_layers(self._layers)
        site_width = self._site_width.value()
        site_depth = self._site_depth.value()
        placement = self._selected_placement()

        if not structure_fits_site(
            site_width,
            site_depth,
            structure_width,
            structure_depth,
            *offsets_for_placement(
                placement,
                site_width,
                site_depth,
                structure_width,
                structure_depth,
            ),
        ):
            self._offset_label.setText("Structure does not fit")
            self.settings_changed.emit()
            return

        self._refresh_labels()
        self.settings_changed.emit()

    def _refresh_labels(self) -> None:
        structure_width, structure_depth = structure_dimensions_from_layers(self._layers)
        site_width = self._site_width.value()
        site_depth = self._site_depth.value()
        placement = self._selected_placement()

        try:
            offset_x, offset_z = offsets_for_placement(
                placement,
                site_width,
                site_depth,
                structure_width,
                structure_depth,
            )
        except ValueError:
            self._offset_label.setText("Structure does not fit")
        else:
            self._offset_label.setText(f"{offset_x}, {offset_z}")

        self._footprint_label.setText(
            f"{structure_width} × {structure_depth} on {site_width} × {site_depth}",
        )

    def set_block_tooltips_enabled(self, enabled: bool) -> None:
        self._block_tooltips.blockSignals(True)
        self._block_tooltips.setChecked(enabled)
        self._block_tooltips.blockSignals(False)

    def block_tooltips_enabled(self) -> bool:
        return self._block_tooltips.isChecked()
