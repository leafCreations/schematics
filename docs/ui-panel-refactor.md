# UI panel refactor plan

Reference document for incremental panel refactors in `ui/widgets/`.  
See also: `docs/ui.md`, `.cursor/rules/ui-panels.mdc`.

**Status:** In progress  
**Last updated:** 2026-06-06

---

## Goals

- Reduce duplication between Groups and Layers panels
- Consolidate layer tool hint panels (paint / selector / eraser)
- Keep signal-out, wire-in-`main_window.py` architecture
- Prefer small helper extraction over a new panel framework
- Preserve column packing behavior (no gaps when panels hide)

---

## Current panel map

| Location | Panels | Base type |
| -------- | ------ | --------- |
| Structure tab, left column | Palettes, Groups, Layers, Structure settings | Mostly `QGroupBox` + `panel_header` |
| Structure tab, right column | Compass, Paint brush, Selector, Eraser, Properties, Materials | Mixed `QGroupBox` / `QWidget` |
| Structure tab, grid header | `LayerToolsPanel` → `LayerActionToolbar` | `QWidget` wrapper |
| Site tab, right column | Compass (duplicate), Path brush, Nudge, Site settings | Mixed |
| Viewer tab | `RenderPanel`, `PreviewPanel` | `QWidget` / `QGroupBox`; preview gallery on Viewer tab |

**Sub-panels (embedded):** `StructurePropertiesPanel`, `StructureSizePanel` inside `StructureSettingsPanel`.

**Shared infrastructure (keep):**

- `ui/widgets/panel_header.py` — bold title rows, panel metric constants
- `ui/widgets/list_panel_base.py` — `ManagedListPanel`, CRUD/reorder button factories
- `ui/widgets/visibility_list_row.py` — shared list row with visibility toggle
- `ui/widgets/panel_tool_button.py` — 18px header buttons
- `ui/main_window.py` — `_update_palette_column_layout`, `_update_structure_tools_column_layout`, `_sync_layer_tool_panels`

---

## Priority 1 — Shared list-panel framework (Groups + Layers)

**Files:** `groups_panel.py`, `layer_list_panel.py`  
**Shared:** `ui/widgets/list_panel_base.py`, `ui/widgets/visibility_list_row.py`

### Problem

`GroupsPanel` and `LayerListPanel` share ~70% structure:

- CRUD header buttons (add, edit, delete, copy, paste)
- `QListWidget` + custom row widget + visibility toggle
- Reorder up/down row
- `_block_signals` pattern
- `setMaximumHeight(220)`

Row widgets `_GroupListRow` and `_LayerListRow` duplicate visibility button setup and `mousePressEvent` logic. Groups row buttons don't use `make_panel_tool_button` / `PANEL_BUTTON_STYLE`.

### Recommendation

1. Extract `VisibilityListRow(QWidget)` — label, optional visibility toggle, shared click handling
2. Extract `ManagedListPanel(QGroupBox)` or shared builders for:
   - CRUD toolbar row
   - List + reorder footer
   - Signal-blocking during `load_*`
3. Thin subclasses: `GroupsPanel`, `LayerListPanel` — only population, selection semantics, reorder rules

### Migration steps

- [x] P1a: Extract `VisibilityListRow`; wire into both panels
- [x] P1b: Extract CRUD toolbar factory (`make_crud_panel_buttons()`)
- [x] P1c: Extract reorder row helper
- [x] P1d: Optional `ManagedListPanel` base class
- [x] P1e: Remove duplicated code; verify Groups/Layers behavior unchanged

### Tests

- `pytest tests/test_main_window.py -q` (group/layer actions, filter, reorder)
- Add unit tests for `VisibilityListRow` and reorder enable rules if extracted

### Done when

- Groups and Layers share row + toolbar helpers
- No behavior change in UI
- Styling consistent (visibility buttons use panel button style)

---

## Priority 2 — Unify layer tool hint panels

**Files:** `layer_paint_brush_panel.py`, `layer_selector_panel.py`, `layer_eraser_panel.py`, `main_window.py` (`_sync_layer_tool_panels`)

### Problem

Three small `QGroupBox` panels toggle visibility based on active tool. Each occupies a slot in `_structure_tools_layout`. Switching tools triggers layout refresh across three widgets.

### Recommendation

Single `LayerToolOptionsPanel(QGroupBox)` with:

- Dynamic title ("Paint brush" / "Selector" / "Eraser")
- `QStackedWidget` or internal show/hide sections
- Public API preserving current getters/setters:
  - `paint_brush_mode()`, `set_selection_range()`, `eraser_size()`, `set_grid_bounds()`, etc.
- `set_active_tool(mode)` called from `_sync_layer_tool_panels`

**Lighter alternative:** Keep three classes; extract shared form layout helper only.

### Migration steps

- [ ] P2a: Define tool mode enum / constants
- [ ] P2b: Create `LayerToolOptionsPanel` with stacked sections
- [ ] P2c: Replace three widgets in `main_window.py` with one
- [ ] P2d: Simplify `_update_structure_tools_column_layout` widget list
- [ ] P2e: Delete old panel files (or keep as thin re-exports during transition)

### Tests

- `pytest tests/test_main_window.py -q` (tool toggles, eraser size, brush mode, selector hints)

### Done when

- One panel slot for tool options in right column
- `_sync_layer_tool_panels` simplified
- No layout gaps when switching tools

---

## Priority 3 — Dismissible panel helper

**Files:** `compass_panel.py`, `materials_panel.py`, `structure_settings_panel.py`, `main_window.py`

### Problem

Three panels repeat close button + `close_requested` signal. Main window repeats action ↔ visibility ↔ prefs sync in `_set_*_visible` methods.

### Recommendation

1. `create_dismissible_panel_layout(panel, title, *, close_tooltip)` in `panel_header.py`
2. Optional `DismissiblePanelMixin` with standard `close_requested` signal
3. Optional `PanelVisibilityController` registering `(panel, menu_action, pref_get/set, layout_updater)`

### Migration steps

- [ ] P3a: Add `create_dismissible_panel_layout`
- [ ] P3b: Migrate Compass, Materials, Structure settings panels
- [ ] P3c: Optional visibility controller in `main_window.py`

### Tests

- `pytest tests/test_app_settings.py -q` (panel visibility prefs)
- `pytest tests/test_main_window.py -q` (View menu, close buttons)

### Done when

- No duplicated close-button setup
- Visibility sync logic centralized or clearly patterned

---

## Priority 4 — Slim or remove `LayerToolsPanel` passthrough

**Files:** `layer_tools_panel.py`, `main_window.py`

### Problem

`LayerToolsPanel` only forwards signals and setters to `LayerActionToolbar` (~15 identical connects).

### Recommendation

- **Preferred:** Use `LayerActionToolbar` directly in `_build_structure_header()`
- **Alternative:** Document wrapper as intentional boundary; use delegation helper

### Migration steps

- [ ] P4a: Wire `LayerActionToolbar` directly in main window (or keep wrapper with explicit rationale in this doc)
- [ ] P4b: Remove redundant signal forwards

### Tests

- `pytest tests/test_main_window.py -q` (toolbar tool toggles)

### Done when

- No maintenance-heavy passthrough layer (or documented exception)

---

## Priority 5 — Column layout registration

**Files:** `main_window.py`

### Problem

Adding a right/left column panel requires edits in three places: `addWidget`, `_update_*_column_layout` widget tuple, and visibility logic.

### Recommendation

`PanelColumn` helper or declarative `PanelSpec` list:

```python
PanelSpec(widget, collapsible=True, stretch=False)
```

Encodes rules from `.cursor/rules/ui-panels.mdc`.

### Migration steps

- [ ] P5a: Define `PanelSpec` / `PanelColumn`
- [ ] P5b: Migrate `_palette_column_layout`
- [ ] P5c: Migrate `_structure_tools_layout`
- [ ] P5d: Document registration in `docs/ui.md`

### Tests

- `pytest tests/test_main_window.py -q` (panel hide/show, no gaps)

### Done when

- New panels registered in one place
- Column packing rules enforced by helper

---

## Priority 6 — Consistent widget base types

**Low urgency — naming/clarity only.**

| Panel | Current | Action |
| ----- | ------- | ------ |
| `SiteNudgeControls` | `QWidget` wrapping `QGroupBox` | Flatten to `QGroupBox` directly |
| `PropertiesPanel` | `QWidget` + nested groups | OK; optional outer title later |
| `RenderPanel`, `SiteSettingsPanel` | Full-tab `QWidget` | OK as-is |
| Sub-panels in Structure settings | `QWidget` | OK — embedded sections |

### Migration steps

- [ ] P6: Flatten `SiteNudgeControls` if touched otherwise

---

## Priority 7 — Shared signal-blocking utility

**Files:** All panels using `_block_signals` manual bool

### Recommendation

```python
@contextmanager
def block_signals(*widgets): ...
# or Qt QSignalBlocker per widget
```

### Migration steps

- [x] P7a: Add helper (e.g. `ui/widgets/signal_utils.py` or `ui/signal_utils.py`)
- [ ] P7b: Migrate panels incrementally (Groups, Layers, SitePath, StructureProperties, SiteSettings) — Groups/Layers done

### Done when

- No hand-rolled `_block_signals = True/False` in new code

---

## Priority 8 — Compass duplication

**Files:** `compass_panel.py`, `main_window.py`

Two `CompassPanel()` instances (Structure + Site tabs) share hide handler and prefs.

### Recommendation

- **Keep two instances** (Qt can't parent one widget twice) — lowest risk
- **Optional:** Extract `CompassContentWidget` shared by two thin `QGroupBox` shells

### Migration steps

- [ ] P8: Only if refactoring compass otherwise; not standalone

---

## Priority 9 — Centralize panel metrics

**Files:** `panel_header.py`, list/compass panels

### Recommendation

Module constants in `panel_header.py`:

| Constant | Value | Used by |
| -------- | ----- | ------- |
| `PANEL_MARGINS` | `(8, 4, 8, 8)` | Title layouts |
| `PANEL_NESTED_MARGINS` | `(8, 8, 8, 8)` | Nested groups |
| `PANEL_LIST_MAX_HEIGHT` | `220` | Groups, Layers |
| `PANEL_COMPASS_MAX_HEIGHT` | `150` | Compass |

### Migration steps

- [x] P9: Add constants; replace magic numbers (Groups, Layers, Compass; `panel_header` defaults)

---

## Priority 10 — Move orchestration out of `main_window.py`

**Largest refactor — do after P1–P2.**

### Problem

`_sync_layer_tool_panels` mixes panel visibility, properties sub-groups, grid tool state, eraser preview, and column layout refresh.

### Recommendation

- `StructureEditorToolCoordinator` — tool mode, panel/grid sync
- Optional `SiteEditorPanelCoordinator` — path brush + nudge + settings

Main window keeps document/history/persistence wiring.

### Migration steps

- [ ] P10a: Extract tool coordinator
- [ ] P10b: Move `_sync_layer_tool_panels` logic
- [ ] P10c: Optional site coordinator

### Tests

- Broad `pytest tests/test_main_window.py -q`

---

## Do not refactor (yet)

| Area | Reason |
| ---- | ------ |
| `LayerActionToolbar` split buttons | Documented in `ui-split-buttons.mdc`; working |
| `PropertiesPanel` brush logic | Domain-heavy; not structural duplication |
| `RenderPanel` internals | Self-contained |
| Dialog layout (`dialog_layout.py`) | Panels intentionally differ from modals |
| Full tab → panel framework | Over-engineering for current panel count |

---

## Migration order

```
P7 (signal blocker) ──┐
P9 (constants)       ──┼──► P1 (Groups/Layers) ──► P2 (tool options)
P3 (dismissible)     ──┘         │
                                 ▼
                    P4 (LayerToolsPanel) + P5 (column registry)
                                 │
                                 ▼
                              P10 (coordinators)
```

**Suggested first PR:** P7 + P9 + P1a (VisibilityListRow)  
**Second PR:** P1 complete  
**Third PR:** P2 (unified tool options panel)

---

## Agent workflow

When the user specifies a priority (e.g. "do P1a" or "Priority 3"):

1. Read this file and the matching **Priority N** section.
2. Complete only the listed migration steps for that priority (or sub-step).
3. Run the **Tests** listed for that priority.
4. Check off completed migration steps in this file.
5. Add a row to **Progress log** with date and brief change summary.
6. Follow `.cursor/rules/ui-panels.mdc` for any new/changed panel UI.

---

## Checklist per PR

- [ ] Targeted pytest run (see priority section)
- [ ] Manual smoke: Structure tab left/right columns, tool toggles, View menu hide/show
- [ ] No gaps below hidden panels (left + right columns)
- [ ] Update `docs/ui.md` if user-facing behavior or registration changes
- [ ] Update this doc: mark completed items, note deviations

---

## Progress log

| Date | Priority | Change | PR/commit |
| ---- | -------- | ------ | --------- |
| 2026-06-06 | — | Plan created | — |
| 2026-06-06 | P1b–P1e | `list_panel_base.ManagedListPanel`, CRUD/reorder helpers; Groups/Layers thin subclasses | — |