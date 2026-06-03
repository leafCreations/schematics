"""Load and save structure layer YAML for the desktop editor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from helpers.grid import resolve_site_dimensions
from helpers.site_ground import ensure_site_ground
from helpers.structure_loader import (
    load_layers_from_paths,
    resolve_layer_paths,
    resolve_structure_source,
    validate_structure_config,
)


@dataclass
class StructureDocument:
    structure_path: Path
    metadata: dict[str, Any]
    layer_files: list[str]
    layer_paths: list[Path]
    layers: list[dict[str, Any]]
    site_ground: list[list[str]]


def resolve_structure_path(structure: str, stage: int) -> Path:
    return resolve_structure_source(structure, stage).resolve()


def resolve_layer_file_paths(path: Path, data: dict[str, Any]) -> list[Path]:
    """Return layer paths from ``layer_files`` or sorted ``layers/layer_*.yaml``."""
    return resolve_layer_paths(path, data, for_editor=True)


def structure_config_from_document(document: StructureDocument) -> dict[str, Any]:
    """Build a render-pipeline config dict from an in-memory editor document."""
    config = dict(document.metadata)
    config["layers"] = document.layers
    config["site_ground"] = document.site_ground
    return config


def validate_structure_document(document: StructureDocument) -> None:
    """Run the same validation as render/worldgen on the editor document."""
    validate_structure_config(structure_config_from_document(document))


def load_structure_document(path: Path) -> StructureDocument:
    if not path.is_file():
        raise FileNotFoundError(f"Structure file not found: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")

    base_dir = path.parent
    layer_paths = resolve_layer_file_paths(path, data)

    if "layer_files" in data:
        layer_files = [str(layer_file) for layer_file in data["layer_files"]]
    else:
        layer_files = [layer_path.relative_to(base_dir).as_posix() for layer_path in layer_paths]

    layers = load_layers_from_paths(layer_paths)

    metadata = {
        key: value
        for key, value in data.items()
        if key not in ("layer_files", "layers", "site_ground")
    }

    grid = metadata.get("grid", {})
    site_width, site_depth = resolve_site_dimensions(grid)
    site_ground = ensure_site_ground(data.get("site_ground"), site_width, site_depth)

    document = StructureDocument(
        structure_path=path,
        metadata=metadata,
        layer_files=layer_files,
        layer_paths=layer_paths,
        layers=layers,
        site_ground=site_ground,
    )
    validate_structure_document(document)
    return document


def load_layer(path: Path) -> dict[str, Any]:
    layer = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(layer, dict):
        raise ValueError(f"{path} must contain a YAML mapping")

    return layer


def save_layer(
    path: Path,
    layer: dict[str, Any],
    *,
    document: StructureDocument | None = None,
) -> None:
    if document is not None:
        validate_structure_document(document)

    path.write_text(
        yaml.safe_dump(layer, default_flow_style=False, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def save_structure_metadata(
    path: Path,
    metadata: dict[str, Any],
    *,
    layer_files: list[str],
    site_ground: list[list[str]],
    document: StructureDocument | None = None,
) -> None:
    if document is not None:
        validate_structure_document(document)

    payload = dict(metadata)
    payload["layer_files"] = layer_files
    payload["site_ground"] = site_ground
    path.write_text(
        yaml.safe_dump(payload, default_flow_style=False, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def open_structure(structure: str, stage: int) -> StructureDocument:
    return load_structure_document(resolve_structure_path(structure, stage))
