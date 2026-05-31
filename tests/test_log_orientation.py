from helpers.log_orientation import orientation_to_axis, resolve_log_orientation
from helpers.registry_blocks import resolve_minecraft_blockstates
from helpers.structure_tokens import ParsedToken


def _log_entry():
    return {
        "behavior": "log",
        "defaults": {"orientation": "vertical"},
        "minecraft": {
            "block": "minecraft:{material}_log",
            "blockstates": {"axis": "{axis}"},
        },
    }


def test_resolve_log_orientation_defaults_to_vertical():
    entry = _log_entry()
    parsed = ParsedToken(token="LOG", material="oak")

    assert resolve_log_orientation(parsed, entry) == "vertical"


def test_resolve_log_orientation_from_direction():
    entry = _log_entry()

    assert (
        resolve_log_orientation(ParsedToken(token="LOG", material="oak", direction="E"), entry)
        == "east_west"
    )
    assert (
        resolve_log_orientation(ParsedToken(token="LOG", material="oak", direction="N"), entry)
        == "north_south"
    )


def test_resolve_log_orientation_from_variant():
    entry = _log_entry()
    parsed = ParsedToken(token="LOG", material="oak", variant="east_west")

    assert resolve_log_orientation(parsed, entry) == "east_west"


def test_orientation_to_axis():
    assert orientation_to_axis("vertical") == "y"
    assert orientation_to_axis("east_west") == "x"
    assert orientation_to_axis("north_south") == "z"


def test_resolve_minecraft_blockstates_for_log_axis():
    entry = _log_entry()
    parsed = ParsedToken(token="LOG", material="oak", direction="W")

    blockstates = resolve_minecraft_blockstates(entry, parsed, entry["minecraft"]["blockstates"])

    assert blockstates == {"axis": "x"}
