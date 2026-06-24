# Structure Editor — User Guide

The **Structure Editor** is a desktop app for building and editing Minecraft structure blueprints. You paint blocks on layer grids, organize layers into groups, place the building on a site, paint paths, and generate schematic images — all from one window.

This guide explains how to use the editor day to day. For install commands, module layout, and developer notes, see [ui.md](ui.md). For a complete list of editable fields (what saves where), see [editor-properties.md](editor-properties.md).

---

## Getting started

### Install and run

You need **Python 3.11+** and the UI dependencies:

```bash
pip install -e ".[dev,ui]"
```

Block textures should exist under `assets/minecraft/textures/block/` (same as the render pipeline). See [sprite-baker.md](sprite-baker.md) if icons look wrong or missing.

Launch the editor for a structure and stage:

```bash
python -m ui --structure residence --stage 1
```

| Option | Default | Meaning |
| ------ | ------- | ------- |
| `--structure` | `residence` | Folder under `structures/` |
| `--stage` | `1` | Stage number |

After changing editor code, use **View → Reload Window** (`Ctrl+Shift+Q`) instead of quitting and reopening.

### What you are editing

Each structure package has a **manifest** and one folder per stage:

```text
structures/residence/
  structure.yaml     # manifest: dimension, grid, site_ground, stages[]
  stage1/
    stage.yaml       # per-stage identity and layer_files list
    layers/
      layer_00.yaml  # one floor / slice: cells grid + group name
      layer_01.yaml
  stage2/
    stage.yaml
    layers/ …
```

- **Layers** (`stage{N}/layers/*.yaml`) hold the block grid (`cells`) you paint in the Structure tab.
- **Manifest** (`structure.yaml`) holds site size, dimension, where the building sits on the site, path cells (`site_ground`), and the stage list.
- **`stage.yaml`** holds structure name, stage number, display name, and `layer_files` order.

See [structure-tokens.md](structure-tokens.md#structure-packages) for the full field reference.

The window title shows the structure name and `(unsaved)` when something has not been written to disk.

### File menu

| Item | Shortcut | Action |
| ---- | -------- | ------ |
| **New Structure** | `Ctrl+N` | Create a new package (manifest + first stage + empty layer) and open it |
| **Open Structure…** | — | Choose an existing structure and stage |
| **Open Recent** | — | Reopen a recently used structure/stage |

---

## The three tabs

| Tab | Purpose |
| --- | ------- |
| **Structure** | Edit layer grids, groups, materials, and building size |
| **Site** | Preview the full site, nudge building placement, paint paths |
| **Viewer** | In-app blueprint preview, export schematics, and worldgen from saved files |

Work in **Structure** to design the building, **Site** to fit it on the ground and add paths, then **Viewer** when you are ready for output.

---

## Structure tab — overview

```text
┌─────────────┬──────────────────────────────┬──────────────┐
│  Palettes   │  Brush · Eraser · Save (above grid) │  Compass │
│  Groups     │                              │  Paint brush │
│  Layers     │      Structure grid          │  Materials   │
│  Structure  │                              │              │
│  settings   │                              │              │
└─────────────┴──────────────────────────────┴──────────────┘
```

**Left column**

- **Palettes** — search all blocks or browse by category; terrain is grouped by dimension (overworld / nether / end).
- **Groups** — filter and manage layer groups (e.g. “Floor 1”, “Roof”).
- **Layers** — choose which layer you are editing, reorder, show/hide in renders.
- **Structure** — structure name, stage, grid width/depth, resize, tooltip preference.

**Center**

- **Structure grid** — top-down view of the **current layer**. Paint and erase here.

**Right column**

- **Compass** — north up; +x is east, +z is south (matches the grid).
- **Selected Block** — material, direction, variant for the palette block you picked.
- **Materials** — live block count for the current layer or all layers.

---

## Painting blocks

### 1. Choose a block type

1. Open the **Category** dropdown (Terrain, Wood, Building, …).
2. Click a block in the list (e.g. Planks, Stairs, Cobblestone).

### 2. Set brush options

In **Selected Block** on the right, set fields that apply to that block:

| Field | When you need it | Example |
| ----- | ---------------- | ------- |
| **Material** | Wood, stairs, doors, … | `oak`, `spruce` |
| **Direction** | Blocks that face a way | `@north`, `@south` |
| **Variant** | Mossy, stair shape, … | `#mossy`, `#outer_left` |
| **Part / Half** | Beds, doors | head/foot, lower/upper |
| **Hanging** | Lanterns | hanging vs standing |

The **Grid cell** panel shows the token that will be placed (e.g. `STAIRS:oak@north#outer_left`). Token rules are documented in [structure-tokens.md](structure-tokens.md).

### 3. Place on the grid

The structure grid shows **column numbers** across the top and **row letters** (A, B, …) down the left edge. Toggle them with **View → Grid axis labels** (on by default; preference is saved locally). The **Grid cell** panel uses the same addressing (e.g. **A8** = row A, column 8).

- **Paint brush**: drag to select a region (light green overlay), then release to place blocks. **Brush type** — **Fill** (every cell) or **Outline** (border cells only).
- **Selector** tool: drag to select cells — a light blue overlay shows the region. Open the selector **dropdown** to switch **Rectangle** (drag a box) or **Same block** (click one cell to select all matching tokens on the layer). The **Selector** panel shows the selection bounds (e.g. **B1: E5**). **Copy** / **Paste** or `Ctrl+C` / `Ctrl+V`. **Ctrl+click** adds or removes cells while the selector is active.
- **Move** tool: drag a rectangle to select, then drag to place the selection at a new top-left (clears the source).
- **Rotate left** / **Rotate right**: rotate **all** layers 90° (swaps width/depth; updates `@direction` and `!rotation` on placed blocks).
- Click a cell that already has the same block type to select it without changing it.
- **Middle-click** a non-empty cell to **pick** that block into the brush (loads material, direction, variant into the panels).

Changing brush fields updates the paint brush only — existing grid cells change only when you paint, erase, paste, or use another grid action.

### Paint brush toggle

The **Paint brush** button above the grid (on by default) controls whether left-click **places** blocks. When it is off, left-click only selects cells. Turning on **Eraser** turns the paint brush off, and vice versa.

### Erase

Enable **Eraser** on the grid toolbar to show the **Eraser** panel on the right. Set **Eraser size** to clear a square of cells centered on each click (1 = one cell, 3 = 3×3, etc., clamped to the layer size). Hover a cell to highlight the erase area in light red before you click.

| Action | Result |
| ------ | ------ |
| **Right-click** a cell | Clear using the current eraser size (or 1×1 when paint brush mode is on) |
| **Eraser** (toolbar above grid) + left-click | Same as right-click |
| **Eraser** + drag and release | Select a region (light red overlay), then clear all blocks in it on mouse up (one Undo) |
| **Eraser** + middle-click a block | Clears every cell on the layer with the same token (one Undo) |
| Eraser menu → **Clear entire layer** | All cells on this layer become empty |

With **Paint brush** on, the **Paint brush** hint panel, **Selected Block**, and **Grid cell** appear on the right. With **Selector** on, **Selected Block** appears when every selected cell is the same block type. The eraser panel replaces these when **Eraser** is active.

Hover tooltips on cells can be turned on/off with **View → Block tooltips** (saved in application settings).

---

## Layers

The **Layers** panel lists every layer file. The highlighted row is the layer shown in the grid.

| Control | What it does |
| ------- | ------------- |
| Click a row | Switch to that layer (prompts if the current layer is unsaved) |
| **+** | Add a new empty layer (Y level and existing or new group) |
| **Edit** | Change the current layer Y level and group |
| **−** | Delete the selected layer (at least one layer must remain) |
| Copy / Paste | Duplicate a layer (paste creates a new layer file) |
| **↑** / **↓** | Change order in `stage.yaml` `layer_files` (save site settings to persist order) |
| Eye icon on a row | Hide that layer from **renders** (save the layer to persist `visible: false`) |

**Save** the active layer with the toolbar **Save** button or **File → Save** (`Ctrl+S`) on the Structure tab. On the Site tab, **Save** / `Ctrl+S` writes site settings (same as **Save Site Settings**). Unsaved layers show `*` in the list.

---

## Groups

Layers belong to a **group** (stored as `group:` in each layer YAML). Groups let you filter the layer list and hide whole sections from renders.

| Control | What it does |
| ------- | ------------- |
| **All** | Show every layer in the list |
| Click a group | Filter the list to layers in that group |
| **Name** field | Rename the selected group (updates all layers in that group) |
| **+** | Add a new group — you must enter a name; can be empty until layers use it |
| **−** | Remove the group (layers in that group lose the group name) |
| Copy / Paste | Copy all layers in a group; paste creates new layers under a `(copy)` name |
| Eye icon | Hide the whole group from renders (save **site settings** to persist) |

Group visibility is saved in the manifest (`grid.hidden_groups`). Layer visibility is saved in each layer file.

---

## Structure size

At the bottom of the left column, **Structure** settings include **width** and **depth** of the grid.

- **Grow** adds empty rows/columns (filled with `.`).
- **Shrink** trims from the east and south edges.

Resize affects **all layers** at once. Undo is available (`Ctrl+Z`).

Structure identity (name, stage, output folder) is edited here too. Save with **Save Site Settings** on the Site tab.

---

## Saving your work

| Button / menu | Saves |
| ------------- | ----- |
| **Save** (Structure toolbar) or **File → Save** (`Ctrl+S`) on Structure tab | Active layer file only (`layers/layer_XX.yaml`) |
| **File → Save** (`Ctrl+S`) on Site tab | Manifest + `stage.yaml` (same as **Save Site Settings**) |
| **Save All** (**File → Save All**, `Ctrl+Shift+S`) | Every unsaved layer plus manifest / site settings when dirty |
| **Save Site Settings** (Site tab) | Manifest (`dimension`, `grid`, `site_ground`, `stages`) and `stage.yaml` (`layer_files`, identity) |

The window title shows `(unsaved)` when layers or site settings need saving. Switching layers with unsaved edits asks **Save / Discard / Cancel**.

**Export and preview** always read from **disk**. Save before exporting or previewing after large edits, or the editor will offer to save first.

---

## Site tab

Use this tab to see the building on the full site grid and to edit paths.

```text
┌────────────────────────────────────┬──────────────────┐
│  Site preview          [Save Site] │  Compass         │
│  ┌────────────────────────────┐  │  Path brush      │
│  │  Site grid (read-only      │  │  Nudge arrows    │
│  │   structure + paths)       │  │  Site settings   │
│  └────────────────────────────┘  │                  │
└────────────────────────────────────┴──────────────────┘
```

### Site grid

- Shows the full **site_width × site_depth** footprint.
- The structure layer chosen for preview appears at **offset_x / offset_z**.
- Green tint = open site; white = structure blocks from the preview layer.

### Placement

In **Site settings**:

- Set **site width** and **site depth**.
- Pick a **placement** anchor (nine presets: top/middle/bottom × left/center/right). Offsets update automatically.

**Precise nudge:** click a block inside the structure footprint on the site grid, then use **arrow keys** or the **Nudge placement** buttons to move one block at a time.

### Paths

**Path brush** (right side):

- Set **path width** (odd number, default 3).
- **Orientation** — row or column strip centered on where you click.
- **Trim block** and **path variety** checkboxes for fence/torch decoration on long runs.
- **Path brush** — paint; **Eraser** — clear a row or column; **Clear all paths** — remove all path cells (with confirmation).

On the site grid:

- **Right-click** open site → clears path cells on that row or column (by orientation).
- Path changes undo with **Ctrl+Z**.

Save paths and placement with **Save Site Settings**.

---

## Viewer tab

The **Viewer** tab combines an in-app preview with export actions.

### Preview

1. Open the **Viewer** tab.
2. Choose a render type from the **Preview** dropdown:
   - **Top Down** — per-layer PNGs for the selected floor group (group selector appears for this type)
   - **Structure Facades** — N / S / W / E elevation PNGs
   - **Site Facades** — site cross-sections by direction
   - **Site Top Down** — one PNG per site path Y level
   - **Materials List** — inventory sheet with icons and counts
3. The editor renders into a session folder under `output/schematics/_preview/{session}/` and shows thumbnails plus Previous/Next navigation.
4. Session preview files are deleted when you quit, open another structure, create a new structure, or reload the window.

Preview uses the same saved YAML as export. Save dirty layers and site settings first when prompted.

### Export and worldgen

| Control | Action |
| ------- | ------ |
| **Export Render** | Writes the **currently selected preview type** to `output/schematics/{output_folder}/` |
| **Export Render → All Renders** | Runs every blueprint type (same as CLI `all`, excluding worldgen) |
| **Generate World** | Worldgen only; uses structure manifest `version` and `worldgen_templates/v{version}/` |
| **Open Output Folder** | Opens the schematic output folder in your file manager |

Progress appears in the status bar. Worldgen needs Amulet — see [worldgen.md](worldgen.md). Output filenames: [render-types.md](render-types.md).

You can also render from the command line:

```bash
python render_main.py --structure residence --stage 1
```

---

## Help menu

**Help → Documentation** opens this guide in your browser (GitHub copy of `docs/structure-editor-guide.md`).

---

## Keyboard shortcuts

| Shortcut | Action |
| -------- | ------ |
| `Ctrl+N` | New Structure |
| `Ctrl+S` | Save (active layer on Structure tab; site settings on Site tab) |
| `Ctrl+Shift+S` | Save All (unsaved layers and site settings) |
| `Ctrl+C` | Copy selected cells |
| `Ctrl+V` | Paste copied cells |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+Q` | Quit (prompts if unsaved) |
| `Ctrl+Shift+Q` | Reload window (after code changes) |
| `Ctrl+Shift+C` | Show or hide compass |
| Arrow keys | Nudge structure on site (when footprint is selected) |

Right-click = erase cell on structure grid; on site grid = erase path row/column.

---

## Undo and redo

Undo/redo covers:

- Paint and erase on the structure grid
- Structure grid resize
- Site width, depth, and placement anchor
- Structure nudge on the site preview
- Path paint, erase, and clear all paths
- Layer/group changes that go through the undo stack (add/delete layer, group rename, etc.)

---

## Compass

The compass shows **north at the top** of the grid, **east to the right** (+x), and **south toward the bottom** (+z). Toggle it with **View → Compass** or hide with **×** on the panel.

---

## Tips

1. **Save often** — layer edits and site settings save separately.
2. **Filter by group** when a structure has many layers — easier to find the floor you want.
3. **Hide layers or groups** from renders without deleting them — use the eye icon, then save layer or site settings.
4. **Middle-click** a cell to copy its block settings into the brush.
5. **Materials** panel helps catch mistakes — switch to “All layers” to see totals before rendering.
6. Validation runs when you save — unknown tokens or size mismatches show an error dialog with the file path.

---

## Troubleshooting

### Editor won’t start on Linux

If you see `Could not load the Qt platform plugin "xcb"`:

```bash
sudo apt install libxcb-cursor0
```

On Wayland:

```bash
QT_QPA_PLATFORM=wayland python -m ui --structure residence --stage 1
```

More detail: [development.md](development.md) and [ui.md](ui.md#linux-troubleshooting).

### Textures missing in the grid

Run the sprite baker and ensure `assets/minecraft/textures/block/` is populated. See [sprite-baker.md](sprite-baker.md).

### Renders don’t match what I see

Save all dirty layers and **Save Site Settings**, then generate again. The render pipeline reads files from disk, not unsaved memory.

---

## Related documentation

| Document | Contents |
| -------- | -------- |
| [structure-tokens.md](structure-tokens.md) | Cell token grammar (`PLANKS:oak@north#…`) |
| [registry.md](registry.md) | Palettes and block behaviors |
| [render-types.md](render-types.md) | Output images and CLI renders |
| [ui.md](ui.md) | Technical UI reference for developers |
| [worldgen.md](worldgen.md) | Minecraft world export |
| [roadmap.md](roadmap.md) | Planned features |

---

## Quick workflow checklist

1. Launch editor for your structure/stage.
2. Select or add layers; assign **groups** if helpful.
3. Pick blocks from **Palettes**; paint on the **Structure** grid.
4. **Save** each layer (`Ctrl+S`).
5. Open **Site** tab; set size and placement; paint paths if needed.
6. **Save Site Settings**.
7. Open **Viewer** tab; pick a preview type or **Export Render** / **Generate World**.
8. Review in-app preview or open `output/schematics/{output_folder}/` for exported PNGs.
