import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QTableWidget

from ui.widgets.grid import measure_table_content_size, sync_table_scroll_and_size

pytest.importorskip("PySide6")


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_measure_table_content_size_includes_headers_and_frame(qapp):
    table = QTableWidget(2, 2)
    table.setRowHeight(0, 20)
    table.setRowHeight(1, 20)
    table.setColumnWidth(0, 30)
    table.setColumnWidth(1, 30)
    table.horizontalHeader().setFixedHeight(18)
    table.verticalHeader().setFixedWidth(24)

    width, height = measure_table_content_size(table)

    assert width >= 24 + 30 + 30
    assert height >= 18 + 20 + 20


def test_sync_table_scroll_and_size_hides_scrollbars_when_grid_fits(qapp):
    table = QTableWidget(3, 3)
    for row in range(3):
        table.setRowHeight(row, 10)
        for col in range(3):
            table.setColumnWidth(col, 10)

    sync_table_scroll_and_size(table, 200, 200)

    assert table.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    assert table.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff


def test_sync_table_scroll_and_size_shows_scrollbars_when_grid_overflows(qapp):
    table = QTableWidget(20, 20)
    for row in range(20):
        table.setRowHeight(row, 20)
        for col in range(20):
            table.setColumnWidth(col, 20)

    sync_table_scroll_and_size(table, 120, 120)

    assert table.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAsNeeded
    assert table.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAsNeeded
