from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from helpers.block_picker import picker_entry_for_cell
from helpers.grid import resolve_site_dimensions
from helpers.grid_cells import count_cells_trimmed_by_resize, resize_structure_layers
from helpers.grid_placement import (
    clamp_grid_offsets_for_structure,
    nudge_structure_offset,
    site_cell_in_structure_footprint,
    structure_dimensions_from_layers,
    structure_site_size_error,
)
from helpers.path_strip import (
    clear_all_paths,
    erase_path_at_site,
    paint_path_at_site,
    resolve_path_orientation,
    resolve_path_width,
)
from helpers.paths import OUTPUT_SCHEMATICS_FOLDER
from helpers.site_ground import resize_site_ground
from ui.document import (
    StructureDocument,
    open_structure,
    save_layer,
    save_structure_metadata,
)
from ui.editor_history import apply_history_state, capture_history_state
from ui.editor_materials import build_editor_materials_context, structure_material_inventory
from ui.editor_prefs import block_tooltips_enabled, set_block_tooltips_enabled
from ui.materials_icons import MaterialsIconCache
from ui.platform import ensure_qt_platform
from ui.render_worker import RenderJobResult, RenderWorker
from ui.site_cells import build_site_display_grid, site_preview_layer_index, structure_offset
from ui.texture_cache import GridTextureCache
from ui.widgets.grid import LayerGridWidget
from ui.widgets.materials_panel import MaterialsPanel
from ui.widgets.palette_panel import PalettePanel
from ui.widgets.properties_panel import PropertiesPanel
from ui.widgets.render_panel import RenderPanel
from ui.widgets.site_grid import SiteGridView
from ui.widgets.site_nudge_controls import SiteNudgeControls
from ui.widgets.site_path_panel import SitePathPanel
from ui.widgets.site_settings_panel import SiteSettingsPanel
from ui.widgets.structure_size_panel import StructureSizePanel


class MainWindow(QMainWindow):
    def __init__(
        self,
        document: StructureDocument,
        *,
        structure: str,
        stage: int,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._document = document
        self._structure = structure
        self._stage = stage
        self._current_layer_index = 0
        self._dirty_layers: set[int] = set()
        self._dirty_structure = False
        self._eraser_active = False
        self._structure_name = document.metadata.get("name", document.structure_path.stem)

        self._layer_selector = QComboBox()
        self._eraser_button = QPushButton("Eraser")
        self._eraser_button.setCheckable(True)
        self._save_layer_button = QPushButton("Save Layer")
        self._save_site_button = QPushButton("Save Site Settings")
        self._status = QStatusBar()
        self._status.showMessage("Loading block textures...")
        QApplication.processEvents()
        self._grid_texture_cache = GridTextureCache()
        self._structure_grid = LayerGridWidget(self._grid_texture_cache)
        self._site_grid_view = SiteGridView(self._grid_texture_cache)
        self._palette_panel = PalettePanel()
        self._properties_panel = PropertiesPanel()
        self._properties_panel.set_texture_cache(self._grid_texture_cache)
        self._materials_context = build_editor_materials_context()
        self._materials_icon_cache = MaterialsIconCache(self._materials_context)
        self._materials_panel = MaterialsPanel(self._materials_icon_cache)
        self._structure_size_panel = StructureSizePanel()
        self._site_settings_panel = SiteSettingsPanel()
        self._site_path_panel = SitePathPanel()
        self._site_nudge_controls = SiteNudgeControls()
        self._render_panel = RenderPanel()
        self._render_thread: QThread | None = None
        self._render_worker: RenderWorker | None = None
        self._last_schematics_dir: Path | None = None
        self._undo_stack: list = []
        self._redo_stack: list = []
        self._restoring_history = False

        self.setStatusBar(self._status)
        self._init_edit_menu()

        for index, layer in enumerate(document.layers):
            label = layer.get("group") or layer.get("name") or f"Layer {layer.get('index', index)}"
            self._layer_selector.addItem(f"{index}: {label}", index)

        self._layer_selector.currentIndexChanged.connect(self._on_layer_changed)
        self._eraser_button.toggled.connect(self._on_eraser_toggled)
        self._save_layer_button.clicked.connect(self._save_current_layer)
        self._save_site_button.clicked.connect(self._save_site_settings)
        self._site_settings_panel.settings_changed.connect(self._on_site_settings_changed)
        self._site_settings_panel.block_tooltips_changed.connect(self._on_block_tooltips_changed)
        self._structure_size_panel.block_tooltips_changed.connect(self._on_block_tooltips_changed)
        self._apply_block_tooltips_pref(block_tooltips_enabled())
        self._site_grid_view.offset_nudge_requested.connect(self._on_site_offset_nudge)
        self._site_nudge_controls.nudge_requested.connect(self._on_site_offset_nudge)
        self._site_grid_view.structure_selection_changed.connect(
            self._on_site_structure_selection_changed
        )
        self._site_grid_view.path_paint_requested.connect(self._on_site_path_paint)
        self._site_grid_view.path_erase_requested.connect(self._on_site_path_erase)
        self._site_path_panel.path_brush_toggled.connect(self._on_path_brush_toggled)
        self._site_path_panel.path_eraser_toggled.connect(self._on_path_eraser_toggled)
        self._site_path_panel.path_width_changed.connect(self._on_path_width_changed)
        self._site_path_panel.path_orientation_changed.connect(self._on_path_orientation_changed)
        self._site_path_panel.path_blocks_changed.connect(self._on_path_blocks_changed)
        self._site_path_panel.clear_all_paths_requested.connect(self._on_clear_all_paths)
        self._palette_panel.entry_selected.connect(self._on_palette_entry_selected)
        self._properties_panel.brush_changed.connect(self._on_brush_changed)
        self._structure_grid.cell_selected.connect(self._on_grid_cell_selected)
        self._structure_grid.cell_pick_block_requested.connect(self._on_cell_pick_block)
        self._structure_grid.cell_paint_requested.connect(self._on_cell_paint)
        self._structure_grid.cell_erase_requested.connect(self._on_cell_erase)
        self._structure_grid.itemSelectionChanged.connect(self._structure_grid.highlight_selection)
        self._materials_panel.scope_changed.connect(self._refresh_materials_list)
        self._structure_size_panel.resize_requested.connect(self._on_structure_resize_requested)

        palette_column = QWidget()
        palette_column_layout = QVBoxLayout(palette_column)
        palette_column_layout.setContentsMargins(0, 0, 0, 0)
        palette_column_layout.addWidget(self._palette_panel, stretch=1)
        palette_column_layout.addWidget(self._structure_size_panel)

        structure_header = self._build_structure_header()
        structure_center = QWidget()
        structure_center_layout = QVBoxLayout(structure_center)
        structure_center_layout.setContentsMargins(0, 0, 0, 0)
        structure_center_layout.addWidget(structure_header)
        structure_center_layout.addWidget(self._structure_grid, stretch=1)

        self._structure_tools_splitter = QSplitter(Qt.Orientation.Vertical)
        self._structure_tools_splitter.addWidget(self._properties_panel)
        self._structure_tools_splitter.addWidget(self._materials_panel)
        self._structure_tools_splitter.setStretchFactor(0, 0)
        self._structure_tools_splitter.setStretchFactor(1, 1)
        self._structure_tools_splitter.setChildrenCollapsible(False)

        structure_splitter = QSplitter(Qt.Orientation.Horizontal)
        structure_splitter.addWidget(palette_column)
        structure_splitter.addWidget(structure_center)
        structure_splitter.addWidget(self._structure_tools_splitter)
        structure_splitter.setStretchFactor(0, 1)
        structure_splitter.setStretchFactor(1, 3)
        structure_splitter.setStretchFactor(2, 1)

        site_header = self._build_site_header()

        site_center = QWidget()
        site_center_layout = QVBoxLayout(site_center)
        site_center_layout.setContentsMargins(0, 0, 0, 0)
        site_center_layout.addWidget(site_header)
        site_center_layout.addWidget(self._site_grid_view, stretch=1)

        site_splitter = QSplitter(Qt.Orientation.Horizontal)
        site_splitter.addWidget(site_center)
        site_settings_column = QWidget()
        site_settings_layout = QVBoxLayout(site_settings_column)
        site_settings_layout.setContentsMargins(0, 0, 0, 0)
        site_settings_layout.addWidget(self._site_path_panel)
        site_settings_layout.addWidget(self._site_nudge_controls)
        site_settings_layout.addWidget(self._site_settings_panel, stretch=1)

        site_splitter.addWidget(site_settings_column)
        site_splitter.setStretchFactor(0, 4)
        site_splitter.setStretchFactor(1, 1)

        self._tabs = QTabWidget()
        self._tabs.addTab(structure_splitter, "Structure")
        self._tabs.addTab(site_splitter, "Site")
        self._tabs.addTab(self._render_panel, "Render")
        self._tabs.currentChanged.connect(self._on_tab_changed)
        self._render_panel.generate_requested.connect(self._on_generate_renders_requested)
        self._render_panel.open_output_requested.connect(self._open_render_output_folder)

        self.setCentralWidget(self._tabs)

        output_folder = document.metadata.get("output_folder")
        if isinstance(output_folder, str):
            self._render_panel.set_output_hint(output_folder)
            self._last_schematics_dir = OUTPUT_SCHEMATICS_FOLDER / output_folder

        self._site_settings_panel.load_from_metadata(document.metadata, document.layers)
        self._sync_path_panel_from_metadata()
        self._show_layer(0)
        self._sync_structure_size_controls()
        self._refresh_materials_list()
        self._refresh_site_preview()
        self._update_window_title()
        self._update_save_site_button()
        self.resize(1280, 800)
        self._balance_structure_tools_splitter()
        self._status.showMessage(
            "Structure tab: paint cells (Undo supported). Site tab: footprint and placement.",
            6000,
        )
        self._update_undo_actions()

    def _init_edit_menu(self) -> None:
        edit_menu = self.menuBar().addMenu("&Edit")

        self._undo_action = QAction("&Undo", self)
        self._undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self._undo_action.triggered.connect(self._undo_edit)
        edit_menu.addAction(self._undo_action)

        self._redo_action = QAction("&Redo", self)
        self._redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self._redo_action.triggered.connect(self._redo_edit)
        edit_menu.addAction(self._redo_action)

    def _push_undo_snapshot(self) -> None:
        if self._restoring_history:
            return

        self._undo_stack.append(
            capture_history_state(
                self._document,
                dirty_layers=self._dirty_layers,
                dirty_structure=self._dirty_structure,
            )
        )
        self._redo_stack.clear()
        self._update_undo_actions()

    def _discard_last_undo_snapshot(self) -> None:
        if self._undo_stack:
            self._undo_stack.pop()
            self._update_undo_actions()

    def _update_undo_actions(self) -> None:
        self._undo_action.setEnabled(bool(self._undo_stack))
        self._redo_action.setEnabled(bool(self._redo_stack))

    def _undo_edit(self) -> None:
        if not self._undo_stack:
            return

        self._redo_stack.append(
            capture_history_state(
                self._document,
                dirty_layers=self._dirty_layers,
                dirty_structure=self._dirty_structure,
            )
        )
        state = self._undo_stack.pop()
        self._restore_history_state(state)
        self._status.showMessage("Undone.", 2000)

    def _redo_edit(self) -> None:
        if not self._redo_stack:
            return

        self._undo_stack.append(
            capture_history_state(
                self._document,
                dirty_layers=self._dirty_layers,
                dirty_structure=self._dirty_structure,
            )
        )
        state = self._redo_stack.pop()
        self._restore_history_state(state)
        self._status.showMessage("Redone.", 2000)

    def _restore_history_state(self, state) -> None:
        self._restoring_history = True

        try:
            dirty_flag = [self._dirty_structure]
            apply_history_state(
                self._document,
                state,
                dirty_layers=self._dirty_layers,
                dirty_structure_holder=dirty_flag,
            )
            self._dirty_structure = dirty_flag[0]
            self._grid_texture_cache.clear_cache()
            self._show_layer(self._current_layer_index)
            self._site_settings_panel.load_from_metadata(
                self._document.metadata,
                self._document.layers,
            )
            self._site_settings_panel.sync_offsets_from_grid(self._document.metadata)
            self._sync_structure_size_controls()
            self._sync_path_panel_from_metadata()
            self._refresh_site_preview()
            self._refresh_materials_list()
            self._update_save_layer_button()
            self._update_save_site_button()
            self._update_window_title()
        finally:
            self._restoring_history = False
            self._update_undo_actions()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._balance_structure_tools_splitter()

    def _balance_structure_tools_splitter(self) -> None:
        """Give Materials all spare height; Properties stays at content size."""
        splitter = self._structure_tools_splitter
        total = splitter.height()

        if total <= 0:
            return

        props_height = splitter.widget(0).sizeHint().height()
        materials_height = max(total - props_height, 120)
        splitter.setSizes([props_height, materials_height])

    def _build_structure_header(self) -> QWidget:
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.addWidget(QLabel("Layer"))
        layout.addWidget(self._layer_selector, stretch=1)
        layout.addWidget(self._eraser_button)
        layout.addWidget(self._save_layer_button)
        return header

    def _build_site_header(self) -> QWidget:
        header = QWidget()
        layout = QHBoxLayout(header)
        self._site_layer_label = QLabel("")
        layout.addWidget(self._site_layer_label, stretch=1)
        layout.addWidget(self._save_site_button)
        return header

    def _on_tab_changed(self, index: int) -> None:
        if index == 0:
            self._status.showMessage(
                "Paint structure cells — palette and brush on the right.",
                4000,
            )
            self._balance_structure_tools_splitter()
            self._sync_structure_size_controls()
        elif index == 1:
            self._status.showMessage(
                "Click the structure, then arrow keys or nudge buttons to move it.",
                5000,
            )
            self._refresh_site_preview()
            if self._site_path_panel.is_path_brush_active():
                self._site_grid_view.set_path_brush_active(True)
            elif self._site_path_panel.is_path_eraser_active():
                self._site_grid_view.set_path_eraser_active(True)
            else:
                self._site_grid_view.set_structure_selected(True)
        else:
            self._status.showMessage(
                "Choose render types and generate — save layers first so disk matches the editor.",
                6000,
            )

    def _on_palette_entry_selected(self, entry) -> None:
        if self._eraser_active:
            self._eraser_button.setChecked(False)

        self._properties_panel.show_picker_entry(entry)

    def _on_eraser_toggled(self, active: bool) -> None:
        self._eraser_active = active

        if active:
            self._palette_panel.clear_selection()
            self._properties_panel.clear_picker_entry()
            self._status.showMessage("Eraser active — left-click or right-click cells to clear.")
        else:
            self._status.showMessage("Select a palette block to paint.", 3000)

        self._update_window_title()

    def _on_layer_changed(self, index: int) -> None:
        if index < 0:
            return

        if index == self._current_layer_index:
            return

        if not self._confirm_discard_layer_changes(self._current_layer_index):
            self._layer_selector.blockSignals(True)
            self._layer_selector.setCurrentIndex(self._current_layer_index)
            self._layer_selector.blockSignals(False)
            return

        self._show_layer(index)

    def _confirm_discard_layer_changes(self, layer_index: int) -> bool:
        if layer_index not in self._dirty_layers:
            return True

        layer_path = self._document.layer_paths[layer_index].name
        answer = QMessageBox.question(
            self,
            "Unsaved changes",
            f"Save changes to {layer_path} before switching layers?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

        if answer == QMessageBox.StandardButton.Cancel:
            return False

        return not (answer == QMessageBox.StandardButton.Save and not self._save_layer(layer_index))

    def _show_layer(self, index: int) -> None:
        layer = self._document.layers[index]
        self._current_layer_index = index
        self._properties_panel.clear_grid_cell()
        self._structure_grid.set_layer_cells(layer["cells"])
        layer_path = self._document.layer_paths[index]
        self._layer_selector.blockSignals(True)
        self._layer_selector.setCurrentIndex(index)
        self._layer_selector.blockSignals(False)
        self._update_site_layer_label()
        if index == self._site_preview_layer_index():
            self._refresh_site_preview()
        self._update_save_layer_button()
        self._update_window_title()
        self._refresh_materials_list()
        self._sync_structure_size_controls()
        self._status.showMessage(f"Editing {layer_path.name}")

    def _sync_structure_size_controls(self) -> None:
        structure_width, structure_depth = structure_dimensions_from_layers(self._document.layers)
        site_width, site_depth = resolve_site_dimensions(self._document.metadata.get("grid", {}))
        self._structure_size_panel.set_structure_size(structure_width, structure_depth)
        self._structure_size_panel.set_site_limits(site_width, site_depth)

    def _on_structure_resize_requested(self, new_width: int, new_depth: int) -> None:
        site_width, site_depth = resolve_site_dimensions(self._document.metadata.get("grid", {}))
        size_error = structure_site_size_error(
            new_width,
            new_depth,
            site_width,
            site_depth,
        )

        if size_error is not None:
            QMessageBox.warning(self, "Structure size", size_error)
            self._sync_structure_size_controls()
            return

        current_width, current_depth = structure_dimensions_from_layers(self._document.layers)

        if new_width == current_width and new_depth == current_depth:
            self._status.showMessage("Structure size unchanged.", 2500)
            return

        trimmed = sum(
            count_cells_trimmed_by_resize(layer.get("cells", []), new_width, new_depth)
            for layer in self._document.layers
        )

        if trimmed:
            answer = QMessageBox.question(
                self,
                "Shrink structure grid",
                f"Resize to {new_width}×{new_depth} will remove {trimmed} placed block(s) "
                "from the east and south edges. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if answer != QMessageBox.StandardButton.Yes:
                self._sync_structure_size_controls()
                return

        self._push_undo_snapshot()
        resize_structure_layers(self._document.layers, new_width, new_depth)

        grid = self._document.metadata.setdefault("grid", {})
        self._document.metadata["grid"] = clamp_grid_offsets_for_structure(
            grid,
            structure_width=new_width,
            structure_depth=new_depth,
        )
        self._dirty_structure = True

        for layer_index in range(len(self._document.layers)):
            self._mark_layer_dirty(layer_index)

        self._grid_texture_cache.clear_cache()
        self._show_layer(self._current_layer_index)
        self._site_settings_panel.load_from_metadata(
            self._document.metadata,
            self._document.layers,
        )
        self._site_settings_panel.sync_offsets_from_grid(self._document.metadata)
        self._sync_structure_size_controls()
        self._sync_path_panel_from_metadata()
        self._update_save_site_button()
        self._status.showMessage(
            f"Structure grid resized to {new_width}×{new_depth} on all layers.",
            4000,
        )

    def _materials_scope_layers(self) -> list[dict]:
        if self._materials_panel.shows_all_layers():
            return self._document.layers

        return [self._document.layers[self._current_layer_index]]

    def _materials_scope_caption(self) -> str:
        if self._materials_panel.shows_all_layers():
            return "All layers"

        layer = self._document.layers[self._current_layer_index]
        index = self._current_layer_index
        label = layer.get("group") or layer.get("name") or f"Layer {layer.get('index', index)}"
        return label

    def _site_preview_layer_index(self) -> int:
        return site_preview_layer_index(self._document.metadata, len(self._document.layers))

    def _update_site_layer_label(self) -> None:
        index = self._site_preview_layer_index()
        layer = self._document.layers[index]
        label = layer.get("group") or layer.get("name") or f"Layer {layer.get('index', index)}"
        self._site_layer_label.setText(f"Site preview: {label}")

    def _refresh_site_preview(self) -> None:
        index = self._site_preview_layer_index()
        layer = self._document.layers[index]
        display, _width, _depth, offset_x, offset_z = build_site_display_grid(
            self._document.metadata,
            self._document.layers,
            layer["cells"],
            self._document.site_ground,
        )
        structure_width, structure_depth = structure_dimensions_from_layers(
            self._document.layers,
        )
        self._site_grid_view.set_site_display(
            display,
            layer_cells=layer["cells"],
            offset_x=offset_x,
            offset_z=offset_z,
            structure_width=structure_width,
            structure_depth=structure_depth,
        )
        self._update_site_layer_label()

    def _on_grid_cell_selected(self, row: int, col: int, raw_token: str) -> None:
        self._properties_panel.show_grid_cell(row, col, raw_token)
        self._properties_panel.sync_brush_from_cell(raw_token)

    def _on_cell_pick_block(self, row: int, col: int, raw_token: str) -> None:
        """Middle-click: adopt the cell's block into the palette brush."""
        self._properties_panel.show_grid_cell(row, col, raw_token)

        if raw_token == ".":
            return

        if self._eraser_active:
            self._eraser_button.setChecked(False)

        entry = picker_entry_for_cell(raw_token)

        if entry is None:
            return

        self._palette_panel.select_entry(entry)
        self._properties_panel.show_picker_entry(entry, emit_brush=False)
        self._properties_panel.sync_brush_from_cell(raw_token)
        self._properties_panel.brush_changed.emit()

    def _on_brush_changed(self) -> None:
        self._update_window_title()
        token = self._properties_panel.build_placement_token()

        if token is not None:
            self._grid_texture_cache.invalidate_token(token)

        self._apply_brush_to_selected_cell()

    def _apply_brush_to_selected_cell(self) -> None:
        if self._eraser_active:
            return

        selected = self._properties_panel.selected_cell()

        if selected is None:
            return

        token = self._properties_panel.build_placement_token()

        if token is None:
            return

        row, col = selected
        self._set_cell(row, col, token)

    def _on_cell_paint(self, row: int, col: int) -> None:
        if self._eraser_active:
            self._set_cell(row, col, ".")
            return

        token = self._properties_panel.build_placement_token()

        if token is None:
            return

        self._set_cell(row, col, token)

    def _on_cell_erase(self, row: int, col: int) -> None:
        self._set_cell(row, col, ".")

    def _set_cell(self, row: int, col: int, raw_token: str) -> None:
        layer = self._document.layers[self._current_layer_index]
        cells = layer["cells"]

        if cells[row][col] == raw_token:
            return

        self._push_undo_snapshot()
        cells[row][col] = raw_token
        self._structure_grid.update_cell(row, col, raw_token)
        if self._current_layer_index == self._site_preview_layer_index():
            self._refresh_site_preview()
        self._mark_layer_dirty(self._current_layer_index)
        self._properties_panel.show_grid_cell(row, col, raw_token)
        self._refresh_materials_list()

    def _refresh_materials_list(self) -> None:
        self._materials_icon_cache.clear()
        materials, icons, icon_tokens = structure_material_inventory(
            self._materials_scope_layers(),
            self._materials_context,
        )
        self._materials_panel.set_inventory(
            materials,
            icons,
            icon_tokens,
            scope_caption=self._materials_scope_caption(),
        )

    def _mark_layer_dirty(self, layer_index: int) -> None:
        self._dirty_layers.add(layer_index)
        self._update_save_layer_button()
        self._update_window_title()

    def _mark_layer_clean(self, layer_index: int) -> None:
        self._dirty_layers.discard(layer_index)
        self._update_save_layer_button()
        self._update_window_title()

    def _update_save_layer_button(self) -> None:
        suffix = " *" if self._current_layer_index in self._dirty_layers else ""
        self._save_layer_button.setText(f"Save Layer{suffix}")

    def _sync_path_panel_from_metadata(self) -> None:
        grid = self._document.metadata.get("grid", {})
        self._site_path_panel.set_path_width(resolve_path_width(grid))
        self._site_path_panel.set_path_orientation(resolve_path_orientation(grid))
        self._site_path_panel.load_path_blocks_from_grid(grid)

    def _on_path_width_changed(self, width: int) -> None:
        grid = self._document.metadata.setdefault("grid", {})
        grid["path_width"] = width
        self._dirty_structure = True
        self._update_save_site_button()
        self._update_window_title()

    def _on_path_orientation_changed(self, orientation: str) -> None:
        grid = self._document.metadata.setdefault("grid", {})
        grid["path_orientation"] = orientation
        self._dirty_structure = True
        self._update_save_site_button()
        self._update_window_title()

    def _on_path_blocks_changed(self) -> None:
        grid = self._document.metadata.setdefault("grid", {})
        grid["trim_block"] = self._site_path_panel.trim_block()
        grid["path_variety_blocks"] = self._site_path_panel.path_variety_blocks()
        self._dirty_structure = True
        self._update_save_site_button()
        self._update_window_title()

    def _on_path_brush_toggled(self, active: bool) -> None:
        self._site_grid_view.set_path_brush_active(active)

        if active:
            self._site_path_panel.set_path_eraser_active(False)
            self._site_grid_view.set_path_eraser_active(False)
            self._site_nudge_controls.set_enabled(False)
            self._status.showMessage(
                "Path brush — click a site cell to paint a path strip (see orientation).",
                5000,
            )
        elif not self._site_path_panel.is_path_eraser_active():
            self._status.showMessage(
                "Click the structure on the site grid to select and nudge it.",
                4000,
            )

    def _on_path_eraser_toggled(self, active: bool) -> None:
        self._site_grid_view.set_path_eraser_active(active)

        if active:
            self._site_path_panel.set_path_brush_active(False)
            self._site_grid_view.set_path_brush_active(False)
            self._site_nudge_controls.set_enabled(False)
            self._status.showMessage(
                "Path eraser — left-click or right-click to erase the full path row or column.",
                6000,
            )
        elif not self._site_path_panel.is_path_brush_active():
            self._status.showMessage(
                "Click the structure on the site grid to select and nudge it.",
                4000,
            )

    def _on_site_structure_selection_changed(self, selected: bool) -> None:
        self._site_nudge_controls.set_enabled(selected)

        if selected:
            self._site_path_panel.set_path_brush_active(False)
            self._site_path_panel.set_path_eraser_active(False)
            self._site_grid_view.set_path_brush_active(False)
            self._site_grid_view.set_path_eraser_active(False)

    def _site_path_footprint(self) -> dict:
        offset_x, offset_z = structure_offset(self._document.metadata)
        structure_width, structure_depth = structure_dimensions_from_layers(
            self._document.layers,
        )
        return {
            "offset_x": offset_x,
            "offset_z": offset_z,
            "structure_width": structure_width,
            "structure_depth": structure_depth,
        }

    def _on_site_path_paint(self, site_x: int, site_z: int) -> None:
        footprint = self._site_path_footprint()

        if site_cell_in_structure_footprint(site_x, site_z, **footprint):
            self._status.showMessage(
                "Cannot paint path on the structure footprint.",
                4000,
            )
            return

        self._push_undo_snapshot()
        path_width = self._site_path_panel.path_width()
        orientation = self._site_path_panel.path_orientation()
        painted = paint_path_at_site(
            self._document.site_ground,
            site_x,
            site_z,
            path_width,
            orientation=orientation,
            trim_block=self._site_path_panel.trim_block(),
            variety_blocks=self._site_path_panel.path_variety_blocks(),
            **footprint,
        )

        if not painted:
            self._discard_last_undo_snapshot()
            self._status.showMessage(
                "Path strip did not change any site cells.",
                3000,
            )
            return

        grid = self._document.metadata.setdefault("grid", {})
        grid["path_width"] = path_width
        grid["path_orientation"] = orientation
        grid["trim_block"] = self._site_path_panel.trim_block()
        grid["path_variety_blocks"] = self._site_path_panel.path_variety_blocks()
        self._dirty_structure = True
        self._grid_texture_cache.clear_cache()
        self._refresh_site_preview()
        self._update_save_site_button()
        self._update_window_title()

        detail = f"column x={site_x}" if orientation == "vertical" else f"row z={site_z}"

        self._status.showMessage(
            f"Path strip (width {path_width}, {orientation}) painted on {detail}.",
            3000,
        )

    def _on_site_path_erase(self, site_x: int, site_z: int) -> None:
        footprint = self._site_path_footprint()

        if site_cell_in_structure_footprint(site_x, site_z, **footprint):
            self._status.showMessage(
                "Cannot erase path on the structure footprint.",
                4000,
            )
            return

        self._push_undo_snapshot()
        orientation = self._site_path_panel.path_orientation()
        erased = erase_path_at_site(
            self._document.site_ground,
            site_x,
            site_z,
            self._site_path_panel.path_width(),
            orientation=orientation,
            **footprint,
        )

        if not erased:
            self._discard_last_undo_snapshot()
            self._status.showMessage(
                "No path cells to erase on that row or column.",
                3000,
            )
            return

        self._dirty_structure = True
        self._grid_texture_cache.clear_cache()
        self._refresh_site_preview()
        self._update_save_site_button()
        self._update_window_title()

        detail = f"column x={site_x}" if orientation == "vertical" else f"row z={site_z}"

        self._status.showMessage(f"Path erased on {detail}.", 3000)

    def _on_clear_all_paths(self) -> None:
        answer = QMessageBox.question(
            self,
            "Clear all paths",
            "Remove every painted path and trim block from the site?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self._push_undo_snapshot()
        cleared = clear_all_paths(self._document.site_ground)

        if cleared == 0:
            self._discard_last_undo_snapshot()
            self._status.showMessage("No painted paths on the site.", 3000)
            return

        self._dirty_structure = True
        self._grid_texture_cache.clear_cache()
        self._refresh_site_preview()
        self._update_save_site_button()
        self._update_window_title()
        self._status.showMessage(f"Cleared {cleared} path cells.", 4000)

    def _on_site_offset_nudge(self, delta_x: int, delta_z: int) -> None:
        if not self._site_grid_view.grid().is_structure_selected():
            self._status.showMessage("Click the structure on the site grid to nudge it.", 3000)
            return

        grid = self._document.metadata.get("grid", {})
        layer_index = self._site_preview_layer_index()
        structure_width, structure_depth = structure_dimensions_from_layers(
            [self._document.layers[layer_index]],
        )
        updated = nudge_structure_offset(
            grid,
            delta_x=delta_x,
            delta_z=delta_z,
            structure_width=structure_width,
            structure_depth=structure_depth,
        )

        if updated is None:
            self._status.showMessage("Structure cannot move further in that direction.", 2500)
            return

        self._push_undo_snapshot()
        self._document.metadata["grid"] = updated
        self._dirty_structure = True
        self._site_settings_panel.sync_offsets_from_grid(self._document.metadata)
        self._refresh_site_preview()
        self._site_grid_view.set_structure_selected(True)
        self._update_save_site_button()
        self._update_window_title()

    def _apply_block_tooltips_pref(self, enabled: bool) -> None:
        set_block_tooltips_enabled(enabled)
        self._structure_grid.set_show_block_tooltips(enabled)
        self._site_grid_view.set_show_block_tooltips(enabled)
        self._site_settings_panel.set_block_tooltips_enabled(enabled)
        self._structure_size_panel.set_block_tooltips_enabled(enabled)

    def _on_block_tooltips_changed(self, enabled: bool) -> None:
        self._apply_block_tooltips_pref(enabled)

    def _on_site_settings_changed(self) -> None:
        self._push_undo_snapshot()

        if not self._site_settings_panel.apply_to_metadata(self._document.metadata):
            self._discard_last_undo_snapshot()
            self._status.showMessage("Structure is larger than the site grid.", 4000)
            return

        site_width, site_depth = resolve_site_dimensions(self._document.metadata.get("grid", {}))
        self._document.site_ground = resize_site_ground(
            self._document.site_ground,
            site_width,
            site_depth,
        )
        self._dirty_structure = True
        self._grid_texture_cache.clear_cache()
        self._refresh_site_preview()
        self._sync_structure_size_controls()
        self._sync_path_panel_from_metadata()
        self._update_save_site_button()
        self._update_window_title()

    def _update_save_site_button(self) -> None:
        suffix = " *" if self._dirty_structure else ""
        self._save_site_button.setText(f"Save Site Settings{suffix}")

    def _save_site_settings(self) -> bool:
        if not self._site_settings_panel.apply_to_metadata(self._document.metadata):
            QMessageBox.warning(
                self,
                "Site settings",
                "The structure footprint does not fit in the selected site size.",
            )
            return False

        try:
            save_structure_metadata(
                self._document.structure_path,
                self._document.metadata,
                layer_files=self._document.layer_files,
                site_ground=self._document.site_ground,
                document=self._document,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid structure", str(exc))
            return False
        except OSError as exc:
            QMessageBox.critical(self, "Save failed", str(exc))
            return False

        self._dirty_structure = False
        self._update_save_site_button()
        self._update_window_title()
        return True

    def _update_window_title(self) -> None:
        dirty_marker = " *" if self._dirty_layers or self._dirty_structure else ""
        self.setWindowTitle(f"Structure Editor — {self._structure_name}{dirty_marker}")

    def _save_current_layer(self) -> None:
        if self._save_layer(self._current_layer_index):
            path = self._document.layer_paths[self._current_layer_index]
            self._status.showMessage(f"Saved {path.name}", 3000)

    def _save_layer(self, layer_index: int) -> bool:
        layer = self._document.layers[layer_index]
        path = self._document.layer_paths[layer_index]

        try:
            save_layer(path, layer, document=self._document)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid structure", str(exc))
            return False
        except OSError as exc:
            QMessageBox.critical(self, "Save failed", str(exc))
            return False

        self._mark_layer_clean(layer_index)
        return True

    def closeEvent(self, event) -> None:
        if self._render_thread is not None:
            QMessageBox.warning(
                self,
                "Render in progress",
                "Wait for the current render job to finish before closing.",
            )
            event.ignore()
            return

        if self._dirty_layers or self._dirty_structure:
            answer = QMessageBox.question(
                self,
                "Unsaved changes",
                "Save unsaved changes before quitting?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )

            if answer == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return

            if answer == QMessageBox.StandardButton.Save:
                if self._dirty_structure and not self._save_site_settings():
                    event.ignore()
                    return

                for layer_index in sorted(self._dirty_layers):
                    if not self._save_layer(layer_index):
                        event.ignore()
                        return

        event.accept()

    def _on_generate_renders_requested(self, renders: list[str]) -> None:
        if self._render_thread is not None:
            self._status.showMessage("A render is already in progress.", 3000)
            return

        if not self._confirm_render_save():
            return

        self._render_panel.set_busy(True)
        self._status.showMessage("Starting renders…")

        self._render_thread = QThread(self)
        self._render_worker = RenderWorker(
            self._structure,
            self._stage,
            renders,
        )
        self._render_worker.moveToThread(self._render_thread)
        self._render_thread.started.connect(self._render_worker.run)
        self._render_worker.progress.connect(self._on_render_progress)
        self._render_worker.finished.connect(self._on_render_finished)
        self._render_worker.failed.connect(self._on_render_failed)
        self._render_worker.finished.connect(self._render_thread.quit)
        self._render_worker.failed.connect(self._render_thread.quit)
        self._render_thread.finished.connect(self._finish_render_thread)
        self._render_thread.start()

    def _on_render_progress(self, label: str) -> None:
        self._status.showMessage(f"Rendering {label}…")

    def _on_render_finished(self, result: RenderJobResult) -> None:
        self._render_panel.set_busy(False)
        self._last_schematics_dir = result.schematics_dir
        self._status.showMessage(
            f"Renders complete — {result.schematics_dir}",
            8000,
        )
        QMessageBox.information(
            self,
            "Renders complete",
            f"Outputs written under:\n{result.schematics_dir}\n\n"
            f"World folder (if worldgen ran):\n{result.worldgen_dir}",
        )

    def _on_render_failed(self, message: str) -> None:
        self._render_panel.set_busy(False)
        self._status.showMessage("Render failed.", 5000)
        QMessageBox.critical(self, "Render failed", message)

    def _finish_render_thread(self) -> None:
        if self._render_thread is not None:
            self._render_thread.deleteLater()
            self._render_thread = None
        self._render_worker = None

    def _open_render_output_folder(self) -> None:
        if self._last_schematics_dir is None:
            QMessageBox.information(
                self,
                "Output folder",
                "Generate renders first, or check output_folder in structure.yaml.",
            )
            return

        path = self._last_schematics_dir.resolve()
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _confirm_render_save(self) -> bool:
        if not self._dirty_layers and not self._dirty_structure:
            return True

        answer = QMessageBox.question(
            self,
            "Unsaved changes",
            "Renders read from saved files on disk. Save all changes before generating?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

        if answer == QMessageBox.StandardButton.Cancel:
            return False

        if answer == QMessageBox.StandardButton.Discard:
            return True

        if self._dirty_structure and not self._save_site_settings():
            return False

        return all(self._save_layer(layer_index) for layer_index in sorted(self._dirty_layers))


def build_main_window(structure: str, stage: int) -> MainWindow:
    from registries.loader import reload_registries

    reload_registries()

    try:
        document = open_structure(structure, stage)
    except ValueError as exc:
        QMessageBox.critical(
            None,
            "Cannot open structure",
            f"{structure} stage {stage} failed validation:\n\n{exc}",
        )
        raise

    return MainWindow(document, structure=structure, stage=stage)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Structure schematic editor")
    parser.add_argument("--structure", default="residence")
    parser.add_argument("--stage", type=int, default=1)
    args = parser.parse_args(argv)

    ensure_qt_platform()
    app = QApplication(sys.argv)
    window = build_main_window(args.structure, args.stage)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
