from renderers.preview_site_topdown import render_preview_site_topdown
from tests.test_layer_visibility import _minimal_ctx


def test_render_preview_site_topdown_writes_y_level_pngs(tmp_path):
    ctx = _minimal_ctx(
        {"index": 0, "cells": [["STONE"]]},
    )
    ctx.output_schematics_dir = tmp_path

    render_preview_site_topdown(ctx)

    for layer_y in (-1, 0, 1):
        assert (tmp_path / f"Site_topdown_y{layer_y}.png").is_file()
