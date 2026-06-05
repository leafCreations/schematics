"""Dialog for renaming a layer group."""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QLabel, QLineEdit

from ui.dialog_layout import (
    DIALOG_FIELD_MIN_WIDTH,
    apply_dialog_field_style,
    create_dialog_button_box,
    create_dialog_form_layout,
    create_dialog_shell,
)


class EditGroupDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        initial_name: str,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit group")

        hint = QLabel(
            "Renames this group on all assigned layers. Changes are saved when you click OK."
        )
        hint.setWordWrap(True)

        self._name_edit = QLineEdit()
        self._name_edit.setText(initial_name)
        self._name_edit.setToolTip("Layer group name.")
        apply_dialog_field_style(self._name_edit, min_width=DIALOG_FIELD_MIN_WIDTH)

        form = create_dialog_form_layout()
        form.addRow("Group name", self._name_edit)

        layout = create_dialog_shell(self)
        layout.addWidget(hint)
        layout.addLayout(form)
        layout.addSpacing(4)
        layout.addWidget(create_dialog_button_box(self))

        self._name_edit.selectAll()
        self._name_edit.setFocus()

    def group_name(self) -> str:
        return self._name_edit.text().strip()
