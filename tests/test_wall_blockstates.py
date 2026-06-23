from helpers.registry_blocks import resolve_minecraft_blockstates
from helpers.structure_tokens import ParsedToken
from helpers.wall_blockstates import resolve_wall_blockstates
from registries.loader import BLOCK_REGISTRY


def test_resolve_wall_blockstates_from_adjacency():
    parsed = ParsedToken(
        token="WALL",
        material="cobblestone",
        states=(
            ("north", True),
            ("south", False),
            ("east", True),
            ("west", False),
        ),
    )

    assert resolve_wall_blockstates(parsed) == {
        "north": "low",
        "south": "none",
        "east": "low",
        "west": "none",
        "up": "false",
    }


def test_resolve_wall_blockstates_isolated_post():
    parsed = ParsedToken(
        token="WALL",
        material="cinnabar",
        states=(
            ("north", False),
            ("south", False),
            ("east", False),
            ("west", False),
        ),
    )

    assert resolve_wall_blockstates(parsed) == {
        "north": "none",
        "south": "none",
        "east": "none",
        "west": "none",
        "up": "true",
    }


def test_resolve_minecraft_blockstates_for_wall_behavior():
    entry = BLOCK_REGISTRY["WALL"]
    parsed = ParsedToken(
        token="WALL",
        material="sulfur",
        states=(
            ("north", True),
            ("south", True),
            ("east", False),
            ("west", False),
        ),
    )

    blockstates = resolve_minecraft_blockstates(
        entry,
        parsed,
        entry["minecraft"]["blockstates"],
    )

    assert blockstates == {
        "north": "low",
        "south": "low",
        "east": "none",
        "west": "none",
        "up": "false",
    }
