from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
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
from helpers.grid_cells import count_cells_trimmed_by_resize, empty_cells, resize_structure_layers
from helpers.grid_placement import (
    clamp_grid_offsets_for_structure,
    nudge_structure_offset,
    site_cell_in_structure_footprint,
    structure_dimensions_from_layers,
    structure_site_size_error,
)
from helpers.layer_groups import (
    add_defined_group,
    collect_layer_groups,
    get_hidden_groups,
    group_name_exists,
    layer_indices_in_group,
    layer_matches_group_filter,
    remove_group,
    rename_group,
    set_group_hidden,
)
from helpers.layer_management import (
    append_layer_to_document,
    copy_layer_dict,
    create_layer,
    layer_label,
    move_layer_in_document,
    next_worldgen_index,
    remap_indices_after_swap,
    remove_layer_from_document,
)
from helpers.layer_visibility import is_layer_visible, set_layer_visible
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
    validate_structure_document,
)
from ui.editor_history import apply_history_state, capture_history_state
from ui.editor_materials import build_editor_materials_context, structure_material_inventory
from ui.editor_prefs import block_tooltips_enabled, set_block_tooltips_enabled
from ui.icon_theme import configure_ui_icon_theme
from ui.materials_icons import MaterialsIconCache
from ui.menu_style import configure_ui_menus
from ui.platform import ensure_qt_platform
from ui.reload import reload_editor_process
from ui.render_worker import RenderJobResult, RenderWorker
from ui.site_cells import build_site_display_grid, site_preview_layer_index, structure_offset
from ui.texture_cache import GridTextureCache
from ui.tooltip_style import configure_ui_tooltips
from ui.widgets.compass_panel import CompassPanel
from ui.widgets.grid import LayerGridWidget
from ui.widgets.groups_panel import GroupsPanel
from ui.widgets.layer_list_panel import LayerListPanel
from ui.widgets.layer_tools_panel import LayerToolsPanel
from ui.widgets.materials_panel import MaterialsPanel
from ui.widgets.palette_panel import PalettePanel
from ui.widgets.properties_panel import PropertiesPanel
from ui.widgets.render_panel import RenderPanel
from ui.widgets.site_grid import SiteGridView
from ui.widgets.site_nudge_controls import SiteNudgeControls
from ui.widgets.site_path_panel import SitePathPanel
from ui.widgets.site_settings_panel import SiteSettingsPanel
from ui.widgets.structure_settings_panel import StructureSettingsPanel


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

        self._layer_tools_panel = LayerToolsPanel()
        self._groups_panel = GroupsPanel()
        self._layer_list_panel = LayerListPanel()
        self._group_filter: str | None = None
        self._compass_panel = CompassPanel()
        self._site_compass_panel = CompassPanel()
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
        self._structure_settings_panel = StructureSettingsPanel()
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
        self._layer_clipboard: dict | None = None
        self._group_clipboard: dict | None = None

        self.setStatusBar(self._status)
        self._init_menus()

        self._layer_tools_panel.eraser_toggled.connect(self._on_eraser_toggled)
        self._layer_tools_panel.clear_entire_layer_requested.connect(self._on_clear_entire_layer)
        self._layer_tools_panel.save_requested.connect(self._save_current_layer)
        self._groups_panel.group_selected.connect(self._on_group_filter_selected)
        self._groups_panel.visibility_toggled.connect(self._on_group_visibility_toggled)
        self._groups_panel.add_requested.connect(self._on_add_group)
        self._groups_panel.delete_requested.connect(self._on_delete_group)
        self._groups_panel.copy_requested.connect(self._on_copy_group)
        self._groups_panel.paste_requested.connect(self._on_paste_group)
        self._groups_panel.group_renamed.connect(self._on_group_renamed)
        self._layer_list_panel.layer_selected.connect(self._on_layer_list_selected)
        self._layer_list_panel.move_up_requested.connect(self._on_move_layer_up)
        self._layer_list_panel.move_down_requested.connect(self._on_move_layer_down)
        self._layer_list_panel.visibility_toggled.connect(self._on_layer_visibility_toggled)
        self._layer_list_panel.add_requested.connect(self._on_add_layer)
        self._layer_list_panel.delete_requested.connect(self._on_delete_layer)
        self._layer_list_panel.copy_requested.connect(self._on_copy_layer)
        self._layer_list_panel.paste_requested.connect(self._on_paste_layer)
        self._save_site_button.clicked.connect(self._save_site_settings)
        self._structure_settings_panel.properties_changed.connect(
            self._on_structure_properties_changed
        )
        self._site_settings_panel.settings_changed.connect(self._on_site_settings_changed)
        self._site_settings_panel.block_tooltips_changed.connect(self._on_block_tooltips_changed)
        self._structure_settings_panel.block_tooltips_changed.connect(
            self._on_block_tooltips_changed
        )
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
        self._structure_settings_panel.resize_requested.connect(self._on_structure_resize_requested)

        palette_column = QWidget()
        palette_column_layout = QVBoxLayout(palette_column)
        palette_column_layout.setContentsMargins(0, 0, 0, 0)
        palette_column_layout.addWidget(self._palette_panel, stretch=1)
        palette_column_layout.addWidget(self._groups_panel)
        palette_column_layout.addWidget(self._layer_list_panel)
        palette_column_layout.addWidget(self._structure_settings_panel)

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

        structure_tools_column = QWidget()
        structure_tools_layout = QVBoxLayout(structure_tools_column)
        structure_tools_layout.setContentsMargins(0, 0, 0, 0)
        self._compass_panel.close_requested.connect(self._hide_compass_panels)
        structure_tools_layout.addWidget(self._compass_panel)
        structure_tools_layout.addWidget(self._structure_tools_splitter, stretch=1)

        structure_splitter = QSplitter(Qt.Orientation.Horizontal)
        structure_splitter.addWidget(palette_column)
        structure_splitter.addWidget(structure_center)
        structure_splitter.addWidget(structure_tools_column)
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
        self._site_compass_panel.close_requested.connect(self._hide_compass_panels)
        site_settings_layout.addWidget(self._site_compass_panel)
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

        self._structure_settings_panel.set_structure_path(document.structure_path)
        self._structure_settings_panel.load_from_metadata(document.metadata)
        self._sync_render_output_hint()
        self._site_settings_panel.load_from_metadata(document.metadata, document.layers)
        self._sync_path_panel_from_metadata()
        self._refresh_layer_panels()
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

    def _init_menus(self) -> None:
        self._init_file_menu()
        self._init_edit_menu()
        self._init_view_menu()

    def _init_file_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")

        new_structure_action = QAction("&New Structure", self)
        new_structure_action.setShortcut(QKeySequence("Ctrl+N"))
        new_structure_action.triggered.connect(self._on_new_structure_placeholder)
        file_menu.addAction(new_structure_action)

        file_menu.addSeparator()

        self._save_action = QAction("&Save", self)
        self._save_action.setShortcut(QKeySequence("Ctrl+S"))
        self._save_action.triggered.connect(self._save_current_layer)
        self._save_action.setEnabled(False)
        file_menu.addAction(self._save_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _init_view_menu(self) -> None:
        view_menu = self.menuBar().addMenu("&View")

        reload_action = QAction("&Reload Window", self)
        reload_action.setShortcut(QKeySequence("Ctrl+Shift+Q"))
        reload_action.triggered.connect(self._reload_window)
        view_menu.addAction(reload_action)

        view_menu.addSeparator()

        self._compass_action = QAction("&Compass", self)
        self._compass_action.setCheckable(True)
        self._compass_action.setChecked(True)
        self._compass_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self._compass_action.triggered.connect(self._on_compass_action_triggered)
        view_menu.addAction(self._compass_action)

    def _on_compass_action_triggered(self, checked: bool) -> None:
        self._set_compass_panels_visible(checked)

    def _hide_compass_panels(self) -> None:
        self._set_compass_panels_visible(False)

    def _set_compass_panels_visible(self, visible: bool) -> None:
        self._compass_action.blockSignals(True)
        self._compass_action.setChecked(visible)
        self._compass_action.blockSignals(False)
        self._compass_panel.setVisible(visible)
        self._site_compass_panel.setVisible(visible)

    def _init_edit_menu(self) -> None:
        edit_menu = self.menuBar().addMenu("&Edit")

        self._undo_action = QAction("&Undo", self)
        self._undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self._undo_action.triggered.connect(self._undo_edit)
        edit_menu.addAction(self._undo_action)

        self._redo_action = QAction("&Redo", self)
        self._redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        self._redo_action.triggered.connect(self._redo_edit)
        edit_menu.addAction(self._redo_action)

    def _on_new_structure_placeholder(self) -> None:
        QMessageBox.information(
            self,
            "New Structure",
            "Creating a new structure from the editor is not implemented yet.",
        )

    def _reload_window(self) -> None:
        if self._render_thread is not None:
            QMessageBox.warning(
                self,
                "Render in progress",
                "Wait for the current render job to finish before reloading.",
            )
            return

        if self._dirty_layers or self._dirty_structure:
            answer = QMessageBox.question(
                self,
                "Reload Window",
                "Reload the editor and discard unsaved changes?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if answer != QMessageBox.StandardButton.Yes:
                return

        reload_editor_process()

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
            self._layer_clipboard = None
            self._group_clipboard = None
            self._layer_list_panel.set_paste_enabled(False)
            self._groups_panel.set_paste_enabled(False)
            self._refresh_layer_panels()
            self._show_layer(self._clamp_layer_index(self._current_layer_index))
            self._structure_settings_panel.load_from_metadata(self._document.metadata)
            self._sync_render_output_hint()
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
        layout = QVBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._layer_tools_panel)

        return header

    def _clamp_layer_index(self, index: int) -> int:
        if not self._document.layers:
            return 0

        return max(0, min(index, len(self._document.layers) - 1))

    def _refresh_layer_panels(self) -> None:
        self._sync_groups_panel()
        self._sync_layer_list_panel()

    def _grid_metadata(self) -> dict:
        return self._document.metadata.setdefault("grid", {})

    def _sync_groups_panel(self) -> None:
        grid = self._grid_metadata()
        self._groups_panel.load_groups(
            collect_layer_groups(self._document.layers, grid),
            hidden_groups=get_hidden_groups(grid),
            selected_filter=self._group_filter,
        )

    def _sync_layer_list_panel(self) -> None:
        self._layer_list_panel.load_layers(
            self._document.layers,
            self._document.layer_paths,
            current_index=self._current_layer_index,
            dirty_layers=self._dirty_layers,
            group_filter=self._group_filter,
        )

    def _on_group_filter_selected(self, group: str | None) -> None:
        self._group_filter = group
        self._sync_layer_list_panel()

        if group is None:
            self._status.showMessage("Showing all layer groups.", 2000)
            return

        if not any(
            layer_matches_group_filter(layer, index, group)
            for index, layer in enumerate(self._document.layers)
        ):
            self._status.showMessage(f"No layers in group {group!r}.", 3000)
            return

        if not layer_matches_group_filter(
            self._document.layers[self._current_layer_index],
            self._current_layer_index,
            group,
        ):
            for index, layer in enumerate(self._document.layers):
                if layer_matches_group_filter(layer, index, group):
                    self._on_layer_changed(index)
                    break

        self._status.showMessage(f"Layers filtered to {group!r}.", 2000)

    def _on_group_visibility_toggled(self, group: str) -> None:
        grid = self._grid_metadata()
        hidden = group not in get_hidden_groups(grid)

        self._push_undo_snapshot()
        set_group_hidden(grid, group, hidden=hidden)
        self._dirty_structure = True
        self._sync_groups_panel()
        self._sync_layer_list_panel()
        self._update_save_site_button()
        self._update_window_title()

        if hidden:
            self._status.showMessage(f"Group {group!r} hidden from renders.", 3000)
        else:
            self._status.showMessage(f"Group {group!r} included in renders.", 2000)

    def _prompt_group_name(self, *, title: str, label: str, initial: str = "") -> str | None:
        while True:
            name, ok = QInputDialog.getText(
                self,
                title,
                label,
                QLineEdit.EchoMode.Normal,
                initial,
            )

            if not ok:
                return None

            normalized = name.strip()

            if normalized:
                return normalized

            QMessageBox.warning(self, title, "Group name is required.")

    def _unique_group_copy_name(self, base: str) -> str:
        grid = self._grid_metadata()
        candidate = f"{base} (copy)"
        suffix = 2

        while group_name_exists(self._document.layers, grid, candidate):
            candidate = f"{base} (copy {suffix})"
            suffix += 1

        return candidate

    def _on_add_group(self) -> None:
        name = self._prompt_group_name(title="Add group", label="Group name:")

        if name is None:
            return

        grid = self._grid_metadata()

        if group_name_exists(self._document.layers, grid, name):
            QMessageBox.warning(
                self,
                "Add group",
                f"A group named {name!r} already exists.",
            )
            return

        self._push_undo_snapshot()
        add_defined_group(grid, name)
        self._dirty_structure = True
        self._group_filter = name
        self._refresh_layer_panels()
        self._update_save_site_button()
        self._status.showMessage(
            f"Added group {name!r} — assign layers or save site settings",
            5000,
        )

    def _on_delete_group(self) -> None:
        group = self._groups_panel.selected_group_name()

        if group is None:
            return

        indices = layer_indices_in_group(self._document.layers, group)
        message = f"Remove group {group!r}?"

        if indices:
            message = (
                f"Remove group {group!r} from {len(indices)} layer(s)? "
                "Those layers will use default layer names."
            )

        answer = QMessageBox.question(
            self,
            "Delete group",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self._push_undo_snapshot()
        grid = self._grid_metadata()
        remove_group(self._document.layers, grid, group)

        for index in indices:
            self._mark_layer_dirty(index)

        if self._group_filter == group:
            self._group_filter = None

        self._dirty_structure = True
        self._refresh_layer_panels()
        self._update_save_site_button()
        self._status.showMessage(f"Removed group {group!r}.", 4000)

    def _on_copy_group(self) -> None:
        group = self._groups_panel.selected_group_name()

        if group is None:
            return

        indices = layer_indices_in_group(self._document.layers, group)
        self._group_clipboard = {
            "name": group,
            "layers": [copy_layer_dict(self._document.layers[index]) for index in indices],
        }
        self._groups_panel.set_paste_enabled(True)
        layer_count = len(indices)
        self._status.showMessage(
            f"Copied group {group!r} ({layer_count} layer(s))",
            3000,
        )

    def _on_paste_group(self) -> None:
        if self._group_clipboard is None:
            return

        if not self._confirm_discard_layer_changes(self._current_layer_index):
            return

        base_name = str(self._group_clipboard["name"])
        new_name = self._unique_group_copy_name(base_name)
        grid = self._grid_metadata()

        self._push_undo_snapshot()
        clipboard_layers = self._group_clipboard["layers"]

        if not clipboard_layers:
            add_defined_group(grid, new_name)
        else:
            width, depth = structure_dimensions_from_layers(self._document.layers)

            for source in clipboard_layers:
                cells = source.get("cells")
                layer = create_layer(
                    width=len(cells[0]) if cells else width,
                    depth=len(cells) if cells else depth,
                    worldgen_index=next_worldgen_index(self._document.layers),
                    group=new_name,
                    cells=cells,
                )
                new_index = append_layer_to_document(self._document, layer)
                self._mark_layer_dirty(new_index)

        self._dirty_structure = True
        self._group_filter = new_name
        self._refresh_layer_panels()

        if clipboard_layers:
            self._show_layer(len(self._document.layers) - 1)

        self._update_save_site_button()
        self._status.showMessage(
            f"Pasted group as {new_name!r} — save layers and site settings",
            5000,
        )

    def _on_group_renamed(self, old_name: str, new_name: str) -> None:
        normalized = new_name.strip()

        if not normalized:
            self._refresh_layer_panels()
            return

        grid = self._grid_metadata()

        if group_name_exists(
            self._document.layers,
            grid,
            normalized,
            except_name=old_name,
        ):
            QMessageBox.warning(
                self,
                "Rename group",
                f"A group named {normalized!r} already exists.",
            )
            self._refresh_layer_panels()
            return

        self._push_undo_snapshot()
        rename_group(self._document.layers, grid, old_name, normalized)

        for index in layer_indices_in_group(self._document.layers, normalized):
            self._mark_layer_dirty(index)

        if self._group_filter == old_name:
            self._group_filter = normalized

        self._dirty_structure = True
        self._refresh_layer_panels()
        self._update_save_site_button()
        self._status.showMessage(f"Group renamed to {normalized!r}", 3000)

    def _on_layer_list_selected(self, index: int) -> None:
        self._on_layer_changed(index)

    def _on_move_layer_up(self) -> None:
        self._move_layer_by_delta(-1)

    def _on_move_layer_down(self) -> None:
        self._move_layer_by_delta(1)

    def _on_layer_visibility_toggled(self, index: int) -> None:
        if index < 0 or index >= len(self._document.layers):
            return

        layer = self._document.layers[index]
        show_in_renders = not is_layer_visible(layer)

        self._push_undo_snapshot()
        set_layer_visible(layer, show_in_renders)
        self._mark_layer_dirty(index)
        self._sync_layer_list_panel()
        self._layer_list_panel.set_current_index(self._current_layer_index)

        if show_in_renders:
            self._status.showMessage("Layer included in renders.", 2000)
        else:
            self._status.showMessage("Layer hidden from renders (still editable).", 3000)

    def _move_layer_by_delta(self, delta: int) -> None:
        index = self._layer_list_panel.current_index()

        if index < 0:
            index = self._current_layer_index

        if not self._confirm_discard_layer_changes(self._current_layer_index):
            self._layer_list_panel.set_current_index(self._current_layer_index)
            return

        self._push_undo_snapshot()
        new_index = move_layer_in_document(self._document, index, delta)

        if new_index is None:
            return

        self._dirty_structure = True
        self._dirty_layers = remap_indices_after_swap(self._dirty_layers, index, new_index)
        self._refresh_layer_panels()
        self._show_layer(new_index)
        self._update_save_site_button()
        direction = "up" if delta < 0 else "down"
        self._status.showMessage(
            f"Moved layer {direction} — save site settings to update layer order in structure.yaml",
            5000,
        )

    def _on_add_layer(self) -> None:
        if not self._confirm_discard_layer_changes(self._current_layer_index):
            return

        width, depth = structure_dimensions_from_layers(self._document.layers)
        worldgen_index = next_worldgen_index(self._document.layers)
        layer = create_layer(
            width=width,
            depth=depth,
            worldgen_index=worldgen_index,
            group=f"Layer {worldgen_index}",
        )

        self._push_undo_snapshot()
        new_index = append_layer_to_document(self._document, layer)
        self._dirty_structure = True
        self._mark_layer_dirty(new_index)
        self._refresh_layer_panels()
        self._show_layer(new_index)
        self._update_save_site_button()
        self._status.showMessage(
            f"Added {self._document.layer_paths[new_index].name} (save layer and site settings)",
            5000,
        )

    def _on_delete_layer(self) -> None:
        if len(self._document.layers) <= 1:
            QMessageBox.information(
                self,
                "Delete layer",
                "At least one layer is required.",
            )
            return

        if not self._confirm_discard_layer_changes(self._current_layer_index):
            return

        path = self._document.layer_paths[self._current_layer_index]
        answer = QMessageBox.question(
            self,
            "Delete layer",
            f"Delete {path.name} from this structure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self._push_undo_snapshot()
        removed_path = remove_layer_from_document(self._document, self._current_layer_index)

        if removed_path is not None:
            removed_path.unlink()

        self._dirty_structure = True
        self._dirty_layers = {
            index for index in self._dirty_layers if index < len(self._document.layers)
        }
        new_index = self._clamp_layer_index(self._current_layer_index)
        self._refresh_layer_panels()
        self._show_layer(new_index)
        self._update_save_site_button()
        self._status.showMessage(
            "Layer deleted — save site settings to update structure.yaml",
            5000,
        )

    def _on_copy_layer(self) -> None:
        layer = self._document.layers[self._current_layer_index]
        self._layer_clipboard = copy_layer_dict(layer)
        self._layer_list_panel.set_paste_enabled(True)
        self._status.showMessage(f"Copied {layer_label(layer, self._current_layer_index)}", 3000)

    def _on_paste_layer(self) -> None:
        if self._layer_clipboard is None:
            return

        if not self._confirm_discard_layer_changes(self._current_layer_index):
            return

        source = self._layer_clipboard
        width = len(source["cells"][0]) if source.get("cells") else 1
        depth = len(source["cells"]) if source.get("cells") else 1
        base_group = str(source.get("group") or "Layer")

        layer = create_layer(
            width=width,
            depth=depth,
            worldgen_index=next_worldgen_index(self._document.layers),
            group=f"{base_group} (copy)",
            cells=source["cells"],
        )

        self._push_undo_snapshot()
        new_index = append_layer_to_document(self._document, layer)
        self._dirty_structure = True
        self._mark_layer_dirty(new_index)
        self._refresh_layer_panels()
        self._show_layer(new_index)
        self._update_save_site_button()
        self._status.showMessage(
            f"Pasted as {self._document.layer_paths[new_index].name}",
            4000,
        )

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
            self._layer_tools_panel.set_eraser_checked(False)

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

    def _on_clear_entire_layer(self) -> None:
        layer = self._document.layers[self._current_layer_index]
        cells = layer.get("cells") or []

        if not cells:
            return

        depth = len(cells)
        width = len(cells[0]) if cells else 0

        if not any(token != "." for row in cells for token in row):
            self._status.showMessage("Layer is already empty.", 3000)
            return

        layer_path = self._document.layer_paths[self._current_layer_index].name
        answer = QMessageBox.question(
            self,
            "Clear entire layer",
            f"Clear all cells in {layer_path}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        if self._eraser_active:
            self._layer_tools_panel.set_eraser_checked(False)

        self._push_undo_snapshot()
        layer["cells"] = empty_cells(width, depth)
        self._structure_grid.set_layer_cells(layer["cells"])
        self._properties_panel.clear_grid_cell()

        if self._current_layer_index == self._site_preview_layer_index():
            self._refresh_site_preview()

        self._mark_layer_dirty(self._current_layer_index)
        self._refresh_materials_list()
        self._sync_layer_list_panel()
        self._status.showMessage(f"Cleared all cells in {layer_path}", 4000)

    def _on_layer_changed(self, index: int) -> None:
        if index < 0:
            return

        if index == self._current_layer_index:
            return

        if not self._confirm_discard_layer_changes(self._current_layer_index):
            self._layer_list_panel.set_current_index(self._current_layer_index)
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
        index = self._clamp_layer_index(index)
        layer = self._document.layers[index]
        self._current_layer_index = index
        self._properties_panel.clear_grid_cell()
        self._structure_grid.set_layer_cells(layer["cells"])
        layer_path = self._document.layer_paths[index]
        self._layer_list_panel.set_delete_enabled(len(self._document.layers) > 1)
        self._layer_list_panel.set_copy_enabled(layer is not None)
        self._layer_list_panel.set_current_index(index)
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
        self._structure_settings_panel.set_structure_size(structure_width, structure_depth)
        self._structure_settings_panel.set_site_limits(site_width, site_depth)

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
            self._layer_tools_panel.set_eraser_checked(False)

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
        dirty = self._current_layer_index in self._dirty_layers
        self._layer_tools_panel.set_save_enabled(dirty)
        self._save_action.setEnabled(dirty)

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
        self._structure_settings_panel.set_block_tooltips_enabled(enabled)

    def _on_block_tooltips_changed(self, enabled: bool) -> None:
        self._apply_block_tooltips_pref(enabled)

    def _sync_render_output_hint(self) -> None:
        output_folder = self._structure_settings_panel.current_output_folder()
        self._render_panel.set_output_hint(output_folder)
        self._last_schematics_dir = OUTPUT_SCHEMATICS_FOLDER / output_folder

    def _on_structure_properties_changed(self) -> None:
        self._push_undo_snapshot()
        self._structure_settings_panel.apply_to_metadata(self._document.metadata)
        self._structure = str(self._document.metadata.get("structure", self._structure))
        self._stage = int(self._document.metadata.get("stage", self._stage))
        self._sync_render_output_hint()
        self._dirty_structure = True
        self._update_save_site_button()
        self._update_window_title()

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
        self._structure_settings_panel.apply_to_metadata(self._document.metadata)
        self._sync_render_output_hint()

        if not self._site_settings_panel.apply_to_metadata(self._document.metadata):
            QMessageBox.warning(
                self,
                "Site settings",
                "The structure footprint does not fit in the selected site size.",
            )
            return False

        try:
            validate_structure_document(self._document)
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
        dirty_marker = " (unsaved)" if self._dirty_layers or self._dirty_structure else ""
        title_name = self._document.metadata.get("name", self._structure_name)
        self.setWindowTitle(f"Structure Editor — {title_name}{dirty_marker}")

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
        structure = str(self._document.metadata.get("structure", self._structure))
        stage = int(self._document.metadata.get("stage", self._stage))
        self._render_worker = RenderWorker(
            structure,
            stage,
            renders,
            structure_path=self._document.structure_path,
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
    configure_ui_icon_theme()
    configure_ui_tooltips()
    configure_ui_menus()
    window = build_main_window(args.structure, args.stage)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
