from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QKeyEvent, QMouseEvent, QPainter
from PySide6.QtWidgets import (
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from helpers.grid_placement import site_cell_in_structure_footprint
from ui.site_cells import SiteDisplayToken
from ui.texture_cache import DEFAULT_ICON_SIZE, GridTextureCache

_SITE_GRASS_FILL = QColor(228, 242, 218)
_STRUCTURE_FILL = QColor(255, 255, 255)
_STRUCTURE_SELECTED_FILL = QColor(220, 235, 255)
_EMPTY_FILL = QColor(235, 235, 235)
_GRID_LINE = QColor(212, 228, 205)
_FALLBACK_TEXT = QColor(45, 45, 45)
_MIN_CELL_PX = 6
_MAX_CELL_PX = DEFAULT_ICON_SIZE + 8
_TOKEN_ROLE = 256
_STRUCTURE_ROLE = 257
_GROUND_OVERLAY_TOKENS = frozenset({"FENCE", "TORCH"})


class SiteGridCellDelegate(QStyledItemDelegate):
    """Paint site cells edge-to-edge; open grass uses faded fill without block texture."""

    def paint(self, painter: QPainter, option, index) -> None:
        table = self.parent()
        item = table.item(index.row(), index.column()) if table is not None else None
        token = item.data(_TOKEN_ROLE) if item is not None else "."
        on_structure = bool(item.data(_STRUCTURE_ROLE)) if item is not None else False

        if item is not None:
            brush = item.background()
            fill = brush.color() if brush.style() != Qt.BrushStyle.NoBrush else _STRUCTURE_FILL
        else:
            fill = _STRUCTURE_FILL

        painter.fillRect(option.rect, fill)

        if item is None or (token == "GRASS" and not on_structure):
            return

        icon = item.icon()

        if icon.isNull():
            label = item.text()

            if not label:
                return

            painter.setPen(_FALLBACK_TEXT)
            painter.setFont(item.font())
            painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, label)
            return

        pixmap = icon.pixmap(table.iconSize())
        scaled = pixmap.scaled(
            option.rect.size(),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        painter.drawPixmap(option.rect.topLeft(), scaled)


class SiteGridWidget(QTableWidget):
    """Site footprint preview with structure overlay and optional path painting."""

    structure_selection_changed = Signal(bool)
    path_paint_requested = Signal(int, int)
    path_erase_requested = Signal(int, int)

    def __init__(self, texture_cache: GridTextureCache | None = None, parent=None) -> None:
        super().__init__(parent)
        self._texture_cache = texture_cache
        self._layer_cells: list[list[str]] = []
        self._display_cells: list[list[SiteDisplayToken]] = []
        self._offset_x = 0
        self._offset_z = 0
        self._structure_width = 0
        self._structure_depth = 0
        self._cell_px = _MAX_CELL_PX
        self._structure_selected = False
        self._path_brush_active = False
        self._path_eraser_active = False
        self._show_block_tooltips = True
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setVisible(False)
        self.setShowGrid(True)
        self.setStyleSheet(
            "QTableWidget {"
            f" gridline-color: rgb({_GRID_LINE.red()}, {_GRID_LINE.green()}, {_GRID_LINE.blue()});"
            " }"
            " QTableWidget::item { padding: 0px; margin: 0px; }"
        )
        self.setItemDelegate(SiteGridCellDelegate(self))

        if texture_cache is not None:
            self.setIconSize(texture_cache.qt_icon_size())

    def set_structure_selected(self, selected: bool) -> None:
        if selected == self._structure_selected:
            return

        self._structure_selected = selected
        self._refresh_structure_highlights()
        self.structure_selection_changed.emit(selected)

    def is_structure_selected(self) -> bool:
        return self._structure_selected

    def set_path_brush_active(self, active: bool) -> None:
        self._path_brush_active = active

        if active:
            self.set_structure_selected(False)
            self._path_eraser_active = False

    def is_path_brush_active(self) -> bool:
        return self._path_brush_active

    def set_path_eraser_active(self, active: bool) -> None:
        self._path_eraser_active = active

        if active:
            self.set_structure_selected(False)
            self._path_brush_active = False

    def is_path_eraser_active(self) -> bool:
        return self._path_eraser_active

    def set_show_block_tooltips(self, show: bool) -> None:
        if show == self._show_block_tooltips:
            return

        self._show_block_tooltips = show
        self._refresh_cell_tooltips()

    def show_block_tooltips(self) -> bool:
        return self._show_block_tooltips

    def set_texture_cache(self, texture_cache: GridTextureCache) -> None:
        self._texture_cache = texture_cache
        self.setIconSize(texture_cache.qt_icon_size())

    def set_site_display(
        self,
        display_cells: list[list[SiteDisplayToken]],
        *,
        layer_cells: list[list[str]],
        offset_x: int,
        offset_z: int,
        structure_width: int,
        structure_depth: int,
    ) -> None:
        self._display_cells = display_cells
        self._layer_cells = layer_cells
        self._offset_x = offset_x
        self._offset_z = offset_z
        self._structure_width = structure_width
        self._structure_depth = structure_depth

        if self._texture_cache is not None:
            self._texture_cache.clear_cache()

        self.blockSignals(True)
        self.clear()
        self.setRowCount(len(display_cells))
        self.setColumnCount(len(display_cells[0]) if display_cells else 0)

        for row_idx, row in enumerate(display_cells):
            for col_idx, token in enumerate(row):
                item = QTableWidgetItem()
                self._apply_display_token(item, token, row_idx, col_idx)
                self.setItem(row_idx, col_idx, item)

        self._apply_cell_pixel_size(self._cell_px)
        self._refresh_structure_highlights()
        self.blockSignals(False)
        self._update_fixed_size()

    def fit_to_viewport(self, viewport_width: int, viewport_height: int) -> None:
        cols = self.columnCount()
        rows = self.rowCount()

        if cols == 0 or rows == 0 or viewport_width <= 0 or viewport_height <= 0:
            return

        cell_px = min(
            max(_MIN_CELL_PX, viewport_width // cols),
            max(_MIN_CELL_PX, viewport_height // rows),
            _MAX_CELL_PX,
        )

        if cell_px != self._cell_px:
            self._apply_cell_pixel_size(cell_px)
            self._refresh_structure_icons()

        self._update_fixed_size()

    def _apply_cell_pixel_size(self, cell_px: int) -> None:
        self._cell_px = cell_px

        if self._texture_cache is not None:
            self._texture_cache.set_icon_size(cell_px)
            self.setIconSize(self._texture_cache.qt_icon_size())

        for row_idx in range(self.rowCount()):
            self.setRowHeight(row_idx, cell_px)

        for col_idx in range(self.columnCount()):
            self.setColumnWidth(col_idx, cell_px)

    def _refresh_structure_icons(self) -> None:
        for row_idx, row in enumerate(self._display_cells):
            for col_idx, token in enumerate(row):
                item = self.item(row_idx, col_idx)

                if item is None:
                    continue

                self._apply_display_token(item, token, row_idx, col_idx)

        self._refresh_structure_highlights()

    def _cell_tooltip(self, token: SiteDisplayToken) -> str:
        if not self._show_block_tooltips or token == ".":
            return ""

        return token

    def _refresh_cell_tooltips(self) -> None:
        for row_idx, row in enumerate(self._display_cells):
            for col_idx, token in enumerate(row):
                item = self.item(row_idx, col_idx)

                if item is not None:
                    item.setToolTip(self._cell_tooltip(token))

    def _refresh_structure_highlights(self) -> None:
        for row_idx, row in enumerate(self._display_cells):
            for col_idx, token in enumerate(row):
                item = self.item(row_idx, col_idx)

                if item is None:
                    continue

                on_structure = bool(item.data(_STRUCTURE_ROLE))

                if self._structure_selected and on_structure:
                    item.setBackground(_STRUCTURE_SELECTED_FILL)
                elif on_structure and token == ".":
                    item.setBackground(_EMPTY_FILL)
                elif on_structure:
                    item.setBackground(_STRUCTURE_FILL)
                elif token == "GRASS" or token in _GROUND_OVERLAY_TOKENS:
                    item.setBackground(_SITE_GRASS_FILL)
                else:
                    item.setBackground(_STRUCTURE_FILL)

    def _update_fixed_size(self) -> None:
        cols = self.columnCount()
        rows = self.rowCount()
        width = max(cols * self._cell_px, 1)
        height = max(rows * self._cell_px, 1)
        self.setFixedSize(width, height)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        item = self.itemAt(event.pos())

        if item is not None and not bool(item.data(_STRUCTURE_ROLE)):
            site_x = item.column()
            site_z = item.row()

            if event.button() == Qt.MouseButton.RightButton:
                self.path_erase_requested.emit(site_x, site_z)
                event.accept()
                return

            if event.button() == Qt.MouseButton.LeftButton:
                if self._path_eraser_active:
                    self.path_erase_requested.emit(site_x, site_z)
                    event.accept()
                    return

                if self._path_brush_active:
                    self.path_paint_requested.emit(site_x, site_z)
                    event.accept()
                    return

        if item is not None and event.button() == Qt.MouseButton.LeftButton:
            on_structure = bool(item.data(_STRUCTURE_ROLE))
            self.set_structure_selected(on_structure)
            event.accept()
            return

        super().mousePressEvent(event)

    def _apply_display_token(
        self,
        item: QTableWidgetItem,
        token: SiteDisplayToken,
        site_row: int,
        site_col: int,
    ) -> None:
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        item.setText("")
        item.setData(_TOKEN_ROLE, token)
        on_structure = self._site_cell_in_footprint(site_row, site_col)
        item.setData(_STRUCTURE_ROLE, on_structure)

        if on_structure:
            if token == ".":
                item.setBackground(_EMPTY_FILL)
                return

            local_x = site_col - self._offset_x
            local_z = site_row - self._offset_z
            icon = (
                self._texture_cache.icon_for_cell(
                    token,
                    layer_cells=self._layer_cells,
                    row=local_z,
                    col=local_x,
                )
                if self._texture_cache is not None and self._layer_cells
                else None
            )
            fill = _STRUCTURE_FILL
        else:
            if token in _GROUND_OVERLAY_TOKENS or token == "GRASS":
                fill = _SITE_GRASS_FILL
            else:
                fill = _STRUCTURE_FILL

            if token == "GRASS":
                item.setBackground(fill)
                item.setToolTip(self._cell_tooltip(token))
                return

            icon = (
                self._texture_cache.icon_for_cell(token)
                if self._texture_cache is not None
                else None
            )

        if icon is not None:
            item.setIcon(icon)
            item.setToolTip(self._cell_tooltip(token))
            item.setBackground(fill)
            return

        item.setText(self._fallback_label(token))
        font = QFont()
        font.setBold(True)
        item.setFont(font)
        item.setToolTip(self._cell_tooltip(token))
        item.setForeground(_FALLBACK_TEXT)
        item.setBackground(fill)

    def _site_cell_in_footprint(self, site_row: int, site_col: int) -> bool:
        return site_cell_in_structure_footprint(
            site_col,
            site_row,
            offset_x=self._offset_x,
            offset_z=self._offset_z,
            structure_width=self._structure_width,
            structure_depth=self._structure_depth,
        )

    @staticmethod
    def _fallback_label(raw_token: str) -> str:
        if len(raw_token) <= 8:
            return raw_token

        return f"{raw_token[:6]}…"


class SiteGridView(QWidget):
    """Centers the site grid, scales cells to fit, and handles structure nudge keys."""

    offset_nudge_requested = Signal(int, int)
    structure_selection_changed = Signal(bool)
    path_paint_requested = Signal(int, int)
    path_erase_requested = Signal(int, int)

    def __init__(self, texture_cache: GridTextureCache | None = None, parent=None) -> None:
        super().__init__(parent)
        self._grid = SiteGridWidget(texture_cache)
        self._grid.structure_selection_changed.connect(self.structure_selection_changed)
        self._grid.path_paint_requested.connect(self.path_paint_requested)
        self._grid.path_erase_requested.connect(self.path_erase_requested)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._grid, alignment=Qt.AlignmentFlag.AlignCenter)
        grass = _SITE_GRASS_FILL
        self.setStyleSheet(
            f"background-color: rgb({grass.red()}, {grass.green()}, {grass.blue()});"
        )

    def grid(self) -> SiteGridWidget:
        return self._grid

    def set_show_block_tooltips(self, show: bool) -> None:
        self._grid.set_show_block_tooltips(show)

    def set_structure_selected(self, selected: bool) -> None:
        self._grid.set_structure_selected(selected)

        if selected:
            self.setFocus()

    def set_path_brush_active(self, active: bool) -> None:
        self._grid.set_path_brush_active(active)

        if active:
            self.setFocus()

    def set_path_eraser_active(self, active: bool) -> None:
        self._grid.set_path_eraser_active(active)

        if active:
            self.setFocus()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._fit_grid()

    def set_site_display(self, *args, **kwargs) -> None:
        self._grid.set_site_display(*args, **kwargs)
        self._fit_grid()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self._grid.is_structure_selected():
            super().keyPressEvent(event)
            return

        key = event.key()
        step = 1

        if key == Qt.Key.Key_Left:
            self.offset_nudge_requested.emit(-step, 0)
            event.accept()
            return

        if key == Qt.Key.Key_Right:
            self.offset_nudge_requested.emit(step, 0)
            event.accept()
            return

        if key == Qt.Key.Key_Up:
            self.offset_nudge_requested.emit(0, -step)
            event.accept()
            return

        if key == Qt.Key.Key_Down:
            self.offset_nudge_requested.emit(0, step)
            event.accept()
            return

        super().keyPressEvent(event)

    def _fit_grid(self) -> None:
        margins = 8
        available_w = max(self.width() - margins, 1)
        available_h = max(self.height() - margins, 1)
        self._grid.fit_to_viewport(available_w, available_h)
