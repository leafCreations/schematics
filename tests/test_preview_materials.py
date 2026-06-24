from pathlib import Path

from renderers.preview_materials import preview_materials_png_path, render_preview_materials
from tests.test_layer_visibility import _minimal_ctx


def test_preview_materials_png_path():
    assert preview_materials_png_path(Path("/tmp/out")) == Path("/tmp/out/Materials_list.png")


def test_render_preview_materials_writes_materials_list_png(tmp_path):
    ctx = _minimal_ctx(
        {"index": 0, "cells": [["STONE"]]},
    )
    ctx.output_schematics_dir = tmp_path

    render_preview_materials(ctx)

    assert (tmp_path / "Materials_list.png").is_file()
