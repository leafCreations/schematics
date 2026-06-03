from helpers.grid import resolve_site_dimensions


def test_resolve_site_dimensions_from_legacy_site_size():
    assert resolve_site_dimensions({"site_size": 30}) == (30, 30)


def test_resolve_site_dimensions_from_width_and_depth():
    assert resolve_site_dimensions({"site_width": 20, "site_depth": 10}) == (20, 10)
