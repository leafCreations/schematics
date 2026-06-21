"""Load and save structure layer YAML for the desktop editor."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from helpers.grid import resolve_site_dimensions
from helpers.grid_placement import (
    DEFAULT_PLACEMENT,
    apply_placement_to_grid,
    structure_site_size_error,
)
from helpers.layer_management import create_layer
from helpers.paths import STRUCTURES_FOLDER
from helpers.site_ground import ensure_site_ground
from helpers.structure_loader import (
    load_layers_from_paths,
    resolve_layer_paths,
    resolve_structure_source,
    validate_structure_config,
)
from helpers.structure_metadata import (
    apply_structure_identity,
    identity_from_structure_path,
    normalize_structure_slug,
)


@dataclass
class StructureDocument:
    structure_path: Path
    metadata: dict[str, Any]
    layer_files: list[str]
    layer_paths: list[Path]
    layers: list[dict[str, Any]]
    site_ground: list[list[str]]


def _structure_manifest_path(structure_slug: str) -> Path:
    return STRUCTURES_FOLDER / structure_slug / "structure.yaml"


def _load_structure_manifest(structure_slug: str) -> dict[str, Any]:
    path = _structure_manifest_path(structure_slug)

    if not path.is_file():
        return {"structure": structure_slug, "stages": []}

    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        return {"structure": structure_slug, "stages": []}

    stages = data.get("stages")
    if not isinstance(stages, list):
        data["stages"] = []

    data["structure"] = structure_slug
    return data


def _save_structure_manifest(structure_slug: str, manifest: dict[str, Any]) -> None:
    path = _structure_manifest_path(structure_slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(manifest, default_flow_style=False, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _upsert_manifest_stage(
    structure_slug: str,
    stage: int,
    *,
    dimension: str,
    grid: dict[str, Any],
    output_folder: str,
    shared_site_ground: list[list[str]] | None = None,
) -> None:
    manifest = _load_structure_manifest(structure_slug)
    stage_value = int(stage)
    stage_entry = {
        "stage": stage_value,
        "path": f"stage{stage_value}/stage.yaml",
        "dimension": _normalize_dimension(dimension),
        "output_folder": output_folder,
        "grid": dict(grid),
    }

    stages = [entry for entry in manifest.get("stages", []) if isinstance(entry, dict)]
    updated = False

    for index, entry in enumerate(stages):
        try:
            entry_stage = int(entry.get("stage"))
        except (TypeError, ValueError):
            continue

        if entry_stage == stage_value:
            stages[index] = stage_entry
            updated = True
            break

    if not updated:
        stages.append(stage_entry)

    stages.sort(key=lambda entry: int(entry.get("stage", 0)))
    manifest["stages"] = stages
    manifest["structure"] = structure_slug

    if shared_site_ground is not None:
        manifest["site_ground"] = shared_site_ground

    _save_structure_manifest(structure_slug, manifest)


def _remove_manifest_stage(structure_slug: str, stage: int) -> None:
    path = _structure_manifest_path(structure_slug)

    if not path.is_file():
        return

    manifest = _load_structure_manifest(structure_slug)
    stage_value = int(stage)
    remaining = []

    for entry in manifest.get("stages", []):
        if not isinstance(entry, dict):
            continue

        try:
            entry_stage = int(entry.get("stage"))
        except (TypeError, ValueError):
            continue

        if entry_stage != stage_value:
            remaining.append(entry)

    if remaining:
        remaining.sort(key=lambda entry: int(entry.get("stage", 0)))
        manifest["stages"] = remaining
        manifest["structure"] = structure_slug
        _save_structure_manifest(structure_slug, manifest)
        return

    path.unlink(missing_ok=True)


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


def _normalize_dimension(value: Any) -> str:
    dimension = str(value or "overworld").strip().lower()
    if dimension not in {"overworld", "nether", "end"}:
        return "overworld"
    return dimension


def load_structure_document(path: Path) -> StructureDocument:
    if not path.is_file():
        raise FileNotFoundError(f"Structure file not found: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")

    identity = identity_from_structure_path(path)
    manifest: dict[str, Any] | None = None
    manifest_entry: dict[str, Any] | None = None

    if identity is not None:
        structure_slug, stage_value = identity
        manifest = _load_structure_manifest(structure_slug)

        for entry in manifest.get("stages", []):
            if not isinstance(entry, dict):
                continue

            try:
                entry_stage = int(entry.get("stage"))
            except (TypeError, ValueError):
                continue

            if entry_stage == stage_value:
                manifest_entry = entry
                break

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

    if manifest_entry is not None:
        if "dimension" in manifest_entry:
            metadata["dimension"] = manifest_entry.get("dimension")
        if "grid" in manifest_entry:
            metadata["grid"] = manifest_entry.get("grid")
        if "output_folder" in manifest_entry:
            metadata["output_folder"] = manifest_entry.get("output_folder")

    metadata["dimension"] = _normalize_dimension(metadata.get("dimension"))

    grid = metadata.get("grid", {})
    site_width, site_depth = resolve_site_dimensions(grid)
    shared_site_ground = manifest.get("site_ground") if isinstance(manifest, dict) else None
    site_ground = ensure_site_ground(
        shared_site_ground or data.get("site_ground"), site_width, site_depth
    )

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
    dimension_value = _normalize_dimension(payload.get("dimension"))
    grid_value = dict(payload.get("grid", {}))
    identity = identity_from_structure_path(path)

    if identity is not None and path.name == "stage.yaml":
        payload.pop("dimension", None)
        payload.pop("grid", None)
        payload.pop("output_folder", None)
        payload.pop("site_ground", None)
    else:
        payload["dimension"] = dimension_value
        payload["grid"] = grid_value
    payload["layer_files"] = layer_files

    if identity is None or path.name != "stage.yaml":
        payload["site_ground"] = site_ground
    path.write_text(
        yaml.safe_dump(payload, default_flow_style=False, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    structure_slug = str(payload.get("structure", "")).strip()

    try:
        stage_value = int(payload.get("stage", 0))
    except (TypeError, ValueError):
        stage_value = 0

    if identity is not None and path.name == "stage.yaml" and structure_slug and stage_value > 0:
        _upsert_manifest_stage(
            structure_slug,
            stage_value,
            dimension=dimension_value,
            grid=grid_value,
            output_folder=str(metadata.get("output_folder", "")),
            shared_site_ground=site_ground,
        )


def open_structure(structure: str, stage: int) -> StructureDocument:
    return load_structure_document(resolve_structure_path(structure, stage))


def create_structure_stage_document(
    *,
    structure: str,
    stage: int,
    site_width: int,
    site_depth: int,
    structure_width: int,
    structure_depth: int,
    dimension: str = "overworld",
) -> Path:
    """Create a new structure stage folder with ``stage.yaml`` and one layer file."""
    structure_slug = normalize_structure_slug(structure)
    stage_value = int(stage)
    site_width_value = int(site_width)
    site_depth_value = int(site_depth)
    structure_width_value = int(structure_width)
    structure_depth_value = int(structure_depth)
    dimension_value = str(dimension).strip().lower()

    if dimension_value not in {"overworld", "nether", "end"}:
        raise ValueError("Dimension must be one of: overworld, nether, end")

    if stage_value < 1:
        raise ValueError("Stage must be at least 1")

    if site_width_value < 1 or site_depth_value < 1:
        raise ValueError("Site width and depth must be at least 1")

    if structure_width_value < 1 or structure_depth_value < 1:
        raise ValueError("Structure width and depth must be at least 1")

    size_error = structure_site_size_error(
        structure_width_value,
        structure_depth_value,
        site_width_value,
        site_depth_value,
    )

    if size_error:
        raise ValueError(size_error)

    structure_dir = STRUCTURES_FOLDER / structure_slug
    stage_dir = structure_dir / f"stage{stage_value}"
    structure_path = stage_dir / "stage.yaml"

    if stage_dir.exists():
        raise FileExistsError(
            f"Stage {stage_value} already exists for structure '{structure_slug}'.",
        )

    metadata: dict[str, Any] = {}
    apply_structure_identity(metadata, structure=structure_slug, stage=stage_value)
    metadata["grid"] = apply_placement_to_grid(
        {
            "site_structure_layers": [0],
            "worldgen_base_y": -60,
        },
        placement=DEFAULT_PLACEMENT,
        site_width=site_width_value,
        site_depth=site_depth_value,
        structure_width=structure_width_value,
        structure_depth=structure_depth_value,
    )

    layers_dir = stage_dir / "layers"
    layer_path = layers_dir / "layer_00.yaml"
    layer_files = ["layers/layer_00.yaml"]
    layer = create_layer(
        width=structure_width_value,
        depth=structure_depth_value,
        worldgen_index=0,
        group="Main",
    )
    manifest = _load_structure_manifest(structure_slug)
    shared_site_ground = manifest.get("site_ground")

    if isinstance(shared_site_ground, list):
        site_ground = ensure_site_ground(shared_site_ground, site_width_value, site_depth_value)
    else:
        ground_token = {
            "overworld": "GRASS",
            "nether": "minecraft:netherrack",
            "end": "minecraft:end_stone",
        }[dimension_value]
        site_ground = [
            [ground_token for _ in range(site_width_value)] for _ in range(site_depth_value)
        ]

    document = StructureDocument(
        structure_path=structure_path,
        metadata=metadata,
        layer_files=layer_files,
        layer_paths=[layer_path],
        layers=[layer],
        site_ground=site_ground,
    )
    validate_structure_document(document)

    try:
        structure_dir.mkdir(parents=True, exist_ok=True)
        layers_dir.mkdir(parents=True, exist_ok=False)
        save_layer(layer_path, layer, document=document)
        save_structure_metadata(
            structure_path,
            metadata,
            layer_files=layer_files,
            site_ground=site_ground,
            document=document,
        )
        _upsert_manifest_stage(
            structure_slug,
            stage_value,
            dimension=dimension_value,
            grid=metadata["grid"],
            output_folder=str(metadata.get("output_folder", "")),
            shared_site_ground=site_ground,
        )
    except Exception:
        shutil.rmtree(stage_dir, ignore_errors=True)
        raise

    return structure_path


def delete_structure_stage_document(*, structure: str, stage: int) -> None:
    structure_slug = normalize_structure_slug(structure)
    stage_value = int(stage)

    if stage_value < 1:
        raise ValueError("Stage must be at least 1")

    structure_dir = STRUCTURES_FOLDER / structure_slug
    stage_dir = structure_dir / f"stage{stage_value}"

    if not stage_dir.is_dir():
        raise FileNotFoundError(
            f"Stage {stage_value} does not exist for structure '{structure_slug}'.",
        )

    shutil.rmtree(stage_dir)
    _remove_manifest_stage(structure_slug, stage_value)

    if structure_dir.is_dir() and not any(structure_dir.iterdir()):
        structure_dir.rmdir()
