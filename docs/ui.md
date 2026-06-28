# Structure Editor (UI)

**User guide:** [structure-editor-guide.md](structure-editor-guide.md) — how to use the editor (layers, groups, site, renders, shortcuts).

**Property reference:** [editor-properties.md](editor-properties.md) — all editable fields grouped by panel, save target, and YAML key.

**Application settings:** defaults in `config/editor_settings.yaml`; your overrides in `~/.config/structure_scripts/editor_settings.yaml` (panel visibility, tooltips, grid axis labels).

PySide6 desktop editor for structure layer YAML. Browse and edit `structures/{structure}/stage{N}/layers/*.yaml` with registry-driven block palettes, Minecraft texture previews in the grid, and per-layer save.

Structure packages use a **manifest** (`structures/{structure}/structure.yaml`) plus per-stage `stage.yaml` files — see [structure-tokens.md](structure-tokens.md#structure-packages).

The editor shares the same token grammar, registry, and texture pipeline as the blueprint renderers. See [registry.md](registry.md) for palette and behavior details.

## Install

Requires **Python 3.11+** and the optional `[ui]` extra:

```bash
pip install -e ".[dev,ui]"
```

Block textures must exist under `assets/minecraft/textures/block/` (same as rendering). Generated sprites under `assets/project/generated/` improve stairs, fences, doors, and similar blocks — see [sprite-baker.md](sprite-baker.md). Toolbar icons load from `assets/icons/` when present.

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

Three tabs at the top: **Structure** (edit layers), **Site** (footprint preview and placement), and **Viewer** (generate blueprint outputs).

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
| **Palettes** (left) | **Search** (all palettes), **Category**, **Dimension** (terrain), and block list from `registries/palettes/*.yaml` |
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

### Viewer tab

| Control | Role |
| ------- | ---- |
| **Preview** | In-app preview: **2D** / **3D** toggle, render-type dropdown (2D only), optional floor **group** selector (Top Down only), thumbnail gallery, **Preview toolbar** (2D zoom), and scrollable main image or orbit GL view |
| **2D \| 3D** | **2D** — existing PNG gallery preview. **3D** — greedy-meshed orbit view with catalog texture atlas from the in-memory structure (`SchematicContext`); **click** the 3D view to capture the pointer for look (**Esc** to release); mesh rebuilds on the same stale/dirty rules as 2D |
| **Preview toolbar** | **Previous** / **Next** gallery navigation (2D only); **zoom slider** (25%–400%), **Reset** (100%), and **zoom level** label. Mouse wheel over the main image zooms in/out. Zoom level is saved to `editor_settings.yaml` and restored when you open the **Viewer** tab |
| **Preview** dropdown | **Top Down** (per-Y PNGs for the selected floor group), **Structure Facades**, **Site Facades**, **Site Top Down** (per site Y), **Materials List** — selecting a type auto-renders into the session folder when needed |
| **Export Render** | Split button — exports the preview dropdown selection to `output/schematics/{output_folder}/`; menu **All Renders** runs all blueprint types |
| **Generate World** | Runs worldgen only using the structure manifest **Minecraft version** (`26.1.2` or `26.2`); disabled when no matching template exists under `worldgen_templates/` |
| **Open Output Folder** | Opens `output/schematics/{output_folder}/` in the file manager (schematic PNG exports) |
| **Open World Folder** | Opens the last generated world under `output/worlds/{output_folder}/v{version}/` after **Generate World** (or **All Renders** with worldgen) succeeds in this session; disabled until then |

Preview PNGs for the current editor session are written under `output/schematics/_preview/{session}/` (one UUID per process). That folder is removed when you quit, open a different structure/stage, create a new structure in the editor, or reload the window.

After you **save** a layer or site settings, session previews are marked stale. Opening the **Viewer** tab (or saving while already on **Viewer**) re-runs the preview for the current mode: **2D** re-renders PNGs for the dropdown selection; **3D** rebuilds the orbit mesh from the in-memory document. If nothing changed since the last preview, existing session PNGs (2D) or the cached mesh (3D) are reused.

**3D orbit preview** uses a greedy-meshed exterior shell with catalog textures from `compile_texture_set()` packed into one GPU atlas at `BLOCK_PX` resolution. Per-block texture tiling and face-aware sampling (C3a) avoid stretched UVs on merged quads; `slab`, `stairs`, `fence`, and `wall` behaviors use simplified partial geometry (C3b). Mesh construction runs on a background thread; OpenGL upload happens on the UI thread. **Free camera:** **click** the **3D** view to capture the pointer for look (system cursor hidden; capture
persists when the mouse leaves the preview — **Esc** releases); while captured, mouse movement adjusts azimuth/elevation; **hold** **W** / **↑** or **S** / **↓** to move forward/back along the look direction (includes vertical when pitched), **hold** **A** / **←** or **D** / **→** to strafe on the horizontal plane, **hold** Space to ascend, **hold** Shift to descend, **R** to reset to the default exterior framing for the current mesh. **Scroll wheel** adjusts keyboard fly movement speed (not camera dolly or mouse look); **+** / **-** keys adjust the same multiplier. Each change shows a transient **Move speed: N.N×** label below the crosshair for ~2s. Speed persists as `viewer.orbit_camera_move_speed` (default **0.65×**, clamp **0.2–1.0**, step **±0.05**). **HUD panel:** when **3D** is active, an overlay shows three live lines — `Facing: North|South|East|West` (full compass words; +x east, +z south), `Position: X n / Y n / Z n` (camera eye, one decimal), and `Looking at: {Name} (cell: X n / Y n / Z n)` from a look-ray into the mesh voxel map — materialized tokens use catalog names (e.g. Oak Log); `Looking at: (none)` on miss. Toggle with **Viewer → HUD Panel**, **F3**, or **Show HUD panel** in **Viewer → HUD Properties…** (enabled only on the **Viewer** tab in **3D**); default **on**, persisted as `viewer.orbit_camera_hud`. A **cog** on the HUD panel opens the same **HUD Properties** modal. **Placement** (nine anchors) and **Show Crosshairs** persist as `viewer.orbit_camera_hud_placement` and `viewer.orbit_camera_hud_crosshair`. A **center-screen crosshair** (white dot plus four gap-separated arms) marks the look-ray origin at the widget midpoint; it can be hidden independently while keeping the HUD panel visible. Both HUD and crosshair hide in **2D** preview or when the HUD panel is off — use the crosshair when QA-ing partial blocks and attachables against the HUD **Looking at** line. **Pose persistence:** the last 3D camera position, azimuth, and elevation for each open **structure/stage** (e.g. `residence/1`) are saved under `viewer.orbit_camera_poses` when you switch **3D → 2D**, leave the **Viewer** tab in 3D, open another structure/stage, or quit; toggling back to **3D** on that stage restores its saved pose (invalid or missing values fall back to the mesh default exterior framing). **R** resets the in-session view only — the saved preference for that stage updates on the next save event. Perspective near/far planes scale with mesh bounds to reduce z-fighting in tight interior rooms. See [render-types.md](render-types.md).

While you have **unsaved** edits (including after **Undo** / **Redo**), preview renders use the in-memory document so the gallery matches the grid without requiring a save first. Export and **Generate World** still prompt to save because they write to the permanent output folders.

Renders always load from **saved** YAML on disk for export and worldgen. If you have unsaved layers or site settings, the editor prompts to save before exporting (or you can export the last saved version).

Worldgen requires `amulet`; see [worldgen.md](worldgen.md).

**Generate World** (and **Structure → Render → Worldgen**) uses the structure manifest **`version`** field and copies the matching template from `worldgen_templates/` (for example `v26_1_2/` or `v26_2/`). Set version in **Structure settings** or when creating a new structure. The window title shows the active version (e.g. `Residence Stage 2 (v26.1.2)`).

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

Open the **Site** tab. The **Site settings** panel edits the structure **manifest** (`structures/{structure}/structure.yaml`), not layer files:

- **Site width (x)** and **Site depth (z)** — rectangular footprint for path view, site facades, and worldgen (e.g. 20×10). Legacy YAML may still use `site_size: 30` for a 30×30 square.
- **Placement** — nine anchors (top/middle/bottom × left/center/right). **Center** is the default; offsets are computed from structure and site dimensions and written as `offset_x` / `offset_z` (and `placement` when saved).
- Read-only summary shows structure size (from layer cells) and the resulting offset.

### Menus

**File**

| Item | Shortcut | Action |
| ---- | -------- | ------ |
| New Structure | `Ctrl+N` | Create a new structure package (`structure.yaml` manifest + `stage{N}/stage.yaml` + first layer) and open it |
| Open Structure… | — | Pick an existing structure and stage to open; in-flight **preview** renders do not block (process restarts). Export/worldgen renders still block until complete. |
| Open Recent | — | Reopen recently used structure/stage pairs (same render rules as Open Structure) |
| Save | `Ctrl+S` | Structure tab: active layer. Site tab: site settings (manifest + `stage.yaml`). |
| Save All | `Ctrl+Shift+S` | Saves every unsaved layer and site settings |
| Exit | `Ctrl+Q` | Close the editor (unsaved-changes prompt) |

**Edit**

| Item | Shortcut | Action |
| ---- | -------- | ------ |
| Undo | `Ctrl+Z` | |
| Redo | `Ctrl+Y` | |
| Copy | `Ctrl+C` | Copy selected grid cells (selector active) |
| Paste | `Ctrl+V` | Paste copied cells |

**View**

| Item | Shortcut | Action |
| ---- | -------- | ------ |
| Reload Window | `Ctrl+Shift+Q` | Restart the editor process (same CLI args); use after code changes instead of quitting |
| Compass | `Ctrl+Shift+C` | Show or hide the compass panel (Structure and Site tabs); use the title-row close button to hide |
| Materials | — | Show or hide the materials inventory (Structure tab); close button on the panel title row |
| Structure settings | — | Show or hide the Structure panel (identity, grid size) on the Structure tab left column |
| Block tooltips | — | Show block tokens when hovering structure and site grid cells; saved in application settings |
| Grid axis labels | — | Column numbers along the top and row letters (A, B, …) along the left; on by default, saved in application settings |

**Viewer** (menu bar — after **Structure**)

| Item | Shortcut | Action |
| ---- | -------- | ------ |
| Zoom In | `Ctrl+=` (`Ctrl++`) | Increase preview zoom one step (×1.1, max 400%); enabled on the **Viewer** tab only |
| Zoom Out | `Ctrl+-` | Decrease preview zoom one step (÷1.1, min 25%) |
| Zoom Reset | `Ctrl+0` | Reset preview zoom to 100% and save to application settings |

**Help**

| Item | Action |
| ---- | ------ |
| Documentation | Opens [structure-editor-guide.md](structure-editor-guide.md) on GitHub in the default browser |

### Save

- **Save Layer** writes only the active layer file (e.g. `layers/layer_00.yaml`), including optional `visible: false` when hidden from renders.
- **File → Save** (`Ctrl+S`) is the same operation when the current layer is dirty.
- **File → Save All** (`Ctrl+Shift+S`) writes all dirty layer files, then site settings if those are unsaved (same order as quitting with save).
- **Save Site Settings** writes the manifest (`structures/{structure}/structure.yaml`: `dimension`, `grid`, `site_ground`, `stages`) and updates `stage{N}/stage.yaml` (`layer_files`, identity fields).
- Unsaved layers or site settings show `(unsaved)` in the window title and `*` on the matching save button.
- Switching layers or quitting with unsaved changes prompts **Save / Discard / Cancel**.

### Undo and redo

**Edit → Undo** (`Ctrl+Z`) and **Edit → Redo** (`Ctrl+Y`) apply to:

* **Paint and erase** on the structure grid (one step per cell change, current layer and site preview stay in sync)
* Structure grid **resize** (all layers)
* **Site** width, depth, and placement anchor
* Structure **nudge** on the site preview (offsets)
* **Path brush**, path **erase**, and **clear all paths** on the site ground layer

After undo or redo, unsaved indicators are recomputed by comparing the in-memory document to saved YAML on disk (not from the history snapshot alone). Session previews are marked stale so the **Viewer** tab can refresh when you switch back.

### Generate renders

**From the editor:** open the **Viewer** tab, choose a preview render type, and click **Export Render** (or **All Renders** from the split menu). Use **Generate World** for worldgen. Save layers and site settings first so disk matches your edits.

**From the CLI** (same pipeline):

```bash
python render_main.py --structure residence --stage 1
```

See [render-types.md](render-types.md) for individual render types and output paths.

## Palette and brush behavior

Palettes are loaded via `list_palettes()` in `helpers/block_picker.py`.

### Browse vs search

* **Search** (top of the panel) — type to search **every** palette at once. The block list is replaced with matches labeled `Block — Category` (e.g. `Cobblestone — Terrain`). Category and dimension controls hide until search is cleared.
* **Category** — pick a palette tab (Building, Terrain, Wood, …) when search is empty.
* **Dimension** — **Terrain** only: filter overworld / nether / end blocks. Defaults to the site `dimension` from structure settings.

### Token types

The block list shows a short type name (e.g. **Planks**, **Stone**). Material and color for semantic tokens are chosen in the paint brush, not in the list label.

* **Semantic tokens** (`PLANKS`, `STAIRS`, …) — behavior + `ui:` metadata from `registries/behaviors/`
* **Catalog blocks** (`minecraft:stone`, …) — display names and textures from `registries/generated/catalog.json`. The **Terrain** palette uses catalog ids exclusively, grouped by dimension in `registries/palettes/terrain.yaml`.

Legacy terrain tokens (`GRASS`, `COBBLESTONE#mossy`, …) still load in existing YAML; migrate with `scripts/migrate_terrain_tokens.py`.

| Brush field | When shown | Example |
| ----------- | ---------- | ------- |
| Material | `requires_material: true` | `PLANKS` → `oak`, `spruce`, … (from catalog) |
| Direction | `requires_direction: true` | `@north`, `@south`, … |
| Variant | Catalog variant key or `ui.variants` | Terrain `stone` → `smooth` writes `minecraft:smooth_stone`; stair shapes on `STAIRS` |
| Part | `BED` (`head` / `foot`) | `BED:blue@north#head`, `BED:blue@north#foot` |
| Half | `DOOR` (`lower` / `upper`) | `DOOR:oak@north#lower`, `DOOR:oak@north#upper` |
| Hanging | `LANTERN` | **Auto** (worldgen: `true` if layer above has a block); **Hanging** → `;hanging=true`; **Standing** → `;hanging=false` |

Integrity checks for palette ↔ registry ↔ catalog references: `registries/validate.py` (`validate_palettes()`).

## Grid textures

The grid does not use text labels for placed blocks. Each cell icon is resolved by:

1. `GridTextureCache` — compiles the registry top-view texture set (same as schematics).
2. `resolve_cell_texture()` in `helpers/utils_schematics.py` — token → image, including fence adjacency and catalog fallback for `minecraft:` cells.

Fence icons refresh on neighboring cells when you paint or erase adjacent blocks.

## Files touched by the editor

```text
structures/residence/
  structure.yaml          # manifest: dimension, grid, site_ground, stages[]
  stage1/
    stage.yaml            # per-stage: structure, stage, name, layer_files
    layers/
      layer_00.yaml       # index, group, cells — edited and saved per layer
      layer_01.yaml
      ...
```

Layer YAML shape:

```yaml
index: 0
group: Floor 1
cells:
  - - minecraft:cobblestone
    - PLANKS:oak
    - .
```

The editor loads `stage{N}/stage.yaml` and the manifest, resolves `layer_files` paths, and keeps layers in memory until **Save Layer** flushes the active layer to disk. See [structure-tokens.md](structure-tokens.md#structure-packages) for the full field split.

## Package layout

```text
ui/
  __main__.py               # CLI: python -m ui
  main_window.py            # MainWindow, dirty tracking, save prompts
  document.py               # StructureDocument load/save (manifest + stage.yaml)
  app_settings.py           # Editor settings YAML
  editor_prefs.py           # Preference accessors
  editor_history.py         # Undo/redo stack
  editor_materials.py       # Shared inventory context for the UI
  materials_icons.py        # Inventory icon cache
  platform.py               # Linux Qt library preflight
  texture_cache.py          # PIL → QIcon, compile_texture_set cache
  dialog_layout.py          # Shared modal dialog metrics
  icon_theme.py             # Bundled icon theme
  menu_style.py             # Global QMenu styling
  tooltip_style.py          # Global QToolTip styling
  toolbar_icons.py          # Grid header and panel icons
  selector_mode.py          # Selector rectangle / same-block modes
  render_worker.py          # Background QThread render jobs
  render_preview.py         # Preview session paths and gallery PNG resolution
  reload.py                 # Editor process reload
  site_cells.py             # Site ↔ structure coordinate mapping
  widgets/
    palette_panel.py        # Search, category, dimension filter, block list
    grid.py                 # Structure layer grid (paint/erase/move)
    layer_tools_panel.py    # Grid header toolbar (selector, move, paint, eraser, …)
    structure_settings_panel.py  # Structure identity + footprint size
    site_grid.py            # Scaled read-only site footprint preview
    preview_panel.py        # In-app preview dropdown, gallery, navigation
    render_panel.py         # Export Render, Generate World, Open Output/World Folder
    materials_panel.py      # Live all-layer materials table
    properties_panel.py     # Brush + cell inspector
    groups_panel.py         # Layer group list
    layer_list_panel.py     # Layer list
    …                       # Other panel and dialog widgets
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
* **Selector** (rectangle and same-block modes), **Move**, **Copy** / **Paste**, paint **Fill** / **Outline**, and **Rotate** (all layers)
* **New Structure** (`Ctrl+N`), **Open Structure…**, and **Open Recent**
* **Viewer** tab — in-app blueprint preview (dropdown + gallery) and export/worldgen actions
* Live **Materials** list on the Structure tab (current layer or all layers)
* Undo/redo for paint/erase, structure resize, site grid, placement nudge, and paths

**Not yet:**

* Multi-stage wizard (add stage to existing structure from the UI)
* Multiple structures per site (independent placement per structure)
* Lightweight 3D orbit preview (see [roadmap.md](roadmap.md))

See [roadmap.md](roadmap.md) for longer-term plans.
