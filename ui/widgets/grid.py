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

from helpers.block_picker import cell_positions_with_same_block_type
from helpers.cell_clipboard import copy_region
from helpers.grid_brush import (
    PaintBrushMode,
    rect_cell_indices,
    region_cell_indices,
    square_cell_indices,
)
from helpers.grid_labels import column_axis_label, row_axis_label
from ui.selector_mode import SelectorMode
from ui.texture_cache import DEFAULT_ICON_SIZE, GridTextureCache

_GRID_BACKGROUND = QColor(234, 234, 255)
_GRID_LINE = QColor(160, 164, 170)
_EMPTY_CELL_FILL = QColor(235, 235, 235)
_CELL_FILL = QColor(242, 244, 248)
_ACTIVE_CELL_FILL = QColor(220, 220, 220)
_SELECTED_FILL = QColor(210, 230, 255)
_ERASER_PREVIEW_OVERLAY = QColor(255, 120, 120, 140)
_SELECTOR_OVERLAY = QColor(120, 180, 255, 140)
_MOVE_SELECT_OVERLAY = QColor(100, 160, 255, 150)
_MOVE_PREVIEW_OVERLAY = QColor(255, 200, 80, 160)
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
        is_move_select_overlay = False
        is_move_preview_overlay = False
        is_move_source_overlay = False

        if isinstance(table, LayerGridWidget):
            row_idx, col_idx = index.row(), index.column()
            is_move_select_overlay = table.is_move_select_overlay_cell(row_idx, col_idx)
            is_move_preview_overlay = table.is_move_preview_overlay_cell(row_idx, col_idx)
            is_move_source_overlay = table.is_move_source_overlay_cell(row_idx, col_idx)
        is_paint_preview = isinstance(table, LayerGridWidget) and table.is_paint_preview_cell(
            index.row(), index.column()
        )
        is_active_cell = isinstance(table, LayerGridWidget) and table.is_active_cell(
            index.row(), index.column()
        )

        move_overlay = is_move_select_overlay or is_move_preview_overlay or is_move_source_overlay

        if is_selector_overlay or move_overlay or is_paint_preview:
            fill = _EMPTY_CELL_FILL if raw_token == "." else _CELL_FILL
        elif is_active_cell:
            fill = _ACTIVE_CELL_FILL
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
            elif is_move_preview_overlay:
                self._paint_cell_overlay(painter, option.rect, _MOVE_PREVIEW_OVERLAY)
            elif is_move_select_overlay or is_move_source_overlay:
                self._paint_cell_overlay(painter, option.rect, _MOVE_SELECT_OVERLAY)
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
        elif is_move_preview_overlay:
            self._paint_cell_overlay(painter, option.rect, _MOVE_PREVIEW_OVERLAY)
        elif is_move_select_overlay or is_move_source_overlay:
            self._paint_cell_overlay(painter, option.rect, _MOVE_SELECT_OVERLAY)
        elif is_paint_preview:
            self._paint_cell_overlay(painter, option.rect, _PAINT_PREVIEW_OVERLAY)


class LayerGridWidget(QTableWidget):
    cell_selected = Signal(int, int, str)
    cell_erase_requested = Signal(int, int)
    cell_pick_block_requested = Signal(int, int, str)
    cell_erase_matching_requested = Signal(str)
    eraser_region_erase_requested = Signal(int, int, int, int)
    paint_region_fill_requested = Signal(int, int, int, int)
    move_region_requested = Signal(int, int)
    move_selection_empty = Signal()

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
        self._eraser_drag_moved = False
        self._selector_active = False
        self._selector_mode = SelectorMode.RECTANGLE
        self._rectangle_selector_drag_active = False
        self._rectangle_selector_drag_anchor: tuple[int, int] | None = None
        self._selector_overlay_cells: frozenset[tuple[int, int]] = frozenset()
        self._move_active = False
        self._move_select_drag_active = False
        self._move_select_anchor: tuple[int, int] | None = None
        self._move_select_overlay_cells: frozenset[tuple[int, int]] = frozenset()
        self._move_relocate_ready = False
        self._move_relocate_drag_active = False
        self._move_source_positions: frozenset[tuple[int, int]] = frozenset()
        self._move_origin: tuple[int, int] | None = None
        self._move_preview_cells: frozenset[tuple[int, int]] = frozenset()
        self._selection_mode_before_move = QTableWidget.SelectionMode.ExtendedSelection
        self._paint_preview_active = False
        self._paint_drag_active = False
        self._paint_drag_anchor: tuple[int, int] | None = None
        self._paint_preview_cells: frozenset[tuple[int, int]] = frozenset()
        self._paint_brush_mode: PaintBrushMode = "fill"
        self._paint_drag_last_pos = None
        self._paint_drag_moved = False
        self._active_cell: tuple[int, int] | None = None
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.setCornerButtonEnabled(False)
        self._cell_grid_visible = True
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

    def set_cell_grid_visible(self, visible: bool) -> None:
        if visible == self._cell_grid_visible:
            return

        self._cell_grid_visible = visible
        self.setShowGrid(visible)
        self.viewport().update()

    def cell_grid_visible(self) -> bool:
        return self._cell_grid_visible

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
        if active == self._selector_active:
            return

        self._selector_active = active

        if not active:
            self._end_rectangle_selector_drag()
            self.viewport().unsetCursor()
        else:
            self.viewport().setCursor(Qt.CursorShape.CrossCursor)

        self.highlight_selection()
        self.viewport().update()

    def set_selector_mode(self, mode: SelectorMode) -> None:
        if mode == self._selector_mode:
            return

        self._selector_mode = mode
        self._end_rectangle_selector_drag()

    def set_move_active(self, active: bool) -> None:
        if active == self._move_active:
            return

        self._move_active = active

        if active:
            self._selection_mode_before_move = self.selectionMode()
            self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        else:
            self.cancel_move_state()
            self.setSelectionMode(self._selection_mode_before_move)

        self.highlight_selection()
        self.viewport().update()

    def cancel_move_state(self) -> None:
        self._end_move_select_drag()
        self._end_move_relocate_drag()
        self._move_relocate_ready = False
        self._move_source_positions = frozenset()
        self._move_origin = None
        self.clearSelection()
        self.viewport().update()

    def move_relocate_pending(self) -> bool:
        return self._move_relocate_ready

    def pending_move_positions(self) -> list[tuple[int, int]]:
        return sorted(self._move_source_positions)

    def clear_move_pending(self) -> None:
        self._move_relocate_ready = False
        self._move_source_positions = frozenset()
        self._move_origin = None
        self._move_preview_cells = frozenset()
        self.clearSelection()
        self.viewport().update()

    def is_move_select_overlay_cell(self, row: int, col: int) -> bool:
        return self._move_active and (row, col) in self._move_select_overlay_cells

    def is_move_preview_overlay_cell(self, row: int, col: int) -> bool:
        return self._move_active and (row, col) in self._move_preview_cells

    def is_move_source_overlay_cell(self, row: int, col: int) -> bool:
        return (
            self._move_active
            and self._move_relocate_ready
            and not self._move_relocate_drag_active
            and (row, col) in self._move_source_positions
        )

    def is_selector_overlay_cell(self, row: int, col: int) -> bool:
        if not self._selector_active:
            return False

        if (row, col) in self._selector_overlay_cells:
            return True

        if self._rectangle_selector_drag_active:
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

    def _index_at_viewport_pos(self, pos):
        return self.indexAt(pos)

    def _end_paint_drag(self) -> None:
        self._paint_drag_active = False
        self._paint_drag_anchor = None
        self._paint_drag_last_pos = None
        self._paint_drag_moved = False
        self._paint_preview_cells = frozenset()
        self.viewport().update()

    def _update_paint_drag_overlay(
        self,
        pos,
        *,
        end_cell: tuple[int, int] | None = None,
    ) -> None:
        if not self._paint_drag_active or self._paint_drag_anchor is None:
            return

        self._paint_drag_last_pos = pos
        rows = self.rowCount()
        cols = self.columnCount()
        anchor_row, anchor_col = self._paint_drag_anchor

        if rows == 0 or cols == 0:
            self._paint_preview_cells = frozenset()
        elif end_cell is not None:
            end_row, end_col = end_cell
            self._paint_preview_cells = frozenset(
                region_cell_indices(
                    anchor_row,
                    anchor_col,
                    end_row,
                    end_col,
                    rows=rows,
                    cols=cols,
                    mode=self._paint_brush_mode,
                )
            )
        else:
            index = self._index_at_viewport_pos(pos)

            if not index.isValid():
                self._paint_preview_cells = frozenset()
            else:
                end_row, end_col = index.row(), index.column()

                if (end_row, end_col) != (anchor_row, anchor_col):
                    self._paint_drag_moved = True

                self._paint_preview_cells = frozenset(
                    region_cell_indices(
                        anchor_row,
                        anchor_col,
                        end_row,
                        end_col,
                        rows=rows,
                        cols=cols,
                        mode=self._paint_brush_mode,
                    )
                )

        self.viewport().update()

    def _paint_drag_end_cell(self, pos) -> tuple[int, int]:
        assert self._paint_drag_anchor is not None
        anchor_row, anchor_col = self._paint_drag_anchor

        if not self._paint_drag_moved:
            return anchor_row, anchor_col

        index = self._index_at_viewport_pos(pos)

        if index.isValid():
            return index.row(), index.column()

        return anchor_row, anchor_col

    def _emit_paint_region_fill(self, row_a: int, col_a: int, row_b: int, col_b: int) -> None:
        self.paint_region_fill_requested.emit(row_a, col_a, row_b, col_b)

    def _finish_paint_drag(self, pos) -> None:
        if not self._paint_drag_active or self._paint_drag_anchor is None:
            self._end_paint_drag()
            return

        anchor_row, anchor_col = self._paint_drag_anchor
        end_row, end_col = self._paint_drag_end_cell(pos)

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
        self._eraser_drag_moved = False
        self._eraser_preview_cells = frozenset()
        self._refresh_eraser_preview()
        self.viewport().update()

    def _update_eraser_drag_overlay(
        self,
        pos,
        *,
        end_cell: tuple[int, int] | None = None,
    ) -> None:
        if not self._eraser_drag_active or self._eraser_drag_anchor is None:
            return

        rows = self.rowCount()
        cols = self.columnCount()
        anchor_row, anchor_col = self._eraser_drag_anchor

        if rows == 0 or cols == 0:
            self._eraser_preview_cells = frozenset()
        elif end_cell is not None:
            end_row, end_col = end_cell
            self._eraser_preview_cells = frozenset(
                rect_cell_indices(
                    anchor_row,
                    anchor_col,
                    end_row,
                    end_col,
                    rows=rows,
                    cols=cols,
                )
            )
        else:
            index = self._index_at_viewport_pos(pos)

            if not index.isValid():
                self._eraser_preview_cells = frozenset()
            else:
                end_row, end_col = index.row(), index.column()

                if (end_row, end_col) != (anchor_row, anchor_col):
                    self._eraser_drag_moved = True

                self._eraser_preview_cells = frozenset(
                    rect_cell_indices(
                        anchor_row,
                        anchor_col,
                        end_row,
                        end_col,
                        rows=rows,
                        cols=cols,
                    )
                )

        self.viewport().update()

    def _eraser_drag_end_cell(self, pos) -> tuple[int, int]:
        assert self._eraser_drag_anchor is not None
        anchor_row, anchor_col = self._eraser_drag_anchor

        if not self._eraser_drag_moved:
            return anchor_row, anchor_col

        index = self._index_at_viewport_pos(pos)

        if index.isValid():
            return index.row(), index.column()

        return anchor_row, anchor_col

    def _emit_eraser_region_erase(self, row_a: int, col_a: int, row_b: int, col_b: int) -> None:
        self.eraser_region_erase_requested.emit(row_a, col_a, row_b, col_b)

    def _finish_eraser_drag(self, pos) -> None:
        if not self._eraser_drag_active or self._eraser_drag_anchor is None:
            self._end_eraser_drag()
            return

        anchor_row, anchor_col = self._eraser_drag_anchor
        end_row, end_col = self._eraser_drag_end_cell(pos)

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

    def _end_rectangle_selector_drag(self) -> None:
        self._rectangle_selector_drag_active = False
        self._rectangle_selector_drag_anchor = None
        self._selector_overlay_cells = frozenset()
        self.viewport().update()

    def select_cell_positions(self, positions: list[tuple[int, int]]) -> None:
        self._apply_rect_selection(positions)

    def clear_cell_selection(self) -> None:
        self._end_rectangle_selector_drag()
        self.clearSelection()

    def _apply_rect_selection(self, positions: list[tuple[int, int]]) -> None:
        self.blockSignals(True)
        self.clearSelection()

        for row, col in positions:
            item = self.item(row, col)

            if item is not None:
                item.setSelected(True)

        self.blockSignals(False)
        self.itemSelectionChanged.emit()

    def _handle_selector_left_press(self, row: int, col: int, viewport_pos) -> None:
        if self._selector_mode is SelectorMode.SAME_BLOCK:
            self._select_same_block_type_at(row, col)
            return

        self._begin_rectangle_selector_drag(row, col, viewport_pos)

    def _select_same_block_type_at(self, row: int, col: int) -> None:
        if row >= len(self._layer_cells):
            return

        line = self._layer_cells[row]

        if col >= len(line):
            return

        token = line[col]
        positions = cell_positions_with_same_block_type(self._layer_cells, token)

        if not positions:
            self.clear_cell_selection()
            self.itemSelectionChanged.emit()
            return

        self.select_cell_positions(positions)

    def _begin_rectangle_selector_drag(self, row: int, col: int, viewport_pos) -> None:
        self._rectangle_selector_drag_anchor = (row, col)
        self._rectangle_selector_drag_active = True
        self._update_rectangle_selector_overlay(viewport_pos)

    def _finish_rectangle_selector_drag(self, pos) -> None:
        if not self._rectangle_selector_drag_active or self._rectangle_selector_drag_anchor is None:
            self._end_rectangle_selector_drag()
            return

        self._update_rectangle_selector_overlay(pos)
        positions = sorted(self._selector_overlay_cells)
        self._end_rectangle_selector_drag()

        if positions:
            self._apply_rect_selection(positions)
        else:
            self.clearSelection()
            self.itemSelectionChanged.emit()

    def _end_move_select_drag(self) -> None:
        self._move_select_drag_active = False
        self._move_select_anchor = None
        self._move_select_overlay_cells = frozenset()
        self.viewport().update()

    def _end_move_relocate_drag(self) -> None:
        self._move_relocate_drag_active = False
        self._move_preview_cells = frozenset()
        self.viewport().update()

    def _update_move_select_overlay(self, pos) -> None:
        if not self._move_select_drag_active or self._move_select_anchor is None:
            return

        index = self.indexAt(pos)
        rows = self.rowCount()
        cols = self.columnCount()

        if not index.isValid() or rows == 0 or cols == 0:
            self._move_select_overlay_cells = frozenset()
        else:
            anchor_row, anchor_col = self._move_select_anchor
            self._move_select_overlay_cells = frozenset(
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

    def _finish_move_select_drag(self, pos) -> None:
        if not self._move_select_drag_active or self._move_select_anchor is None:
            self._end_move_select_drag()
            return

        self._update_move_select_overlay(pos)
        positions = sorted(self._move_select_overlay_cells)
        self._end_move_select_drag()

        if not positions:
            return

        clipboard = copy_region(self._layer_cells, positions)

        if clipboard is None or not any(token != "." for row in clipboard.cells for token in row):
            self.move_selection_empty.emit()
            return

        self._move_source_positions = frozenset(positions)
        self._move_origin = min(positions)
        self._move_relocate_ready = True
        self.clearSelection()
        self.viewport().update()

    def _begin_move_left_press(self, row: int, col: int, viewport_pos) -> bool:
        """Start a move select or relocate drag; return True if handled."""
        if self._move_relocate_ready:
            self._move_relocate_drag_active = True
            self._update_move_relocate_preview(viewport_pos)
            return True

        self._move_select_anchor = (row, col)
        self._move_select_drag_active = True
        self._update_move_select_overlay(viewport_pos)
        return True

    def _update_move_relocate_preview(self, pos) -> None:
        if (
            not self._move_relocate_drag_active
            or self._move_origin is None
            or not self._move_source_positions
        ):
            return

        index = self.indexAt(pos)
        rows = self.rowCount()
        cols = self.columnCount()

        if not index.isValid() or rows == 0 or cols == 0:
            self._move_preview_cells = frozenset()
        else:
            origin_row, origin_col = self._move_origin
            delta_row = index.row() - origin_row
            delta_col = index.column() - origin_col
            preview: set[tuple[int, int]] = set()

            for row, col in self._move_source_positions:
                target_row = row + delta_row
                target_col = col + delta_col

                if 0 <= target_row < rows and 0 <= target_col < cols:
                    preview.add((target_row, target_col))

            self._move_preview_cells = frozenset(preview)

        self.viewport().update()

    def _finish_move_relocate_drag(self, pos) -> None:
        if not self._move_relocate_drag_active or self._move_origin is None:
            self._end_move_relocate_drag()
            return

        self._update_move_relocate_preview(pos)
        index = self.indexAt(pos)

        if index.isValid():
            origin_row, origin_col = self._move_origin
            delta_row = index.row() - origin_row
            delta_col = index.column() - origin_col
            dest_row, dest_col = origin_row + delta_row, origin_col + delta_col
            self.move_region_requested.emit(dest_row, dest_col)

        self._end_move_relocate_drag()

    def _update_rectangle_selector_overlay(self, pos) -> None:
        if not self._rectangle_selector_drag_active or self._rectangle_selector_drag_anchor is None:
            return

        index = self.indexAt(pos)
        rows = self.rowCount()
        cols = self.columnCount()

        if not index.isValid() or rows == 0 or cols == 0:
            self._selector_overlay_cells = frozenset()
        else:
            anchor_row, anchor_col = self._rectangle_selector_drag_anchor
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

        if (
            event.type() == QEvent.Type.MouseButtonPress
            and isinstance(event, QMouseEvent)
            and event.button() == Qt.MouseButton.LeftButton
        ):
            pos = self._viewport_pos(event)
            index = self.indexAt(pos)

            if index.isValid():
                row, col = index.row(), index.column()

                if self._move_active:
                    self._begin_move_left_press(row, col, pos)
                    return True

                if self._selector_active:
                    if event.modifiers() & (
                        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
                    ):
                        return False

                    self._handle_selector_left_press(row, col, pos)
                    return True

        if event.type() == QEvent.Type.MouseMove and isinstance(event, QMouseEvent):
            pos = self._viewport_pos(event)
            self._update_eraser_hover_from_viewport_pos(pos)

            if self._move_select_drag_active and event.buttons() & Qt.MouseButton.LeftButton:
                self._update_move_select_overlay(pos)
            elif self._move_relocate_drag_active and event.buttons() & Qt.MouseButton.LeftButton:
                self._update_move_relocate_preview(pos)
            elif (
                self._rectangle_selector_drag_active and event.buttons() & Qt.MouseButton.LeftButton
            ):
                self._update_rectangle_selector_overlay(pos)
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
            pos = self._viewport_pos(event)

            if self._paint_drag_active:
                self._finish_paint_drag(pos)
                return True

            if self._eraser_drag_active:
                self._finish_eraser_drag(pos)
                return True

            if self._move_select_drag_active:
                self._finish_move_select_drag(pos)
                return True

            if self._move_relocate_drag_active:
                self._finish_move_relocate_drag(pos)
                return True

            if self._rectangle_selector_drag_active:
                self._finish_rectangle_selector_drag(pos)
                return True

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
                if self._move_active:
                    viewport_pos = self._viewport_pos_from_widget_event(event)
                    self._begin_move_left_press(row, col, viewport_pos)
                    event.accept()
                    return

                if self._selector_active:
                    if self._selection_modifier_held(event):
                        super().mousePressEvent(event)
                        return

                    self._handle_selector_left_press(
                        row,
                        col,
                        self._viewport_pos_from_widget_event(event),
                    )
                    event.accept()
                    return

                if self._selection_modifier_held(event):
                    super().mousePressEvent(event)
                    return

                if self._eraser_preview_active:
                    self._eraser_drag_anchor = (row, col)
                    self._eraser_drag_active = True
                    self._eraser_drag_moved = False
                    self._update_eraser_drag_overlay(
                        self._viewport_pos_from_widget_event(event),
                        end_cell=(row, col),
                    )
                    event.accept()
                    return

                if self._paint_preview_active:
                    self._paint_drag_anchor = (row, col)
                    self._paint_drag_active = True
                    self._paint_drag_moved = False
                    self._update_paint_drag_overlay(
                        self._viewport_pos_from_widget_event(event),
                        end_cell=(row, col),
                    )
                    event.accept()
                    return

        super().mousePressEvent(event)

    def is_active_cell(self, row: int, col: int) -> bool:
        return self._active_cell == (row, col)

    def set_active_cell(self, row: int, col: int) -> None:
        if self._active_cell == (row, col):
            return

        self._active_cell = (row, col)
        self._refresh_active_cell_display()

    def clear_active_cell(self) -> None:
        if self._active_cell is None:
            return

        self._active_cell = None
        self._refresh_active_cell_display()

    def active_cell(self) -> tuple[int, int] | None:
        return self._active_cell

    def _refresh_active_cell_display(self) -> None:
        self.highlight_selection()
        self.viewport().update()

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

                if self._selector_active or self._move_active or self._paint_preview_active:
                    fill = _EMPTY_CELL_FILL if raw_token == "." else _CELL_FILL
                elif (row, col) == self._active_cell:
                    fill = _ACTIVE_CELL_FILL
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
