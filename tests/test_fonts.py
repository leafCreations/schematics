from helpers import fonts as font_utils


def test_load_fonts_returns_named_fonts():
    loaded = font_utils.load_fonts({"label": (font_utils.DEJAVU_SANS, 12)})

    assert "label" in loaded
    assert loaded["label"] is not None


def test_load_layer_panel_fonts_includes_expected_keys():
    loaded = font_utils.load_layer_panel_fonts()

    assert set(loaded) == {"floor", "layer", "inventory"}


def test_load_materials_fonts_includes_expected_keys():
    loaded = font_utils.load_materials_fonts()

    assert set(loaded) == {"title", "header", "body", "count"}
