# Structure Editor — Editable Properties

Reference for every user-editable value in the desktop editor: where it appears, what it affects on disk, and whether it persists across sessions.

**Related docs:** [structure-editor-guide.md](structure-editor-guide.md) (workflow), [ui.md](ui.md) (install and layout), [structure-tokens.md](structure-tokens.md) (cell token grammar), [registry.md](registry.md) (palette and brush metadata).

---

## How changes are saved

| Action | Writes | Typical contents |
| ------ | ------ | ---------------- |
| **Save** (`Ctrl+S`, grid toolbar) | Active `layers/layer_NN.yaml` | `cells`, `group`, `visible`, `index`, `description` |
| **Save Site Settings** (Site tab) | Manifest `structures/{name}/structure.yaml` + `stage{N}/stage.yaml` | Manifest: `dimension`, `grid`, `site_ground`, `stages`. Stage: `structure`, `stage`, `name`, `layer_files` |
| *(automatic)* | User `editor_settings.yaml` (see below) | Display prefs, panel visibility |
| *(none)* | Session only | Tool mode, selection, render checkboxes, materials scope, group list filter |

Layer **reorder** and **group reorder** update the in-memory document immediately; persist them with **Save Site Settings** (`layer_files` on `stage.yaml`, `grid.groups` on the manifest).

Modal dialogs (add/edit layer, rename group, etc.) **auto-save on OK** via `_persist_dialog_changes()` in `main_window.py`.

---

## Application settings (YAML)

Editor preferences live outside structure packages. Defaults are in [`config/editor_settings.yaml`](../config/editor_settings.yaml); your overrides are written to:

- `~/.config/structure_scripts/editor_settings.yaml`, or
- `$XDG_CONFIG_HOME/structure_scripts/editor_settings.yaml`, or
- path in `STRUCTURE_SCRIPTS_EDITOR_SETTINGS`

Load/save: `ui/app_settings.py`. Accessors: `ui/editor_prefs.py`.

On first run, legacy **QSettings** values (`block_tooltips`, `grid_axis_labels`) are migrated into the user YAML file.

| YAML path | UI control | Default | Applies to |
| --------- | ---------- | ------- | ---------- |
| `display.block_tooltips` | **View → Block tooltips** | `true` | Structure + site grid hover |
| `display.grid_axis_labels` | **View → Grid axis labels** | `true` | Structure grid column/row headers |
| `panels.compass` | **View → Compass** (and panel close) | `true` | Structure + Site compass |
| `panels.materials` | **View → Materials** | `true` | Materials panel |
| `panels.structure_settings` | **View → Structure settings** | `true` | Structure identity + size panel |
| `viewer.preview_zoom_percent` | Viewer preview zoom (wheel / toolbar slider) | `100` | **Viewer** tab main preview (25–400); saved on change and on exit |

Changes save when toggled in the UI; preview zoom saves when adjusted. The full state is also flushed on exit.

---

## View menu (panel visibility and display)

Checkable actions in **View** (`ui/main_window.py`). Panel visibility persists in application settings YAML (see above).

| Menu item | Shortcut | Panel(s) |
| --------- | -------- | -------- |
| Reload Window | `Ctrl+Shift+Q` | Reloads the app (dev convenience) |
| Compass | `Ctrl+Shift+C` | Structure + Site compass roses |
| Materials | — | Materials inventory (right column) |
| Structure settings | — | Structure identity + size (left column, bottom) |
| Block tooltips | — | Structure + site grid hover tokens (`display.block_tooltips`) |
| Grid axis labels | — | Structure grid headers (`display.grid_axis_labels`) |

Dismissible panels also expose a **close** control (window-close icon); that hides the panel and unchecks the matching View action.

---

## Structure tab

### Palettes (`ui/widgets/palette_panel.py`)

Controls are stacked top to bottom: **Search**, **Category**, **Dimension** (terrain only), **Blocks**.

| Property | Control | Persisted | Notes |
| -------- | ------- | --------- | ----- |
| Search | Text field | No | Searches **all** palettes; replaces the block list with global matches (palette name shown as `Block — Category`). Category and dimension hide while searching. |
| Category | Dropdown | No | Palette tab from `registries/palettes/*.yaml` (Building, Terrain, Wood, …). Browse mode when search is empty. |
| Dimension | Dropdown | No | **Terrain** only: `All`, `Overworld`, `Nether`, `The End`. Defaults to the site **Dimension** from structure settings (`structure.yaml` → `dimension`). |
| Block | List selection | No | Drives **Selected Block** brush fields; placement via `helpers/block_picker.py` → `cell_token()`. Terrain blocks write `minecraft:` ids. |

### Groups (`ui/widgets/groups_panel.py`)

| Property | Control | Persisted | YAML / behavior |
| -------- | ------- | --------- | --------------- |
| Filter | **All** or group row | No | Filters Layers list only |
| Edit | Toolbar | Mixed | Opens **Edit group** dialog; renames `group:` on all layers in that group; updates `grid.groups`, `grid.hidden_groups` — save affected layers and site settings |
| Visibility | Eye per group | **Save Site Settings** | `grid.hidden_groups` — group omitted from renders |
| Order | ↑ / ↓ | **Save Site Settings** | `grid.groups` order; moves all layers in adjacent groups |
| Add / Edit / Delete / Copy / Paste | Toolbar | Mixed | Add/delete/copy/paste layers and empty groups in memory; copy/paste creates layers; save site for `layer_files` / groups |

### Layers (`ui/widgets/layer_list_panel.py`)

| Property | Control | Persisted | YAML / behavior |
| -------- | ------- | --------- | --------------- |
| Active layer | Row click | No | Which `cells` grid is edited |
| Order | ↑ / ↓ | **Save Site Settings** | `layer_files` order (list position, not worldgen `index`) |
| Visibility | Eye per layer | **Save Layer** | `visible: false` on layer file when hidden |
| Add / Edit / Delete / Copy / Paste | Toolbar | Mixed | **Add** / **Edit** prompt for Y level, description, and group; **Save Layer** for `index` / `description` / `group`; delete/reorder need **Save Site Settings** for `layer_files` |

**Worldgen `index`** in each layer file is the Minecraft Y offset (`actual_y = worldgen_base_y + index`). **Add** and **Edit** open the same dialog for Y level and group (existing group or **— New group —**). Paste still auto-assigns the next free index and copies the source group.

### Structure settings (`ui/widgets/structure_settings_panel.py`)

Combines identity (`structure_properties_panel.py`) and footprint (`structure_size_panel.py`).

| Property | Control | Persisted | YAML field |
| -------- | ------- | --------- | ---------- |
| Structure | Line edit (`a-z`) | **Save Site Settings** | `structure` |
| Stage | Spin 1–99 | **Save Site Settings** | `stage` |
| Name | Read-only label | **Save Site Settings** | `name` (derived: `{Title} Stage {N}`) |
| Output folder | Read-only label | **Save Site Settings** | `output_folder` (derived: `stage{N}_{structure}`) |
| Site width / depth | Spin 1–512 | **Save Site Settings** | `grid.site_width`, `grid.site_depth` |
| Dimension | Combo | **Save Site Settings** | `dimension` (`overworld`, `nether`, `end`); also sets default **Terrain** palette filter |
| Minecraft version | Combo | **Save Site Settings** | Manifest `version` (`26.1.2`, `26.2`); filters palettes and worldgen template. Downgrading shows a warning — placed blocks are not rewritten. |
| Width (x) | Spin 1–512 | **Resize grid** → all layers | `cells` width (padded with `.` or trimmed east) |
| Depth (z) | Spin 1–512 | **Resize grid** | `cells` depth (trim south) |
| Resize grid | Button | Per-layer **Save** or bulk save | Applies size to every layer’s `cells` |

Width/depth cannot exceed current site dimensions (shown in the site-limit hint).

### Structure grid (`ui/widgets/grid.py`)

| Property | Control | Persisted | Notes |
| -------- | ------- | --------- | ----- |
| Cell token | Paint / erase / paste | **Save Layer** | Each `cells[z][x]` string; see [structure-tokens.md](structure-tokens.md) |
| Axis labels | View → Grid axis labels | `display.grid_axis_labels` | `column_axis_label` / `row_axis_label` |
| Block tooltips | View → Block tooltips | `display.block_tooltips` | Hover shows raw token |
| Icon size | *(automatic)* | No | Scales with viewport; brush preview uses fixed 48×48 |

### Layer toolbar (tools)

| Tool | Persisted | Behavior |
| ---- | --------- | -------- |
| Selector | No | Drag selection (rectangle or same-block mode); **Copy** / **Paste**; `Ctrl+click` toggles cells |
| Move | No | Drag rectangle to select, then drag to place (clears source) |
| Paint brush | No | Drag + release paints with current brush token (Fill or Outline) |
| Eraser | No | Region erase on release; middle-click erases matching token on layer |
| Copy / Paste | No | Clipboard of selected cell tokens (`Ctrl+C` / `Ctrl+V`) |
| Rotate left / right | **Save Layer** (all layers) | 90° rotation of every layer; updates `@direction` and `!rotation` |
| Save | **Save Layer** | Writes active layer YAML |

**Selector mode** (dropdown on the selector split button): **Rectangle** (default) or **Same block** (select all cells with the clicked token on the layer).

### Inspector — Selected Block (`ui/widgets/properties_panel.py`)

Shown in **paint** mode only. Fields depend on registry `ui:` metadata (`requires_material`, `requires_direction`, `variants`, behavior).

| Property | Control | In token | When shown |
| -------- | ------- | -------- | ---------- |
| Label | Read-only | — | Palette entry label |
| Material | Combo | `:material` | `requires_material: true` |
| Direction | Combo | `@direction` | `requires_direction: true` |
| Variant | Combo | `#variant` | `ui.variants` non-empty; label **Part** for `BED` (`head`/`foot`), **Half** for `DOOR` (`lower`/`upper`) |
| Hanging | Combo | `;hanging=` | `LANTERN` only: Auto (omit), Hanging (`true`), Standing (`false`) |
| Preview | Icon | — | Creative-style item icon when available (`textures/item/`); otherwise block or inventory fallback. Grid cells use baked top-view sprites. |

Changing brush fields updates the paint brush token. When a **Grid cell** is selected and its token matches the active palette entry, **Material**, **Direction**, **Variant**, **Hanging**, **Open**, and **Lit** changes also live-apply to that cell and mark the layer dirty (no repainting required). Otherwise, grid cells change when you paint or use another grid action.

### Inspector — Grid cell (read-only + brush sync)

| Display | Source |
| ------- | ------ |
| Position | `grid_axis_position(row, col)` e.g. `A8` |
| Raw | Cell token or `.` |
| Token / Material / Direction / Variant / Hanging | Parsed token |

Middle-click a cell in paint mode loads brush combos from that cell.

### Paint brush panel (`ui/widgets/layer_paint_brush_panel.py`)

| Property | Control | Persisted | Notes |
| -------- | ------- | --------- | ----- |
| Brush type | Fill / Outline | No | Fill = full rectangle; Outline = border only |

### Eraser panel (`ui/widgets/layer_eraser_panel.py`)

| Property | Control | Persisted | Notes |
| -------- | ------- | --------- | ----- |
| Eraser size | Spin 1…min(w,d) | No | Square brush; hover preview on grid |

### Selector panel (`ui/widgets/layer_selector_panel.py`)

| Property | Control | Persisted | Notes |
| -------- | ------- | --------- | ----- |
| Selected cells | Read-only range | No | e.g. `B1: E5` via `grid_axis_selection_range` |
| Selector mode | Toolbar dropdown | No | Rectangle or Same block |

When every selected cell is the same block type (e.g. all `PLANKS` with different woods), **Selected Block** appears so you can inspect or adjust the brush for repainting.

### Materials (`ui/widgets/materials_panel.py`)

| Property | Control | Persisted | Notes |
| -------- | ------- | --------- | ----- |
| Scope | Current layer / All layers | No | Live counts; same grouping as materials render |
| Inventory table | — | No | Read-only; updates on paint, erase, layer change |

### Compass (`ui/widgets/compass_panel.py`)

Reference only — no editable properties.

---

## Site tab

### Site grid (`ui/widgets/site_grid.py`)

| Property | Control | Persisted | Notes |
| -------- | ------- | --------- | ----- |
| Ground cells | Path brush / eraser / clear | **Save Site Settings** | `site_ground` 2D token grid |
| Structure placement | Click footprint + arrows / nudge | **Save Site Settings** | `grid.offset_x`, `grid.offset_z`, `grid.placement` |

Site preview uses the first entry in `grid.site_structure_layers` (not editable in UI — see YAML-only below).

### Site settings (`ui/widgets/site_settings_panel.py`)

| Property | Control | Persisted | YAML field |
| -------- | ------- | --------- | ---------- |
| Site width (x) | Spin | **Save Site Settings** | `grid.site_width` (or legacy `site_size`) |
| Site depth (z) | Spin | **Save Site Settings** | `grid.site_depth` |
| Placement | 3×3 anchor buttons | **Save Site Settings** | `grid.placement` → derives offsets |
| Offset (x, z) | Read-only | **Save Site Settings** | `grid.offset_x`, `grid.offset_z` |
| Structure footprint | Read-only | — | From layer `cells` dimensions |

### Path brush (`ui/widgets/site_path_panel.py`)

| Property | Control | Persisted | YAML field |
| -------- | ------- | --------- | ---------- |
| Path width | Spin 1–21, step 2 | **Save Site Settings** | `grid.path_width` (odd widths) |
| Orientation | Horizontal / Vertical | **Save Site Settings** | `grid.path_orientation` |
| Trim block | Combo | **Save Site Settings** | `grid.trim_block` |
| Path variety | Checkboxes per block | **Save Site Settings** | `grid.path_variety_blocks` |
| Path brush / Eraser | Toggle buttons | No | Painting mode only |
| Clear all paths | Button | **Save Site Settings** | Clears path/trim tokens in `site_ground` |

Defaults: path width `3`, trim `minecraft:gravel`, variety all of `minecraft:gravel`, `minecraft:dirt`, `minecraft:cobblestone`, `minecraft:mossy_cobblestone` (`helpers/path_strip.py`, `helpers/terrain_tokens.py`). Legacy `GRAVEL` / `COBBLESTONE#mossy` tokens still resolve.

### Nudge placement

Arrow buttons and keyboard arrows when the structure footprint is selected on the site grid. Updates offsets in memory; persist with **Save Site Settings**.

---

## Viewer tab

### Preview panel (`ui/widgets/preview_panel.py`)

| Property | Control | Persisted | Notes |
| -------- | ------- | --------- | ----- |
| Preview render type | Dropdown | No | Keys from `PREVIEW_RENDER_REGISTRY` in `renderers/registry.py` |
| Floor group | Dropdown | No | Shown only for **Top Down**; hidden for facades, site top-down, materials |
| Gallery | Thumbnails + Previous/Next | No | Multi-image types show one PNG per direction, site Y, or layer Y |
| Main image | Scroll area | No | Loaded from session preview dir; mouse wheel zooms (25%–400%) |
| Zoom level | Label (preview toolbar, far right) | No | Resets to **100%** when **Viewer** tab is opened |

### Preview toolbar (`ui/widgets/preview_toolbar.py`)

| Property | Control | Persisted | Notes |
| -------- | ------- | --------- | ----- |
| Previous / Next | Buttons | No | Gallery navigation when multiple PNGs |
| Zoom level | Label (far right) | No | Displays current zoom percent; wheel zoom on main image |

Preview PNGs are written to `output/schematics/_preview/{session}/` and removed on quit, structure switch, new structure, or window reload.

### Render panel (`ui/widgets/render_panel.py`)

| Property | Control | Persisted | Notes |
| -------- | ------- | --------- | ----- |
| Export Render | Split button | No | Exports the **preview dropdown selection**; uses saved YAML on disk |
| All Renders | Menu action | No | Runs all blueprint types (`all`) |
| Generate World | Button | No | Worldgen only; uses structure manifest `version` and matching `worldgen_templates/v{version}/` |
| Open Output Folder | Button | No | `output/schematics/{output_folder}/` |

| Preview dropdown label | Export render key |
| ---------------------- | ----------------- |
| Top Down | `top_view` |
| Structure Facades | `structure_facades` |
| Site Facades | `site_facades` |
| Site Top Down | `path` |
| Materials List | `materials` |

Structure menu **Render** submenu still offers direct shortcuts to individual render types and worldgen (same pipeline as CLI).

| Render key | Export label |
| ---------- | ------------ |
| `top_view` | Top-Down Floor Blueprints |
| `roof` | Roof Blueprints |
| `structure_facades` | Structure Facades |
| `path` | Path-Focused Blueprints |
| `site_facades` | Site Facades |
| `materials` | Materials Inventory Blueprint |
| `worldgen` | Minecraft World (requires `[worldgen]` deps) |

---

## YAML files — fields by editor surface

Structure packages split settings between the **manifest** and each **stage file**. See [structure-tokens.md](structure-tokens.md#structure-packages).

### Manifest (`structures/{name}/structure.yaml`)

Written on **Save Site Settings** (shared grid and site data):

| Field | Edited in UI | Notes |
| ----- | ------------ | ----- |
| `dimension` | Structure settings | `overworld`, `nether`, or `end` |
| `version` | Structure settings / New Structure | `26.1.2` or `26.2`; defaults to `26.1.2` when missing |
| `grid.site_width` / `grid.site_depth` | Site settings / Structure settings | |
| `grid.offset_x` / `grid.offset_z` | Placement + nudge | |
| `grid.placement` | Site settings anchors | |
| `grid.groups` | Group add/reorder/rename | Empty groups allowed |
| `grid.hidden_groups` | Group visibility | |
| `grid.path_width` | Path brush | |
| `grid.path_orientation` | Path brush | `horizontal` / `vertical` |
| `grid.trim_block` | Path brush | Catalog id (e.g. `minecraft:gravel`) |
| `grid.path_variety_blocks` | Path brush | |
| `site_ground` | Site path tools | 2D cell grid |
| `stages[]` | *(automatic)* | Per-stage `stage`, `path`, `output_folder` updated when site settings save |

### Stage file (`stage{N}/stage.yaml`)

Written on **Save Site Settings** (identity and layer list):

| Field | Edited in UI | Notes |
| ----- | ------------ | ----- |
| `structure` | Structure settings | Lowercase slug |
| `stage` | Structure settings | Integer |
| `name` | Derived | From structure + stage |
| `layer_files` | Layer reorder, add/delete | Ordered list of layer paths |

### YAML-only `grid` fields (no UI)

Edit in the manifest `structure.yaml` directly. Documented in [structure-tokens.md](structure-tokens.md).

| Field | Default / role |
| ----- | -------------- |
| `site_structure_layers` | `[0, 1]` — which **layer list positions** appear on site preview Y=0/1 |
| `worldgen_base_y` | `-60` — Minecraft Y base for export |
| `path_center_local_x` | Half structure width — auto-path center when no painted path |
| `site_size` | Legacy square site shorthand |

### Token features not in UI

| Feature | Set in |
| ------- | ------ |
| `!rotation` | Layer `cells` YAML |
| Arbitrary `;states` | Layer `cells` YAML (lantern hanging is exposed) |

---

## Layer file (`layers/layer_NN.yaml`)

| Field | Edited in UI | Notes |
| ----- | ------------ | ----- |
| `cells` | Structure grid | 2D array of tokens |
| `group` | Groups name field / layer dialog | String; optional |
| `visible` | Layers eye icon | Omitted when `true` |
| `index` | Layer Add/Edit dialog | Worldgen Y offset; unique per stage |
| `description` | Layer Add/Edit dialog | Optional list label |

---

## Brush fields vs registry

Palette entries resolve to a `PickerEntry` (`helpers/block_picker.py`). The **Selected Block** panel shows combos based on:

| Registry `ui` flag | Brush field |
| ------------------ | ----------- |
| `requires_material: true` | Material |
| `requires_direction: true` | Direction |
| `variants: [...]` | Variant (or Part/Half for bed/door) |
| `behavior: lantern` | Hanging |

Catalog-backed palette blocks (`minecraft:…`) use catalog materials when required.

---

## Session-only state (quick reference)

| State | Location |
| ----- | -------- |
| Active tool (selector / paint / eraser) | `main_window` |
| Grid selection / paste buffer | `LayerGridWidget` |
| Group list filter (**All** vs name) | `GroupsPanel` |
| Path brush vs path eraser mode | `SitePathPanel` |
| Materials scope | `MaterialsPanel` |
| Render type selection | `RenderPanel` |
| Undo stack | `ui/editor_history.py` |
| Dirty flags / window title `(unsaved)` | `main_window` |

---

## Code index

| Area | Primary modules |
| ---- | ---------------- |
| App settings | `ui/app_settings.py`, `config/editor_settings.yaml` |
| Prefs accessors | `ui/editor_prefs.py` |
| Document load/save | `ui/document.py` |
| Grid + tools | `ui/widgets/grid.py`, `helpers/grid_brush.py` |
| Tokens / brush | `helpers/block_picker.py`, `helpers/structure_tokens.py` |
| Axis labels | `helpers/grid_labels.py` |
| Groups | `helpers/layer_groups.py` |
| Layers | `helpers/layer_management.py`, `helpers/layer_visibility.py` |
| Site / paths | `helpers/grid_placement.py`, `helpers/path_strip.py`, `helpers/site_ground.py` |
| Panels | `ui/widgets/*_panel.py` |
| Orchestration | `ui/main_window.py` |
