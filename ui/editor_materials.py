"""SchematicContext and inventory helpers for the structure editor."""

from __future__ import annotations

from helpers.context import SchematicContext
from helpers.materials import (
    MaterialsIconList,
    MaterialsIconTokens,
    MaterialsList,
    build_material_inventory_from_raw_tokens,
    collect_raw_tokens_from_layers,
)
from helpers.paths import (
    BLOCK_TEXTURES_FOLDER,
    OUTPUT_SCHEMATICS_FOLDER,
    OUTPUT_WORLDS_FOLDER,
    resolve_worldgen_template_dir,
)
from registries.loader import BLOCK_REGISTRY


def build_editor_materials_context() -> SchematicContext:
    return SchematicContext(
        structure="editor",
        stage=0,
        name="Editor",
        layers=[],
        grid={},
        block_registry=BLOCK_REGISTRY,
        assets_dir=BLOCK_TEXTURES_FOLDER,
        worldgen_template_dir=resolve_worldgen_template_dir(),
        output_schematics_dir=OUTPUT_SCHEMATICS_FOLDER / "_editor",
        output_worldgen_dir=OUTPUT_WORLDS_FOLDER / "_editor",
    )


def structure_material_inventory(
    layers: list[dict],
    ctx: SchematicContext,
) -> tuple[MaterialsList, MaterialsIconList, MaterialsIconTokens]:
    raw_tokens = collect_raw_tokens_from_layers(layers)
    return build_material_inventory_from_raw_tokens(raw_tokens, ctx)
