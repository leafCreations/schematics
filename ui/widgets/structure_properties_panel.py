"""Edit structure identity fields stored in ``structure.yaml``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QRegularExpression, Signal
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from helpers.structure_metadata import (
    apply_structure_identity,
    derive_output_folder,
    derive_structure_name,
    identity_from_structure_path,
    normalize_structure_slug,
    read_structure_identity,
)


class StructurePropertiesPanel(QWidget):
    properties_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._structure_path: Path | None = None
        self._block_signals = False

        self._structure_edit = QLineEdit()
        self._structure_edit.setPlaceholderText("e.g. residence")
        self._structure_edit.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^[a-z]*$"))
        )
        self._structure_edit.setToolTip("Lowercase letters a-z only (e.g. residence).")
        self._structure_edit.textChanged.connect(self._on_structure_text_changed)

        self._stage_spin = QSpinBox()
        self._stage_spin.setRange(1, 99)
        self._stage_spin.valueChanged.connect(self._on_field_changed)

        self._name_label = QLabel("—")
        self._name_label.setWordWrap(True)
        self._name_label.setToolTip("Derived from structure and stage (e.g. Residence Stage 1).")

        self._output_folder_label = QLabel("—")
        self._output_folder_label.setWordWrap(True)
        self._output_folder_label.setToolTip(
            "Derived automatically as stage{N}_{structure} for render/world output."
        )

        self._path_warning = QLabel("")
        self._path_warning.setWordWrap(True)
        self._path_warning.setStyleSheet("color: #a63;")

        form = QFormLayout()
        form.addRow("Structure", self._structure_edit)
        form.addRow("Stage", self._stage_spin)
        form.addRow("Name", self._name_label)
        form.addRow("Output folder", self._output_folder_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(form)
        layout.addWidget(self._path_warning)

    def set_structure_path(self, path: Path) -> None:
        self._structure_path = path
        self._refresh_path_warning()

    def load_from_metadata(self, metadata: dict[str, Any]) -> None:
        structure, stage, name, output_folder = read_structure_identity(metadata)
        self._block_signals = True
        self._structure_edit.setText(structure)
        self._stage_spin.setValue(stage)
        self._name_label.setText(name)
        self._output_folder_label.setText(output_folder)
        self._block_signals = False
        self._refresh_path_warning()

    def apply_to_metadata(self, metadata: dict[str, Any]) -> None:
        apply_structure_identity(
            metadata,
            structure=self._structure_edit.text(),
            stage=self._stage_spin.value(),
        )
        self._name_label.setText(metadata["name"])
        self._output_folder_label.setText(metadata["output_folder"])

    def current_output_folder(self) -> str:
        return derive_output_folder(self._structure_edit.text(), self._stage_spin.value())

    def _on_structure_text_changed(self, text: str) -> None:
        slug = normalize_structure_slug(text)

        if text != slug:
            cursor = self._structure_edit.cursorPosition()
            self._block_signals = True
            self._structure_edit.setText(slug)
            self._structure_edit.setCursorPosition(min(cursor, len(slug)))
            self._block_signals = False

        self._on_field_changed()

    def _on_field_changed(self) -> None:
        if self._block_signals:
            return

        structure = self._structure_edit.text()
        stage = self._stage_spin.value()
        self._name_label.setText(derive_structure_name(structure, stage))
        self._output_folder_label.setText(derive_output_folder(structure, stage))
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
        edit_stage = self._stage_spin.value()

        if edit_structure == disk_structure and edit_stage == disk_stage:
            self._path_warning.setText("")
            return

        self._path_warning.setText(
            f"Note: file is under structures/{disk_structure}/stage{disk_stage}/. "
            "Changing structure or stage here updates YAML only — move the folder "
            "manually if you need a new path."
        )
