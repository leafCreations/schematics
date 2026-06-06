"""Tests for ui.widgets.visibility_list_row."""

import pytest
from PySide6.QtWidgets import QApplication

from ui.widgets.visibility_list_row import VisibilityListRow


@pytest.fixture(scope="module")
def qapp():
    application = QApplication.instance() or QApplication([])
    yield application


def test_visibility_list_row_without_toggle(qapp):
    row = VisibilityListRow(
        row_key="all",
        label_text="All",
        hidden=False,
        show_visibility=False,
    )
    assert row._visibility_button is None


def test_visibility_list_row_with_toggle(qapp):
    row = VisibilityListRow(
        row_key=3,
        label_text="Y 64: floor",
        hidden=True,
        hidden_tooltip="Show layer",
        visible_tooltip="Hide layer",
    )
    assert row._visibility_button is not None
    assert row._visibility_button.toolTip() == "Show layer"

    row._set_hidden(False)
    assert row._visibility_button.toolTip() == "Hide layer"
