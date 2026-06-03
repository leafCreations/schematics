import importlib.util
import warnings
from pathlib import Path
from typing import Any

import yaml

import helpers.constants as constants
from helpers.context import SchematicContext
from helpers.grid import resolve_site_dimensions
from helpers.paths import (
    ASSET_FOLDER,
    OUTPUT_SCHEMATICS_FOLDER,
    OUTPUT_WORLDS_FOLDER,
    STRUCTURES_FOLDER,
    TEMPLATE_FOLDER,
)
from helpers.site_ground import validate_site_ground
from helpers.structure_tokens import parse_structure_token
from helpers.types import GridConfig, LayerConfig, StructureConfig
from registries.loader import BLOCK_REGISTRY, compile_inventory_texture_set, compile_texture_set

REQUIRED_CONFIG_KEYS = ("structure", "stage", "name", "output_folder", "layers", "grid")
REQUIRED_GRID_KEYS = ("offset_x", "offset_z")

INLINE_LAYERS_EDITOR_MESSAGE = (
    "uses inline layers; split into layers/*.yaml and add layer_files "
    "(see structures/residence/stage2/structure.yaml)"
)


def discover_layer_paths(base_dir: Path) -> list[Path]:
    """Return sorted ``layers/layer_*.yaml`` paths when present."""
    layers_dir = base_dir / "layers"

    if not layers_dir.is_dir():
        return []

    return sorted(layers_dir.glob("layer_*.yaml"))


def load_layers_from_paths(layer_paths: list[Path]) -> list[dict[str, Any]]:
    layers: list[dict[str, Any]] = []

    for layer_path in layer_paths:
        if not layer_path.is_file():
            raise FileNotFoundError(f"Layer file not found: {layer_path}")

        with layer_path.open(encoding="utf-8") as handle:
            layer = yaml.safe_load(handle)

        if not isinstance(layer, dict):
            raise ValueError(f"{layer_path} must contain a YAML mapping")

        layers.append(layer)

    return layers


def resolve_layer_paths(
    path: Path,
    data: dict[str, Any],
    *,
    for_editor: bool = False,
) -> list[Path]:
    """Resolve layer YAML paths from ``layer_files`` or ``layers/layer_*.yaml``."""
    base_dir = path.parent

    if "layer_files" in data:
        return [base_dir / layer_file for layer_file in data["layer_files"]]

    if for_editor and "layers" in data:
        raise ValueError(f"{path} {INLINE_LAYERS_EDITOR_MESSAGE}")

    discovered = discover_layer_paths(base_dir)

    if discovered:
        return discovered

    if "layers" in data:
        raise ValueError(
            f"{path} uses inline layers; use layer_files or layers/layer_*.yaml on disk"
        )

    raise ValueError(f"{path} must define layer_files, inline layers, or layers/layer_*.yaml")


def load_structure_layers(path: Path, data: dict[str, Any]) -> list[dict[str, Any]]:
    """Load layer dicts for CLI/render: layer_files, inline ``layers``, or discovery."""
    inline = data.get("layers")

    if "layer_files" in data:
        return load_layers_from_paths(resolve_layer_paths(path, data))

    if isinstance(inline, list) and inline and isinstance(inline[0], dict):
        return inline

    discovered = discover_layer_paths(path.parent)

    if discovered:
        return load_layers_from_paths(discovered)

    raise ValueError(f"{path} must define layer_files, inline layers, or layers/layer_*.yaml")


def collect_structure_cell_token_errors(config: dict[str, Any]) -> list[str]:
    """Return errors for non-empty cells that do not resolve in the registry/catalog."""
    from helpers.registry_lookup import get_block_entry

    errors: list[str] = []

    for layer_idx, layer in enumerate(config.get("layers", []) or []):
        cells = layer.get("cells", [])

        for row_idx, row in enumerate(cells):
            for col_idx, raw_token in enumerate(row):
                if raw_token == ".":
                    continue

                parsed = parse_structure_token(raw_token)

                if parsed is None:
                    errors.append(
                        f"layer {layer_idx} cell ({row_idx}, {col_idx}): "
                        f"invalid token {raw_token!r}"
                    )
                    continue

                if get_block_entry(parsed) is None:
                    errors.append(
                        f"layer {layer_idx} cell ({row_idx}, {col_idx}): "
                        f"unknown token {raw_token!r}"
                    )

    site_ground = config.get("site_ground")

    if site_ground:
        for row_idx, row in enumerate(site_ground):
            for col_idx, raw_token in enumerate(row):
                if raw_token == ".":
                    continue

                parsed = parse_structure_token(raw_token)

                if parsed is None:
                    errors.append(
                        f"site_ground ({row_idx}, {col_idx}): invalid token {raw_token!r}"
                    )
                    continue

                if get_block_entry(parsed) is None:
                    errors.append(
                        f"site_ground ({row_idx}, {col_idx}): unknown token {raw_token!r}"
                    )

    return errors


def validate_structure_cell_tokens(config: dict[str, Any]) -> None:
    errors = collect_structure_cell_token_errors(config)

    if errors:
        joined = "\n".join(f"  - {error}" for error in errors)
        raise ValueError(f"Structure contains unknown or invalid cell tokens:\n{joined}")


def validate_grid_config(grid: dict[str, Any], *, path: str = "grid") -> GridConfig:
    missing = [key for key in REQUIRED_GRID_KEYS if key not in grid]

    if missing:
        raise ValueError(f"{path} missing required keys: {', '.join(missing)}")

    has_legacy_site = "site_size" in grid
    has_rectangular_site = "site_width" in grid and "site_depth" in grid

    if not has_legacy_site and not has_rectangular_site:
        raise ValueError(
            f"{path} must define site_size (square site) or both site_width and site_depth",
        )

    normalized = dict(grid)
    site_width, site_depth = resolve_site_dimensions(normalized)
    normalized["site_width"] = site_width
    normalized["site_depth"] = site_depth
    grid = normalized

    site_structure_layers = grid.get("site_structure_layers")

    if site_structure_layers is not None and not isinstance(site_structure_layers, list):
        raise ValueError(f"{path}.site_structure_layers must be a list of layer list indices")

    return grid  # type: ignore[return-value]  # normalized site_width/site_depth


def validate_layer(layer: dict[str, Any], layer_idx: int) -> LayerConfig:
    if "cells" not in layer:
        raise ValueError(f"Layer {layer_idx} missing required key 'cells'")

    if "index" not in layer:
        raise ValueError(f"Layer {layer_idx} missing required key 'index'")

    cells = layer["cells"]

    if not cells:
        raise ValueError(f"Layer {layer_idx} has empty cells")

    if not isinstance(cells[0], list):
        raise ValueError(f"Layer {layer_idx} cells must be a 2D grid")

    width = len(cells[0])

    for row_idx, row in enumerate(cells):
        if len(row) != width:
            raise ValueError(
                f"Layer {layer_idx} row {row_idx} width {len(row)} != expected {width}"
            )

    return layer  # type: ignore[return-value]


def layer_grid_dimensions(layer: dict[str, Any]) -> tuple[int, int]:
    """Return (width, depth) for a layer's ``cells`` grid."""
    cells = layer["cells"]
    return len(cells[0]), len(cells)


def validate_layers_consistent_dimensions(layers: list[dict[str, Any]]) -> None:
    """Require every layer to use the same width and depth."""
    if len(layers) < 2:
        return

    ref_width, ref_depth = layer_grid_dimensions(layers[0])
    mismatched: list[int] = []

    for layer_idx, layer in enumerate(layers[1:], start=1):
        width, depth = layer_grid_dimensions(layer)

        if (width, depth) != (ref_width, ref_depth):
            mismatched.append(layer_idx)

    if mismatched:
        raise ValueError(
            f"All layers must share the same width and depth ({ref_width}x{ref_depth}); "
            f"layer(s) {mismatched} differ"
        )


def validate_structure_config(config: dict[str, Any]) -> StructureConfig:
    missing = [key for key in REQUIRED_CONFIG_KEYS if key not in config]

    if missing:
        raise ValueError(f"STRUCTURE_CONFIG missing required keys: {', '.join(missing)}")

    grid = validate_grid_config(config["grid"])
    layers = config["layers"]

    if not isinstance(layers, list) or not layers:
        raise ValueError("STRUCTURE_CONFIG.layers must be a non-empty list")

    validated_layers = [validate_layer(layer, idx) for idx, layer in enumerate(layers)]
    validate_layers_consistent_dimensions(validated_layers)

    layer_indices = [layer["index"] for layer in validated_layers]
    duplicate_indices = {index for index in layer_indices if layer_indices.count(index) > 1}

    if duplicate_indices:
        raise ValueError(
            f"Duplicate layer index values {sorted(duplicate_indices)}; "
            "each layer must have a unique index for worldgen"
        )

    site_structure_layers = grid.get("site_structure_layers", [0, 1])

    for layer_idx in site_structure_layers:
        if not isinstance(layer_idx, int) or layer_idx < 0 or layer_idx >= len(validated_layers):
            raise ValueError(
                f"grid.site_structure_layers contains invalid list index {layer_idx!r}; "
                f"expected 0..{len(validated_layers) - 1}"
            )

    site_width, site_depth = resolve_site_dimensions(grid)
    site_ground = None

    if "site_ground" in config:
        site_ground = validate_site_ground(
            config["site_ground"],
            site_width,
            site_depth,
        )

    validate_structure_cell_tokens(config)

    return {
        **config,
        "grid": grid,
        "layers": validated_layers,
        "site_ground": site_ground,
    }  # type: ignore[return-value]


def build_schematic_context(config: StructureConfig) -> SchematicContext:
    validated = validate_structure_config(config)

    ctx = SchematicContext(
        structure=validated["structure"],
        stage=validated["stage"],
        layers=validated["layers"],
        grid=validated["grid"],
        name=validated["name"],
        block_registry=BLOCK_REGISTRY,
        assets_dir=ASSET_FOLDER / "textures/block",
        output_schematics_dir=OUTPUT_SCHEMATICS_FOLDER / validated["output_folder"],
        output_worldgen_dir=OUTPUT_WORLDS_FOLDER / validated["output_folder"],
        worldgen_template_dir=TEMPLATE_FOLDER,
        site_ground=validated.get("site_ground"),
    )

    ctx.topdown_textures = compile_texture_set(
        constants.TEXTURE_TOP, ctx.assets_dir, block_px=constants.BLOCK_PX
    )
    ctx.sideview_textures = compile_texture_set(
        constants.TEXTURE_SIDE, ctx.assets_dir, block_px=constants.BLOCK_PX
    )
    ctx.inventory_textures = compile_inventory_texture_set(
        ctx.assets_dir, block_px=constants.BLOCK_PX
    )

    return ctx


def load_structure_yaml(path: Path) -> StructureConfig:
    if not path.exists():
        raise FileNotFoundError(f"Structure file not found: {path}")

    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")

    layers = load_structure_layers(path, data)
    config = {**data, "layers": layers}
    config.pop("layer_files", None)

    return validate_structure_config(config)


def load_structure_module(path: Path) -> StructureConfig:
    """Load a legacy ``stage{N}_structure.py`` module (deprecated; use YAML)."""
    warnings.warn(
        f"Python structure modules are deprecated ({path.name}); "
        f"migrate to {path.parent / 'structure.yaml'} "
        "(see scripts/migrate_structure_to_yaml.py).",
        DeprecationWarning,
        stacklevel=2,
    )

    if not path.exists():
        raise FileNotFoundError(f"Structure file not found: {path}")

    spec = importlib.util.spec_from_file_location(path.stem, path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load structure module: {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "STRUCTURE_CONFIG"):
        raise AttributeError(f"{path} must define STRUCTURE_CONFIG")

    return validate_structure_config(module.STRUCTURE_CONFIG)


def resolve_structure_source(structure: str, stage: int) -> Path:
    yaml_path = STRUCTURES_FOLDER / structure / f"stage{stage}" / "structure.yaml"

    if yaml_path.is_file():
        return yaml_path

    python_path = STRUCTURES_FOLDER / structure / f"stage{stage}_structure.py"

    if python_path.is_file():
        return python_path

    raise FileNotFoundError(
        f"No structure definition found for {structure} stage {stage}; "
        f"expected {yaml_path} or {python_path}"
    )


def load_structure_config(structure: str, stage: int) -> SchematicContext:
    structure_path = resolve_structure_source(structure, stage).resolve()

    if structure_path.suffix == ".yaml":
        config = load_structure_yaml(structure_path)
    else:
        config = load_structure_module(structure_path)

    return build_schematic_context(config)
