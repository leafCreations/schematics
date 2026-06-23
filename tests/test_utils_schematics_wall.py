from pathlib import Path

from helpers import constants
from helpers.sprite_baker.compose_wall import compose_wall
from helpers.utils_schematics import paste_topdown_token


def test_paste_wall_uses_neighbor_connections(tmp_path: Path):
    textures_dir = tmp_path / "textures"
    textures_dir.mkdir()
    from PIL import Image

    Image.new("RGBA", (16, 16), (200, 100, 50, 255)).save(textures_dir / "cobblestone.png")

    post = compose_wall(
        key="WALL:cobblestone#post",
        view="top",
        size=constants.BLOCK_PX,
        textures_dir=textures_dir,
    )
    cross = compose_wall(
        key="WALL:cobblestone#cross",
        view="top",
        size=constants.BLOCK_PX,
        textures_dir=textures_dir,
    )

    textures = {
        "WALL:cobblestone#post": post,
        "WALL:cobblestone#cross": cross,
    }
    layer_cells = [
        [".", "WALL:cobblestone", "."],
        ["WALL:cobblestone", "WALL:cobblestone", "WALL:cobblestone"],
        [".", "WALL:cobblestone", "."],
    ]

    isolated = Image.new("RGBA", (constants.BLOCK_PX, constants.BLOCK_PX), (0, 0, 0, 0))
    connected = Image.new("RGBA", (constants.BLOCK_PX, constants.BLOCK_PX), (0, 0, 0, 0))

    paste_topdown_token(
        isolated,
        textures,
        "WALL:cobblestone",
        (0, 0),
        constants.BLOCK_PX,
        layer_cells=layer_cells,
        cell_x=0,
        cell_z=0,
    )
    paste_topdown_token(
        connected,
        textures,
        "WALL:cobblestone",
        (0, 0),
        constants.BLOCK_PX,
        layer_cells=layer_cells,
        cell_x=1,
        cell_z=1,
    )

    assert isolated.getpixel((0, 2)) == (0, 0, 0, 0)
    assert connected.getpixel((0, 2)) != (0, 0, 0, 0)
