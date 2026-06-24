from pathlib import Path

import helpers.constants as constants
from ui.render_preview import (
    clear_preview_session_dir,
    direction_from_facade_preview_png,
    list_direction_facade_preview_pngs,
    list_facade_preview_pngs,
    list_gallery_preview_pngs,
    list_group_preview_pngs,
    list_materials_preview_pngs,
    list_preview_pngs,
    list_site_facade_preview_pngs,
    list_site_topdown_preview_pngs,
    preview_floor_groups,
    preview_session_dir,
    primary_preview_png,
    y_index_from_preview_png,
)


def test_preview_session_dir_uses_uuid_segment(tmp_path, monkeypatch):
    monkeypatch.setattr("ui.render_preview.OUTPUT_SCHEMATICS_FOLDER", tmp_path)
    session_id = "f47ac10b-58cc-4372-a567-0e02b2c3d479"

    assert preview_session_dir(session_id) == tmp_path / "_preview" / session_id


def test_clear_preview_session_dir_removes_files(tmp_path: Path):
    session_dir = tmp_path / "_preview" / "session-1"
    session_dir.mkdir(parents=True)
    (session_dir / "Materials_list.png").write_bytes(b"png")
    (session_dir / "Structure_facades_N.png").write_bytes(b"png")

    clear_preview_session_dir(session_dir)

    assert not session_dir.exists()


def test_clear_preview_session_dir_noop_when_missing(tmp_path: Path):
    missing = tmp_path / "_preview" / "missing"

    clear_preview_session_dir(missing)

    assert not missing.exists()


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"png")


def test_preview_floor_groups_excludes_roofs_keeps_defined_empty_groups():
    layers = [
        {"group": "Floor 1", "cells": [["."]]},
        {"group": "Roof", "cells": [["."]]},
    ]
    grid = {"groups": ["Floor 1", "Roof", "Empty Wing"]}

    assert preview_floor_groups(layers, grid) == ["Floor 1", "Empty Wing"]


def test_list_group_preview_pngs_sorts_by_y_index(tmp_path: Path):
    schematics_dir = tmp_path / "output"
    schematics_dir.mkdir()
    _touch(schematics_dir / "Structure_floor_1_y10.png")
    _touch(schematics_dir / "Structure_floor_1_y2.png")
    _touch(schematics_dir / "Structure_floor_1_y5.png")

    paths = list_group_preview_pngs(schematics_dir, "Floor 1")

    assert [y_index_from_preview_png(path) for path in paths] == [2, 5, 10]


def test_list_facade_preview_pngs_orders_directions(tmp_path: Path):
    schematics_dir = tmp_path / "output"
    schematics_dir.mkdir()
    _touch(schematics_dir / "Structure_facades_W.png")
    _touch(schematics_dir / "Structure_facades_N.png")
    _touch(schematics_dir / "Structure_facades_E.png")

    paths = list_facade_preview_pngs(schematics_dir)

    assert [path.name for path in paths] == [
        "Structure_facades_N.png",
        "Structure_facades_W.png",
        "Structure_facades_E.png",
    ]
    assert direction_from_facade_preview_png(paths[0]) == "N"


def test_list_site_facade_preview_pngs_orders_directions(tmp_path: Path):
    schematics_dir = tmp_path / "output"
    schematics_dir.mkdir()
    _touch(schematics_dir / "Site_facades_E.png")
    _touch(schematics_dir / "Site_facades_N.png")
    _touch(schematics_dir / "Site_facades_S.png")

    paths = list_site_facade_preview_pngs(schematics_dir)

    assert [path.name for path in paths] == [
        "Site_facades_N.png",
        "Site_facades_S.png",
        "Site_facades_E.png",
    ]


def test_y_index_from_preview_png_supports_signed_y(tmp_path: Path):
    assert y_index_from_preview_png(tmp_path / "Site_topdown_y-1.png") == -1
    assert y_index_from_preview_png(tmp_path / "Structure_floor_1_y10.png") == 10


def test_list_site_topdown_preview_pngs_orders_by_y(tmp_path: Path):
    schematics_dir = tmp_path / "output"
    schematics_dir.mkdir()
    _touch(schematics_dir / "Site_topdown_y1.png")
    _touch(schematics_dir / "Site_topdown_y-1.png")
    _touch(schematics_dir / "Site_topdown_y0.png")

    paths = list_site_topdown_preview_pngs(schematics_dir)

    assert [y_index_from_preview_png(path) for path in paths] == [-1, 0, 1]


def test_list_gallery_preview_pngs_dispatches_materials(tmp_path: Path):
    schematics_dir = tmp_path / "output"
    schematics_dir.mkdir()
    _touch(schematics_dir / "Materials_list.png")

    assert list_gallery_preview_pngs(schematics_dir, constants.RENDER_MATERIALS) == [
        schematics_dir / "Materials_list.png"
    ]


def test_list_materials_preview_pngs_returns_single_file(tmp_path: Path):
    schematics_dir = tmp_path / "output"
    schematics_dir.mkdir()
    _touch(schematics_dir / "Materials_list.png")

    assert list_materials_preview_pngs(schematics_dir) == [schematics_dir / "Materials_list.png"]


def test_list_gallery_preview_pngs_dispatches_site_top_down(tmp_path: Path):
    schematics_dir = tmp_path / "output"
    schematics_dir.mkdir()
    _touch(schematics_dir / "Site_topdown_y0.png")

    assert list_gallery_preview_pngs(schematics_dir, constants.RENDER_PATH) == [
        schematics_dir / "Site_topdown_y0.png"
    ]


def test_list_direction_facade_preview_pngs_dispatches_by_render(tmp_path: Path):
    schematics_dir = tmp_path / "output"
    schematics_dir.mkdir()
    _touch(schematics_dir / "Structure_facades_N.png")
    _touch(schematics_dir / "Site_facades_N.png")

    assert list_direction_facade_preview_pngs(
        schematics_dir,
        constants.RENDER_STRUCTURE_FACADES,
    ) == [schematics_dir / "Structure_facades_N.png"]
    assert list_direction_facade_preview_pngs(
        schematics_dir,
        constants.RENDER_SITE_FACADES,
    ) == [schematics_dir / "Site_facades_N.png"]


def test_primary_preview_prefers_top_view_floor_blueprint(tmp_path: Path):
    schematics_dir = tmp_path / "output"
    schematics_dir.mkdir()
    _touch(schematics_dir / "Structure_roof.png")
    _touch(schematics_dir / "Structure_floor_1.png")
    _touch(schematics_dir / "residence_structure_facades.png")

    assert primary_preview_png(schematics_dir, [constants.RENDER_ALL]) == (
        schematics_dir / "Structure_floor_1.png"
    )


def test_primary_preview_png_uses_group_per_y_files(tmp_path: Path):
    schematics_dir = tmp_path / "output"
    schematics_dir.mkdir()
    _touch(schematics_dir / "Structure_floor_1_y3.png")
    _touch(schematics_dir / "Structure_floor_1_y1.png")

    assert (
        primary_preview_png(
            schematics_dir,
            [constants.RENDER_TOP_VIEW],
            group_name="Floor 1",
        )
        == schematics_dir / "Structure_floor_1_y1.png"
    )


def test_list_preview_pngs_respects_render_subset(tmp_path: Path):
    schematics_dir = tmp_path / "output"
    schematics_dir.mkdir()
    floor = schematics_dir / "Structure_floor_1.png"
    facades = schematics_dir / "residence_structure_facades.png"
    _touch(floor)
    _touch(facades)

    assert list_preview_pngs(schematics_dir, [constants.RENDER_TOP_VIEW]) == [floor]
    assert list_preview_pngs(schematics_dir, [constants.RENDER_STRUCTURE_FACADES]) == [facades]


def test_primary_preview_falls_back_to_newest_png(tmp_path: Path):
    schematics_dir = tmp_path / "output"
    schematics_dir.mkdir()
    older = schematics_dir / "older.png"
    newer = schematics_dir / "newer.png"
    _touch(older)
    _touch(newer)
    newer.touch()

    assert primary_preview_png(schematics_dir, [constants.RENDER_WORLDGEN]) == newer
