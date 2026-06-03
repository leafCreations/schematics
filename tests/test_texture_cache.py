from ui.texture_cache import GridTextureCache


def test_invalidate_cell_drops_cached_icons_for_position():
    cache = GridTextureCache(icon_size=16)
    cache._icon_cache[("LANTERN", 1, 2)] = object()  # type: ignore[assignment]
    cache._icon_cache[("LANTERN#soul", 1, 2)] = object()  # type: ignore[assignment]
    cache._icon_cache[("LANTERN", 3, 4)] = object()  # type: ignore[assignment]

    cache.invalidate_cell(1, 2)

    assert ("LANTERN", 1, 2) not in cache._icon_cache
    assert ("LANTERN#soul", 1, 2) not in cache._icon_cache
    assert ("LANTERN", 3, 4) in cache._icon_cache


def test_invalidate_token_drops_all_matching_entries():
    cache = GridTextureCache(icon_size=16)
    cache._icon_cache[("LANTERN#soul", 0, 0)] = object()  # type: ignore[assignment]
    cache._icon_cache[("LANTERN#soul", -1, -1)] = object()  # type: ignore[assignment]
    cache._icon_cache[("LANTERN", 0, 0)] = object()  # type: ignore[assignment]

    cache.invalidate_token("LANTERN#soul")

    assert ("LANTERN#soul", 0, 0) not in cache._icon_cache
    assert ("LANTERN#soul", -1, -1) not in cache._icon_cache
    assert ("LANTERN", 0, 0) in cache._icon_cache
