"""Single-line text prompt dialog."""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QLineEdit

from ui.dialog_layout import (
    DIALOG_FIELD_MIN_WIDTH,
    apply_dialog_field_style,
    create_dialog_button_box,
    create_dialog_form_layout,
    create_dialog_shell,
)


class InputTextDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        title: str,
        field_label: str,
        initial: str = "",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)

        self._line = QLineEdit()
        self._line.setText(initial)
        apply_dialog_field_style(self._line, min_width=DIALOG_FIELD_MIN_WIDTH)

        form = create_dialog_form_layout()
        form.addRow(field_label, self._line)

        layout = create_dialog_shell(self)
        layout.addLayout(form)
        layout.addSpacing(4)
        layout.addWidget(create_dialog_button_box(self))

        self._line.setFocus()

    def text(self) -> str:
        return self._line.text().strip()
