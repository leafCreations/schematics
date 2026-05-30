from helpers import materials as material_utils
from helpers.structure_tokens import ParsedToken


class _RegistryEntry(dict):
    pass


def _ctx_with_registry(block_registry: dict):
    from pathlib import Path

    from helpers.context import SchematicContext

    return SchematicContext(
        structure="test",
        stage=1,
        name="Test",
        layers=[],
        grid={},
        block_registry=block_registry,
        assets_dir=Path("."),
        worldgen_template_dir=Path("."),
        output_schematics_dir=Path("."),
        output_worldgen_dir=Path("."),
    )


def test_build_material_inventory_from_raw_tokens():
    ctx = _ctx_with_registry(
        {
            "PLANKS": {
                "behavior": "solid",
                "minecraft": {"block": "minecraft:oak_planks"},
            },
        }
    )

    inventory, icons = material_utils.build_material_inventory_from_raw_tokens(
        ["PLANKS:oak", "PLANKS:oak", "."],
        ctx,
    )

    assert inventory == [("Oak Planks", 2)]
    assert "Oak Planks" in icons


def test_build_material_inventory_matches_raw_token_wrapper():
    ctx = _ctx_with_registry(
        {
            "PLANKS": {
                "behavior": "solid",
                "minecraft": {"block": "minecraft:oak_planks"},
            },
        }
    )
    parsed = [ParsedToken(token="PLANKS", material="oak")]

    from_raw = material_utils.build_material_inventory_from_raw_tokens(["PLANKS:oak"], ctx)
    from_parsed = material_utils.build_material_inventory(parsed, ctx)

    assert from_raw == from_parsed


def test_should_count_material_skips_door_upper():
    ctx = _ctx_with_registry(
        {"DOOR": {"behavior": "door", "minecraft": {"block": "minecraft:oak_door"}}}
    )
    parsed = ParsedToken(token="DOOR", material="oak", variant="upper")

    assert material_utils.should_count_material(parsed, ctx) is False


def test_should_count_material_skips_bed_foot():
    ctx = _ctx_with_registry(
        {"BED": {"behavior": "bed", "minecraft": {"block": "minecraft:red_bed"}}}
    )
    parsed = ParsedToken(token="BED", material="red", variant="foot")

    assert material_utils.should_count_material(parsed, ctx) is False


def test_should_count_material_counts_normal_blocks():
    ctx = _ctx_with_registry(
        {"PLANKS": {"behavior": "solid", "minecraft": {"block": "minecraft:oak_planks"}}}
    )
    parsed = ParsedToken(token="PLANKS", material="oak")

    assert material_utils.should_count_material(parsed, ctx) is True
