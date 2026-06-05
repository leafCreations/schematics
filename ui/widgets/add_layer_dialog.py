"""Dialog for adding a structure layer (Y level and group)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QLabel,
    QLineEdit,
    QSpinBox,
)

from ui.dialog_layout import (
    DIALOG_FIELD_MIN_WIDTH,
    apply_dialog_field_style,
    create_dialog_button_box,
    create_dialog_form_layout,
    create_dialog_shell,
)

NEW_GROUP_CHOICE = "— New group —"


class AddLayerDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        y_default: int,
        y_min: int,
        y_max: int,
        groups: list[str],
        initial_group: str | None = None,
        initial_description: str = "",
        editing: bool = False,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit layer" if editing else "Add layer")

        if editing:
            hint_text = (
                "Update the layer Y level, description, and group assignment. "
                "Changes are saved when you click OK."
            )
        else:
            hint_text = (
                "Y level is the worldgen index (exported Y = worldgen_base_y + index). "
                "Description is optional and shown in the layer list; "
                "when empty, the group name is used. "
                "The new layer is saved when you click OK."
            )

        hint = QLabel(hint_text)
        hint.setWordWrap(True)

        self._y_spin = QSpinBox()
        self._y_spin.setRange(y_min, y_max)
        self._y_spin.setValue(y_default)
        self._y_spin.setToolTip("Minecraft Y offset for this layer; may be negative.")
        apply_dialog_field_style(self._y_spin, min_width=120)

        self._group_combo = QComboBox()
        apply_dialog_field_style(self._group_combo, min_width=DIALOG_FIELD_MIN_WIDTH)

        for group in groups:
            self._group_combo.addItem(group)

        self._group_combo.addItem(NEW_GROUP_CHOICE)

        self._new_group = QLineEdit()
        self._new_group.setPlaceholderText("New group name")
        self._new_group.setToolTip("Name for a new layer group.")
        apply_dialog_field_style(self._new_group, min_width=DIALOG_FIELD_MIN_WIDTH)

        self._description = QLineEdit()
        self._description.setText(initial_description)
        self._description.setPlaceholderText("Optional layer label")
        self._description.setToolTip("Shown in the layer list. Leave empty to use the group name.")
        apply_dialog_field_style(self._description, min_width=DIALOG_FIELD_MIN_WIDTH)

        if initial_group and initial_group in groups:
            self._group_combo.setCurrentText(initial_group)
        elif not groups:
            self._group_combo.setCurrentText(NEW_GROUP_CHOICE)

        form = create_dialog_form_layout()
        form.addRow("Y level", self._y_spin)
        form.addRow("Description", self._description)
        form.addRow("Group", self._group_combo)
        form.addRow("New group name", self._new_group)
        self._form = form

        self._group_combo.currentTextChanged.connect(self._sync_new_group_visible)
        self._sync_new_group_visible(self._group_combo.currentText())

        layout = create_dialog_shell(self)
        layout.addWidget(hint)
        layout.addLayout(form)
        layout.addSpacing(4)
        layout.addWidget(create_dialog_button_box(self))

    def _sync_new_group_visible(self, choice: str) -> None:
        is_new = choice == NEW_GROUP_CHOICE
        self._new_group.setVisible(is_new)

        label = self._form.labelForField(self._new_group)

        if label is not None:
            label.setVisible(is_new)

        if is_new:
            self._new_group.setFocus()

    def y_level(self) -> int:
        return self._y_spin.value()

    def description(self) -> str:
        return self._description.text().strip()

    def group_name(self) -> str:
        if self._group_combo.currentText() == NEW_GROUP_CHOICE:
            return self._new_group.text().strip()

        return self._group_combo.currentText().strip()

    def is_new_group(self) -> bool:
        return self._group_combo.currentText() == NEW_GROUP_CHOICE
