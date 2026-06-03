import pytest

from helpers.structure_tokens import parse_structure_token
from renderers import worldgen


def test_generate_block_unknown_token_raises_value_error():
    worldgen.BLOCK_CACHE.clear()

    with pytest.raises(ValueError, match="Unknown block token"):
        worldgen.generate_block(parse_structure_token("NOT_A_REAL_TOKEN"))
