from helpers.fence_adjacency import (
    classify_fence_variant,
    fence_facing_for_connections,
    resolve_fence_connections,
)


def test_classify_fence_variant_shapes():
    assert classify_fence_variant(frozenset()) == "post"
    assert classify_fence_variant(frozenset({"north"})) == "end"
    assert classify_fence_variant(frozenset({"north", "south"})) == "straight"
    assert classify_fence_variant(frozenset({"east", "west"})) == "straight"
    assert classify_fence_variant(frozenset({"north", "east"})) == "corner"
    assert classify_fence_variant(frozenset({"north", "east", "south"})) == "tee"
    assert classify_fence_variant(frozenset({"north", "east", "south", "west"})) == "cross"


def test_fence_facing_for_connections():
    assert fence_facing_for_connections("post", frozenset()) is None
    assert (
        fence_facing_for_connections("cross", frozenset({"north", "east", "south", "west"})) is None
    )
    assert fence_facing_for_connections("end", frozenset({"north"})) is None
    assert fence_facing_for_connections("end", frozenset({"west"})) == "W"
    assert fence_facing_for_connections("straight", frozenset({"east", "west"})) == "E"
    assert fence_facing_for_connections("corner", frozenset({"south", "east"})) == "E"


def test_resolve_fence_connections():
    cells = [
        [".", "FENCE:oak", "."],
        ["FENCE:oak", "FENCE:oak", "FENCE:oak"],
        [".", "FENCE:oak", "."],
    ]

    assert resolve_fence_connections(cells, 1, 1) == frozenset({"north", "east", "south", "west"})
    assert resolve_fence_connections(cells, 0, 1) == frozenset({"east"})
    assert resolve_fence_connections(cells, 1, 0) == frozenset({"south"})


def test_resolve_fence_connections_includes_walls():
    cells = [
        ["WALL:cobblestone", "FENCE:oak"],
        ["FENCE:oak", "WALL:cobblestone"],
    ]

    assert resolve_fence_connections(cells, 0, 0) == frozenset({"east", "south"})
    assert resolve_fence_connections(cells, 1, 1) == frozenset({"north", "west"})
