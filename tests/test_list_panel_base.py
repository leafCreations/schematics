"""Tests for ui.widgets.list_panel_base."""

import pytest
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

from ui.widgets.list_panel_base import (
    CrudTooltips,
    ReorderTooltips,
    add_reorder_row,
    make_crud_panel_buttons,
    make_reorder_panel_buttons,
)


@pytest.fixture(scope="module")
def qapp():
    application = QApplication.instance() or QApplication([])
    yield application


def test_make_crud_panel_buttons_returns_five_buttons(qapp):
    clicks: list[str] = []
    tooltips = CrudTooltips(
        add="add",
        edit="edit",
        delete="delete",
        copy="copy",
        paste="paste",
    )
    buttons = make_crud_panel_buttons(
        add_clicked=lambda: clicks.append("add"),
        edit_clicked=lambda: clicks.append("edit"),
        delete_clicked=lambda: clicks.append("delete"),
        copy_clicked=lambda: clicks.append("copy"),
        paste_clicked=lambda: clicks.append("paste"),
        tooltips=tooltips,
        icon_px=18,
    )
    assert len(buttons.header_widgets()) == 5
    assert buttons.add.toolTip() == "add"

    buttons.copy.click()
    assert clicks == ["copy"]


def test_add_reorder_row_adds_two_buttons(qapp):
    host = QWidget()
    layout = QVBoxLayout(host)
    reorder = make_reorder_panel_buttons(
        up_clicked=lambda: None,
        down_clicked=lambda: None,
        tooltips=ReorderTooltips(up="up", down="down"),
        icon_px=18,
    )
    add_reorder_row(layout, reorder)
    assert layout.count() == 1
