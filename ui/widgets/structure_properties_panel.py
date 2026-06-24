"""Edit structure identity fields stored in ``structure.yaml``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QRegularExpression, Signal
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from helpers.grid import resolve_site_dimensions
from helpers.minecraft_versions import (
    SUPPORTED_MINECRAFT_VERSIONS,
    compare_minecraft_versions,
    normalize_minecraft_version,
)
from helpers.structure_metadata import (
    apply_structure_identity,
    apply_structure_version,
    derive_output_folder,
    identity_from_structure_path,
    normalize_structure_slug,
    read_structure_identity,
    resolve_structure_version,
)


class StructurePropertiesPanel(QWidget):
    properties_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._structure_path: Path | None = None
        self._block_signals = False
        self._stage_value = 1
        self._loaded_version = normalize_minecraft_version(None)

        self._structure_edit = QLineEdit()
        self._structure_edit.setPlaceholderText("e.g. residence")
        self._structure_edit.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^[a-z]*$"))
        )
        self._structure_edit.setToolTip("Lowercase letters a-z only (e.g. residence).")
        self._structure_edit.textChanged.connect(self._on_structure_text_changed)

        self._site_width_spin = QSpinBox()
        self._site_width_spin.setRange(1, 512)
        self._site_width_spin.valueChanged.connect(self._on_field_changed)

        self._site_depth_spin = QSpinBox()
        self._site_depth_spin.setRange(1, 512)
        self._site_depth_spin.valueChanged.connect(self._on_field_changed)

        self._dimension_combo = QComboBox()
        self._dimension_combo.addItem("Overworld", "overworld")
        self._dimension_combo.addItem("Nether", "nether")
        self._dimension_combo.addItem("End", "end")
        self._dimension_combo.currentIndexChanged.connect(self._on_field_changed)

        self._version_combo = QComboBox()
        for supported_version in SUPPORTED_MINECRAFT_VERSIONS:
            self._version_combo.addItem(supported_version, supported_version)
        self._version_combo.currentIndexChanged.connect(self._on_version_changed)

        self._path_warning = QLabel("")
        self._path_warning.setWordWrap(True)
        self._path_warning.setStyleSheet("color: #a63;")

        form = QFormLayout()
        form.addRow("Structure name", self._structure_edit)
        form.addRow("Site width", self._site_width_spin)
        form.addRow("Site depth", self._site_depth_spin)
        form.addRow("Dimension", self._dimension_combo)
        form.addRow("Minecraft version", self._version_combo)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(form)
        layout.addWidget(self._path_warning)

    def set_structure_path(self, path: Path) -> None:
        self._structure_path = path
        self._refresh_path_warning()

    def load_from_metadata(self, metadata: dict[str, Any]) -> None:
        structure, stage, _name, _output_folder = read_structure_identity(metadata)
        site_width, site_depth = resolve_site_dimensions(metadata.get("grid", {}))
        dimension = str(metadata.get("dimension", "overworld")).strip().lower()
        version = resolve_structure_version(metadata)

        if dimension not in {"overworld", "nether", "end"}:
            dimension = "overworld"

        self._block_signals = True
        self._stage_value = int(stage)
        self._loaded_version = version
        self._structure_edit.setText(structure)
        self._site_width_spin.setValue(site_width)
        self._site_depth_spin.setValue(site_depth)
        index = self._dimension_combo.findData(dimension)
        self._dimension_combo.setCurrentIndex(max(0, index))
        version_index = self._version_combo.findData(version)
        self._version_combo.setCurrentIndex(max(0, version_index))
        self._block_signals = False
        self._refresh_path_warning()

    def apply_to_metadata(self, metadata: dict[str, Any]) -> None:
        apply_structure_identity(
            metadata,
            structure=self._structure_edit.text(),
            stage=int(metadata.get("stage", self._stage_value)),
        )
        grid = dict(metadata.get("grid", {}))
        grid["site_width"] = int(self._site_width_spin.value())
        grid["site_depth"] = int(self._site_depth_spin.value())
        metadata["grid"] = grid
        metadata["dimension"] = str(self._dimension_combo.currentData())
        apply_structure_version(
            metadata,
            version=str(self._version_combo.currentData()),
        )

    def current_output_folder(self) -> str:
        return derive_output_folder(self._structure_edit.text(), self._stage_value)

    def current_minecraft_version(self) -> str:
        return normalize_minecraft_version(self._version_combo.currentData())

    def set_site_grid_size(self, site_width: int, site_depth: int) -> None:
        self._block_signals = True
        self._site_width_spin.setValue(max(1, int(site_width)))
        self._site_depth_spin.setValue(max(1, int(site_depth)))
        self._block_signals = False

    def _on_structure_text_changed(self, text: str) -> None:
        slug = normalize_structure_slug(text)

        if text != slug:
            cursor = self._structure_edit.cursorPosition()
            self._block_signals = True
            self._structure_edit.setText(slug)
            self._structure_edit.setCursorPosition(min(cursor, len(slug)))
            self._block_signals = False

        self._on_field_changed()

    def _on_version_changed(self) -> None:
        if self._block_signals:
            return

        new_version = normalize_minecraft_version(self._version_combo.currentData())

        if compare_minecraft_versions(new_version, self._loaded_version) < 0:
            reply = QMessageBox.warning(
                self,
                "Downgrade Minecraft version",
                "Lowering the structure version may hide palette blocks that remain placed "
                "in layers. Those blocks may not render correctly in exports or worldgen "
                "for the older version.\n\nContinue?",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )

            if reply == QMessageBox.StandardButton.Cancel:
                self._block_signals = True
                revert_index = self._version_combo.findData(self._loaded_version)
                self._version_combo.setCurrentIndex(max(0, revert_index))
                self._block_signals = False
                return

        self._loaded_version = new_version
        self._on_field_changed()

    def _on_field_changed(self) -> None:
        if self._block_signals:
            return
        self._refresh_path_warning()
        self.properties_changed.emit()

    def _refresh_path_warning(self) -> None:
        if self._structure_path is None:
            self._path_warning.setText("")
            return

        on_disk = identity_from_structure_path(self._structure_path)
        if on_disk is None:
            self._path_warning.setText("")
            return

        disk_structure, disk_stage = on_disk
        edit_structure = self._structure_edit.text().strip().lower()
        edit_stage = self._stage_value

        if edit_structure == disk_structure and edit_stage == disk_stage:
            self._path_warning.setText("")
            return

        self._path_warning.setText(
            f"Note: file is under structures/{disk_structure}/stage{disk_stage}/. "
            "Changing structure or stage here updates YAML only — move the folder "
            "manually if you need a new path."
        )
