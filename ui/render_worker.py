"""Background render jobs for the structure editor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from helpers.types import RenderList
from render_main import run_stage_renders


@dataclass(frozen=True)
class RenderJobResult:
    schematics_dir: Path
    worldgen_dir: Path
    output_folder: str


class RenderWorker(QObject):
    progress = Signal(str)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        structure: str,
        stage: int,
        renders: RenderList | str,
        *,
        structure_path: Path | None = None,
        worldgen_version: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._structure = structure
        self._stage = stage
        self._renders = renders
        self._structure_path = structure_path
        self._worldgen_version = worldgen_version

    def run(self) -> None:
        try:
            ctx = run_stage_renders(
                self._structure,
                self._stage,
                self._renders,
                structure_path=self._structure_path,
                worldgen_version=self._worldgen_version,
                progress=self._emit_progress,
            )
        except Exception as exc:  # noqa: BLE001 — surface pipeline errors in the UI
            self.failed.emit(str(exc))
            return

        self.finished.emit(
            RenderJobResult(
                schematics_dir=ctx.output_schematics_dir,
                worldgen_dir=ctx.output_worldgen_dir,
                output_folder=ctx.output_schematics_dir.name,
            )
        )

    def _emit_progress(self, _render_name: str, label: str) -> None:
        self.progress.emit(label)
