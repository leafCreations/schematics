from __future__ import annotations

import sys
from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QThread, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence, QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from helpers.block_picker import homogeneous_picker_entry_for_positions, picker_entry_for_cell
from helpers.cell_clipboard import CellRegionClipboard, copy_region, move_region, paste_region
from helpers.grid import resolve_site_dimensions
from helpers.grid_brush import rect_cell_indices, region_cell_indices, square_cell_indices
from helpers.grid_cells import (
    count_cells_trimmed_by_resize,
    empty_cells,
    occupied_cell_positions,
    resize_structure_layers,
)
from helpers.grid_labels import grid_axis_position, grid_axis_selection_range
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
    get_defined_groups,
    get_hidden_groups,
    group_name_exists,
    layer_indices_in_group,
    layer_matches_group_filter,
    move_group,
    remove_group,
    rename_group,
    set_group_hidden,
)
from helpers.layer_management import (
    append_layer_to_document,
    copy_layer_dict,
    create_layer,
    layer_display_label,
    layer_label,
    move_layer_by_worldgen_delta,
    next_worldgen_index,
    remap_indices_after_permutation,
    remove_layer_from_document,
    reorder_layers_in_document,
    set_layer_description,
    worldgen_index_in_use,
)
from helpers.layer_rotation import (
    rotate_layer_cells,
)
from helpers.layer_visibility import is_layer_visible, set_layer_visible
from helpers.path_strip import (
    clear_all_paths,
    erase_path_at_site,
    paint_path_at_site,
    resolve_path_orientation,
    resolve_path_width,
)
from helpers.paths import OUTPUT_SCHEMATICS_FOLDER, STRUCTURES_FOLDER
from helpers.site_ground import resize_site_ground
from helpers.structure_metadata import identity_from_structure_path
from ui.app_settings import (
    add_recent_structure,
    clear_recent_structures,
    load_recent_structures,
    sync_editor_settings_from_ui,
)
from ui.dialog_layout import (
    DIALOG_FIELD_MIN_WIDTH,
    apply_dialog_field_style,
    create_dialog_form_layout,
    create_dialog_shell,
)
from ui.document import (
    StructureDocument,
    create_structure_stage_document,
    delete_structure_stage_document,
    open_structure,
    save_layer,
    save_structure_metadata,
    validate_structure_document,
)
from ui.editor_history import apply_history_state, capture_history_state
from ui.editor_materials import build_editor_materials_context, structure_material_inventory
from ui.editor_prefs import (
    block_tooltips_enabled,
    grid_axis_labels_enabled,
    panel_compass_visible,
    panel_materials_visible,
    set_block_tooltips_enabled,
    set_grid_axis_labels_enabled,
    set_panel_compass_visible,
    set_panel_materials_visible,
)
from ui.icon_theme import configure_ui_icon_theme
from ui.materials_icons import MaterialsIconCache
from ui.menu_style import configure_ui_menus
from ui.platform import ensure_qt_platform
from ui.reload import (
    open_editor_in_empty_state_process,
    open_structure_in_editor_process,
    reload_editor_process,
)
from ui.render_worker import RenderJobResult, RenderWorker
from ui.selector_mode import SelectorMode
from ui.site_cells import build_site_display_grid, site_preview_layer_index, structure_offset
from ui.texture_cache import GridTextureCache
from ui.tooltip_style import configure_ui_tooltips
from ui.widgets.add_layer_dialog import AddLayerDialog
from ui.widgets.compass_panel import CompassPanel
from ui.widgets.edit_group_dialog import EditGroupDialog
from ui.widgets.grid import LayerGridViewport, LayerGridWidget
from ui.widgets.groups_panel import GroupsPanel
from ui.widgets.input_text_dialog import InputTextDialog
from ui.widgets.layer_eraser_panel import LayerEraserPanel
from ui.widgets.layer_list_panel import LayerListPanel
from ui.widgets.layer_paint_brush_panel import LayerPaintBrushPanel
from ui.widgets.layer_selector_panel import LayerSelectorPanel
from ui.widgets.layer_tools_panel import LayerToolsPanel
from ui.widgets.materials_panel import MaterialsPanel
from ui.widgets.new_structure_dialog import NewStructureDialog
from ui.widgets.palette_panel import PalettePanel
from ui.widgets.properties_panel import PropertiesPanel
from ui.widgets.render_panel import RenderPanel
from ui.widgets.site_grid import SiteGridView
from ui.widgets.site_nudge_controls import SiteNudgeControls
from ui.widgets.site_path_panel import SitePathPanel
from ui.widgets.site_settings_panel import SiteSettingsPanel
from ui.widgets.structure_settings_panel import StructureSettingsPanel

_STRUCTURE_EDITOR_GUIDE_URL = (
    "https://github.com/leafCreations/schematics/blob/main/docs/structure-editor-guide.md"
)


def _resolve_structure_stage_from_selected_dir(selected_dir: Path) -> tuple[str, int] | None:
    structure_path = selected_dir / "stage.yaml"

    if not structure_path.is_file():
        structure_path = selected_dir / "structure.yaml"

    if not structure_path.is_file():
        return None

    return identity_from_structure_path(structure_path)


def _structure_stage_choices(structure_dir: Path) -> list[tuple[str, int]]:
    if not structure_dir.is_dir():
        return []

    choices: list[tuple[str, int]] = []

    for child in sorted(structure_dir.iterdir()):
        if not child.is_dir():
            continue

        resolved = _resolve_structure_stage_from_selected_dir(child)

        if resolved is None:
            continue

        choices.append(resolved)

    return choices


def _select_stage_for_structure(
    parent: QWidget | None,
    structure: str,
    stages: list[tuple[str, int]],
) -> tuple[str, int] | None:
    if not stages:
        return None

    if len(stages) == 1:
        return stages[0]

    dialog = QDialog(parent)
    dialog.setWindowTitle(f"Open Structure — {structure}")
    layout = QVBoxLayout(dialog)

    prompt = QLabel("Select a stage:")
    layout.addWidget(prompt)

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
    layout.addWidget(buttons)
    buttons.rejected.connect(dialog.reject)

    selected: dict[str, tuple[str, int] | None] = {"value": None}

    for _, stage in sorted(stages, key=lambda item: item[1]):
        button = QPushButton(f"Stage {stage}")

        def pick(value: tuple[str, int]) -> None:
            selected["value"] = value
            dialog.accept()

        button.clicked.connect(lambda _checked=False, value=(structure, stage): pick(value))
        layout.insertWidget(layout.count() - 1, button)

    if not dialog.exec():
        return None

    return selected["value"]


def _pick_structure_stage(parent: QWidget | None) -> tuple[str, int] | None:
    selected = QFileDialog.getExistingDirectory(
        parent,
        "Open Structure",
        str(STRUCTURES_FOLDER),
        QFileDialog.Option.ShowDirsOnly,
    )

    if not selected:
        return None

    selected_dir = Path(selected)
    stage_choice = _resolve_structure_stage_from_selected_dir(selected_dir)

    if stage_choice is not None:
        return stage_choice

    structure = selected_dir.name.lower()
    choices = _structure_stage_choices(selected_dir)
    return _select_stage_for_structure(parent, structure, choices)


def _format_recent_entry_label(index: int, structure: str, stage: int) -> str:
    dimension = "unknown"

    try:
        document = open_structure(structure, stage)
        dimension = str(document.metadata.get("dimension", "overworld"))
    except (FileNotFoundError, ValueError, OSError):
        pass

    return f"{index}. {dimension}:{structure}_stage{stage}"


class NoStructureLoadedWindow(QMainWindow):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Structure Editor — No structure loaded")
        self.resize(1280, 800)

        center = QLabel("No structure loaded")
        center.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center.setStyleSheet("font-size: 24px; color: #666;")
        open_button = QPushButton("Open Structure...")
        open_button.clicked.connect(self._on_open_structure)

        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addStretch(1)
        layout.addWidget(center, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(open_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)
        self.setCentralWidget(wrapper)

        status = QStatusBar()
        status.showMessage("Use File > New Structure or File > Open Recent.", 5000)
        self.setStatusBar(status)

        self._init_file_menu()

    def _init_file_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")

        new_structure_action = QAction("&New Structure", self)
        new_structure_action.setShortcut(QKeySequence("Ctrl+N"))
        new_structure_action.triggered.connect(self._on_new_structure)
        file_menu.addAction(new_structure_action)

        open_structure_action = QAction("&Open Structure...", self)
        open_structure_action.setShortcut(QKeySequence.StandardKey.Open)
        open_structure_action.triggered.connect(self._on_open_structure)
        file_menu.addAction(open_structure_action)

        delete_stage_action = QAction("Delete Current &Stage...", self)
        delete_stage_action.triggered.connect(self._on_delete_current_stage)
        file_menu.addAction(delete_stage_action)

        self._open_recent_menu = file_menu.addMenu("Open &Recent")
        self._open_recent_menu.aboutToShow.connect(self._refresh_open_recent_menu)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _refresh_open_recent_menu(self) -> None:
        self._open_recent_menu.clear()
        entries = load_recent_structures()

        if entries:
            for index, (structure, stage) in enumerate(entries, start=1):
                action = QAction(_format_recent_entry_label(index, structure, stage), self)
                action.triggered.connect(
                    lambda _checked=False, s=structure, st=stage: self._open_recent_entry(s, st)
                )
                self._open_recent_menu.addAction(action)
        else:
            empty_action = QAction("(No recent files)", self)
            empty_action.setEnabled(False)
            self._open_recent_menu.addAction(empty_action)

        self._open_recent_menu.addSeparator()
        clear_action = QAction("Clear Recent Files", self)
        clear_action.setEnabled(bool(entries))
        clear_action.triggered.connect(self._clear_recent_entries)
        self._open_recent_menu.addAction(clear_action)

    def _clear_recent_entries(self) -> None:
        clear_recent_structures()
        self._refresh_open_recent_menu()

    def _open_recent_entry(self, structure: str, stage: int) -> None:
        add_recent_structure(structure, stage)

        try:
            open_structure_in_editor_process(structure, stage)
        except OSError as exc:
            QMessageBox.critical(self, "Open recent failed", str(exc))

    def _on_open_structure(self) -> None:
        selection = _pick_structure_stage(self)

        if selection is None:
            return

        structure, stage = selection
        add_recent_structure(structure, stage)

        try:
            open_structure_in_editor_process(structure, stage)
        except OSError as exc:
            QMessageBox.critical(self, "Open Structure failed", str(exc))

    def _on_delete_current_stage(self) -> None:
        structure = str(self._document.metadata.get("structure", self._structure))
        stage = int(self._document.metadata.get("stage", self._stage))

        answer = QMessageBox.question(
            self,
            "Delete Current Stage",
            (
                f"Delete {structure} Stage {stage}?\n\n"
                "This removes its stage folder and cannot be undone."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        if self._dirty_layers or self._dirty_structure:
            save_answer = QMessageBox.question(
                self,
                "Unsaved changes",
                "Save unsaved changes before deleting this stage?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )

            if save_answer == QMessageBox.StandardButton.Cancel:
                return

            if save_answer == QMessageBox.StandardButton.Save:
                if self._dirty_structure and not self._save_site_settings():
                    return

                for layer_index in sorted(self._dirty_layers):
                    if not self._save_layer(layer_index):
                        return

        try:
            delete_structure_stage_document(structure=structure, stage=stage)
        except (FileNotFoundError, ValueError, OSError) as exc:
            QMessageBox.critical(self, "Delete Stage failed", str(exc))
            return

        remaining = _structure_stage_choices(STRUCTURES_FOLDER / structure)

        if remaining:
            _, next_stage = remaining[0]
            add_recent_structure(structure, next_stage)

            try:
                open_structure_in_editor_process(structure, next_stage)
            except OSError as exc:
                QMessageBox.critical(self, "Open Structure failed", str(exc))
            return

        reload_editor_process()

    def _on_new_structure(self) -> None:
        while True:
            dialog = NewStructureDialog(
                self,
                stage=1,
                allow_stage_edit=False,
            )

            if not dialog.exec():
                return

            (
                structure,
                stage,
                site_width,
                site_depth,
                structure_width,
                structure_depth,
                dimension,
            ) = dialog.values()

            try:
                create_structure_stage_document(
                    structure=structure,
                    stage=stage,
                    site_width=site_width,
                    site_depth=site_depth,
                    structure_width=structure_width,
                    structure_depth=structure_depth,
                    dimension=dimension,
                )
            except FileExistsError as exc:
                QMessageBox.warning(self, "New Structure", str(exc))
                continue
            except ValueError as exc:
                QMessageBox.warning(self, "New Structure", str(exc))
                continue
            except OSError as exc:
                QMessageBox.critical(self, "Save failed", str(exc))
                return

            add_recent_structure(structure, stage)

            try:
                open_structure_in_editor_process(structure, stage)
            except OSError as exc:
                QMessageBox.critical(self, "Open New Structure failed", str(exc))

            return


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
        self._paint_brush_active = True
        self._selector_active = False
        self._move_active = False
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
        self._layer_paint_brush_panel = LayerPaintBrushPanel()
        self._layer_selector_panel = LayerSelectorPanel()
        self._layer_eraser_panel = LayerEraserPanel()
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
        self._cell_clipboard: CellRegionClipboard | None = None

        self.setStatusBar(self._status)
        self._init_menus()

        self._layer_tools_panel.paint_brush_toggled.connect(self._on_paint_brush_toggled)
        self._layer_tools_panel.selector_toggled.connect(self._on_selector_toggled)
        self._layer_tools_panel.selector_mode_changed.connect(self._on_selector_mode_changed)
        self._layer_tools_panel.move_toggled.connect(self._on_move_toggled)
        self._layer_tools_panel.eraser_toggled.connect(self._on_eraser_toggled)
        self._layer_eraser_panel.eraser_size_changed.connect(self._on_eraser_size_changed)
        self._layer_tools_panel.clear_entire_layer_requested.connect(self._on_clear_entire_layer)
        self._layer_tools_panel.copy_requested.connect(self._on_copy_cells)
        self._layer_tools_panel.paste_requested.connect(self._on_paste_cells)
        self._layer_tools_panel.rotate_left_requested.connect(
            lambda: self._on_rotate_layer(clockwise=False)
        )
        self._layer_tools_panel.rotate_right_requested.connect(
            lambda: self._on_rotate_layer(clockwise=True)
        )
        self._layer_tools_panel.painting_grid_toggled.connect(self._on_painting_grid_toggled)
        self._layer_paint_brush_panel.brush_mode_changed.connect(self._on_paint_brush_mode_changed)
        self._groups_panel.group_selected.connect(self._on_group_filter_selected)
        self._groups_panel.visibility_toggled.connect(self._on_group_visibility_toggled)
        self._groups_panel.add_requested.connect(self._on_add_group)
        self._groups_panel.delete_requested.connect(self._on_delete_group)
        self._groups_panel.copy_requested.connect(self._on_copy_group)
        self._groups_panel.paste_requested.connect(self._on_paste_group)
        self._groups_panel.edit_requested.connect(self._on_edit_group)
        self._groups_panel.move_up_requested.connect(self._on_move_group_up)
        self._groups_panel.move_down_requested.connect(self._on_move_group_down)
        self._layer_list_panel.layer_selected.connect(self._on_layer_list_selected)
        self._layer_list_panel.move_up_requested.connect(self._on_move_layer_up)
        self._layer_list_panel.move_down_requested.connect(self._on_move_layer_down)
        self._layer_list_panel.visibility_toggled.connect(self._on_layer_visibility_toggled)
        self._layer_list_panel.add_requested.connect(self._on_add_layer)
        self._layer_list_panel.edit_requested.connect(self._on_edit_layer)
        self._layer_list_panel.delete_requested.connect(self._on_delete_layer)
        self._layer_list_panel.copy_requested.connect(self._on_copy_layer)
        self._layer_list_panel.paste_requested.connect(self._on_paste_layer)
        self._save_site_button.clicked.connect(self._save_site_settings)
        self._site_settings_panel.settings_changed.connect(self._on_site_settings_changed)
        self._apply_block_tooltips_pref(block_tooltips_enabled())
        self._apply_grid_axis_labels_pref(grid_axis_labels_enabled())
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
        self._structure_grid.cell_erase_matching_requested.connect(self._on_erase_matching_cells)
        self._structure_grid.paint_region_fill_requested.connect(self._on_paint_region_fill)
        self._structure_grid.cell_erase_requested.connect(self._on_cell_erase)
        self._structure_grid.eraser_region_erase_requested.connect(self._on_eraser_region_erase)
        self._structure_grid.move_region_requested.connect(self._on_move_region)
        self._structure_grid.move_selection_empty.connect(self._on_move_selection_empty)
        self._structure_grid.itemSelectionChanged.connect(self._on_grid_selection_changed)
        self._materials_panel.scope_changed.connect(self._refresh_materials_list)

        palette_column = QWidget()
        self._palette_column_layout = QVBoxLayout(palette_column)
        self._palette_column_layout.setContentsMargins(0, 0, 0, 0)
        self._palette_column_layout.setSpacing(0)
        self._palette_column_layout.addWidget(self._palette_panel)
        self._palette_column_layout.addWidget(self._groups_panel)
        self._palette_column_layout.addWidget(self._layer_list_panel)
        self._update_palette_column_layout()

        self._structure_properties_dialog = QDialog(self)
        self._structure_properties_dialog.setWindowTitle("Structure Properties")
        self._structure_properties_dialog.setModal(True)
        self._structure_properties_dialog_layout = QVBoxLayout(self._structure_properties_dialog)
        self._structure_properties_dialog_layout.setContentsMargins(0, 0, 0, 0)
        self._structure_properties_dialog_layout.addWidget(self._structure_settings_panel)
        self._structure_properties_buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            self._structure_properties_dialog,
        )
        self._structure_properties_buttons.accepted.connect(
            self._on_save_structure_properties_requested
        )
        self._structure_properties_buttons.rejected.connect(
            self._structure_properties_dialog.reject
        )
        self._structure_properties_dialog_layout.addWidget(self._structure_properties_buttons)
        self._structure_settings_panel.close_requested.connect(
            self._structure_properties_dialog.reject
        )

        structure_header = self._build_structure_header()
        self._structure_grid_viewport = LayerGridViewport(self._structure_grid)

        structure_center = QWidget()
        structure_center_layout = QVBoxLayout(structure_center)
        structure_center_layout.setContentsMargins(0, 0, 0, 0)
        structure_center_layout.addWidget(structure_header)
        structure_center_layout.addWidget(self._structure_grid_viewport, stretch=1)

        self._materials_panel.close_requested.connect(self._hide_materials_panel)

        structure_tools_column = QWidget()
        self._structure_tools_layout = QVBoxLayout(structure_tools_column)
        self._structure_tools_layout.setContentsMargins(0, 0, 0, 0)
        self._structure_tools_layout.setSpacing(0)
        self._structure_tools_bottom_spacer: QSpacerItem | None = None
        self._compass_panel.close_requested.connect(self._hide_compass_panels)
        self._structure_tools_layout.addWidget(self._compass_panel)
        self._structure_tools_layout.addWidget(self._layer_paint_brush_panel)
        self._structure_tools_layout.addWidget(self._layer_selector_panel)
        self._structure_tools_layout.addWidget(self._layer_eraser_panel)
        self._structure_tools_layout.addWidget(self._properties_panel)
        self._structure_tools_layout.addWidget(self._materials_panel)
        self._sync_layer_tool_panels()

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
        QApplication.instance().installEventFilter(self)

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
        self._update_cell_clipboard_actions()
        self.resize(1280, 800)
        self._update_structure_tools_column_layout()
        self._apply_panel_visibility_prefs()
        self._status.showMessage(
            "Structure tab: paint cells (Undo supported). Site tab: footprint and placement.",
            6000,
        )
        self._update_undo_actions()

    def _init_menus(self) -> None:
        self._init_file_menu()
        self._init_edit_menu()
        self._init_view_menu()
        self._init_structure_menu()
        self._init_help_menu()

    def _init_structure_menu(self) -> None:
        structure_menu = self.menuBar().addMenu("&Structure")

        new_stage_action = QAction("&New Stage...", self)
        new_stage_action.triggered.connect(self._on_new_stage)
        structure_menu.addAction(new_stage_action)

        stage_properties_action = QAction("Stage &Properties...", self)
        stage_properties_action.triggered.connect(self._on_open_stage_properties)
        structure_menu.addAction(stage_properties_action)

        structure_menu.addSeparator()

        delete_stage_action = QAction("&Delete Stage...", self)
        delete_stage_action.triggered.connect(self._on_delete_stage)
        structure_menu.addAction(delete_stage_action)

        structure_menu.addSeparator()

        structure_properties_action = QAction("Structure &Properties", self)
        structure_properties_action.triggered.connect(self._on_open_structure_properties)
        structure_menu.addAction(structure_properties_action)

    def _init_file_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")

        new_structure_action = QAction("&New Structure", self)
        new_structure_action.setShortcut(QKeySequence("Ctrl+N"))
        new_structure_action.triggered.connect(self._on_new_structure_placeholder)
        file_menu.addAction(new_structure_action)

        open_structure_action = QAction("&Open Structure...", self)
        open_structure_action.setShortcut(QKeySequence.StandardKey.Open)
        open_structure_action.triggered.connect(self._on_open_structure)
        file_menu.addAction(open_structure_action)

        self._open_recent_menu = file_menu.addMenu("Open &Recent")
        self._open_recent_menu.aboutToShow.connect(self._refresh_open_recent_menu)

        file_menu.addSeparator()

        self._save_action = QAction("&Save", self)
        self._save_action.setShortcut(QKeySequence("Ctrl+S"))
        self._save_action.triggered.connect(self._on_save)
        self._save_action.setEnabled(False)
        file_menu.addAction(self._save_action)

        self._save_all_action = QAction("Save A&ll", self)
        self._save_all_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self._save_all_action.triggered.connect(self._save_all)
        self._save_all_action.setEnabled(False)
        file_menu.addAction(self._save_all_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _refresh_open_recent_menu(self) -> None:
        self._open_recent_menu.clear()
        entries = load_recent_structures()

        if entries:
            for index, (structure, stage) in enumerate(entries, start=1):
                action = QAction(_format_recent_entry_label(index, structure, stage), self)
                action.triggered.connect(
                    lambda _checked=False, s=structure, st=stage: self._open_recent_entry(s, st)
                )
                self._open_recent_menu.addAction(action)
        else:
            empty_action = QAction("(No recent files)", self)
            empty_action.setEnabled(False)
            self._open_recent_menu.addAction(empty_action)

        self._open_recent_menu.addSeparator()
        clear_action = QAction("Clear Recent Files", self)
        clear_action.setEnabled(bool(entries))
        clear_action.triggered.connect(self._clear_recent_entries)
        self._open_recent_menu.addAction(clear_action)

    def _clear_recent_entries(self) -> None:
        clear_recent_structures()
        self._refresh_open_recent_menu()
        self._status.showMessage("Cleared recent files.", 3000)

    def _open_recent_entry(self, structure: str, stage: int) -> None:
        current_structure = str(self._document.metadata.get("structure", self._structure))
        current_stage = int(self._document.metadata.get("stage", self._stage))

        if structure == current_structure and int(stage) == current_stage:
            return

        if self._dirty_layers or self._dirty_structure:
            answer = QMessageBox.question(
                self,
                "Unsaved changes",
                "Save unsaved changes before opening a recent structure?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )

            if answer == QMessageBox.StandardButton.Cancel:
                return

            if answer == QMessageBox.StandardButton.Save:
                if self._dirty_structure and not self._save_site_settings():
                    return

                for layer_index in sorted(self._dirty_layers):
                    if not self._save_layer(layer_index):
                        return

        add_recent_structure(structure, stage)

        try:
            open_structure_in_editor_process(structure, stage)
        except OSError as exc:
            QMessageBox.critical(self, "Open recent failed", str(exc))

    def _on_open_structure(self) -> None:
        selection = _pick_structure_stage(self)

        if selection is None:
            return

        structure, stage = selection
        current_structure = str(self._document.metadata.get("structure", self._structure))
        current_stage = int(self._document.metadata.get("stage", self._stage))

        if structure == current_structure and stage == current_stage:
            return

        if self._dirty_layers or self._dirty_structure:
            answer = QMessageBox.question(
                self,
                "Unsaved changes",
                "Save unsaved changes before opening a structure?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )

            if answer == QMessageBox.StandardButton.Cancel:
                return

            if answer == QMessageBox.StandardButton.Save:
                if self._dirty_structure and not self._save_site_settings():
                    return

                for layer_index in sorted(self._dirty_layers):
                    if not self._save_layer(layer_index):
                        return

        add_recent_structure(structure, stage)

        try:
            open_structure_in_editor_process(structure, stage)
        except OSError as exc:
            QMessageBox.critical(self, "Open Structure failed", str(exc))

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

        self._materials_action = QAction("&Materials", self)
        self._materials_action.setCheckable(True)
        self._materials_action.setChecked(True)
        self._materials_action.triggered.connect(self._on_materials_action_triggered)
        view_menu.addAction(self._materials_action)

        self._block_tooltips_action = QAction("Block &tooltips", self)
        self._block_tooltips_action.setCheckable(True)
        self._block_tooltips_action.setChecked(True)
        self._block_tooltips_action.setToolTip(
            "Show block tokens when hovering cells on the structure and site grids"
        )
        self._block_tooltips_action.triggered.connect(self._on_block_tooltips_action_triggered)
        view_menu.addAction(self._block_tooltips_action)

        self._grid_axis_labels_action = QAction("Grid &axis labels", self)
        self._grid_axis_labels_action.setCheckable(True)
        self._grid_axis_labels_action.setChecked(True)
        self._grid_axis_labels_action.triggered.connect(self._on_grid_axis_labels_action_triggered)
        view_menu.addAction(self._grid_axis_labels_action)

    def _on_block_tooltips_action_triggered(self, checked: bool) -> None:
        self._apply_block_tooltips_pref(checked)

    def _on_grid_axis_labels_action_triggered(self, checked: bool) -> None:
        self._apply_grid_axis_labels_pref(checked)

    def _apply_grid_axis_labels_pref(self, enabled: bool) -> None:
        set_grid_axis_labels_enabled(enabled)
        self._structure_grid.set_show_axis_labels(enabled)
        self._grid_axis_labels_action.blockSignals(True)
        self._grid_axis_labels_action.setChecked(enabled)
        self._grid_axis_labels_action.blockSignals(False)

    def _apply_panel_visibility_prefs(self) -> None:
        self._set_compass_panels_visible(panel_compass_visible())
        self._set_materials_panel_visible(panel_materials_visible())

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
        set_panel_compass_visible(visible)
        self._update_structure_tools_column_layout()

    def _on_materials_action_triggered(self, checked: bool) -> None:
        self._set_materials_panel_visible(checked)

    def _hide_materials_panel(self) -> None:
        self._set_materials_panel_visible(False)

    def _set_materials_panel_visible(self, visible: bool) -> None:
        self._materials_action.blockSignals(True)
        self._materials_action.setChecked(visible)
        self._materials_action.blockSignals(False)
        self._materials_panel.setVisible(visible)
        set_panel_materials_visible(visible)
        self._update_structure_tools_column_layout()

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

        edit_menu.addSeparator()

        self._copy_cells_action = QAction("&Copy", self)
        self._copy_cells_action.setShortcut(QKeySequence.StandardKey.Copy)
        self._copy_cells_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self._copy_cells_action.triggered.connect(self._on_copy_cells)
        edit_menu.addAction(self._copy_cells_action)

        self._paste_cells_action = QAction("&Paste", self)
        self._paste_cells_action.setShortcut(QKeySequence.StandardKey.Paste)
        self._paste_cells_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self._paste_cells_action.triggered.connect(self._on_paste_cells)
        edit_menu.addAction(self._paste_cells_action)

        self._delete_cells_action = QAction("&Delete", self)
        self._delete_cells_action.setShortcut(QKeySequence.StandardKey.Delete)
        self._delete_cells_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self._delete_cells_action.triggered.connect(self._on_delete_selected_cells)
        edit_menu.addAction(self._delete_cells_action)

        edit_menu.addSeparator()

        self._select_all_cells_action = QAction("Select &All", self)
        self._select_all_cells_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        self._select_all_cells_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self._select_all_cells_action.triggered.connect(self._on_select_all_cells)
        edit_menu.addAction(self._select_all_cells_action)

        self._unselect_cells_action = QAction("Unselect &All", self)
        self._unselect_cells_action.triggered.connect(self._on_unselect_cells)
        edit_menu.addAction(self._unselect_cells_action)

    def _on_open_structure_properties(self) -> None:
        self._structure_settings_panel.set_structure_path(self._document.structure_path)
        self._structure_settings_panel.load_from_metadata(self._document.metadata)
        self._structure_properties_dialog.adjustSize()
        size_hint = self._structure_properties_dialog.sizeHint()
        self._structure_properties_dialog.resize(max(460, size_hint.width()), size_hint.height())
        self._structure_properties_dialog.exec()

    def _on_save_structure_properties_requested(self) -> None:
        if self._on_structure_properties_changed():
            self._structure_properties_dialog.accept()

    def _on_open_stage_properties(self) -> None:
        current_stage = int(self._document.metadata.get("stage", self._stage))
        current_width, current_depth = structure_dimensions_from_layers(self._document.layers)
        site_width, site_depth = resolve_site_dimensions(self._document.metadata.get("grid", {}))

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Stage {current_stage} Properties")
        layout = create_dialog_shell(dialog, min_width=460)

        description = QLabel("Adjust the current stage footprint across all layers.")
        description.setWordWrap(True)
        layout.addWidget(description)

        form = create_dialog_form_layout()
        width_spin = QSpinBox(dialog)
        width_spin.setRange(1, max(1, site_width))
        width_spin.setValue(max(1, min(current_width, site_width)))
        width_spin.setSuffix(" x")
        apply_dialog_field_style(width_spin, min_width=DIALOG_FIELD_MIN_WIDTH)
        form.addRow("Stage width", width_spin)

        depth_spin = QSpinBox(dialog)
        depth_spin.setRange(1, max(1, site_depth))
        depth_spin.setValue(max(1, min(current_depth, site_depth)))
        depth_spin.setSuffix(" z")
        apply_dialog_field_style(depth_spin, min_width=DIALOG_FIELD_MIN_WIDTH)
        form.addRow("Stage depth", depth_spin)

        layout.addLayout(form)

        limits_label = QLabel(f"Site maximum: {site_width} x {site_depth}")
        limits_label.setWordWrap(True)
        layout.addWidget(limits_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            parent=dialog,
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.adjustSize()
        size_hint = dialog.sizeHint()
        dialog.resize(max(460, size_hint.width()), size_hint.height())

        if not dialog.exec():
            return

        self._on_structure_resize_requested(width_spin.value(), depth_spin.value())

    def _on_new_stage(self) -> None:
        current_structure = str(self._document.metadata.get("structure", self._structure))
        current_stage = int(self._document.metadata.get("stage", self._stage))
        site_width, site_depth = resolve_site_dimensions(self._document.metadata.get("grid", {}))
        structure_width, structure_depth = structure_dimensions_from_layers(self._document.layers)
        default_stage = current_stage + 1

        existing = _structure_stage_choices(STRUCTURES_FOLDER / current_structure)
        if existing:
            default_stage = max(stage for _, stage in existing) + 1

        while True:
            dialog = NewStructureDialog(
                self,
                structure=current_structure,
                stage=default_stage,
                site_width=site_width,
                site_depth=site_depth,
                structure_width=structure_width,
                structure_depth=structure_depth,
                dimension=str(self._document.metadata.get("dimension", "overworld")),
                title="New Stage",
                allow_structure_edit=False,
                allow_stage_edit=False,
                show_site_size_fields=False,
                show_dimension_field=False,
            )

            if not dialog.exec():
                return

            (
                selected_structure,
                stage,
                selected_site_width,
                selected_site_depth,
                selected_structure_width,
                selected_structure_depth,
                _selected_dimension,
            ) = dialog.values()

            if selected_structure != current_structure:
                QMessageBox.warning(
                    self,
                    "New Stage",
                    "Structure cannot be changed from Structure > New Stage.",
                )
                continue

            if self._dirty_layers or self._dirty_structure:
                answer = QMessageBox.question(
                    self,
                    "Unsaved changes",
                    "Save unsaved changes before creating and opening the new stage?",
                    QMessageBox.StandardButton.Save
                    | QMessageBox.StandardButton.Discard
                    | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Save,
                )

                if answer == QMessageBox.StandardButton.Cancel:
                    return

                if answer == QMessageBox.StandardButton.Save:
                    if self._dirty_structure and not self._save_site_settings():
                        return

                    for layer_index in sorted(self._dirty_layers):
                        if not self._save_layer(layer_index):
                            return

            try:
                create_structure_stage_document(
                    structure=current_structure,
                    stage=stage,
                    site_width=selected_site_width,
                    site_depth=selected_site_depth,
                    structure_width=selected_structure_width,
                    structure_depth=selected_structure_depth,
                    dimension=str(self._document.metadata.get("dimension", "overworld")),
                )
            except (FileExistsError, ValueError) as exc:
                QMessageBox.warning(self, "New Stage", str(exc))
                default_stage = stage + 1
                continue
            except OSError as exc:
                QMessageBox.critical(self, "New Stage", str(exc))
                return

            add_recent_structure(current_structure, stage)
            open_structure_in_editor_process(current_structure, stage)
            return

    def _on_delete_stage(self) -> None:
        structure = str(self._document.metadata.get("structure", self._structure))
        stage = int(self._document.metadata.get("stage", self._stage))

        answer = QMessageBox.question(
            self,
            "Delete Stage",
            f"Delete {structure} stage {stage}? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        if self._dirty_layers or self._dirty_structure:
            save_answer = QMessageBox.question(
                self,
                "Unsaved changes",
                "Save unsaved changes before deleting this stage?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )

            if save_answer == QMessageBox.StandardButton.Cancel:
                return

            if save_answer == QMessageBox.StandardButton.Save:
                if self._dirty_structure and not self._save_site_settings():
                    return

                for layer_index in sorted(self._dirty_layers):
                    if not self._save_layer(layer_index):
                        return

        try:
            delete_structure_stage_document(structure=structure, stage=stage)
        except (FileNotFoundError, ValueError, OSError) as exc:
            QMessageBox.critical(self, "Delete Stage", str(exc))
            return

        remaining = _structure_stage_choices(STRUCTURES_FOLDER / structure)
        if remaining:
            _, next_stage = remaining[0]
            add_recent_structure(structure, next_stage)
            open_structure_in_editor_process(structure, next_stage)
            return

        open_editor_in_empty_state_process()

    def _init_help_menu(self) -> None:
        help_menu = self.menuBar().addMenu("&Help")

        documentation_action = QAction("&Documentation", self)
        documentation_action.triggered.connect(self._open_structure_editor_guide)
        help_menu.addAction(documentation_action)

    def _open_structure_editor_guide(self) -> None:
        QDesktopServices.openUrl(QUrl(_STRUCTURE_EDITOR_GUIDE_URL))

    def _on_new_structure_placeholder(self) -> None:
        site_width, site_depth = 15, 15
        structure_width, structure_depth = 9, 9
        default_structure = ""

        while True:
            dialog = NewStructureDialog(
                self,
                structure=default_structure,
                stage=1,
                site_width=site_width,
                site_depth=site_depth,
                structure_width=structure_width,
                structure_depth=structure_depth,
                allow_stage_edit=False,
            )

            if not dialog.exec():
                self._status.showMessage("New structure canceled.", 2500)
                return

            (
                structure,
                stage,
                selected_site_width,
                selected_site_depth,
                selected_structure_width,
                selected_structure_depth,
                dimension,
            ) = dialog.values()

            default_structure = structure
            site_width = selected_site_width
            site_depth = selected_site_depth
            structure_width = selected_structure_width
            structure_depth = selected_structure_depth

            try:
                structure_path = create_structure_stage_document(
                    structure=structure,
                    stage=stage,
                    site_width=selected_site_width,
                    site_depth=selected_site_depth,
                    structure_width=selected_structure_width,
                    structure_depth=selected_structure_depth,
                    dimension=dimension,
                )
            except FileExistsError as exc:
                QMessageBox.warning(self, "New Structure", str(exc))
                continue
            except ValueError as exc:
                QMessageBox.warning(self, "New Structure", str(exc))
                continue
            except OSError as exc:
                QMessageBox.critical(self, "Save failed", str(exc))
                return

            if self._dirty_layers or self._dirty_structure:
                answer = QMessageBox.question(
                    self,
                    "Open New Structure",
                    "Open the newly created structure now and discard unsaved changes "
                    "in the current editor?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )

                if answer != QMessageBox.StandardButton.Yes:
                    self._status.showMessage(f"Created {structure_path}", 5000)
                    return

            self._status.showMessage(f"Created {structure_path}. Opening...", 2000)
            add_recent_structure(structure, stage)

            try:
                open_structure_in_editor_process(structure, stage)
            except OSError as exc:
                QMessageBox.critical(
                    self,
                    "Open New Structure failed",
                    f"Created:\n{structure_path}\n\nCould not open automatically:\n{exc}",
                )
            return

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
                group_filter=self._group_filter,
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
                group_filter=self._group_filter,
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
                group_filter=self._group_filter,
            )
        )
        state = self._redo_stack.pop()
        self._restore_history_state(state)
        self._status.showMessage("Redone.", 2000)

    def _restore_history_state(self, state) -> None:
        self._ensure_eraser_drag_closed()
        self._restoring_history = True

        try:
            dirty_flag = [self._dirty_structure]
            group_filter_flag: list[str | None] = [self._group_filter]
            apply_history_state(
                self._document,
                state,
                dirty_layers=self._dirty_layers,
                dirty_structure_holder=dirty_flag,
                group_filter_holder=group_filter_flag,
            )
            self._dirty_structure = dirty_flag[0]
            self._group_filter = group_filter_flag[0]
            self._grid_texture_cache.clear_cache()
            self._layer_clipboard = None
            self._group_clipboard = None
            self._cell_clipboard = None
            self._layer_list_panel.set_paste_enabled(False)
            self._groups_panel.set_paste_enabled(False)
            self._update_cell_clipboard_actions()
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

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if (
            event.type() == QEvent.Type.MouseButtonRelease
            and isinstance(event, QMouseEvent)
            and event.button() == Qt.MouseButton.LeftButton
            and watched is not self._structure_grid.viewport()
        ):
            if self._structure_grid.paint_drag_active():
                self._structure_grid.commit_paint_drag()
            elif self._structure_grid.eraser_drag_active():
                self._structure_grid.commit_eraser_drag()

        return super().eventFilter(watched, event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._update_palette_column_layout()
        self._update_structure_tools_column_layout()
        self._structure_grid.refit_viewport()

    def _update_palette_column_layout(self) -> None:
        """Palettes grow at the top; lower panels pack with no gap when Structure is hidden."""
        layout = self._palette_column_layout

        for widget in (
            self._groups_panel,
            self._layer_list_panel,
        ):
            layout.setStretchFactor(widget, 0)
            widget.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Maximum,
            )

        layout.setStretchFactor(self._palette_panel, 1)
        self._palette_panel.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding,
        )

    def _update_structure_tools_column_layout(self) -> None:
        """Pack visible panels to the top; Materials grows when shown; no empty gaps."""
        layout = self._structure_tools_layout

        for index in range(layout.count()):
            item = layout.itemAt(index)
            widget = item.widget() if item is not None else None

            if widget is None:
                continue

            if widget in (
                self._compass_panel,
                self._layer_paint_brush_panel,
                self._layer_selector_panel,
                self._layer_eraser_panel,
                self._properties_panel,
            ):
                layout.setStretchFactor(widget, 0)
                widget.setSizePolicy(
                    QSizePolicy.Policy.Preferred,
                    QSizePolicy.Policy.Maximum,
                )

        if self._structure_tools_bottom_spacer is not None:
            layout.removeItem(self._structure_tools_bottom_spacer)
            self._structure_tools_bottom_spacer = None

        if self._materials_panel.isVisible():
            layout.setStretchFactor(self._materials_panel, 1)
            self._materials_panel.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Expanding,
            )
        else:
            layout.setStretchFactor(self._materials_panel, 0)
            self._structure_tools_bottom_spacer = QSpacerItem(
                0,
                0,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            )
            layout.addItem(self._structure_tools_bottom_spacer)

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

    _WORLDGEN_INDEX_MIN = -128
    _WORLDGEN_INDEX_MAX = 512

    def _prompt_layer_settings(
        self,
        *,
        layer_index: int | None = None,
    ) -> tuple[int, str, str] | None:
        editing = layer_index is not None
        dialog_title = "Edit layer" if editing else "Add layer"
        grid = self._grid_metadata()
        groups = list(collect_layer_groups(self._document.layers, grid))

        if editing:
            layer = self._document.layers[layer_index]
            y_default = int(layer.get("index", layer_index))
            initial_group = layer.get("group")
            initial_description = str(layer.get("description", ""))

            if isinstance(initial_group, str) and initial_group and initial_group not in groups:
                groups.append(initial_group)
        else:
            y_default = next_worldgen_index(self._document.layers)
            initial_group = self._group_filter if self._group_filter in groups else None
            initial_description = ""

        while True:
            dialog = AddLayerDialog(
                self,
                y_default=y_default,
                y_min=self._WORLDGEN_INDEX_MIN,
                y_max=self._WORLDGEN_INDEX_MAX,
                groups=groups,
                initial_group=initial_group if isinstance(initial_group, str) else None,
                initial_description=initial_description,
                editing=editing,
            )

            if dialog.exec() != AddLayerDialog.DialogCode.Accepted:
                return None

            y_level = dialog.y_level()
            group = dialog.group_name()

            if not group:
                QMessageBox.warning(self, dialog_title, "Group name is required.")
                continue

            if worldgen_index_in_use(
                self._document.layers,
                y_level,
                except_layer_index=layer_index,
            ):
                QMessageBox.warning(
                    self,
                    dialog_title,
                    f"Y level {y_level} is already used by another layer.",
                )
                continue

            if dialog.is_new_group() and group_name_exists(self._document.layers, grid, group):
                QMessageBox.warning(
                    self,
                    dialog_title,
                    f"A group named {group!r} already exists.",
                )
                continue

            return y_level, group, dialog.description()

    def _prompt_add_layer_settings(self) -> tuple[int, str, str] | None:
        return self._prompt_layer_settings()

    def _prompt_group_name(self, *, title: str, label: str, initial: str = "") -> str | None:
        while True:
            dialog = InputTextDialog(
                self,
                title=title,
                field_label=label,
                initial=initial,
            )

            if dialog.exec() != InputTextDialog.DialogCode.Accepted:
                return None

            normalized = dialog.text()

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
        self._group_filter = name
        self._refresh_layer_panels()
        self._persist_dialog_changes(
            success_message=f"Added group {name!r}",
            action_phrase=f"Added group {name!r}",
        )

    def _on_delete_group(self) -> None:
        group = self._groups_panel.selected_group_name()
        if group is None:
            return

        indices = layer_indices_in_group(self._document.layers, group)

        # Guard: cannot delete if it would remove all layers
        if indices and len(self._document.layers) <= len(indices):
            QMessageBox.information(
                self,
                "Delete group",
                "Cannot delete this group: it contains all layers. At least one layer is required.",
            )
            return

        if indices:
            message = f"Delete group {group!r} and its {len(indices)} layer(s)?"
        else:
            message = f"Remove group {group!r}?"

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

        # Delete layers in reverse order to avoid index shifting
        for idx in sorted(indices, reverse=True):
            removed_path = remove_layer_from_document(self._document, idx)
            if removed_path is not None:
                removed_path.unlink()

        # Clean up group metadata (grid.groups, hidden_groups) — no layers remain in group now
        grid = self._grid_metadata()
        remove_group(self._document.layers, grid, group)

        self._dirty_layers = {idx for idx in self._dirty_layers if idx < len(self._document.layers)}

        if self._group_filter == group:
            self._group_filter = None

        new_index = self._clamp_layer_index(self._current_layer_index)
        self._refresh_layer_panels()
        self._show_layer(new_index)
        self._persist_dialog_changes(
            success_message=f"Deleted group {group!r}",
            action_phrase=f"Deleted group {group!r}",
        )

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
        new_indices: list[int] = []

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
                    description=str(source.get("description", "")),
                    cells=cells,
                )
                new_indices.append(append_layer_to_document(self._document, layer))

        self._group_filter = new_name
        self._refresh_layer_panels()

        if clipboard_layers:
            self._show_layer(len(self._document.layers) - 1)

        self._persist_dialog_changes(
            layer_indices=new_indices,
            success_message=f"Pasted group as {new_name!r}",
            action_phrase=f"Pasted group as {new_name!r}",
        )

    def _on_edit_group(self) -> None:
        old_name = self._groups_panel.selected_group_name()

        if old_name is None:
            return

        dialog = EditGroupDialog(self, initial_name=old_name)

        if dialog.exec() != EditGroupDialog.DialogCode.Accepted:
            return

        new_name = dialog.group_name()

        if not new_name:
            QMessageBox.warning(self, "Edit group", "Group name is required.")
            return

        self._on_group_renamed(old_name, new_name)

    def _on_group_renamed(self, old_name: str, new_name: str) -> None:
        normalized = new_name.strip()

        if not normalized:
            self._refresh_layer_panels()
            return

        if normalized == old_name:
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

        has_old_name = any(
            layer_label(layer, index) == old_name
            for index, layer in enumerate(self._document.layers)
        ) or old_name in get_defined_groups(grid)

        if not has_old_name:
            self._refresh_layer_panels()
            return

        self._push_undo_snapshot()
        rename_group(self._document.layers, grid, old_name, normalized)
        affected_indices = layer_indices_in_group(self._document.layers, normalized)

        if self._group_filter == old_name:
            self._group_filter = normalized

        self._refresh_layer_panels()
        self._persist_dialog_changes(
            layer_indices=affected_indices,
            success_message=f"Group renamed to {normalized!r}",
            action_phrase=f"Group renamed to {normalized!r}",
        )

    def _on_layer_list_selected(self, index: int) -> None:
        self._on_layer_changed(index)

    def _on_move_group_up(self) -> None:
        self._move_group_by_delta(-1)

    def _on_move_group_down(self) -> None:
        self._move_group_by_delta(1)

    def _move_group_by_delta(self, delta: int) -> None:
        group = self._groups_panel.selected_group_name()

        if group is None:
            return

        if not self._confirm_discard_layer_changes(self._current_layer_index):
            return

        self._push_undo_snapshot()
        grid = self._document.metadata.setdefault("grid", {})
        permutation = move_group(self._document.layers, grid, group, delta)

        if permutation is None:
            return

        old_current = self._current_layer_index
        identity = list(range(len(permutation)))

        if permutation != identity:
            reorder_layers_in_document(self._document, permutation)
            self._dirty_layers = remap_indices_after_permutation(
                self._dirty_layers,
                permutation,
            )

            for layer_index in range(len(permutation)):
                self._mark_layer_dirty(layer_index)

            if old_current in permutation:
                self._current_layer_index = permutation.index(old_current)

        self._dirty_structure = True
        self._refresh_layer_panels()
        self._show_layer(self._current_layer_index)
        self._update_save_site_button()
        direction = "up" if delta < 0 else "down"
        self._status.showMessage(
            f"Moved group {group!r} {direction} — save affected layers and site settings",
            5000,
        )

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
        swapped = move_layer_by_worldgen_delta(self._document, index, delta)

        if swapped is None:
            return

        layer_index, other_index = swapped
        self._mark_layer_dirty(layer_index)
        self._mark_layer_dirty(other_index)
        self._refresh_layer_panels()
        self._show_layer(layer_index)
        direction = "up" if delta < 0 else "down"
        self._status.showMessage(
            f"Moved layer {direction} in Y order — save affected layers",
            5000,
        )

    def _on_add_layer(self) -> None:
        if not self._confirm_discard_layer_changes(self._current_layer_index):
            return

        settings = self._prompt_add_layer_settings()

        if settings is None:
            return

        worldgen_index, group, description = settings
        width, depth = structure_dimensions_from_layers(self._document.layers)
        layer = create_layer(
            width=width,
            depth=depth,
            worldgen_index=worldgen_index,
            group=group,
            description=description,
        )

        self._push_undo_snapshot()
        grid = self._grid_metadata()
        add_defined_group(grid, group)
        new_index = append_layer_to_document(self._document, layer)
        label = layer_display_label(layer, new_index)

        self._refresh_layer_panels()
        self._show_layer(new_index)
        self._persist_dialog_changes(
            layer_indices=[new_index],
            success_message=f"Added {label!r} to {group!r} at Y={worldgen_index}",
            action_phrase=f"Added {label!r}",
        )

    def _on_edit_layer(self) -> None:
        layer_index = self._current_layer_index
        layer = self._document.layers[layer_index]
        settings = self._prompt_layer_settings(layer_index=layer_index)

        if settings is None:
            return

        worldgen_index, group, description = settings
        current_group = str(layer.get("group", ""))
        current_description = str(layer.get("description", "")).strip()
        current_y = int(layer.get("index", layer_index))

        if (
            worldgen_index == current_y
            and group == current_group
            and description == current_description
        ):
            return

        self._push_undo_snapshot()
        grid = self._grid_metadata()
        layer["index"] = worldgen_index
        layer["group"] = group
        set_layer_description(layer, description)
        add_defined_group(grid, group)
        label = layer_display_label(layer, layer_index)

        self._refresh_layer_panels()
        self._persist_dialog_changes(
            layer_indices=[layer_index],
            success_message=f"Updated {label!r} — {group!r} at Y={worldgen_index}",
            action_phrase=f"Updated {label!r}",
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

        self._dirty_layers = {
            index for index in self._dirty_layers if index < len(self._document.layers)
        }

        new_index = self._clamp_layer_index(self._current_layer_index)
        self._refresh_layer_panels()
        self._show_layer(new_index)
        self._persist_dialog_changes(
            success_message="Layer deleted",
            action_phrase="Layer deleted",
        )

    def _on_copy_layer(self) -> None:
        layer = self._document.layers[self._current_layer_index]
        self._layer_clipboard = copy_layer_dict(layer)
        self._layer_list_panel.set_paste_enabled(True)
        self._status.showMessage(
            f"Copied {layer_display_label(layer, self._current_layer_index)}",
            3000,
        )

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
            description=str(source.get("description", "")),
            cells=source["cells"],
        )

        self._push_undo_snapshot()
        new_index = append_layer_to_document(self._document, layer)
        label = layer_display_label(layer, new_index)
        self._refresh_layer_panels()
        self._show_layer(new_index)
        self._persist_dialog_changes(
            layer_indices=[new_index],
            success_message=f"Pasted as {label!r}",
            action_phrase=f"Pasted as {label!r}",
        )

    def _build_site_header(self) -> QWidget:
        header = QWidget()
        layout = QHBoxLayout(header)
        self._site_layer_label = QLabel("")
        layout.addWidget(self._site_layer_label, stretch=1)
        layout.addWidget(self._save_site_button)
        return header

    def _on_tab_changed(self, index: int) -> None:
        self._update_cell_clipboard_actions()

        if index == 0:
            self._status.showMessage(
                "Paint structure cells — palette and brush on the right.",
                4000,
            )
            self._update_structure_tools_column_layout()
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

        self._update_save_actions()

    def _on_palette_entry_selected(self, entry) -> None:
        if self._eraser_active:
            self._layer_tools_panel.set_eraser_checked(False)
            self._eraser_active = False

        if self._selector_active:
            self._layer_tools_panel.set_selector_checked(False)
            self._selector_active = False

        if self._move_active:
            self._layer_tools_panel.set_move_checked(False)
            self._move_active = False
            self._ensure_move_state_closed()

        if not self._paint_brush_active:
            self._layer_tools_panel.set_paint_brush_checked(True)
            self._paint_brush_active = True

        self._sync_layer_tool_panels()
        self._properties_panel.show_picker_entry(entry)

    def _sync_layer_tool_panels(self) -> None:
        paint_visible = (
            self._paint_brush_active
            and not self._eraser_active
            and not self._selector_active
            and not self._move_active
        )
        selector_picker_visible = (
            self._selector_active and self._selector_homogeneous_entry() is not None
        )
        picker_visible = paint_visible or selector_picker_visible
        inspector_visible = (
            (self._paint_brush_active or self._selector_active)
            and not self._eraser_active
            and not self._move_active
        )
        self._layer_paint_brush_panel.setVisible(paint_visible)
        self._properties_panel.setVisible(inspector_visible)
        self._properties_panel.set_picker_group_visible(picker_visible)
        self._layer_selector_panel.setVisible(self._selector_active)
        if self._selector_active:
            self._update_selector_selection_display()
        selector_mode = self._layer_tools_panel.selector_mode()
        self._layer_selector_panel.set_hint_for_mode(
            rectangle=selector_mode is SelectorMode.RECTANGLE,
        )
        self._layer_eraser_panel.setVisible(self._eraser_active)
        self._structure_grid.set_selector_active(self._selector_active)
        self._structure_grid.set_selector_mode(selector_mode)
        self._structure_grid.set_move_active(self._move_active)
        self._structure_grid.set_paint_brush_active(self._paint_brush_active)
        self._structure_grid.set_paint_brush_mode(self._layer_paint_brush_panel.paint_brush_mode())
        self._update_structure_eraser_preview()
        self._update_structure_tools_column_layout()

    def _update_structure_eraser_preview(self) -> None:
        self._structure_grid.set_eraser_preview(
            active=self._eraser_active,
            size=self._layer_eraser_panel.eraser_size(),
        )

    def _on_eraser_size_changed(self, _size: int) -> None:
        self._ensure_eraser_drag_closed()
        self._update_structure_eraser_preview()

    def _ensure_paint_drag_closed(self) -> None:
        if self._structure_grid.paint_drag_active():
            self._structure_grid.cancel_paint_drag()

    def _ensure_eraser_drag_closed(self) -> None:
        """Cancel an in-progress eraser marquee (e.g. mouse released outside the grid)."""
        self._ensure_paint_drag_closed()
        if self._structure_grid.eraser_drag_active():
            self._structure_grid.cancel_eraser_drag()

    def _ensure_move_state_closed(self) -> None:
        self._structure_grid.cancel_move_state()

    def _sync_eraser_panel_bounds(self) -> None:
        layer = self._document.layers[self._current_layer_index]
        cells = layer.get("cells") or []

        if not cells:
            self._layer_eraser_panel.set_grid_bounds(width=1, depth=1)
            return

        depth = len(cells)
        width = len(cells[0]) if cells else 1
        self._layer_eraser_panel.set_grid_bounds(width=width, depth=depth)

    def _on_paint_brush_mode_changed(self) -> None:
        self._structure_grid.set_paint_brush_mode(self._layer_paint_brush_panel.paint_brush_mode())

    def _on_paint_region_fill(
        self,
        row_a: int,
        col_a: int,
        row_b: int,
        col_b: int,
    ) -> None:
        if not self._paint_brush_active:
            return

        token = self._properties_panel.build_placement_token()

        if token is None:
            self._status.showMessage(
                "Choose a palette block before painting.",
                4000,
            )
            return

        layer = self._document.layers[self._current_layer_index]
        cells = layer["cells"]
        depth = len(cells)
        width = len(cells[0]) if cells else 0

        if depth == 0 or width == 0:
            return

        mode = self._layer_paint_brush_panel.paint_brush_mode()
        indices = region_cell_indices(
            row_a,
            col_a,
            row_b,
            col_b,
            rows=depth,
            cols=width,
            mode=mode,
        )
        to_place = [(r, c) for r, c in indices if cells[r][c] != token]

        if not to_place:
            self._status.showMessage("Selection already matches the brush.", 3000)
            return

        self._grid_texture_cache.invalidate_token(token)
        self._push_undo_snapshot()

        last_row, last_col = to_place[0]

        for row, col in to_place:
            cells[row][col] = token
            self._structure_grid.update_cell(row, col, token)
            last_row, last_col = row, col

        if self._current_layer_index == self._site_preview_layer_index():
            self._refresh_site_preview()

        self._mark_layer_dirty(self._current_layer_index)
        self._properties_panel.show_grid_cell(last_row, last_col, token)
        self._refresh_materials_list()

        count = len(to_place)
        mode_label = "outline" if mode == "outline" else "fill"

        self._status.showMessage(
            f"Placed {count} cell{'s' if count != 1 else ''} ({mode_label} brush).",
            4000,
        )

    def _on_eraser_region_erase(
        self,
        row_a: int,
        col_a: int,
        row_b: int,
        col_b: int,
    ) -> None:
        layer = self._document.layers[self._current_layer_index]
        cells = layer["cells"]
        depth = len(cells)
        width = len(cells[0]) if cells else 0

        if depth == 0 or width == 0:
            return

        indices = rect_cell_indices(row_a, col_a, row_b, col_b, rows=depth, cols=width)
        to_clear = [(r, c) for r, c in indices if cells[r][c] != "."]

        if not to_clear:
            self._status.showMessage("No blocks to erase in that region.", 3000)
            return

        self._push_undo_snapshot()

        last_row, last_col = to_clear[0]

        for row, col in to_clear:
            cells[row][col] = "."
            self._structure_grid.update_cell(row, col, ".")
            last_row, last_col = row, col

        if self._current_layer_index == self._site_preview_layer_index():
            self._refresh_site_preview()

        self._mark_layer_dirty(self._current_layer_index)
        self._properties_panel.show_grid_cell(last_row, last_col, ".")
        self._refresh_materials_list()

        count = len(to_clear)

        self._status.showMessage(
            f"Erased {count} cell{'s' if count != 1 else ''} in selected region.",
            4000,
        )

    def _erase_cells_at(self, row: int, col: int) -> None:
        layer = self._document.layers[self._current_layer_index]
        cells = layer["cells"]
        depth = len(cells)
        width = len(cells[0]) if cells else 0

        if depth == 0 or width == 0:
            return

        size = self._layer_eraser_panel.eraser_size() if self._eraser_active else 1
        indices = square_cell_indices(row, col, size, rows=depth, cols=width)
        to_clear = [(r, c) for r, c in indices if cells[r][c] != "."]

        if not to_clear:
            return

        self._push_undo_snapshot()

        last_row, last_col = row, col

        for r, c in to_clear:
            cells[r][c] = "."
            self._structure_grid.update_cell(r, c, ".")
            last_row, last_col = r, c

        self._mark_layer_dirty(self._current_layer_index)
        self._properties_panel.show_grid_cell(last_row, last_col, ".")

        if self._current_layer_index == self._site_preview_layer_index():
            self._refresh_site_preview()

        self._refresh_materials_list()

    def _on_paint_brush_toggled(self, active: bool) -> None:
        self._paint_brush_active = active

        if active:
            self._layer_tools_panel.set_selector_checked(False)
            self._selector_active = False
            self._layer_tools_panel.set_move_checked(False)
            self._move_active = False
            self._ensure_move_state_closed()
            self._layer_tools_panel.set_eraser_checked(False)
            self._eraser_active = False
            self._ensure_eraser_drag_closed()
            self._status.showMessage(
                "Paint brush active — choose a palette block, then drag on the grid to paint.",
                4000,
            )
        else:
            self._status.showMessage("Paint brush off — use Selector to choose cells.", 3000)

        self._sync_layer_tool_panels()
        self._update_window_title()

    def _on_move_toggled(self, active: bool) -> None:
        self._move_active = active

        if active:
            self._ensure_paint_drag_closed()
            self._layer_tools_panel.set_paint_brush_checked(False)
            self._paint_brush_active = False
            self._layer_tools_panel.set_selector_checked(False)
            self._selector_active = False
            self._layer_tools_panel.set_eraser_checked(False)
            self._eraser_active = False
            self._ensure_eraser_drag_closed()
            self._palette_panel.clear_selection()
            self._properties_panel.clear_picker_entry()
            self._status.showMessage(
                "Move active — drag to select blocks, then drag to the new location.",
                6000,
            )
        else:
            self._ensure_move_state_closed()
            self._layer_tools_panel.set_paint_brush_checked(True)
            self._paint_brush_active = True
            self._status.showMessage("Paint brush active — choose a palette block to paint.", 3000)

        self._sync_layer_tool_panels()
        self._update_window_title()

    def _selector_status_message(self) -> str:
        if self._layer_tools_panel.selector_mode() is SelectorMode.SAME_BLOCK:
            return "Same block selection — click a block to select matching cells."
        return "Rectangle selection — drag to select cells."

    def _on_selector_toggled(self, active: bool) -> None:
        self._selector_active = active

        if active:
            self._ensure_paint_drag_closed()
            self._layer_tools_panel.set_paint_brush_checked(False)
            self._paint_brush_active = False
            self._layer_tools_panel.set_move_checked(False)
            self._move_active = False
            self._ensure_move_state_closed()
            self._layer_tools_panel.set_eraser_checked(False)
            self._eraser_active = False
            self._ensure_eraser_drag_closed()
            self._status.showMessage(self._selector_status_message(), 4000)
            self._sync_selector_brush_from_selection()
        else:
            self._layer_tools_panel.set_paint_brush_checked(True)
            self._paint_brush_active = True
            self._status.showMessage("Paint brush active — choose a palette block to paint.", 3000)

        self._sync_layer_tool_panels()
        self._update_window_title()

    def _on_selector_mode_changed(self, mode: SelectorMode) -> None:
        self._structure_grid.set_selector_mode(mode)
        self._structure_grid.clear_cell_selection()
        self._layer_selector_panel.set_hint_for_mode(
            rectangle=mode is SelectorMode.RECTANGLE,
        )

        if self._selector_active:
            self._status.showMessage(self._selector_status_message(), 4000)

    def _on_eraser_toggled(self, active: bool) -> None:
        self._eraser_active = active

        if active:
            self._ensure_paint_drag_closed()
            self._layer_tools_panel.set_paint_brush_checked(False)
            self._paint_brush_active = False
            self._layer_tools_panel.set_selector_checked(False)
            self._selector_active = False
            self._layer_tools_panel.set_move_checked(False)
            self._move_active = False
            self._ensure_move_state_closed()
            self._palette_panel.clear_selection()
            self._properties_panel.clear_picker_entry()
            self._sync_eraser_panel_bounds()
            self._status.showMessage(
                "Eraser active — left-click or right-click cells to clear "
                f"(size {self._layer_eraser_panel.eraser_size()}).",
            )
        else:
            self._layer_tools_panel.set_paint_brush_checked(True)
            self._paint_brush_active = True
            self._status.showMessage("Paint brush active — choose a palette block to paint.", 3000)

        self._sync_layer_tool_panels()
        self._update_window_title()

    def _on_rotate_layer(self, *, clockwise: bool) -> None:
        if not self._structure_tab_active():
            return

        if not any(layer.get("cells") for layer in self._document.layers):
            self._status.showMessage("All layers are empty.", 3000)
            return

        self._push_undo_snapshot()

        for index, entry in enumerate(self._document.layers):
            entry_cells = entry.get("cells", [])

            if not entry_cells:
                continue

            entry["cells"] = rotate_layer_cells(entry_cells, clockwise=clockwise)
            self._mark_layer_dirty(index)

        layer_index = self._current_layer_index
        self._structure_grid.set_layer_cells(self._document.layers[layer_index]["cells"])
        self._properties_panel.clear_grid_cell()
        self._sync_selector_brush_from_selection()
        self._sync_structure_size_controls()
        self._sync_eraser_panel_bounds()

        if self._current_layer_index == self._site_preview_layer_index():
            self._refresh_site_preview()

        self._refresh_materials_list()
        self._sync_layer_list_panel()

        direction = "clockwise" if clockwise else "counter-clockwise"
        layer_count = len(self._document.layers)
        self._status.showMessage(
            f"Rotated all {layer_count} layer{'s' if layer_count != 1 else ''} {direction}.",
            4000,
        )

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
            self._eraser_active = False

        if self._selector_active:
            self._layer_tools_panel.set_selector_checked(False)
            self._selector_active = False

        if self._move_active:
            self._layer_tools_panel.set_move_checked(False)
            self._move_active = False
            self._ensure_move_state_closed()

        if not self._paint_brush_active:
            self._layer_tools_panel.set_paint_brush_checked(True)
            self._paint_brush_active = True

        self._sync_layer_tool_panels()
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
        self._layer_list_panel.set_edit_enabled(layer is not None)
        self._layer_list_panel.set_copy_enabled(layer is not None)
        self._layer_list_panel.set_current_index(index)
        self._update_site_layer_label()
        if index == self._site_preview_layer_index():
            self._refresh_site_preview()
        self._update_save_layer_button()
        self._update_window_title()
        self._refresh_materials_list()
        self._sync_structure_size_controls()
        self._sync_eraser_panel_bounds()
        self._status.showMessage(f"Editing {layer_path.name}")

    def _sync_structure_size_controls(self) -> None:
        site_width, site_depth = resolve_site_dimensions(self._document.metadata.get("grid", {}))
        self._structure_settings_panel.set_site_grid_size(site_width, site_depth)

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

        self._grid_texture_cache.clear_cache()
        self._show_layer(self._current_layer_index)
        self._site_settings_panel.load_from_metadata(
            self._document.metadata,
            self._document.layers,
        )
        self._site_settings_panel.sync_offsets_from_grid(self._document.metadata)
        self._sync_structure_size_controls()
        self._sync_path_panel_from_metadata()
        self._persist_dialog_changes(
            layer_indices=range(len(self._document.layers)),
            success_message=f"Structure grid resized to {new_width}×{new_depth} on all layers.",
            action_phrase=f"Resized structure grid to {new_width}×{new_depth}",
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
        if self._selector_active or self._move_active:
            return

        self._properties_panel.show_grid_cell(row, col, raw_token)
        self._properties_panel.sync_brush_from_cell(raw_token)

    def _on_grid_selection_changed(self) -> None:
        self._structure_grid.highlight_selection()
        self._sync_selector_brush_from_selection()
        self._update_selector_selection_display()
        self._update_cell_clipboard_actions()

    def _selector_homogeneous_entry(self):
        if not self._selector_active:
            return None

        positions = self._structure_grid.selected_cell_positions()

        if not positions:
            return None

        layer = self._document.layers[self._current_layer_index]
        return homogeneous_picker_entry_for_positions(layer["cells"], positions)

    def _sync_selector_brush_from_selection(self) -> None:
        if not self._selector_active:
            return

        positions = self._structure_grid.selected_cell_positions()
        layer = self._document.layers[self._current_layer_index]
        entry = homogeneous_picker_entry_for_positions(layer["cells"], positions)

        if entry is None:
            if positions:
                self._properties_panel.show_selection_summary(positions)
            else:
                self._properties_panel.clear_grid_cell()

            self._properties_panel.clear_picker_entry(emit_brush=False)
            self._sync_layer_tool_panels()
            return

        sample_row, sample_col = min(positions)
        sample_token = layer["cells"][sample_row][sample_col]
        self._properties_panel.show_picker_entry(entry, emit_brush=False)
        self._properties_panel.sync_brush_from_cell(sample_token)

        if len(positions) == 1:
            self._properties_panel.show_grid_cell(sample_row, sample_col, sample_token)
        else:
            self._properties_panel.show_selection_summary(
                positions,
                entry_label=entry.label,
                sample_token=sample_token,
            )

        self._sync_layer_tool_panels()

    def _update_selector_selection_display(self) -> None:
        positions = self._structure_grid.selected_cell_positions()
        self._layer_selector_panel.set_selection_range(grid_axis_selection_range(positions))

    def _structure_tab_active(self) -> bool:
        return self._tabs.currentIndex() == 0

    def _site_tab_active(self) -> bool:
        return self._tabs.currentIndex() == 1

    def _update_cell_clipboard_actions(self) -> None:
        on_structure = self._structure_tab_active()
        has_selection = bool(self._structure_grid.selected_cell_positions())
        can_paste = self._cell_clipboard is not None

        self._layer_tools_panel.set_copy_enabled(on_structure and has_selection)
        self._layer_tools_panel.set_paste_enabled(on_structure and can_paste)
        self._copy_cells_action.setEnabled(on_structure and has_selection)
        self._paste_cells_action.setEnabled(on_structure and can_paste)
        self._delete_cells_action.setEnabled(on_structure and has_selection)
        self._select_all_cells_action.setEnabled(on_structure)
        self._unselect_cells_action.setEnabled(on_structure and has_selection)

    def _on_unselect_cells(self) -> None:
        if not self._structure_tab_active():
            return

        if not self._structure_grid.selected_cell_positions():
            self._status.showMessage("No cells selected.", 2000)
            return

        self._structure_grid.clear_cell_selection()
        self._status.showMessage("Selection cleared.", 3000)

    def _on_select_all_cells(self) -> None:
        if not self._structure_tab_active():
            return

        if self._move_active:
            self._layer_tools_panel.set_move_checked(False)
            self._move_active = False
            self._ensure_move_state_closed()
            self._structure_grid.set_move_active(False)
            self._sync_layer_tool_panels()

        self._ensure_paint_drag_closed()
        self._ensure_eraser_drag_closed()

        layer = self._document.layers[self._current_layer_index]
        positions = occupied_cell_positions(layer.get("cells") or [])

        if not positions:
            self._structure_grid.clearSelection()
            self._on_grid_selection_changed()
            self._status.showMessage("No blocks on this layer.", 3000)
            return

        if not self._selector_active:
            self._layer_tools_panel.set_selector_checked(True)
            self._on_selector_toggled(True)

        self._structure_grid.select_cell_positions(positions)

        count = len(positions)
        plural = "s" if count != 1 else ""
        self._status.showMessage(f"Selected {count} cell{plural} with blocks.", 4000)

    def _on_move_selection_empty(self) -> None:
        self._status.showMessage("Selection has no blocks to move.", 3000)

    def _on_move_region(self, dest_row: int, dest_col: int) -> None:
        if not self._structure_tab_active():
            self._structure_grid.clear_move_pending()
            return

        positions = self._structure_grid.pending_move_positions()

        if not positions:
            self._structure_grid.clear_move_pending()
            return

        layer = self._document.layers[self._current_layer_index]
        changes = move_region(layer["cells"], positions, dest_row, dest_col)
        self._structure_grid.clear_move_pending()

        if not changes:
            self._status.showMessage("Nothing to move (same place or out of bounds).", 3000)
            return

        self._push_undo_snapshot()

        last_row, last_col, last_token = changes[0]

        for row, col, token in changes:
            layer["cells"][row][col] = token
            self._structure_grid.update_cell(row, col, token)
            last_row, last_col, last_token = row, col, token

        if self._current_layer_index == self._site_preview_layer_index():
            self._refresh_site_preview()

        self._mark_layer_dirty(self._current_layer_index)
        self._properties_panel.show_grid_cell(last_row, last_col, last_token)
        self._refresh_materials_list()

        at = grid_axis_position(dest_row, dest_col)
        self._status.showMessage(f"Moved selection to {at}.", 4000)

    def _on_delete_selected_cells(self) -> None:
        if not self._structure_tab_active():
            return

        positions = self._structure_grid.selected_cell_positions()

        if not positions:
            self._status.showMessage("Select cells to delete.", 3000)
            return

        layer = self._document.layers[self._current_layer_index]
        cells = layer["cells"]
        to_clear = [(row, col) for row, col in positions if cells[row][col] != "."]

        if not to_clear:
            self._status.showMessage("Selected cells are already empty.", 3000)
            return

        self._push_undo_snapshot()

        last_row, last_col = to_clear[0]

        for row, col in to_clear:
            cells[row][col] = "."
            self._structure_grid.update_cell(row, col, ".")
            last_row, last_col = row, col

        if self._current_layer_index == self._site_preview_layer_index():
            self._refresh_site_preview()

        self._mark_layer_dirty(self._current_layer_index)
        self._properties_panel.show_grid_cell(last_row, last_col, ".")
        self._refresh_materials_list()
        self._sync_selector_brush_from_selection()

        count = len(to_clear)
        plural = "s" if count != 1 else ""
        self._status.showMessage(f"Deleted {count} cell{plural}.", 4000)

    def _on_copy_cells(self) -> None:
        if not self._structure_tab_active():
            return

        positions = self._structure_grid.selected_cell_positions()

        if not positions:
            self._status.showMessage("Select cells to copy (Ctrl+click or drag).", 3000)
            return

        layer = self._document.layers[self._current_layer_index]
        clipboard = copy_region(layer["cells"], positions)

        if clipboard is None:
            return

        self._cell_clipboard = clipboard
        self._update_cell_clipboard_actions()

        count = len(positions)

        plural = "s" if count != 1 else ""
        region = f"{clipboard.width}×{clipboard.height}"
        self._status.showMessage(
            f"Copied {count} cell{plural} ({region} region).",
            3000,
        )

    def _on_paste_cells(self) -> None:
        if not self._structure_tab_active() or self._cell_clipboard is None:
            return

        self._ensure_eraser_drag_closed()

        anchor = self._structure_grid.selection_anchor() or (0, 0)
        dest_row, dest_col = anchor
        layer = self._document.layers[self._current_layer_index]
        changes = paste_region(layer["cells"], self._cell_clipboard, dest_row, dest_col)

        if not changes:
            self._status.showMessage("Nothing to paste (out of bounds or unchanged).", 3000)
            return

        self._push_undo_snapshot()

        last_row, last_col, last_token = changes[0]

        for row, col, token in changes:
            layer["cells"][row][col] = token
            self._structure_grid.update_cell(row, col, token)
            last_row, last_col, last_token = row, col, token

        if self._current_layer_index == self._site_preview_layer_index():
            self._refresh_site_preview()

        self._mark_layer_dirty(self._current_layer_index)
        self._properties_panel.show_grid_cell(last_row, last_col, last_token)
        self._refresh_materials_list()

        pasted = len(changes)
        plural = "s" if pasted != 1 else ""
        at = grid_axis_position(dest_row, dest_col)
        self._status.showMessage(f"Pasted {pasted} cell{plural} at {at}.", 4000)

    def _on_erase_matching_cells(self, raw_token: str) -> None:
        """Middle-click in eraser mode: clear every cell with the same token."""
        self._ensure_eraser_drag_closed()

        layer = self._document.layers[self._current_layer_index]
        cells = layer["cells"]
        depth = len(cells)
        width = len(cells[0]) if cells else 0

        if depth == 0 or width == 0:
            return

        to_clear = [
            (row, col)
            for row in range(depth)
            for col in range(width)
            if cells[row][col] == raw_token
        ]

        if not to_clear:
            self._status.showMessage("No matching cells to erase.", 3000)
            return

        self._push_undo_snapshot()

        last_row, last_col = to_clear[0]

        for row, col in to_clear:
            cells[row][col] = "."
            self._structure_grid.update_cell(row, col, ".")
            last_row, last_col = row, col

        if self._current_layer_index == self._site_preview_layer_index():
            self._refresh_site_preview()

        self._mark_layer_dirty(self._current_layer_index)
        self._properties_panel.show_grid_cell(last_row, last_col, ".")
        self._refresh_materials_list()

        count = len(to_clear)
        label = raw_token if len(raw_token) <= 40 else f"{raw_token[:38]}…"

        self._status.showMessage(
            f"Erased {count} cell{'s' if count != 1 else ''} matching {label}.",
            4000,
        )

    def _on_cell_pick_block(self, row: int, col: int, raw_token: str) -> None:
        """Middle-click: adopt the cell's block into the palette brush."""
        self._properties_panel.show_grid_cell(row, col, raw_token)

        if raw_token == ".":
            return

        if self._selector_active:
            self._layer_tools_panel.set_selector_checked(False)
            self._selector_active = False

        if self._move_active:
            self._layer_tools_panel.set_move_checked(False)
            self._move_active = False
            self._ensure_move_state_closed()

        if not self._paint_brush_active:
            self._layer_tools_panel.set_paint_brush_checked(True)
            self._paint_brush_active = True

        self._sync_layer_tool_panels()

        entry = picker_entry_for_cell(raw_token)

        if entry is None:
            return

        self._palette_panel.select_entry(entry)
        self._properties_panel.show_picker_entry(entry, emit_brush=False)
        self._properties_panel.sync_brush_from_cell(raw_token)

    def _on_brush_changed(self) -> None:
        self._update_window_title()
        token = self._properties_panel.build_placement_token()

        if token is not None:
            self._grid_texture_cache.invalidate_token(token)

        self._apply_brush_to_selected_cell()

    def _apply_brush_to_selected_cell(self) -> None:
        if self._eraser_active:
            return

        token = self._properties_panel.build_placement_token()

        if token is None:
            return

        if self._selector_active:
            positions = self._structure_grid.selected_cell_positions()

            if (
                not positions
                or homogeneous_picker_entry_for_positions(
                    self._document.layers[self._current_layer_index]["cells"],
                    positions,
                )
                is None
            ):
                return

            self._push_undo_snapshot()

            for row, col in positions:
                self._set_cell(
                    row,
                    col,
                    token,
                    record_undo=False,
                    update_inspector=False,
                    refresh_materials=False,
                )

            self._sync_selector_brush_from_selection()
            self._refresh_materials_list()

            count = len(positions)
            self._status.showMessage(
                f"Updated {count} cell{'s' if count != 1 else ''}.",
                3000,
            )
            return

        if not self._paint_brush_active:
            return

        selected = self._properties_panel.selected_cell()

        if selected is None:
            return

        row, col = selected
        self._set_cell(row, col, token)

    def _on_cell_erase(self, row: int, col: int) -> None:
        self._erase_cells_at(row, col)

    def _set_cell(
        self,
        row: int,
        col: int,
        raw_token: str,
        *,
        record_undo: bool = True,
        update_inspector: bool = True,
        refresh_materials: bool = True,
    ) -> None:
        layer = self._document.layers[self._current_layer_index]
        cells = layer["cells"]

        if cells[row][col] == raw_token:
            return

        if record_undo:
            self._push_undo_snapshot()

        cells[row][col] = raw_token
        self._structure_grid.update_cell(row, col, raw_token)

        if self._current_layer_index == self._site_preview_layer_index():
            self._refresh_site_preview()

        self._mark_layer_dirty(self._current_layer_index)

        if update_inspector:
            self._properties_panel.show_grid_cell(row, col, raw_token)

        if refresh_materials:
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
        self._sync_layer_list_panel()
        self._update_save_layer_button()
        self._update_window_title()

    def _mark_layer_clean(self, layer_index: int) -> None:
        self._dirty_layers.discard(layer_index)
        self._update_save_layer_button()
        self._sync_layer_list_panel()
        self._update_window_title()

    def _on_painting_grid_toggled(self, visible: bool) -> None:
        self._structure_grid.set_cell_grid_visible(visible)

        if visible:
            self._status.showMessage("Cell grid borders shown.", 2500)
        else:
            self._status.showMessage("Cell grid borders hidden.", 2500)

    def _update_save_actions(self) -> None:
        dirty_current_layer = self._current_layer_index in self._dirty_layers

        if self._structure_tab_active():
            self._save_action.setEnabled(dirty_current_layer)
        elif self._site_tab_active():
            self._save_action.setEnabled(self._dirty_structure)
        else:
            self._save_action.setEnabled(False)

        self._save_all_action.setEnabled(bool(self._dirty_layers or self._dirty_structure))

    def _update_save_layer_button(self) -> None:
        self._update_save_actions()

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
        self._block_tooltips_action.blockSignals(True)
        self._block_tooltips_action.setChecked(enabled)
        self._block_tooltips_action.blockSignals(False)

    def _sync_render_output_hint(self) -> None:
        output_folder = self._structure_settings_panel.current_output_folder()
        self._render_panel.set_output_hint(output_folder)
        self._last_schematics_dir = OUTPUT_SCHEMATICS_FOLDER / output_folder

    def _on_structure_properties_changed(self) -> bool:
        previous_metadata = {
            "structure": self._document.metadata.get("structure"),
            "name": self._document.metadata.get("name"),
            "output_folder": self._document.metadata.get("output_folder"),
            "dimension": self._document.metadata.get("dimension"),
            "grid": dict(self._document.metadata.get("grid", {})),
        }
        self._push_undo_snapshot()
        self._structure_settings_panel.apply_to_metadata(self._document.metadata)

        structure_width, structure_depth = structure_dimensions_from_layers(self._document.layers)
        site_width, site_depth = resolve_site_dimensions(self._document.metadata.get("grid", {}))
        size_error = structure_site_size_error(
            structure_width,
            structure_depth,
            site_width,
            site_depth,
        )

        if size_error is not None:
            self._discard_last_undo_snapshot()
            self._document.metadata.update(previous_metadata)
            self._structure_settings_panel.load_from_metadata(self._document.metadata)
            self._status.showMessage(size_error, 4000)
            return False

        self._document.site_ground = resize_site_ground(
            self._document.site_ground,
            site_width,
            site_depth,
        )
        self._structure = str(self._document.metadata.get("structure", self._structure))
        self._stage = int(self._document.metadata.get("stage", self._stage))
        self._site_settings_panel.load_from_metadata(self._document.metadata, self._document.layers)
        self._site_settings_panel.sync_offsets_from_grid(self._document.metadata)
        self._refresh_site_preview()
        self._sync_path_panel_from_metadata()
        self._sync_structure_size_controls()
        self._sync_render_output_hint()
        self._dirty_structure = True
        self._update_save_site_button()
        self._update_window_title()
        return True

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
        self._update_save_layer_button()

    def _persist_dialog_changes(
        self,
        *,
        layer_indices: Iterable[int] = (),
        save_structure: bool = True,
        success_message: str,
        action_phrase: str,
    ) -> None:
        """Save layer YAML and/or structure.yaml after a dialog action."""
        layers_saved = True
        for layer_index in layer_indices:
            if not self._save_layer(layer_index):
                layers_saved = False
                self._mark_layer_dirty(layer_index)

        structure_saved = True
        if save_structure:
            structure_saved = self._write_structure_yaml_to_disk()
            self._dirty_structure = not structure_saved

        self._update_save_site_button()
        self._update_window_title()

        if layers_saved and structure_saved:
            self._status.showMessage(success_message, 4000)
        elif layers_saved:
            self._status.showMessage(
                f"{action_phrase} — save site settings to update structure.yaml",
                5000,
            )
        else:
            self._status.showMessage(
                f"{action_phrase} in editor — save layer and site settings",
                5000,
            )

    def _write_structure_yaml_to_disk(self) -> bool:
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

        return True

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

        if not self._write_structure_yaml_to_disk():
            return False

        self._dirty_structure = False
        self._update_save_site_button()
        self._update_save_layer_button()
        self._update_window_title()
        return True

    def _update_window_title(self) -> None:
        dirty_marker = " (unsaved)" if self._dirty_layers or self._dirty_structure else ""
        title_name = self._document.metadata.get("name", self._structure_name)
        self.setWindowTitle(f"Structure Editor — {title_name}{dirty_marker}")

    def _on_save(self) -> None:
        if self._structure_tab_active():
            self._save_current_layer()
            return

        if self._site_tab_active():
            if not self._dirty_structure:
                self._status.showMessage("Site settings are already saved.", 2000)
                return

            if self._save_site_settings():
                self._status.showMessage("Saved site settings.", 3000)
            return

        self._status.showMessage("Nothing to save on the Render tab.", 2000)

    def _save_current_layer(self) -> None:
        if self._current_layer_index not in self._dirty_layers:
            self._status.showMessage("No unsaved changes on this layer.", 2000)
            return

        if self._save_layer(self._current_layer_index):
            path = self._document.layer_paths[self._current_layer_index]
            self._status.showMessage(f"Saved {path.name}", 3000)

    def _save_all(self) -> None:
        if not self._dirty_layers and not self._dirty_structure:
            self._status.showMessage("All files are already saved.", 2000)
            return

        save_site = self._dirty_structure
        layer_indices = sorted(self._dirty_layers)

        if save_site and not self._save_site_settings():
            return

        failed: list[str] = []

        for layer_index in layer_indices:
            if not self._save_layer(layer_index):
                failed.append(self._document.layer_paths[layer_index].name)

        if failed:
            self._status.showMessage(
                f"Save All incomplete — could not save: {', '.join(failed)}",
                5000,
            )
            return

        parts: list[str] = []

        if save_site:
            parts.append("structure.yaml")

        if layer_indices:
            count = len(layer_indices)
            label = "layer" if count == 1 else "layers"
            parts.append(f"{count} {label}")

        self._status.showMessage(f"Saved {' and '.join(parts)}.", 4000)

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

        self._persist_editor_settings()
        event.accept()

    def _persist_editor_settings(self) -> None:
        sync_editor_settings_from_ui(
            block_tooltips=self._structure_grid.show_block_tooltips(),
            grid_axis_labels=self._structure_grid.show_axis_labels(),
            panel_compass=self._compass_panel.isVisible(),
            panel_materials=self._materials_panel.isVisible(),
            panel_structure_settings=self._structure_settings_panel.isVisible(),
        )

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

    add_recent_structure(structure, stage)
    return MainWindow(document, structure=structure, stage=stage)


def _resolve_startup_target(structure: str | None, stage: int | None) -> tuple[str, int] | None:
    if structure:
        return structure, int(stage or 1)

    for recent_structure, recent_stage in load_recent_structures():
        try:
            open_structure(recent_structure, recent_stage)
        except Exception:
            continue

        return recent_structure, recent_stage

    return None


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Structure schematic editor")
    parser.add_argument("--structure")
    parser.add_argument("--stage", type=int)
    args = parser.parse_args(argv)

    if args.stage is not None and not args.structure:
        parser.error("--stage requires --structure")

    ensure_qt_platform()
    app = QApplication(sys.argv)
    configure_ui_icon_theme()
    configure_ui_tooltips()
    configure_ui_menus()
    target = _resolve_startup_target(args.structure, args.stage)

    if target is None:
        window = NoStructureLoadedWindow()
        window.show()
        return app.exec()

    structure, stage = target
    window = build_main_window(structure, stage)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
