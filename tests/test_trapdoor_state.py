from helpers.structure_tokens import parse_structure_token
from helpers.trapdoor_state import explicit_open, with_trapdoor_open


def test_explicit_open_from_token_states():
    assert explicit_open(parse_structure_token("TRAPDOOR:oak@north;open=true")) is True
    assert explicit_open(parse_structure_token("TRAPDOOR:oak@north;open=false")) is False
    assert explicit_open(parse_structure_token("TRAPDOOR:oak@north")) is None


def test_with_trapdoor_open_updates_token():
    assert with_trapdoor_open("TRAPDOOR:oak@south", True) == "TRAPDOOR:oak@south;open=true"
    assert (
        with_trapdoor_open("TRAPDOOR:oak@south;open=true", False) == "TRAPDOOR:oak@south;open=false"
    )
    assert with_trapdoor_open("COBBLESTONE", True) == "COBBLESTONE"
