"""Export and worldgen actions for the structure editor Render tab."""

from __future__ import annotations

import importlib.util

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

import helpers.constants as constants
from renderers.registry import PREVIEW_RENDER_REGISTRY
from ui.widgets.panel_header import PANEL_MARGINS


def worldgen_dependencies_available() -> bool:
    return importlib.util.find_spec("amulet") is not None


def export_renders_for_preview(preview_render: str) -> list[str]:
    """Map the in-app preview render key to a single CLI export render list."""
    if preview_render not in PREVIEW_RENDER_REGISTRY:
        raise ValueError(f"Unknown preview render: {preview_render!r}.")
    return [preview_render]


class RenderPanel(QWidget):
    export_render_requested = Signal(list)
    export_all_renders_requested = Signal()
    generate_world_requested = Signal()
    open_output_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._preview_render = constants.RENDER_TOP_VIEW
        self._worldgen_available = worldgen_dependencies_available()
        self._worldgen_template_available = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(*PANEL_MARGINS)
        layout.setSpacing(8)

        intro = QLabel(
            "Export blueprint PNGs to the structure output folder using the same "
            "pipeline as render_main.py. The preview dropdown selects which render "
            "type is exported. Unsaved editor changes are not included unless you save first."
        )
        intro.setWordWrap(True)

        self._output_label = QLabel()
        self._output_label.setWordWrap(True)

        self._export_button = QToolButton()
        self._export_button.setText("Export Render")
        self._export_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._export_button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self._export_button.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Fixed,
        )
        export_menu = QMenu(self._export_button)
        self._all_renders_action = export_menu.addAction("All Renders")
        self._export_button.setMenu(export_menu)
        self._export_button.clicked.connect(self._on_export_render_clicked)
        self._all_renders_action.triggered.connect(self.export_all_renders_requested.emit)

        self._generate_world_button = QPushButton("Generate World")
        self._generate_world_button.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Fixed,
        )
        self._generate_world_button.clicked.connect(self.generate_world_requested.emit)
        if not self._worldgen_available:
            self._generate_world_button.setEnabled(False)
            self._generate_world_button.setToolTip(
                'Install worldgen dependencies (see docs/worldgen.md): pip install -e ".[worldgen]"'
            )

        self._open_output_button = QPushButton("Open Output Folder")
        self._open_output_button.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Fixed,
        )
        self._open_output_button.clicked.connect(self.open_output_requested.emit)

        actions_row = QWidget()
        actions_layout = QHBoxLayout(actions_row)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)
        actions_layout.addWidget(self._export_button)
        actions_layout.addWidget(self._generate_world_button)
        actions_layout.addWidget(self._open_output_button)
        actions_layout.addStretch(1)

        layout.addWidget(intro)
        layout.addWidget(self._output_label)
        layout.addWidget(actions_row)

    def set_preview_render(self, render_name: str) -> None:
        self._preview_render = render_name
        label = PREVIEW_RENDER_REGISTRY.get(render_name, render_name)
        self._export_button.setToolTip(f"Export {label} to the schematic output folder.")

    def set_output_hint(
        self,
        output_folder: str | None,
        *,
        minecraft_version: str | None = None,
        worldgen_template_available: bool = True,
    ) -> None:
        if not output_folder:
            self._output_label.setText("Output folder is set in structure.yaml (output_folder).")
        else:
            version_label = minecraft_version or "version"
            self._output_label.setText(
                f"Schematics: output/schematics/{output_folder}/\n"
                f"Worlds: output/worlds/{output_folder}/v{version_label.replace('.', '_')}/"
            )

        self._worldgen_template_available = worldgen_template_available
        self._update_generate_world_button()

    def _update_generate_world_button(self) -> None:
        if not self._worldgen_available:
            return

        enabled = self._worldgen_template_available
        self._generate_world_button.setEnabled(enabled)

        if enabled:
            self._generate_world_button.setToolTip("")
            return

        self._generate_world_button.setToolTip(
            "No worldgen template exists for this structure's Minecraft version. "
            "Add a folder under worldgen_templates/ (see docs/worldgen.md)."
        )

    def set_busy(self, busy: bool) -> None:
        self._export_button.setEnabled(not busy)
        self._generate_world_button.setEnabled(
            not busy and self._worldgen_available and self._worldgen_template_available,
        )
        self._open_output_button.setEnabled(not busy)

    def _on_export_render_clicked(self) -> None:
        try:
            renders = export_renders_for_preview(self._preview_render)
        except ValueError as exc:
            QMessageBox.warning(self, "Export Render", str(exc))
            return

        self.export_render_requested.emit(renders)
