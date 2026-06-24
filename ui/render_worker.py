"""Background render jobs for the structure editor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

import helpers.constants as constants
from helpers.types import RenderList
from render_main import (
    run_preview_materials,
    run_preview_site_facades,
    run_preview_site_top_down,
    run_preview_structure_facades,
    run_preview_top_down,
    run_stage_renders,
)


@dataclass(frozen=True)
class RenderJobResult:
    schematics_dir: Path
    worldgen_dir: Path
    output_folder: str
    renders: list[str]
    preview_render: str | None = None
    preview_group: str | None = None


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
        structure_config: dict[str, Any] | None = None,
        worldgen_version: str | None = None,
        output_schematics_dir: Path | None = None,
        preview_render: str | None = None,
        preview_group: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._structure = structure
        self._stage = stage
        self._renders = renders
        self._structure_path = structure_path
        self._structure_config = structure_config
        self._worldgen_version = worldgen_version
        self._output_schematics_dir = output_schematics_dir
        self._preview_render = preview_render
        self._preview_group = preview_group

    def run(self) -> None:
        try:
            if self._preview_render == constants.RENDER_STRUCTURE_FACADES:
                ctx = run_preview_structure_facades(
                    self._structure,
                    self._stage,
                    structure_path=self._structure_path,
                    structure_config=self._structure_config,
                    worldgen_version=self._worldgen_version,
                    output_schematics_dir=self._output_schematics_dir,
                    progress=self._emit_progress,
                )
            elif self._preview_render == constants.RENDER_SITE_FACADES:
                ctx = run_preview_site_facades(
                    self._structure,
                    self._stage,
                    structure_path=self._structure_path,
                    structure_config=self._structure_config,
                    worldgen_version=self._worldgen_version,
                    output_schematics_dir=self._output_schematics_dir,
                    progress=self._emit_progress,
                )
            elif self._preview_render == constants.RENDER_PATH:
                ctx = run_preview_site_top_down(
                    self._structure,
                    self._stage,
                    structure_path=self._structure_path,
                    structure_config=self._structure_config,
                    worldgen_version=self._worldgen_version,
                    output_schematics_dir=self._output_schematics_dir,
                    progress=self._emit_progress,
                )
            elif self._preview_render == constants.RENDER_MATERIALS:
                ctx = run_preview_materials(
                    self._structure,
                    self._stage,
                    structure_path=self._structure_path,
                    structure_config=self._structure_config,
                    worldgen_version=self._worldgen_version,
                    output_schematics_dir=self._output_schematics_dir,
                    progress=self._emit_progress,
                )
            elif self._preview_group is not None:
                ctx = run_preview_top_down(
                    self._structure,
                    self._stage,
                    self._preview_group,
                    structure_path=self._structure_path,
                    structure_config=self._structure_config,
                    worldgen_version=self._worldgen_version,
                    output_schematics_dir=self._output_schematics_dir,
                    progress=self._emit_progress,
                )
            else:
                ctx = run_stage_renders(
                    self._structure,
                    self._stage,
                    self._renders,
                    structure_path=self._structure_path,
                    worldgen_version=self._worldgen_version,
                    output_schematics_dir=self._output_schematics_dir,
                    progress=self._emit_progress,
                )
        except Exception as exc:  # noqa: BLE001 — surface pipeline errors in the UI
            self.failed.emit(str(exc))
            return

        renders = self._renders if isinstance(self._renders, list) else [self._renders]
        self.finished.emit(
            RenderJobResult(
                schematics_dir=ctx.output_schematics_dir,
                worldgen_dir=ctx.output_worldgen_dir,
                output_folder=ctx.output_schematics_dir.name,
                renders=renders,
                preview_render=self._preview_render,
                preview_group=self._preview_group,
            )
        )

    def _emit_progress(self, _render_name: str, label: str) -> None:
        self.progress.emit(label)
