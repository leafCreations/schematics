from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter
from PySide6.QtWidgets import (
    QHeaderView,
    QStyle,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from helpers.grid_brush import (
    PaintBrushMode,
    rect_cell_indices,
    region_cell_indices,
    square_cell_indices,
)
from helpers.grid_labels import column_axis_label, row_axis_label
from ui.texture_cache import DEFAULT_ICON_SIZE, GridTextureCache

_GRID_BACKGROUND = QColor(234, 234, 255)
_GRID_LINE = QColor(160, 164, 170)
_EMPTY_CELL_FILL = QColor(235, 235, 235)
_CELL_FILL = QColor(242, 244, 248)
_SELECTED_FILL = QColor(210, 230, 255)
_ERASER_PREVIEW_OVERLAY = QColor(255, 120, 120, 140)
_SELECTOR_OVERLAY = QColor(120, 180, 255, 140)
_PAINT_PREVIEW_OVERLAY = QColor(200, 240, 160, 150)
_FALLBACK_TEXT = QColor(45, 45, 45)
_HEADER_TEXT = QColor(55, 55, 60)
_HEADER_FILL = QColor(220, 222, 228)
_HEADER_LINE = QColor(160, 164, 170)
_AXIS_HEADER_PX = 22
_MIN_CELL_PX = 6
_MAX_CELL_PX = DEFAULT_ICON_SIZE
_TOKEN_ROLE = 256

_NEIGHBOR_OFFSETS = ((-1, 0), (1, 0), (0, -1), (0, 1))


class LayerGridCellDelegate(QStyledItemDelegate):
    """Paint block icons edge-to-edge; default item view leaves margins and white fill."""

    @staticmethod
    def _paint_cell_overlay(painter: QPainter, rect, color: QColor) -> None:
        painter.save()
        painter.fillRect(rect, color)
        painter.restore()

    def paint(self, painter: QPainter, option, index) -> None:
        table = self.parent()
        item = table.item(index.row(), index.column()) if table is not None else None
        raw_token = item.data(_TOKEN_ROLE) if item is not None else "."
        is_eraser_preview = isinstance(table, LayerGridWidget) and table.is_eraser_preview_cell(
            index.row(), index.column()
        )
        is_selector_overlay = isinstance(table, LayerGridWidget) and table.is_selector_overlay_cell(
            index.row(), index.column()
        )
        is_paint_preview = isinstance(table, LayerGridWidget) and table.is_paint_preview_cell(
            index.row(), index.column()
        )

        if is_selector_overlay or is_paint_preview:
            fill = _EMPTY_CELL_FILL if raw_token == "." else _CELL_FILL
        elif option.state & QStyle.StateFlag.State_Selected:
            fill = _SELECTED_FILL
        elif raw_token == ".":
            fill = _EMPTY_CELL_FILL
        else:
            fill = _CELL_FILL

        painter.fillRect(option.rect, fill)

        if item is None or raw_token == ".":
            if is_eraser_preview:
                self._paint_cell_overlay(painter, option.rect, _ERASER_PREVIEW_OVERLAY)
            elif is_selector_overlay:
                self._paint_cell_overlay(painter, option.rect, _SELECTOR_OVERLAY)
            elif is_paint_preview:
                self._paint_cell_overlay(painter, option.rect, _PAINT_PREVIEW_OVERLAY)
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
        else:
            label = item.text()

            if label:
                painter.setPen(_FALLBACK_TEXT)
                painter.setFont(item.font())
                painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, label)

        if is_eraser_preview:
            self._paint_cell_overlay(painter, option.rect, _ERASER_PREVIEW_OVERLAY)
        elif is_selector_overlay:
            self._paint_cell_overlay(painter, option.rect, _SELECTOR_OVERLAY)
        elif is_paint_preview:
            self._paint_cell_overlay(painter, option.rect, _PAINT_PREVIEW_OVERLAY)


class LayerGridWidget(QTableWidget):
    cell_selected = Signal(int, int, str)
    cell_erase_requested = Signal(int, int)
    cell_pick_block_requested = Signal(int, int, str)
    cell_erase_matching_requested = Signal(str)
    eraser_region_erase_requested = Signal(int, int, int, int)
    paint_region_fill_requested = Signal(int, int, int, int)

    def __init__(self, texture_cache: GridTextureCache | None = None, parent=None) -> None:
        super().__init__(parent)
        self._texture_cache = texture_cache
        self._layer_cells: list[list[str]] = []
        self._cell_px = _MAX_CELL_PX
        self._show_block_tooltips = True
        self._show_axis_labels = True
        self._eraser_preview_active = False
        self._eraser_preview_size = 1
        self._eraser_hover: tuple[int, int] | None = None
        self._eraser_preview_cells: frozenset[tuple[int, int]] = frozenset()
        self._eraser_drag_active = False
        self._eraser_drag_anchor: tuple[int, int] | None = None
        self._selector_active = False
        self._selector_drag_active = False
        self._selector_drag_anchor: tuple[int, int] | None = None
        self._selector_overlay_cells: frozenset[tuple[int, int]] = frozenset()
        self._paint_preview_active = False
        self._paint_drag_active = False
        self._paint_drag_anchor: tuple[int, int] | None = None
        self._paint_preview_cells: frozenset[tuple[int, int]] = frozenset()
        self._paint_brush_mode: PaintBrushMode = "fill"
        self._paint_drag_last_pos = None
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.setCornerButtonEnabled(False)
        self.setShowGrid(True)
        self._configure_axis_headers()
        self.setStyleSheet(
            "QTableWidget {"
            f" background-color: rgb({_GRID_BACKGROUND.red()}, {_GRID_BACKGROUND.green()}, "
            f"{_GRID_BACKGROUND.blue()});"
            f" gridline-color: rgb({_GRID_LINE.red()}, {_GRID_LINE.green()}, {_GRID_LINE.blue()});"
            " }"
            " QTableWidget::item { padding: 0px; margin: 0px; }"
            " QHeaderView::section {"
            f" background-color: rgb({_HEADER_FILL.red()}, {_HEADER_FILL.green()}, "
            f"{_HEADER_FILL.blue()});"
            f" color: rgb({_HEADER_TEXT.red()}, {_HEADER_TEXT.green()}, {_HEADER_TEXT.blue()});"
            f" border: 1px solid rgb({_HEADER_LINE.red()}, {_HEADER_LINE.green()}, "
            f"{_HEADER_LINE.blue()});"
            " padding: 0px;"
            " }"
        )
        self.set_show_axis_labels(True)
        self.setItemDelegate(LayerGridCellDelegate(self))
        self.itemSelectionChanged.connect(self._emit_cell_selection)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.viewport().installEventFilter(self)

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

    def set_show_axis_labels(self, show: bool) -> None:
        if show == self._show_axis_labels:
            return

        self._show_axis_labels = show
        self.horizontalHeader().setVisible(show)
        self.verticalHeader().setVisible(show)
        self._update_fixed_size()
        self.refit_viewport()

    def show_axis_labels(self) -> bool:
        return self._show_axis_labels

    def _configure_axis_headers(self) -> None:
        for header in (self.horizontalHeader(), self.verticalHeader()):
            header.setHighlightSections(False)
            header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
            header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        self.horizontalHeader().setFixedHeight(_AXIS_HEADER_PX)
        self.verticalHeader().setFixedWidth(_AXIS_HEADER_PX)

    def _sync_axis_labels(self) -> None:
        if not self._show_axis_labels:
            return

        for col in range(self.columnCount()):
            item = QTableWidgetItem(column_axis_label(col))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setHorizontalHeaderItem(col, item)

        rows = self.rowCount()

        for row in range(rows):
            item = QTableWidgetItem(row_axis_label(row))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setVerticalHeaderItem(row, item)

        if rows > 0:
            longest = max(row_axis_label(row) for row in range(rows))
            label_w = self.fontMetrics().horizontalAdvance(longest) + 8
            self.verticalHeader().setFixedWidth(max(_AXIS_HEADER_PX, label_w))

    def _axis_label_chrome_size(self) -> tuple[int, int]:
        if not self._show_axis_labels:
            return 0, 0

        return self.verticalHeader().width(), self.horizontalHeader().height()

    def set_paint_brush_active(self, active: bool) -> None:
        self._paint_preview_active = active

        if not active:
            self.cancel_paint_drag()

        self.viewport().update()

    def set_paint_brush_mode(self, mode: PaintBrushMode) -> None:
        self._paint_brush_mode = mode if mode in ("fill", "outline") else "fill"

        if self._paint_drag_active and self._paint_drag_last_pos is not None:
            self._update_paint_drag_overlay(self._paint_drag_last_pos)

    def is_paint_preview_cell(self, row: int, col: int) -> bool:
        return (row, col) in self._paint_preview_cells

    def set_selector_active(self, active: bool) -> None:
        self._selector_active = active

        if not active:
            self._end_selector_drag()

        self.highlight_selection()
        self.viewport().update()

    def is_selector_overlay_cell(self, row: int, col: int) -> bool:
        if not self._selector_active:
            return False

        if (row, col) in self._selector_overlay_cells:
            return True

        if self._selector_drag_active:
            return False

        item = self.item(row, col)

        return item is not None and item.isSelected()

    def set_eraser_preview(self, *, active: bool, size: int = 1) -> None:
        self._eraser_preview_active = active
        self._eraser_preview_size = max(1, size)

        if not active:
            self._eraser_hover = None
            self._eraser_preview_cells = frozenset()

        self._refresh_eraser_preview()

    def is_eraser_preview_cell(self, row: int, col: int) -> bool:
        return (row, col) in self._eraser_preview_cells

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
        self._eraser_hover = None
        self._eraser_preview_cells = frozenset()

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

        self._apply_cell_pixel_size(self._cell_px)
        self._sync_axis_labels()
        self.blockSignals(False)
        self.refit_viewport()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.refit_viewport()

    def fit_to_viewport(self, viewport_width: int, viewport_height: int) -> None:
        cols = self.columnCount()
        rows = self.rowCount()

        if cols == 0 or rows == 0 or viewport_width <= 0 or viewport_height <= 0:
            return

        label_w, label_h = self._axis_label_chrome_size()
        grid_w = max(viewport_width - label_w, 1)
        grid_h = max(viewport_height - label_h, 1)

        cell_px = min(
            max(_MIN_CELL_PX, grid_w // cols),
            max(_MIN_CELL_PX, grid_h // rows),
            _MAX_CELL_PX,
        )

        if cell_px != self._cell_px:
            self._apply_cell_pixel_size(cell_px)
            self._refresh_cell_icons()

        self._update_fixed_size()

    def refit_viewport(self) -> None:
        """Scale cells so the full grid fits the available center panel."""
        host = self.parentWidget()
        margins = 4

        if host is not None and host.width() > margins and host.height() > margins:
            available_w = host.width() - margins
            available_h = host.height() - margins
        else:
            available_w = max(self.width() - margins, 1)
            available_h = max(self.height() - margins, 1)

        self.fit_to_viewport(available_w, available_h)

    def _apply_cell_pixel_size(self, cell_px: int) -> None:
        self._cell_px = cell_px

        if self._texture_cache is not None:
            self._texture_cache.set_icon_size(cell_px)
            self.setIconSize(self._texture_cache.qt_icon_size())

        for row_idx in range(self.rowCount()):
            self.setRowHeight(row_idx, cell_px)

        for col_idx in range(self.columnCount()):
            self.setColumnWidth(col_idx, cell_px)

        if self._show_axis_labels:
            self._sync_axis_labels()

    def _refresh_cell_icons(self) -> None:
        for row_idx, row in enumerate(self._layer_cells):
            for col_idx, raw_token in enumerate(row):
                item = self.item(row_idx, col_idx)

                if item is not None:
                    self._apply_token_to_item(item, raw_token, row_idx, col_idx)

        self.highlight_selection()

    def _update_fixed_size(self) -> None:
        cols = self.columnCount()
        rows = self.rowCount()
        label_w, label_h = self._axis_label_chrome_size()
        width = label_w + max(cols * self._cell_px, 1)
        height = label_h + max(rows * self._cell_px, 1)
        self.setFixedSize(width, height)

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
            item.setBackground(_EMPTY_CELL_FILL)
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

        item.setBackground(_CELL_FILL)

    @staticmethod
    def _empty_icon():
        from PySide6.QtGui import QIcon

        return QIcon()

    def _fallback_label(self, raw_token: str) -> str:
        if len(raw_token) <= 8:
            return raw_token

        return f"{raw_token[:6]}…"

    def _refresh_eraser_preview(self) -> None:
        if (
            not self._eraser_preview_active
            or self._eraser_drag_active
            or self._eraser_hover is None
        ):
            if not self._eraser_drag_active:
                self._eraser_preview_cells = frozenset()
        else:
            row, col = self._eraser_hover
            rows = self.rowCount()
            cols = self.columnCount()
            self._eraser_preview_cells = frozenset(
                square_cell_indices(
                    row,
                    col,
                    self._eraser_preview_size,
                    rows=rows,
                    cols=cols,
                )
            )

        self.viewport().update()

    def _viewport_pos(self, event: QMouseEvent):
        return event.position().toPoint()

    def _viewport_pos_from_widget_event(self, event: QMouseEvent):
        return self.viewport().mapFrom(self, event.pos())

    def _end_paint_drag(self) -> None:
        self._paint_drag_active = False
        self._paint_drag_anchor = None
        self._paint_drag_last_pos = None
        self._paint_preview_cells = frozenset()
        self.viewport().update()

    def _update_paint_drag_overlay(self, pos) -> None:
        if not self._paint_drag_active or self._paint_drag_anchor is None:
            return

        self._paint_drag_last_pos = pos
        index = self.indexAt(pos)
        rows = self.rowCount()
        cols = self.columnCount()

        if not index.isValid() or rows == 0 or cols == 0:
            self._paint_preview_cells = frozenset()
        else:
            anchor_row, anchor_col = self._paint_drag_anchor
            self._paint_preview_cells = frozenset(
                region_cell_indices(
                    anchor_row,
                    anchor_col,
                    index.row(),
                    index.column(),
                    rows=rows,
                    cols=cols,
                    mode=self._paint_brush_mode,
                )
            )

        self.viewport().update()

    def _emit_paint_region_fill(self, row_a: int, col_a: int, row_b: int, col_b: int) -> None:
        self.paint_region_fill_requested.emit(row_a, col_a, row_b, col_b)

    def _finish_paint_drag(self, pos) -> None:
        if not self._paint_drag_active or self._paint_drag_anchor is None:
            self._end_paint_drag()
            return

        anchor_row, anchor_col = self._paint_drag_anchor
        index = self.indexAt(pos)

        if index.isValid():
            end_row, end_col = index.row(), index.column()
        else:
            end_row, end_col = anchor_row, anchor_col

        self._emit_paint_region_fill(anchor_row, anchor_col, end_row, end_col)
        self._end_paint_drag()

    def commit_paint_drag(self) -> None:
        """Fill the current drag region on release outside the grid viewport."""
        if not self._paint_drag_active or self._paint_drag_anchor is None:
            self._end_paint_drag()
            return

        if self._paint_preview_cells:
            rows = [row for row, _col in self._paint_preview_cells]
            cols = [col for _row, col in self._paint_preview_cells]
            self._emit_paint_region_fill(min(rows), min(cols), max(rows), max(cols))
        else:
            anchor_row, anchor_col = self._paint_drag_anchor
            self._emit_paint_region_fill(anchor_row, anchor_col, anchor_row, anchor_col)

        self._end_paint_drag()

    def paint_drag_active(self) -> bool:
        return self._paint_drag_active

    def cancel_paint_drag(self) -> None:
        if not self._paint_drag_active:
            return

        self._end_paint_drag()

    def _end_eraser_drag(self) -> None:
        self._eraser_drag_active = False
        self._eraser_drag_anchor = None
        self._eraser_preview_cells = frozenset()
        self._refresh_eraser_preview()
        self.viewport().update()

    def _update_eraser_drag_overlay(self, pos) -> None:
        if not self._eraser_drag_active or self._eraser_drag_anchor is None:
            return

        index = self.indexAt(pos)
        rows = self.rowCount()
        cols = self.columnCount()

        if not index.isValid() or rows == 0 or cols == 0:
            self._eraser_preview_cells = frozenset()
        else:
            anchor_row, anchor_col = self._eraser_drag_anchor
            self._eraser_preview_cells = frozenset(
                rect_cell_indices(
                    anchor_row,
                    anchor_col,
                    index.row(),
                    index.column(),
                    rows=rows,
                    cols=cols,
                )
            )

        self.viewport().update()

    def _emit_eraser_region_erase(self, row_a: int, col_a: int, row_b: int, col_b: int) -> None:
        self.eraser_region_erase_requested.emit(row_a, col_a, row_b, col_b)

    def _finish_eraser_drag(self, pos) -> None:
        if not self._eraser_drag_active or self._eraser_drag_anchor is None:
            self._end_eraser_drag()
            return

        anchor_row, anchor_col = self._eraser_drag_anchor
        index = self.indexAt(pos)

        if index.isValid():
            end_row, end_col = index.row(), index.column()
        else:
            end_row, end_col = anchor_row, anchor_col

        self._emit_eraser_region_erase(anchor_row, anchor_col, end_row, end_col)
        self._end_eraser_drag()

    def commit_eraser_drag(self) -> None:
        """Erase the current drag region and end the drag (e.g. mouse released outside the grid)."""
        if not self._eraser_drag_active or self._eraser_drag_anchor is None:
            self._end_eraser_drag()
            return

        if self._eraser_preview_cells:
            rows = [row for row, _col in self._eraser_preview_cells]
            cols = [col for _row, col in self._eraser_preview_cells]
            self._emit_eraser_region_erase(min(rows), min(cols), max(rows), max(cols))
        else:
            anchor_row, anchor_col = self._eraser_drag_anchor
            self._emit_eraser_region_erase(anchor_row, anchor_col, anchor_row, anchor_col)

        self._end_eraser_drag()

    def _update_eraser_hover_from_viewport_pos(self, pos) -> None:
        if not self._eraser_preview_active or self._eraser_drag_active:
            return

        index = self.indexAt(pos)
        hover = (index.row(), index.column()) if index.isValid() else None

        if hover == self._eraser_hover:
            return

        self._eraser_hover = hover
        self._refresh_eraser_preview()

    def _end_selector_drag(self) -> None:
        self._selector_drag_active = False
        self._selector_drag_anchor = None
        self._selector_overlay_cells = frozenset()
        self.viewport().update()

    def _update_selector_drag_overlay(self, pos) -> None:
        if not self._selector_drag_active or self._selector_drag_anchor is None:
            return

        index = self.indexAt(pos)
        rows = self.rowCount()
        cols = self.columnCount()

        if not index.isValid() or rows == 0 or cols == 0:
            self._selector_overlay_cells = frozenset()
        else:
            anchor_row, anchor_col = self._selector_drag_anchor
            self._selector_overlay_cells = frozenset(
                rect_cell_indices(
                    anchor_row,
                    anchor_col,
                    index.row(),
                    index.column(),
                    rows=rows,
                    cols=cols,
                )
            )

        self.viewport().update()

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if watched is not self.viewport():
            return super().eventFilter(watched, event)

        if event.type() == QEvent.Type.MouseMove and isinstance(event, QMouseEvent):
            pos = self._viewport_pos(event)
            self._update_eraser_hover_from_viewport_pos(pos)

            if self._selector_drag_active and event.buttons() & Qt.MouseButton.LeftButton:
                self._update_selector_drag_overlay(pos)
            elif self._paint_drag_active and event.buttons() & Qt.MouseButton.LeftButton:
                self._update_paint_drag_overlay(pos)
            elif self._eraser_drag_active and event.buttons() & Qt.MouseButton.LeftButton:
                self._update_eraser_drag_overlay(pos)
        elif event.type() == QEvent.Type.Leave and self._eraser_hover is not None:
            self._eraser_hover = None
            self._refresh_eraser_preview()
        elif (
            event.type() == QEvent.Type.MouseButtonRelease
            and isinstance(event, QMouseEvent)
            and event.button() == Qt.MouseButton.LeftButton
        ):
            if self._paint_drag_active:
                self._finish_paint_drag(pos)
            elif self._eraser_drag_active:
                self._finish_eraser_drag(pos)
            elif self._selector_drag_active:
                self._end_selector_drag()

        return super().eventFilter(watched, event)

    def eraser_drag_active(self) -> bool:
        return self._eraser_drag_active

    def cancel_eraser_drag(self) -> None:
        """Abort a drag without erasing (e.g. tool change while dragging)."""
        if not self._eraser_drag_active:
            return

        self._end_eraser_drag()

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

                if self._eraser_preview_active and raw_token != ".":
                    self.cell_erase_matching_requested.emit(raw_token)
                    event.accept()
                    return

                self.cell_pick_block_requested.emit(row, col, raw_token)
                event.accept()
                return

            if event.button() == Qt.MouseButton.LeftButton:
                if self._selector_active:
                    self._selector_drag_anchor = (row, col)
                    self._selector_drag_active = True
                    self._update_selector_drag_overlay(
                        self._viewport_pos_from_widget_event(event),
                    )
                    super().mousePressEvent(event)
                    return

                if self._selection_modifier_held(event):
                    super().mousePressEvent(event)
                    return

                if self._eraser_preview_active:
                    self._eraser_drag_anchor = (row, col)
                    self._eraser_drag_active = True
                    self._update_eraser_drag_overlay(
                        self._viewport_pos_from_widget_event(event),
                    )
                    event.accept()
                    return

                if self._paint_preview_active:
                    self._paint_drag_anchor = (row, col)
                    self._paint_drag_active = True
                    self._update_paint_drag_overlay(
                        self._viewport_pos_from_widget_event(event),
                    )
                    event.accept()
                    return

        super().mousePressEvent(event)

    def selected_cell_positions(self) -> list[tuple[int, int]]:
        return sorted({(item.row(), item.column()) for item in self.selectedItems()})

    def selection_anchor(self) -> tuple[int, int] | None:
        """Top-left cell of the current selection bounding box."""
        positions = self.selected_cell_positions()

        if not positions:
            return None

        return min(positions)

    def _emit_cell_selection(self) -> None:
        items = self.selectedItems()

        if not items:
            return

        item = items[0]
        raw_token = item.data(_TOKEN_ROLE) or "."

        self.cell_selected.emit(item.row(), item.column(), raw_token)

    @staticmethod
    def _selection_modifier_held(event: QMouseEvent) -> bool:
        return bool(
            event.modifiers()
            & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
        )

    def highlight_selection(self) -> None:
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)

                if item is None:
                    continue

                raw_token = item.data(_TOKEN_ROLE) or "."

                if self._selector_active or self._paint_preview_active:
                    fill = _EMPTY_CELL_FILL if raw_token == "." else _CELL_FILL
                elif item.isSelected():
                    fill = _SELECTED_FILL
                elif raw_token == ".":
                    fill = _EMPTY_CELL_FILL
                else:
                    fill = _CELL_FILL

                item.setBackground(fill)

        self.viewport().update()


class LayerGridViewport(QWidget):
    """Centers the structure grid and refits cell size when the panel is resized."""

    def __init__(self, grid: LayerGridWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._grid = grid

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(grid, alignment=Qt.AlignmentFlag.AlignCenter)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._grid.refit_viewport()
