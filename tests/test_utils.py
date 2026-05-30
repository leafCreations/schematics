import helpers.utils as utils


def test_normalize_direction_aliases():
    assert utils.normalize_direction("north") == "N"
    assert utils.normalize_direction("EAST") == "E"
    assert utils.normalize_direction("s") == "S"
    assert utils.normalize_direction("W") == "W"


def test_normalize_direction_none_and_unknown():
    assert utils.normalize_direction(None) is None
    assert utils.normalize_direction("up") is None
