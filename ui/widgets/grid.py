from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QTableWidget, QTableWidgetItem

from ui.texture_cache import DEFAULT_ICON_SIZE, GridTextureCache

_EMPTY_FILL = QColor(235, 235, 235)
_SELECTED_FILL = QColor(210, 230, 255)
_GRID_LINE = QColor(214, 214, 214)
_FALLBACK_TEXT = QColor(45, 45, 45)
_CELL_PX = DEFAULT_ICON_SIZE
_TOKEN_ROLE = 256

_NEIGHBOR_OFFSETS = ((-1, 0), (1, 0), (0, -1), (0, 1))


class LayerGridCellDelegate(QStyledItemDelegate):
    """Paint block icons edge-to-edge; default item view leaves margins and white fill."""

    def paint(self, painter: QPainter, option, index) -> None:
        table = self.parent()
        item = table.item(index.row(), index.column()) if table is not None else None
        raw_token = item.data(_TOKEN_ROLE) if item is not None else "."

        fill = _SELECTED_FILL if option.state & QStyle.StateFlag.State_Selected else _EMPTY_FILL
        painter.fillRect(option.rect, fill)

        if item is None or raw_token == ".":
            return

        icon = item.icon()

        if not icon.isNull():
            pixmap = icon.pixmap(table.iconSize())
            scaled = pixmap.scaled(
                option.rect.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
            painter.drawPixmap(option.rect.topLeft(), scaled)
            return

        label = item.text()

        if not label:
            return

        painter.setPen(_FALLBACK_TEXT)
        painter.setFont(item.font())
        painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, label)


class LayerGridWidget(QTableWidget):
    cell_selected = Signal(int, int, str)
    cell_paint_requested = Signal(int, int)
    cell_erase_requested = Signal(int, int)
    cell_pick_block_requested = Signal(int, int, str)

    def __init__(self, texture_cache: GridTextureCache | None = None, parent=None) -> None:
        super().__init__(parent)
        self._texture_cache = texture_cache
        self._layer_cells: list[list[str]] = []
        self._show_block_tooltips = True
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setVisible(False)
        self.setShowGrid(True)
        self.setStyleSheet(
            "QTableWidget {"
            f" gridline-color: rgb({_GRID_LINE.red()}, {_GRID_LINE.green()}, {_GRID_LINE.blue()});"
            " }"
            " QTableWidget::item { padding: 0px; margin: 0px; }"
        )
        self.setItemDelegate(LayerGridCellDelegate(self))
        self.itemSelectionChanged.connect(self._emit_cell_selection)

        if texture_cache is not None:
            self.setIconSize(texture_cache.qt_icon_size())

    def set_texture_cache(self, texture_cache: GridTextureCache) -> None:
        self._texture_cache = texture_cache
        self.setIconSize(texture_cache.qt_icon_size())

    def set_show_block_tooltips(self, show: bool) -> None:
        if show == self._show_block_tooltips:
            return

        self._show_block_tooltips = show
        self._refresh_cell_tooltips()

    def show_block_tooltips(self) -> bool:
        return self._show_block_tooltips

    def _cell_tooltip(self, raw_token: str) -> str:
        if not self._show_block_tooltips or raw_token == ".":
            return ""

        return raw_token

    def _refresh_cell_tooltips(self) -> None:
        for row_idx in range(self.rowCount()):
            for col_idx in range(self.columnCount()):
                item = self.item(row_idx, col_idx)

                if item is None:
                    continue

                raw_token = item.data(_TOKEN_ROLE) or "."

                if raw_token == "." and row_idx < len(self._layer_cells):
                    row = self._layer_cells[row_idx]

                    if col_idx < len(row):
                        raw_token = row[col_idx]

                item.setToolTip(self._cell_tooltip(raw_token))

    def set_layer_cells(self, cells: list[list[str]]) -> None:
        self._layer_cells = cells

        if self._texture_cache is not None:
            self._texture_cache.clear_cache()

        self.blockSignals(True)
        self.clear()
        self.setRowCount(len(cells))
        self.setColumnCount(len(cells[0]) if cells else 0)

        for row_idx, row in enumerate(cells):
            for col_idx, raw_token in enumerate(row):
                item = QTableWidgetItem()
                self._apply_token_to_item(item, raw_token, row_idx, col_idx)
                self.setItem(row_idx, col_idx, item)

            self.setRowHeight(row_idx, _CELL_PX)

        for col_idx in range(self.columnCount()):
            self.setColumnWidth(col_idx, _CELL_PX)

        self.blockSignals(False)

    def update_cell(self, row: int, col: int, raw_token: str) -> None:
        if not self._layer_cells:
            return

        self._layer_cells[row][col] = raw_token

        if self._texture_cache is not None:
            self._texture_cache.invalidate_cell(row, col)

        item = self.item(row, col)

        if item is not None:
            self._apply_token_to_item(item, raw_token, row, col)

        self._refresh_fence_neighbors(row, col)

    def _refresh_fence_neighbors(self, row: int, col: int) -> None:
        for delta_row, delta_col in _NEIGHBOR_OFFSETS:
            neighbor_row = row + delta_row
            neighbor_col = col + delta_col

            if not self._cell_in_bounds(neighbor_row, neighbor_col):
                continue

            raw_token = self._layer_cells[neighbor_row][neighbor_col]

            if not raw_token.startswith("FENCE"):
                continue

            item = self.item(neighbor_row, neighbor_col)

            if item is not None:
                self._apply_token_to_item(item, raw_token, neighbor_row, neighbor_col)

    def _cell_in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rowCount() and 0 <= col < self.columnCount()

    def _apply_token_to_item(
        self,
        item: QTableWidgetItem,
        raw_token: str,
        row: int,
        col: int,
    ) -> None:
        item.setData(_TOKEN_ROLE, raw_token)
        item.setText("")
        item.setIcon(self._empty_icon())
        item.setFont(QFont())
        item.setForeground(_FALLBACK_TEXT)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        if raw_token == ".":
            item.setToolTip("")
            item.setBackground(_EMPTY_FILL)
            return

        icon = (
            self._texture_cache.icon_for_cell(
                raw_token,
                layer_cells=self._layer_cells,
                row=row,
                col=col,
            )
            if self._texture_cache is not None
            else None
        )

        if icon is not None:
            item.setIcon(icon)
            item.setToolTip(self._cell_tooltip(raw_token))
        else:
            item.setText(self._fallback_label(raw_token))
            font = QFont()
            font.setBold(True)
            item.setFont(font)
            item.setToolTip(self._cell_tooltip(raw_token))

        item.setBackground(_EMPTY_FILL)

    @staticmethod
    def _empty_icon():
        from PySide6.QtGui import QIcon

        return QIcon()

    def _fallback_label(self, raw_token: str) -> str:
        if len(raw_token) <= 8:
            return raw_token

        return f"{raw_token[:6]}…"

    def mousePressEvent(self, event: QMouseEvent) -> None:
        item = self.itemAt(event.pos())

        if item is not None:
            row = item.row()
            col = item.column()

            if event.button() == Qt.MouseButton.RightButton:
                self.cell_erase_requested.emit(row, col)
                event.accept()
                return

            raw_token = item.data(_TOKEN_ROLE) or "."

            if event.button() == Qt.MouseButton.MiddleButton:
                self.setCurrentItem(item)
                self.cell_pick_block_requested.emit(row, col, raw_token)
                event.accept()
                return

            if event.button() == Qt.MouseButton.LeftButton:
                self.cell_paint_requested.emit(row, col)

        super().mousePressEvent(event)

    def _emit_cell_selection(self) -> None:
        items = self.selectedItems()

        if not items:
            return

        item = items[0]
        raw_token = item.data(_TOKEN_ROLE) or "."

        self.cell_selected.emit(item.row(), item.column(), raw_token)

    def highlight_selection(self) -> None:
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)

                if item is None:
                    continue

                selected = item.isSelected()
                fill = _SELECTED_FILL if selected else _EMPTY_FILL
                item.setBackground(fill)

        self.viewport().update()
