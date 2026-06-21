# Structure Editor (UI)

**User guide:** [structure-editor-guide.md](structure-editor-guide.md) — how to use the editor (layers, groups, site, renders, shortcuts).

**Property reference:** [editor-properties.md](editor-properties.md) — all editable fields grouped by panel, save target, and YAML key.

**Application settings:** defaults in `config/editor_settings.yaml`; your overrides in `~/.config/structure_scripts/editor_settings.yaml` (panel visibility, tooltips, grid axis labels).

PySide6 desktop editor for structure layer YAML. Browse and edit `structures/{structure}/stage{N}/layers/*.yaml` with registry-driven block palettes, Minecraft texture previews in the grid, and per-layer save.

The editor shares the same token grammar, registry, and texture pipeline as the blueprint renderers. See [structure-tokens.md](structure-tokens.md) and [registry.md](registry.md) for token and palette details.

## Install

Requires **Python 3.11+** and the optional `[ui]` extra:

```bash
pip install -e ".[dev,ui]"
```

Block textures must exist under `assets/minecraft/textures/block/` (same as rendering). Generated sprites under `assets/minecraft/generated/` improve stairs, fences, doors, and similar blocks — see [sprite-baker.md](sprite-baker.md). Toolbar icons load from `assets/icons/` when present.

## Launch

```bash
python -m ui --structure residence --stage 1
```

| Flag | Default | Meaning |
| ---- | ------- | ------- |
| `--structure` | `residence` | Structure package under `structures/` |
| `--stage` | `1` | Stage number |

Equivalent entry points:

```bash
python -m ui.main_window --structure residence --stage 1
```

## Window layout

Three tabs at the top: **Structure** (edit layers), **Site** (footprint preview and placement), and **Render** (generate blueprint outputs).

### Structure tab

```text
┌─────────────┬──────────────────────────────┬──────────────┐
│  Category ▼ │  [Eraser|Save]  (grid header)            │  Compass     │
│  Blocks     │  Groups / Layers (left)                  │
│  Layers     │  [+ − ⎘ ⎗] list + ↑↓       │  Paint brush │
│  Structure  │  ┌────────────────────────┐  │  Grid cell   │
│  (identity  │  │  Structure grid        │  │  Materials   │
│   + size)   │  └────────────────────────┘  │              │
└─────────────┴──────────────────────────────┴──────────────┘
```

| Area | Role |
| ---- | ---- |
| **Palettes** (left) | Category dropdown plus block list from `registries/palettes/*.yaml` |
| **Structure grid** (center) | Current layer `cells` — paint and erase; use **Structure size** to grow (pad with `.`) or shrink (trim east/south) |
| **Structure** (left, bottom) | Combined identity (**Structure**, **Stage**, derived name/output folder) and grid size (width/depth, resize). Saved with **Save Site Settings** on the Site tab |
| **Compass** (right, top) | North-up reference (+x east, +z south) |
| **Inspector** (right) | **Grid cell** when paint or selector is active; **Selected Block** (material, direction, variant) only in paint mode; paint hint panel only in paint mode |
| **Eraser** (right) | Shown when eraser mode is on: **Eraser size** (square brush centered on the click) |
| **Materials** (right) | Live inventory; **Current layer** (default) or **All layers** from the scope dropdown — same grouping as the materials render; updates when you paint, erase, or switch layers |
| **Groups** (left) | Top-right: add, edit, delete, copy, paste (18px icons). **All** (default) plus each layer `group` name and any empty groups in `grid.groups`; click a row to filter the Layers list. **↑** / **↓** reorder groups (moves all layers in the group; save site settings to persist). **Edit** opens the group dialog to rename the selected group (layers and saved metadata). **visibility** toggles hide the whole group from renders (`hidden_groups` in `structure.yaml`, saved with **Save Site Settings**). **Add** requires a name; empty groups persist in `grid.groups` until layers are assigned |
| **Layers** (left, below Groups) | Top-right: add, edit, delete, copy, paste (18px icons). **Edit** opens the layer dialog (Y level and group). Select the active layer; **↑** / **↓** reorder `layer_files` (save site settings to persist). **Visibility** (per row): click to hide a layer from renders (`visible: false` in layer YAML); hidden layers show `layer-visible-off` — save the layer to persist |
| **Layer toolbar** (grid header) | **Selector**, **Move**, **Paint brush**, **Eraser**, **Copy**, **Paste**, **Rotate left** / **Rotate right**, **Save**. Only one of selector / move / paint / eraser is active at a time. **Move**: drag a rectangle to select, then drag to place (clears the source and writes at the new top-left). **Rotate** turns **all** layers 90° (swaps width/depth; updates `@direction` and `!rotation`). **Copy**/**Paste** use the selection. |
| **Save Site Settings** | Also updates `layer_files` in `structure.yaml` after add/delete |

### Site tab

```text
┌────────────────────────────────────┬──────────────────┐
│  Site preview: …     [Save Site *] │  Site width/depth│
│  ┌────────────────────────────┐  │  Placement 3×3   │
│  │  Full site grid (read-only) │  │  Offset summary  │
│  │  structure at offset        │  │                  │
│  └────────────────────────────┘  │                  │
└────────────────────────────────────┴──────────────────┘
```

| Area | Role |
| ---- | ---- |
| **Site grid** (center) | `site_width` × `site_depth` preview; structure layer shown at `offset_x` / `offset_z` (faded green = open site; white = structure blocks); path **fence/torch** on long **trim block** runs (≥8 contiguous trim cells; first post at +10 along the run, then every 7) |
| **Compass** (right, top) | Same north-up rose as the Structure tab |
| **Site settings** (right) | `site_width`, `site_depth`, nine placement anchors, derived offsets |
| **Nudge placement** (right) | Arrow buttons; same as keyboard arrows when structure is selected |
| **Site preview** | First layer in `grid.site_structure_layers` (same layer path/site renders use for the ground floor) |
| **Save Site Settings** | Write `structure.yaml` grid fields and `site_ground` |
| **Path brush** (right) | **Path width** (default 3, odd); **Orientation** (row or column strip centered on the click); **Trim block** (default GRAVEL); **Path variety** checkboxes; **Path brush** / **Eraser** / **Clear all paths**; repainting an existing path updates only that strip, not the whole path leg |

**Precise placement:** click any block in the structure footprint on the site grid (highlighted), then use **arrow keys** or **↑↓←→** nudge buttons to move it one block at a time. Offsets update live; anchor presets stay in sync when close.

### Render tab

| Control | Role |
| ------- | ---- |
| **Render types** | Checkboxes for each renderer in `render_main.py` (top view, roof, facades, path, materials, worldgen) |
| **All render types** | Same as `renders all` on the CLI |
| **Generate Renders** | Runs the pipeline in a background thread; status bar shows progress |
| **Open schematic output folder** | Opens `output/schematics/{output_folder}/` in the file manager |

Renders always load from **saved** YAML on disk. If you have unsaved layers or site settings, the editor prompts to save before generating (or you can render the last saved version).

Worldgen is only available when `amulet` is installed; see [worldgen.md](worldgen.md).

## Editing workflow

### Paint a block

1. Choose a **Category** in the dropdown (Terrain, Wood, Functional, Building, …).
2. Pick a block in the list below.
2. Set **Material**, **Direction**, or **Variant** in the properties panel when the token requires them.
3. Confirm the token in **Grid cell** (e.g. `STAIRS:oak@north#outer_left`).
4. **Left-click** a grid cell to place that token (or select a cell already placed with the same token type).

**Middle-click** a non-empty cell to select that block in the palette and load its material, variant, direction, and hanging options into the paint brush (also selects the cell for the grid-cell panel). In **Eraser** mode, middle-click instead clears every cell on the layer with the same token.

Changing **Material**, **Direction**, **Part**, or **Variant** updates the paint brush only — existing grid cells change only when you paint, erase, paste, or use another grid action.

Placement strings are built by `helpers/block_picker.py` → `cell_token()`, matching the grammar in [structure-tokens.md](structure-tokens.md).

Opening a structure or saving a layer/site file runs the same validation as render/worldgen (grid, layer dimensions, duplicate worldgen `index`, and **unknown cell tokens** in layers and `site_ground`).

### Erase

**Structure tab**

- **Right-click** any cell → sets `.` (empty).
- Or enable **Eraser** and **left-click** to clear.

**Site tab (paths)**

- **Right-click** an open site cell → clears every path/trim cell on that **row** (horizontal orientation) or **column** (vertical orientation). Fence/torch overlays disappear when no trim remains on the site.
- Enable **Eraser** in the path panel and **left-click** → same row/column erase as right-click.
- **Clear all paths** removes every painted path/trim cell on the site (confirmation dialog). Undo applies to all of the above.

### Site placement

Open the **Site** tab. The **Site settings** panel edits `structure.yaml` (not layer files):

- **Site width (x)** and **Site depth (z)** — rectangular footprint for path view, site facades, and worldgen (e.g. 20×10). Legacy YAML may still use `site_size: 30` for a 30×30 square.
- **Placement** — nine anchors (top/middle/bottom × left/center/right). **Center** is the default; offsets are computed from structure and site dimensions and written as `offset_x` / `offset_z` (and `placement` when saved).
- Read-only summary shows structure size (from layer cells) and the resulting offset.

### Menus

**File**

| Item | Shortcut | Action |
| ---- | -------- | ------ |
| New Structure | `Ctrl+N` | Placeholder (not implemented) |
| Save | `Ctrl+S` | Structure tab: active layer. Site tab: site settings (`structure.yaml`). |
| Save All | `Ctrl+Shift+S` | Saves every unsaved layer and site settings (`structure.yaml`) |
| Exit | `Ctrl+Q` | Close the editor (unsaved-changes prompt) |

**Edit**

| Item | Shortcut |
| ---- | -------- |
| Undo | `Ctrl+Z` |
| Redo | `Ctrl+Y` |

**View**

| Item | Shortcut | Action |
| ---- | -------- | ------ |
| Reload Window | `Ctrl+Shift+Q` | Restart the editor process (same CLI args); use after code changes instead of quitting |
| Compass | `Ctrl+Shift+C` | Show or hide the compass panel (Structure and Site tabs); use the title-row close button to hide |
| Materials | — | Show or hide the materials inventory (Structure tab); close button on the panel title row |
| Structure settings | — | Show or hide the Structure panel (identity, grid size) on the Structure tab left column |
| Block tooltips | — | Show block tokens when hovering structure and site grid cells; saved in application settings |
| Grid axis labels | — | Column numbers along the top and row letters (A, B, …) along the left; on by default, saved in application settings |

**Help**

| Item | Action |
| ---- | ------ |
| Documentation | Opens [structure-editor-guide.md](structure-editor-guide.md) on GitHub in the default browser |

### Save

- **Save Layer** writes only the active layer file (e.g. `layers/layer_00.yaml`), including optional `visible: false` when hidden from renders.
- **File → Save** (`Ctrl+S`) is the same operation when the current layer is dirty.
- **File → Save All** (`Ctrl+Shift+S`) writes all dirty layer files, then `structure.yaml` / site settings if those are unsaved (same order as quitting with save).
- **Save Site Settings** writes `structure.yaml` grid fields (`site_width`, `site_depth`, `placement`, `offset_x`, `offset_z`).
- Unsaved layers or site settings show `(unsaved)` in the window title and `*` on the matching save button.
- Switching layers or quitting with unsaved changes prompts **Save / Discard / Cancel**.

### Undo and redo

**Edit → Undo** (`Ctrl+Z`) and **Edit → Redo** (`Ctrl+Y`) apply to:

* **Paint and erase** on the structure grid (one step per cell change, current layer and site preview stay in sync)
* Structure grid **resize** (all layers)
* **Site** width, depth, and placement anchor
* Structure **nudge** on the site preview (offsets)
* **Path brush**, path **erase**, and **clear all paths** on the site ground layer

### Generate renders

**From the editor:** open the **Render** tab, choose render types, and click **Generate Renders**. Save layers and site settings first so disk matches your edits.

**From the CLI** (same pipeline):

```bash
python render_main.py --structure residence --stage 1
```

See [render-types.md](render-types.md) for individual render types and output paths.

## Palette and brush behavior

Palettes are loaded via `list_palettes()` in `helpers/block_picker.py`. The block list shows a short type name (e.g. **Planks**, **Log**); material and color are chosen in the paint brush, not in the list label.

* **Semantic tokens** (`PLANKS`, `STAIRS`, …) — behavior + `ui:` metadata from `registries/behaviors/`
* **Catalog blocks** (`minecraft:stone`, …) — display names and textures from `registries/generated/catalog.json`

| Brush field | When shown | Example |
| ----------- | ---------- | ------- |
| Material | `requires_material: true` | `PLANKS` → `oak`, `spruce`, … (from catalog) |
| Direction | `requires_direction: true` | `@north`, `@south`, … |
| Variant | `ui.variants` non-empty | `#mossy` on `COBBLESTONE`; stair shapes on `STAIRS` |
| Part | `BED` (`head` / `foot`) | `BED:blue@north#head`, `BED:blue@north#foot` |
| Half | `DOOR` (`lower` / `upper`) | `DOOR:oak@north#lower`, `DOOR:oak@north#upper` |
| Hanging | `LANTERN` | **Auto** (worldgen: `true` if layer above has a block); **Hanging** → `;hanging=true`; **Standing** → `;hanging=false` |
| (default) variant | First combo item on other tokens | Omits `#variant` (e.g. plain `COBBLESTONE`) |

Integrity checks for palette ↔ registry ↔ catalog references: `registries/validate.py` (`validate_palettes()`).

## Grid textures

The grid does not use text labels for placed blocks. Each cell icon is resolved by:

1. `GridTextureCache` — compiles the registry top-view texture set (same as schematics).
2. `resolve_cell_texture()` in `helpers/utils_schematics.py` — token → image, including fence adjacency and catalog fallback for `minecraft:` cells.

Fence icons refresh on neighboring cells when you paint or erase adjacent blocks.

## Files touched by the editor

```text
structures/residence/stage1/
  structure.yaml          # metadata + layer_files list (read-only in UI today)
  layers/
    layer_00.yaml           # index, group, cells — edited and saved per layer
    layer_01.yaml
    ...
```

Layer YAML shape:

```yaml
index: 0
group: Floor 1
cells:
  - - COBBLESTONE
    - PLANKS:oak
    - .
```

The editor loads `structure.yaml`, resolves `layer_files` paths, and keeps layers in memory until **Save Layer** flushes the active layer to disk.

## Package layout

```text
ui/
  __main__.py           # CLI: python -m ui
  main_window.py        # MainWindow, dirty tracking, save prompts
  document.py           # StructureDocument load/save
  platform.py           # Linux Qt library preflight
  texture_cache.py      # PIL → QIcon, compile_texture_set cache
  widgets/
    palette_panel.py    # Category dropdown + block list
    grid.py             # Structure layer grid (paint/erase)
    structure_settings_panel.py  # Structure identity + footprint size (combined)
    structure_size_panel.py  # Grid size section (embedded in settings panel)
    site_grid.py        # Scaled read-only site footprint preview
    render_panel.py     # Render type checkboxes and generate action
  site_cells.py         # Site ↔ structure coordinate mapping
  render_worker.py      # Background QThread render jobs
    materials_panel.py  # Live all-layer materials table
    properties_panel.py # Brush + cell inspector
  editor_materials.py # Shared inventory context for the UI
  materials_icons.py    # Inventory icon cache for the materials table
```

Shared helpers (not under `ui/`):

| Module | Role |
| ------ | ---- |
| `helpers/block_picker.py` | Palette resolution, `cell_token()`, material enumeration |
| `helpers/registry_lookup.py` | `get_block_entry()`, catalog solid entries |
| `helpers/structure_loader.py` | Same structure paths as `render_main.py` |
| `registries/validate.py` | Palette integrity tests |

## Editor chrome

At startup (`ui.main_window` `main()`), three helpers configure shared Qt styling:

| Module | Role |
| ------ | ---- |
| `ui/icon_theme.py` | Bundled icon theme from `assets/icons/` |
| `ui/tooltip_style.py` | Global `QToolTip` colors |
| `ui/menu_style.py` | Global `QMenu` row height, font, and gray selection highlight |

Any new menu bar entry, context menu, or toolbar popup should use a plain `QMenu` — no per-menu stylesheet. Call `configure_ui_menus()` only if you add a second application entry point.

### Modal dialogs

Custom editor dialogs (`QDialog` subclasses) share layout from `ui/dialog_layout.py`: **32px** field height (`DIALOG_FIELD_HEIGHT`), **420px** minimum width, and standard margins/spacing. Use `apply_dialog_field_style` on every spinbox, combo, and line edit. Single-line prompts use `InputTextDialog` — not `QInputDialog`.

### Panel boxes with header buttons

Use this layout for new left/right column panels (Groups, Layers, Compass):

| Piece | Module |
| ----- | ------ |
| Title + actions on one row | `ui/widgets/panel_header.py` — `create_titled_panel_layout(panel, "Title", [buttons…])` |
| 18px icon buttons | `ui/widgets/panel_tool_button.py` — `make_panel_tool_button`; `ui/toolbar_icons.py` — `panel_icon_size()`, `layer_*_icon(size=…)` |
| Signals | Panel emits `*_requested`; `main_window.py` connects handlers |

Do not use the built-in `QGroupBox` title plus a second row only for buttons — the title and icons share the top row (`Compass … ×`). Secondary fields (e.g. Groups **Name**) sit below that row. Grid-header toolbars (eraser/save) stay at 22px via `toolbar_icon_size()`.

## Linux troubleshooting

PySide6 needs system libraries pip does not install. If startup fails with `Could not load the Qt platform plugin "xcb"`:

```bash
sudo apt install libxcb-cursor0
```

On Wayland:

```bash
QT_QPA_PLATFORM=wayland python -m ui --structure residence --stage 1
```

The editor runs `ui/platform.py` preflight on Linux and prints install hints when libraries are missing. Install notes: [development.md](development.md).

## Current scope and roadmap

**Implemented (UI-0 / UI-1):**

* Palette browser and layer grid with texture icons
* Paint / erase / per-layer save with unsaved indicators
* Direction, material, and variant in placed tokens
* **Render** tab — generate schematics/worldgen from the editor (background job)
* Live **Materials** list on the Structure tab (current layer or all layers)
* Undo/redo for paint/erase, structure resize, site grid, and placement nudge

**Not yet:**

* Live render preview pane (embedded thumbnails in the editor)
* Copy/paste, fill tools
* New structure / stage wizard

See [roadmap.md](roadmap.md) for longer-term plans.
