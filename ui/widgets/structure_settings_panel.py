"""Combined structure identity and grid size controls (Structure tab, bottom left)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QGroupBox

from ui.widgets.panel_header import create_titled_panel_layout
from ui.widgets.panel_tool_button import make_panel_close_button
from ui.widgets.structure_properties_panel import StructurePropertiesPanel
from ui.widgets.structure_size_panel import StructureSizePanel


class StructureSettingsPanel(QGroupBox):
    properties_changed = Signal()
    resize_requested = Signal(int, int)
    close_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        close_button = make_panel_close_button(
            tooltip="Hide structure settings",
            clicked=self.close_requested.emit,
        )
        layout = create_titled_panel_layout(self, "Structure", [close_button])
        self._properties = StructurePropertiesPanel()
        self._size = StructureSizePanel()

        self._properties.properties_changed.connect(self.properties_changed.emit)
        self._size.resize_requested.connect(self.resize_requested.emit)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)

        layout.addWidget(self._properties)
        layout.addWidget(divider)
        layout.addWidget(self._size)

    def set_structure_path(self, path: Path) -> None:
        self._properties.set_structure_path(path)

    def load_from_metadata(self, metadata: dict[str, Any]) -> None:
        self._properties.load_from_metadata(metadata)

    def apply_to_metadata(self, metadata: dict[str, Any]) -> None:
        self._properties.apply_to_metadata(metadata)

    def current_output_folder(self) -> str:
        return self._properties.current_output_folder()

    def set_structure_size(self, width: int, depth: int) -> None:
        self._size.set_structure_size(width, depth)

    def set_site_limits(self, site_width: int, site_depth: int) -> None:
        self._size.set_site_limits(site_width, site_depth)
