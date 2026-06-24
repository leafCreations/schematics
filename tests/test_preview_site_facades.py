from renderers.preview_site_facades import render_preview_site_facades
from renderers.structure_facades import FACADE_DIRECTIONS
from tests.test_layer_visibility import _minimal_ctx


def test_render_preview_site_facades_writes_direction_pngs(tmp_path):
    ctx = _minimal_ctx(
        {"index": 0, "cells": [["STONE"]]},
    )
    ctx.output_schematics_dir = tmp_path

    render_preview_site_facades(ctx)

    for direction in FACADE_DIRECTIONS:
        assert (tmp_path / f"Site_facades_{direction}.png").is_file()
