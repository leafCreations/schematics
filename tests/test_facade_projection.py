from helpers import facade_projection


def test_collect_facade_elevations_projects_all_compass_faces():
    grid = [
        ["NW", "N", "NE"],
        ["W", "C", "E"],
        ["SW", "S", "SE"],
    ]

    def get_token(layer_y: int, x: int, z: int) -> str:
        if layer_y != 0:
            return "."
        return grid[z][x]

    elevations = facade_projection.collect_facade_elevations([0], 3, 3, get_token)

    assert elevations["N"][0] == ["NW", "N", "NE"]
    assert elevations["S"][0] == ["SW", "S", "SE"]
    assert elevations["W"][0] == ["NW", "W", "SW"]
    assert elevations["E"][0] == ["NE", "E", "SE"]


def test_collect_facade_elevations_uses_visibility_predicate():
    grid = [
        ["A", "B", "C"],
        ["HIDDEN", "HIDDEN", "HIDDEN"],
        ["HIDDEN", "HIDDEN", "HIDDEN"],
    ]

    def get_token(layer_y: int, x: int, z: int) -> str:
        return grid[z][x]

    def is_visible(token: str) -> bool:
        return token not in {".", "HIDDEN"}

    elevations = facade_projection.collect_facade_elevations(
        [0],
        3,
        3,
        get_token,
        is_visible=is_visible,
    )

    assert elevations["N"][0] == ["A", "B", "C"]
