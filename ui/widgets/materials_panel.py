"""Live materials inventory for the structure editor."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from helpers.types import MaterialsIconList, MaterialsIconTokens, MaterialsList
from ui.materials_icons import MaterialsIconCache

SCOPE_CURRENT_LAYER = "current_layer"
SCOPE_ALL_LAYERS = "all_layers"


class MaterialsPanel(QGroupBox):
    scope_changed = Signal()

    def __init__(self, icon_cache: MaterialsIconCache, parent=None) -> None:
        super().__init__("Materials", parent)
        self._icon_cache = icon_cache
        self._scope_combo = QComboBox()
        self._scope_combo.addItem("Current layer", SCOPE_CURRENT_LAYER)
        self._scope_combo.addItem("All layers", SCOPE_ALL_LAYERS)
        self._scope_combo.currentIndexChanged.connect(self._on_scope_changed)

        self._summary = QLabel("Current layer — no blocks placed")
        self._summary.setWordWrap(True)

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["", "Material", "Count"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 32)
        self._table.setColumnWidth(2, 52)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.addWidget(self._scope_combo)
        layout.addWidget(self._summary)
        layout.addWidget(self._table, stretch=1)

    def shows_all_layers(self) -> bool:
        return self._scope_combo.currentData() == SCOPE_ALL_LAYERS

    def _on_scope_changed(self, _index: int) -> None:
        self.scope_changed.emit()

    def set_inventory(
        self,
        materials: MaterialsList,
        material_icons: MaterialsIconList,
        material_icon_tokens: MaterialsIconTokens,
        *,
        scope_caption: str,
    ) -> None:
        if not materials:
            self._summary.setText(f"{scope_caption} — no blocks placed")
            self._table.setRowCount(0)
            return

        total = sum(count for _, count in materials)
        kinds = len(materials)
        kind_label = "kind" if kinds == 1 else "kinds"
        self._summary.setText(
            f"{scope_caption} — {total} block{'s' if total != 1 else ''} ({kinds} {kind_label})"
        )

        self._table.setRowCount(len(materials))

        for row_idx, (display_name, count) in enumerate(materials):
            parsed = material_icon_tokens.get(display_name)
            icon = self._icon_cache.icon_for(
                display_name,
                material_icons.get(display_name),
                parsed=parsed,
            )

            icon_item = QTableWidgetItem()
            icon_item.setIcon(icon)
            icon_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self._table.setItem(row_idx, 0, icon_item)

            name_item = QTableWidgetItem(display_name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self._table.setItem(row_idx, 1, name_item)

            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            count_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self._table.setItem(row_idx, 2, count_item)

            self._table.setRowHeight(row_idx, 30)
