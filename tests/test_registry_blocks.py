import pytest

from helpers.registry_blocks import resolve_minecraft_block_id
from helpers.structure_tokens import ParsedToken


def test_resolve_minecraft_block_id_applies_material():
    entry = {
        "minecraft": {"block": "minecraft:{material}_planks"},
        "material_default": "oak",
    }
    parsed = ParsedToken(token="PLANKS", material="spruce")

    assert resolve_minecraft_block_id(entry, parsed) == "minecraft:spruce_planks"


def test_resolve_minecraft_block_id_requires_variant():
    entry = {
        "minecraft": {
            "variants": {
                "upper": {"block": "minecraft:oak_door"},
            }
        }
    }
    parsed = ParsedToken(token="DOOR", material="oak")

    with pytest.raises(ValueError, match="variant"):
        resolve_minecraft_block_id(entry, parsed)
