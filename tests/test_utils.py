import helpers.utils as utils


def test_normalize_direction_aliases():
    assert utils.normalize_direction("north") == "N"
    assert utils.normalize_direction("EAST") == "E"
    assert utils.normalize_direction("s") == "S"
    assert utils.normalize_direction("W") == "W"


def test_normalize_direction_none_and_unknown():
    assert utils.normalize_direction(None) is None
    assert utils.normalize_direction("up") is None


def _directional_feature_center(texture, direction: str | None) -> tuple[float, float]:
    rotated = utils.rotate_directional_texture(texture, direction)
    width, height = rotated.size
    points = [
        (x, y) for y in range(height) for x in range(width) if rotated.getpixel((x, y))[3] > 128
    ]

    return (
        sum(point[0] for point in points) / len(points),
        sum(point[1] for point in points) / len(points),
    )


def test_rotate_directional_texture_maps_cardinal_facings():
    from PIL import Image

    texture = Image.new("RGBA", (30, 30), (0, 0, 0, 0))
    for x in range(8, 22):
        texture.putpixel((x, 0), (255, 0, 0, 255))

    north_x, north_y = _directional_feature_center(texture, "N")
    east_x, east_y = _directional_feature_center(texture, "E")
    south_x, south_y = _directional_feature_center(texture, "S")
    west_x, west_y = _directional_feature_center(texture, "W")

    assert north_y < south_y
    assert west_x < east_x
    assert north_y < east_y
    assert west_x < south_y
