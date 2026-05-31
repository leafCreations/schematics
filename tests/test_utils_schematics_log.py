from pathlib import Path

import pytest
from PIL import Image

from helpers import constants
from helpers.sprite_baker.compose_log import compose_log
from helpers.utils_schematics import paste_topdown_token


@pytest.mark.requires_assets
def test_paste_log_uses_material_and_orientation_keys():
    textures = {
        "LOG:oak": compose_log(
            key="LOG:oak",
            view="top",
            size=constants.BLOCK_PX,
            textures_dir=Path("assets/textures/block"),
        ),
        "LOG:oak#east_west": compose_log(
            key="LOG:oak#east_west",
            view="top",
            size=constants.BLOCK_PX,
            textures_dir=Path("assets/textures/block"),
        ),
    }

    vertical_canvas = Image.new("RGBA", (constants.BLOCK_PX, constants.BLOCK_PX), (0, 0, 0, 0))
    horizontal_canvas = Image.new("RGBA", (constants.BLOCK_PX, constants.BLOCK_PX), (0, 0, 0, 0))

    assert paste_topdown_token(
        vertical_canvas, textures, "LOG:oak", (0, 0), size=constants.BLOCK_PX
    )
    assert paste_topdown_token(
        horizontal_canvas,
        textures,
        "LOG:oak@east",
        (0, 0),
        size=constants.BLOCK_PX,
    )

    assert vertical_canvas.tobytes() != horizontal_canvas.tobytes()
