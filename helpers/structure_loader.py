import importlib.util
import warnings
from pathlib import Path
from typing import Any

import helpers.constants as constants
from helpers.context import SchematicContext
from helpers.paths import (
    ASSET_FOLDER,
    OUTPUT_SCHEMATICS_FOLDER,
    OUTPUT_WORLDS_FOLDER,
    STRUCTURES_FOLDER,
    TEMPLATE_FOLDER,
)
from helpers.types import GridConfig, LayerConfig, StructureConfig
from registries.loader import BLOCK_REGISTRY, compile_inventory_texture_set, compile_texture_set

REQUIRED_CONFIG_KEYS = ("structure", "stage", "name", "output_folder", "layers", "grid")
REQUIRED_GRID_KEYS = ("site_size", "offset_x", "offset_z")


def validate_grid_config(grid: dict[str, Any], *, path: str = "grid") -> GridConfig:
    missing = [key for key in REQUIRED_GRID_KEYS if key not in grid]

    if missing:
        raise ValueError(f"{path} missing required keys: {', '.join(missing)}")

    site_structure_layers = grid.get("site_structure_layers")

    if site_structure_layers is not None and not isinstance(site_structure_layers, list):
        raise ValueError(f"{path}.site_structure_layers must be a list of layer list indices")

    return grid  # type: ignore[return-value]


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


def validate_structure_config(config: dict[str, Any]) -> StructureConfig:
    missing = [key for key in REQUIRED_CONFIG_KEYS if key not in config]

    if missing:
        raise ValueError(f"STRUCTURE_CONFIG missing required keys: {', '.join(missing)}")

    grid = validate_grid_config(config["grid"])
    layers = config["layers"]

    if not isinstance(layers, list) or not layers:
        raise ValueError("STRUCTURE_CONFIG.layers must be a non-empty list")

    validated_layers = [validate_layer(layer, idx) for idx, layer in enumerate(layers)]

    layer_indices = [layer["index"] for layer in validated_layers]
    duplicate_indices = {index for index in layer_indices if layer_indices.count(index) > 1}

    if duplicate_indices:
        warnings.warn(
            f"Duplicate layer index values {sorted(duplicate_indices)}; "
            "worldgen will overwrite blocks at the same Y level.",
            stacklevel=2,
        )

    site_structure_layers = grid.get("site_structure_layers", [0, 1])

    for layer_idx in site_structure_layers:
        if not isinstance(layer_idx, int) or layer_idx < 0 or layer_idx >= len(validated_layers):
            raise ValueError(
                f"grid.site_structure_layers contains invalid list index {layer_idx!r}; "
                f"expected 0..{len(validated_layers) - 1}"
            )

    return {
        **config,
        "grid": grid,
        "layers": validated_layers,
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


def load_structure_module(path: Path) -> StructureConfig:
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


def load_structure_config(structure: str, stage: int) -> SchematicContext:
    structure_path = STRUCTURES_FOLDER / structure / f"stage{stage}_structure.py"
    config = load_structure_module(structure_path.resolve())
    return build_schematic_context(config)
