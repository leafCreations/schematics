import pytest

import helpers.constants as constants
from ui.widgets.render_panel import resolve_selected_renders, worldgen_dependencies_available


def test_worldgen_dependencies_available_is_bool():
    assert isinstance(worldgen_dependencies_available(), bool)


def test_resolve_selected_renders_all():
    assert resolve_selected_renders(
        select_all=True,
        checked_by_name={constants.RENDER_TOP_VIEW: False},
    ) == [constants.RENDER_ALL]


def test_resolve_selected_renders_subset():
    assert resolve_selected_renders(
        select_all=False,
        checked_by_name={
            constants.RENDER_TOP_VIEW: True,
            constants.RENDER_ROOF: False,
        },
    ) == [constants.RENDER_TOP_VIEW]


def test_resolve_selected_renders_requires_one():
    with pytest.raises(ValueError, match="at least one"):
        resolve_selected_renders(
            select_all=False,
            checked_by_name={constants.RENDER_TOP_VIEW: False},
        )
