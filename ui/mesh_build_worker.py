"""Background mesh build jobs for the 3D orbit preview."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from helpers.context import SchematicContext
from helpers.orbit_mesh import build_orbit_mesh_from_context


class MeshBuildWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, ctx: SchematicContext, parent=None) -> None:
        super().__init__(parent)
        self._ctx = ctx

    def run(self) -> None:
        try:
            mesh = build_orbit_mesh_from_context(self._ctx)
        except Exception as exc:  # noqa: BLE001 — surface to UI
            self.failed.emit(str(exc))
            return
        self.finished.emit(mesh)
