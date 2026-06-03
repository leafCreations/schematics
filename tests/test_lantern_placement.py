from helpers.context import SchematicContext
from helpers.lantern_placement import (
    explicit_hanging,
    infer_hanging_from_above,
    resolve_lantern_worldgen,
)
from helpers.structure_tokens import parse_structure_token
from renderers import worldgen


def _ctx_with_layers(*layer_cells: list[list[str]]) -> SchematicContext:
    layers = [{"index": index, "cells": cells} for index, cells in enumerate(layer_cells)]

    return SchematicContext(
        structure="test",
        stage=1,
        name="Test",
        layers=layers,
        grid={"offset_x": 0, "offset_z": 0},
        block_registry={},
        assets_dir=".",
        worldgen_template_dir=".",
        output_schematics_dir=".",
        output_worldgen_dir=".",
    )


def test_explicit_hanging_from_token_states():
    assert explicit_hanging(parse_structure_token("LANTERN;hanging=true")) is True
    assert explicit_hanging(parse_structure_token("LANTERN;hanging=false")) is False
    assert explicit_hanging(parse_structure_token("LANTERN")) is None


def test_infer_hanging_when_block_above():
    ctx = _ctx_with_layers(
        [["."]],
        [["LANTERN"]],
        [["SLAB:oak"]],
    )

    assert infer_hanging_from_above(ctx, 1, 0, 0) is True


def test_infer_standing_when_air_above():
    ctx = _ctx_with_layers(
        [["LANTERN"]],
        [["."]],
    )

    assert infer_hanging_from_above(ctx, 0, 0, 0) is False


def test_resolve_lantern_worldgen_respects_manual_override():
    ctx = _ctx_with_layers([["LANTERN;hanging=true"]])

    parsed = parse_structure_token("LANTERN;hanging=true")
    resolved = resolve_lantern_worldgen(parsed, ctx, 0, 0, 0)

    assert dict(resolved.states)["hanging"] is True


def test_generate_lantern_hanging_under_slab():
    worldgen.BLOCK_CACHE.clear()

    ctx = _ctx_with_layers(
        [["LANTERN"]],
        [["SLAB:oak"]],
    )

    parsed = parse_structure_token("LANTERN")
    resolved = resolve_lantern_worldgen(parsed, ctx, 0, 0, 0)
    block = worldgen.generate_block(resolved)

    assert block.base_name == "lantern"
    assert str(block.properties["hanging"]) == "true"


def test_generate_lantern_standing_without_support():
    worldgen.BLOCK_CACHE.clear()

    parsed = parse_structure_token("LANTERN")
    resolved = resolve_lantern_worldgen(
        parsed,
        _ctx_with_layers([["LANTERN"]]),
        0,
        0,
        0,
    )
    block = worldgen.generate_block(resolved)

    assert str(block.properties["hanging"]) == "false"


def test_generate_copper_lantern_hanging_under_slab():
    worldgen.BLOCK_CACHE.clear()

    ctx = _ctx_with_layers(
        [["COPPER_LANTERN#oxidized"]],
        [["SLAB:oak"]],
    )

    parsed = parse_structure_token("COPPER_LANTERN#oxidized")
    resolved = resolve_lantern_worldgen(parsed, ctx, 0, 0, 0)
    block = worldgen.generate_block(resolved)

    assert block.base_name == "oxidized_copper_lantern"
    assert str(block.properties["hanging"]) == "true"


def test_generate_soul_lantern_manual_standing():
    worldgen.BLOCK_CACHE.clear()

    block = worldgen.generate_block(parse_structure_token("LANTERN#soul;hanging=false"))

    assert block.base_name == "soul_lantern"
    assert str(block.properties["hanging"]) == "false"
