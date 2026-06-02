"""Load and save structure layer YAML for the desktop editor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from helpers.structure_loader import resolve_structure_source


@dataclass
class StructureDocument:
    structure_path: Path
    metadata: dict[str, Any]
    layer_paths: list[Path]
    layers: list[dict[str, Any]]


def resolve_structure_path(structure: str, stage: int) -> Path:
    return resolve_structure_source(structure, stage).resolve()


def load_structure_document(path: Path) -> StructureDocument:
    if not path.is_file():
        raise FileNotFoundError(f"Structure file not found: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")

    if "layer_files" not in data:
        raise ValueError(f"{path} must define layer_files for the editor")

    base_dir = path.parent
    layer_paths = [base_dir / layer_file for layer_file in data["layer_files"]]
    layers: list[dict[str, Any]] = []

    for layer_path in layer_paths:
        if not layer_path.is_file():
            raise FileNotFoundError(f"Layer file not found: {layer_path}")

        layer = yaml.safe_load(layer_path.read_text(encoding="utf-8"))

        if not isinstance(layer, dict):
            raise ValueError(f"{layer_path} must contain a YAML mapping")

        layers.append(layer)

    metadata = {key: value for key, value in data.items() if key != "layer_files"}

    return StructureDocument(
        structure_path=path,
        metadata=metadata,
        layer_paths=layer_paths,
        layers=layers,
    )


def load_layer(path: Path) -> dict[str, Any]:
    layer = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(layer, dict):
        raise ValueError(f"{path} must contain a YAML mapping")

    return layer


def save_layer(path: Path, layer: dict[str, Any]) -> None:
    path.write_text(
        yaml.safe_dump(layer, default_flow_style=False, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def open_structure(structure: str, stage: int) -> StructureDocument:
    return load_structure_document(resolve_structure_path(structure, stage))
