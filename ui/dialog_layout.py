"""Shared layout metrics and helpers for editor modal dialogs."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

DIALOG_MIN_WIDTH = 420
DIALOG_FIELD_HEIGHT = 32
DIALOG_FIELD_MIN_WIDTH = 260
DIALOG_MARGINS = 16
DIALOG_SPACING = 14
DIALOG_FORM_H_SPACING = 12
DIALOG_FORM_V_SPACING = 14


def apply_dialog_field_style(
    widget: QWidget,
    *,
    min_width: int | None = None,
) -> None:
    """Apply the standard dialog control height and horizontal growth."""
    if min_width is not None:
        widget.setMinimumWidth(min_width)

    widget.setFixedHeight(DIALOG_FIELD_HEIGHT)
    widget.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Fixed,
    )


def create_dialog_form_layout() -> QFormLayout:
    form = QFormLayout()
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
    form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    form.setHorizontalSpacing(DIALOG_FORM_H_SPACING)
    form.setVerticalSpacing(DIALOG_FORM_V_SPACING)
    return form


def create_dialog_shell(
    dialog: QDialog,
    *,
    min_width: int = DIALOG_MIN_WIDTH,
) -> QVBoxLayout:
    dialog.setMinimumWidth(min_width)

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(
        DIALOG_MARGINS,
        DIALOG_MARGINS,
        DIALOG_MARGINS,
        DIALOG_MARGINS,
    )
    layout.setSpacing(DIALOG_SPACING)
    return layout


def create_dialog_button_box(dialog: QDialog) -> QDialogButtonBox:
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        parent=dialog,
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    return buttons
