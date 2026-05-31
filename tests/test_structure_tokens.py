from helpers.structure_tokens import ParsedToken, parse_structure_token


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
