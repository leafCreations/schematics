"""Dialog for choosing the Minecraft worldgen template version."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QDialog, QLabel

from helpers.paths import DEFAULT_WORLGEN_VERSION
from ui.dialog_layout import (
    DIALOG_FIELD_MIN_WIDTH,
    apply_dialog_field_style,
    create_dialog_button_box,
    create_dialog_form_layout,
    create_dialog_shell,
)


class WorldgenVersionDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        versions: list[str],
        default_version: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Worldgen version")

        hint = QLabel(
            "Choose the Minecraft version for the world template copied during worldgen. "
            "Templates live under worldgen_templates/ (see docs/worldgen.md)."
        )
        hint.setWordWrap(True)

        self._version_combo = QComboBox()
        apply_dialog_field_style(self._version_combo, min_width=DIALOG_FIELD_MIN_WIDTH)
        for version in versions:
            self._version_combo.addItem(f"Minecraft Java {version}", version)

        preferred = default_version or DEFAULT_WORLGEN_VERSION
        preferred_index = self._version_combo.findData(preferred)
        if preferred_index >= 0:
            self._version_combo.setCurrentIndex(preferred_index)

        form = create_dialog_form_layout()
        form.addRow("Version", self._version_combo)

        layout = create_dialog_shell(self)
        layout.addWidget(hint)
        layout.addLayout(form)
        layout.addSpacing(4)
        layout.addWidget(create_dialog_button_box(self))

    def selected_version(self) -> str:
        return str(self._version_combo.currentData())
