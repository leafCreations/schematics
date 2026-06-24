"""Combined structure identity and grid size controls (Structure tab, bottom left)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGroupBox

from ui.widgets.panel_header import create_titled_panel_layout
from ui.widgets.panel_tool_button import make_panel_close_button
from ui.widgets.structure_properties_panel import StructurePropertiesPanel


class StructureSettingsPanel(QGroupBox):
    properties_changed = Signal()
    close_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        close_button = make_panel_close_button(
            tooltip="Hide structure settings",
            clicked=self.close_requested.emit,
        )
        layout = create_titled_panel_layout(self, "Structure", [close_button])
        self._properties = StructurePropertiesPanel()

        self._properties.properties_changed.connect(self.properties_changed.emit)

        layout.addWidget(self._properties)

    def set_structure_path(self, path: Path) -> None:
        self._properties.set_structure_path(path)

    def load_from_metadata(self, metadata: dict[str, Any]) -> None:
        self._properties.load_from_metadata(metadata)

    def apply_to_metadata(self, metadata: dict[str, Any]) -> None:
        self._properties.apply_to_metadata(metadata)

    def current_output_folder(self) -> str:
        return self._properties.current_output_folder()

    def current_minecraft_version(self) -> str:
        return self._properties.current_minecraft_version()

    def set_site_grid_size(self, site_width: int, site_depth: int) -> None:
        self._properties.set_site_grid_size(site_width, site_depth)
