"""Dialog for creating a new structure stage package."""

from __future__ import annotations

import re

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QComboBox, QDialog, QLabel, QLineEdit, QSpinBox

from helpers.structure_metadata import derive_output_folder, normalize_structure_slug
from ui.dialog_layout import (
    DIALOG_FIELD_MIN_WIDTH,
    apply_dialog_field_style,
    create_dialog_button_box,
    create_dialog_form_layout,
    create_dialog_shell,
)

_LOWERCASE_SLUG_RE = re.compile(r"[^a-z]+")


def _normalize_structure_input(value: str) -> str:
    return _LOWERCASE_SLUG_RE.sub("", value.strip().lower())


class NewStructureDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        structure: str = "",
        stage: int = 1,
        site_width: int = 15,
        site_depth: int = 15,
        structure_width: int = 9,
        structure_depth: int = 9,
        dimension: str = "overworld",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Structure")

        self._structure = QLineEdit()
        self._structure.setPlaceholderText("e.g. residence")
        self._structure.setValidator(QRegularExpressionValidator(QRegularExpression(r"^[a-z]*$")))
        apply_dialog_field_style(self._structure, min_width=DIALOG_FIELD_MIN_WIDTH)

        self._stage = QSpinBox()
        self._stage.setRange(1, 99)
        self._stage.setValue(max(1, int(stage)))
        apply_dialog_field_style(self._stage, min_width=120)

        self._site_width = QSpinBox()
        self._site_width.setRange(1, 512)
        self._site_width.setValue(max(1, int(site_width)))
        apply_dialog_field_style(self._site_width, min_width=120)

        self._site_depth = QSpinBox()
        self._site_depth.setRange(1, 512)
        self._site_depth.setValue(max(1, int(site_depth)))
        apply_dialog_field_style(self._site_depth, min_width=120)

        self._structure_width = QSpinBox()
        self._structure_width.setRange(1, 512)
        self._structure_width.setValue(max(1, int(structure_width)))
        apply_dialog_field_style(self._structure_width, min_width=120)

        self._structure_depth = QSpinBox()
        self._structure_depth.setRange(1, 512)
        self._structure_depth.setValue(max(1, int(structure_depth)))
        apply_dialog_field_style(self._structure_depth, min_width=120)

        self._dimension = QComboBox()
        self._dimension.addItem("Overworld", "overworld")
        self._dimension.addItem("Nether", "nether")
        self._dimension.addItem("End", "end")
        self._dimension.setCurrentIndex(max(0, self._dimension.findData(str(dimension).lower())))
        apply_dialog_field_style(self._dimension, min_width=DIALOG_FIELD_MIN_WIDTH)

        self._name_label = QLabel("")
        self._name_label.setWordWrap(True)

        self._output_folder_label = QLabel("")
        self._output_folder_label.setWordWrap(True)

        self._hint = QLabel(
            "Creates structures/{structure}/stage{N}/stage.yaml and layers/layer_00.yaml."
        )
        self._hint.setWordWrap(True)

        form = create_dialog_form_layout()
        form.addRow("Structure", self._structure)
        form.addRow("Stage", self._stage)
        form.addRow("Site width", self._site_width)
        form.addRow("Site depth", self._site_depth)
        form.addRow("Structure width", self._structure_width)
        form.addRow("Structure depth", self._structure_depth)
        form.addRow("Dimension", self._dimension)
        form.addRow("Name", self._name_label)
        form.addRow("Output folder", self._output_folder_label)

        layout = create_dialog_shell(self)
        layout.addWidget(self._hint)
        layout.addLayout(form)
        layout.addSpacing(4)
        layout.addWidget(create_dialog_button_box(self))

        self._structure.setText(_normalize_structure_input(structure))
        self._structure.textChanged.connect(self._on_identity_changed)
        self._stage.valueChanged.connect(self._on_identity_changed)
        self._on_identity_changed()
        self._structure.setFocus()

    def _on_identity_changed(self) -> None:
        slug = _normalize_structure_input(self._structure.text())

        if slug != self._structure.text():
            cursor = self._structure.cursorPosition()
            self._structure.blockSignals(True)
            self._structure.setText(slug)
            self._structure.setCursorPosition(min(cursor, len(slug)))
            self._structure.blockSignals(False)

        stage = self._stage.value()
        identity_slug = normalize_structure_slug(slug)
        self._name_label.setText(f"{identity_slug.title()} Stage {stage}")
        self._output_folder_label.setText(derive_output_folder(identity_slug, stage))

    def values(self) -> tuple[str, int, int, int, int, int, str]:
        return (
            normalize_structure_slug(self._structure.text()),
            int(self._stage.value()),
            int(self._site_width.value()),
            int(self._site_depth.value()),
            int(self._structure_width.value()),
            int(self._structure_depth.value()),
            str(self._dimension.currentData()),
        )
