from helpers.structure_tokens import (
    ParsedToken,
    format_structure_token,
    parse_structure_token,
)


def test_empty_cell_returns_none():
    assert parse_structure_token(".") is None


def test_simple_token():
    assert parse_structure_token("COBBLESTONE") == ParsedToken(token="COBBLESTONE")


def test_material():
    assert parse_structure_token("PLANKS:oak") == ParsedToken(token="PLANKS", material="oak")


def test_direction():
    assert parse_structure_token("DOOR:oak@north") == ParsedToken(
        token="DOOR",
        material="oak",
        direction="north",
    )


def test_variant():
    assert parse_structure_token("COBBLESTONE#mossy") == ParsedToken(
        token="COBBLESTONE",
        variant="mossy",
    )


def test_full_token_with_rotation():
    assert parse_structure_token("STAIRS:oak@north#outer_left!-90") == ParsedToken(
        token="STAIRS",
        material="oak",
        direction="north",
        variant="outer_left",
        rotation=-90,
    )


def test_bed_color_direction_and_part():
    assert parse_structure_token("BED:black@north#head") == ParsedToken(
        token="BED",
        material="black",
        direction="north",
        variant="head",
    )


def test_block_states_suffix():
    assert parse_structure_token("LANTERN#soul;hanging=false") == ParsedToken(
        token="LANTERN",
        variant="soul",
        states=(("hanging", False),),
    )


def test_format_structure_token_round_trip():
    parsed = parse_structure_token("LANTERN#soul;hanging=true!90")

    assert format_structure_token(parsed) == "LANTERN#soul;hanging=true!90"


def test_trapdoor_open_state_suffix():
    assert parse_structure_token("TRAPDOOR:oak@north;open=true") == ParsedToken(
        token="TRAPDOOR",
        material="oak",
        direction="north",
        states=(("open", True),),
    )

    parsed = parse_structure_token("TRAPDOOR:oak@north#top;open=true!90")
    assert format_structure_token(parsed) == "TRAPDOOR:oak@north#top;open=true!90"
