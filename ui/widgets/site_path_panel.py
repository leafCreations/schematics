"""Path brush controls for the site preview."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from helpers.path_strip import (
    DEFAULT_PATH_VARIETY_BLOCKS,
    DEFAULT_PATH_WIDTH,
    DIRT_PATH_BLOCK,
    PATH_VARIETY_OPTIONS,
    TRIM_BLOCK,
    TRIM_BLOCK_OPTIONS,
    PathOrientation,
)


class SitePathPanel(QGroupBox):
    path_brush_toggled = Signal(bool)
    path_eraser_toggled = Signal(bool)
    path_width_changed = Signal(int)
    path_orientation_changed = Signal(str)
    path_blocks_changed = Signal()
    clear_all_paths_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__("Path brush", parent)
        self._block_signals = False
        self._variety_checks: dict[str, QCheckBox] = {}

        self._path_width = QSpinBox()
        self._path_width.setRange(1, 21)
        self._path_width.setSingleStep(2)
        self._path_width.setValue(DEFAULT_PATH_WIDTH)
        self._path_width.setToolTip("Odd widths center the strip on the clicked cell.")
        self._path_width.valueChanged.connect(self._on_path_width_changed)

        self._orientation = QComboBox()
        self._orientation.addItem("Horizontal (row)", "horizontal")
        self._orientation.addItem("Vertical (column)", "vertical")
        self._orientation.setToolTip(
            "Horizontal: east–west strip on the clicked row. "
            "Vertical: north–south strip on the clicked column."
        )
        self._orientation.currentIndexChanged.connect(self._on_orientation_changed)

        self._trim_block = QComboBox()
        for block in TRIM_BLOCK_OPTIONS:
            self._trim_block.addItem(block, block)
        self._trim_block.setCurrentIndex(self._trim_block.findData(TRIM_BLOCK))
        self._trim_block.setToolTip("Block used for path strip trim (outside the path band).")
        self._trim_block.currentIndexChanged.connect(self._on_path_blocks_changed)

        variety_group = QGroupBox("Path variety")
        variety_layout = QVBoxLayout(variety_group)
        variety_layout.addWidget(QLabel(f"Center path is always {DIRT_PATH_BLOCK}. Optional mix:"))

        for block in PATH_VARIETY_OPTIONS:
            checkbox = QCheckBox(block)
            checkbox.setChecked(block in DEFAULT_PATH_VARIETY_BLOCKS)
            checkbox.toggled.connect(self._on_path_blocks_changed)
            self._variety_checks[block] = checkbox
            variety_layout.addWidget(checkbox)

        self._path_brush_button = QPushButton("Path brush")
        self._path_brush_button.setCheckable(True)
        self._path_brush_button.toggled.connect(self._on_path_brush_toggled)

        self._path_eraser_button = QPushButton("Eraser")
        self._path_eraser_button.setCheckable(True)
        self._path_eraser_button.setToolTip(
            "Erase paths — left-click clears the full row or column (see orientation). "
            "Right-click does the same without enabling the eraser."
        )
        self._path_eraser_button.toggled.connect(self._on_path_eraser_toggled)

        self._clear_paths_button = QPushButton("Clear all paths")
        self._clear_paths_button.setToolTip(
            "Remove every painted path and trim block from the site (restores grass)."
        )
        self._clear_paths_button.clicked.connect(self.clear_all_paths_requested.emit)

        form = QFormLayout()
        form.addRow("Path width", self._path_width)
        form.addRow("Orientation", self._orientation)
        form.addRow("Trim block", self._trim_block)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(variety_group)
        layout.addWidget(self._path_brush_button)
        layout.addWidget(self._path_eraser_button)
        layout.addWidget(self._clear_paths_button)

    def set_path_width(self, width: int) -> None:
        odd_width = width if width % 2 == 1 else width + 1
        odd_width = max(1, min(21, odd_width))

        self._block_signals = True
        self._path_width.setValue(odd_width)
        self._block_signals = False

    def path_width(self) -> int:
        return self._path_width.value()

    def path_orientation(self) -> PathOrientation:
        return self._orientation.currentData()

    def set_path_orientation(self, orientation: PathOrientation) -> None:
        index = self._orientation.findData(orientation)
        self._block_signals = True

        if index >= 0:
            self._orientation.setCurrentIndex(index)

        self._block_signals = False

    def trim_block(self) -> str:
        return self._trim_block.currentData()

    def path_variety_blocks(self) -> list[str]:
        return [block for block in PATH_VARIETY_OPTIONS if self._variety_checks[block].isChecked()]

    def set_trim_block(self, block: str) -> None:
        index = self._trim_block.findData(block)
        self._block_signals = True

        if index >= 0:
            self._trim_block.setCurrentIndex(index)

        self._block_signals = False

    def set_path_variety_blocks(self, blocks: list[str]) -> None:
        allowed = set(blocks)
        self._block_signals = True

        for block, checkbox in self._variety_checks.items():
            checkbox.setChecked(block in allowed)

        self._block_signals = False

    def load_path_blocks_from_grid(self, grid: dict) -> None:
        from helpers.path_strip import resolve_path_variety_blocks, resolve_trim_block

        self._block_signals = True
        self.set_trim_block(resolve_trim_block(grid))
        self.set_path_variety_blocks(resolve_path_variety_blocks(grid))
        self._block_signals = False

    def is_path_brush_active(self) -> bool:
        return self._path_brush_button.isChecked()

    def set_path_brush_active(self, active: bool) -> None:
        self._block_signals = True
        self._path_brush_button.setChecked(active)

        if active:
            self._path_eraser_button.setChecked(False)

        self._block_signals = False

    def is_path_eraser_active(self) -> bool:
        return self._path_eraser_button.isChecked()

    def set_path_eraser_active(self, active: bool) -> None:
        self._block_signals = True
        self._path_eraser_button.setChecked(active)

        if active:
            self._path_brush_button.setChecked(False)

        self._block_signals = False

    def _on_path_width_changed(self, value: int) -> None:
        if value % 2 == 0:
            self._block_signals = True
            self._path_width.setValue(value + 1)
            self._block_signals = False
            value += 1

        if self._block_signals:
            return

        self.path_width_changed.emit(value)

    def _on_orientation_changed(self, _index: int) -> None:
        if self._block_signals:
            return

        self.path_orientation_changed.emit(self._orientation.currentData())

    def _on_path_blocks_changed(self, _checked: bool = False) -> None:
        if self._block_signals:
            return

        self.path_blocks_changed.emit()

    def _on_path_brush_toggled(self, active: bool) -> None:
        if self._block_signals:
            return

        if active:
            self.set_path_eraser_active(False)

        self.path_brush_toggled.emit(active)

    def _on_path_eraser_toggled(self, active: bool) -> None:
        if self._block_signals:
            return

        if active:
            self.set_path_brush_active(False)

        self.path_eraser_toggled.emit(active)
