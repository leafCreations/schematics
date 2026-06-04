# Structure Editor — User Guide

The **Structure Editor** is a desktop app for building and editing Minecraft structure blueprints. You paint blocks on layer grids, organize layers into groups, place the building on a site, paint paths, and generate schematic images — all from one window.

This guide explains how to use the editor day to day. For install commands, module layout, and developer notes, see [ui.md](ui.md).

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

Each stage is a folder on disk, for example:

```text
structures/residence/stage1/
  structure.yaml     # site size, placement, layer list, paths
  layers/
    layer_00.yaml    # one floor / slice: cells grid + group name
    layer_01.yaml
    ...
```

- **Layers** hold the block grid (`cells`) you paint in the Structure tab.
- **structure.yaml** holds site size, where the building sits on the site, which layers appear in site preview, path settings, and group visibility for renders.

The window title shows the structure name and `(unsaved)` when something has not been written to disk.

---

## The three tabs

| Tab | Purpose |
| --- | ------- |
| **Structure** | Edit layer grids, groups, materials, and building size |
| **Site** | Preview the full site, nudge building placement, paint paths |
| **Render** | Generate blueprint images and worldgen from saved files |

Work in **Structure** to design the building, **Site** to fit it on the ground and add paths, then **Render** when you are ready for output.

---

## Structure tab — overview

```text
┌─────────────┬──────────────────────────────┬──────────────┐
│  Palettes   │  Eraser · Save  (above grid) │  Compass     │
│  Groups     │                              │  Paint brush │
│  Layers     │      Structure grid          │  Materials   │
│  Structure  │                              │              │
│  settings   │                              │              │
└─────────────┴──────────────────────────────┴──────────────┘
```

**Left column**

- **Palettes** — pick block types (stairs, planks, terrain, …).
- **Groups** — filter and manage layer groups (e.g. “Floor 1”, “Roof”).
- **Layers** — choose which layer you are editing, reorder, show/hide in renders.
- **Structure** — structure name, stage, grid width/depth, resize, tooltip preference.

**Center**

- **Structure grid** — top-down view of the **current layer**. Paint and erase here.

**Right column**

- **Compass** — north up; +x is east, +z is south (matches the grid).
- **Paint brush** — material, direction, variant for the active block type.
- **Materials** — live block count for the current layer or all layers.

---

## Painting blocks

### 1. Choose a block type

1. Open the **Category** dropdown (Terrain, Wood, Building, …).
2. Click a block in the list (e.g. Planks, Stairs, Cobblestone).

### 2. Set brush options

In **Paint brush** on the right, set fields that apply to that block:

| Field | When you need it | Example |
| ----- | ---------------- | ------- |
| **Material** | Wood, stairs, doors, … | `oak`, `spruce` |
| **Direction** | Blocks that face a way | `@north`, `@south` |
| **Variant** | Mossy, stair shape, … | `#mossy`, `#outer_left` |
| **Part / Half** | Beds, doors | head/foot, lower/upper |
| **Hanging** | Lanterns | hanging vs standing |

The **Cell token** line shows exactly what will be placed (e.g. `STAIRS:oak@north#outer_left`). Token rules are documented in [structure-tokens.md](structure-tokens.md).

### 3. Place on the grid

- **Left-click** a cell to place the token.
- Click a cell that already has the same block type to select it without changing it.
- **Middle-click** a non-empty cell to **pick** that block into the brush (loads material, direction, variant into the panels).

Changing brush fields updates the **selected** cell immediately — you do not need to click again.

### Erase

| Action | Result |
| ------ | ------ |
| **Right-click** a cell | Clear to empty (`.`) |
| **Eraser** (toolbar above grid) + left-click | Same as right-click |
| Eraser menu → **Clear entire layer** | All cells on this layer become empty |

Hover tooltips on cells can be turned on/off under **Structure** settings (saved locally).

---

## Layers

The **Layers** panel lists every layer file. The highlighted row is the layer shown in the grid.

| Control | What it does |
| ------- | ------------- |
| Click a row | Switch to that layer (prompts if the current layer is unsaved) |
| **+** | Add a new empty layer |
| **−** | Delete the selected layer (at least one layer must remain) |
| Copy / Paste | Duplicate a layer (paste creates a new layer file) |
| **↑** / **↓** | Change order in `structure.yaml` (save site settings to persist order) |
| Eye icon on a row | Hide that layer from **renders** (save the layer to persist `visible: false`) |

**Save** the active layer with the toolbar **Save** button or **File → Save** (`Ctrl+S`). Unsaved layers show `*` in the list.

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

Group visibility is saved in `structure.yaml` (`hidden_groups`). Layer visibility is saved in each layer file.

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
| **Save** (grid toolbar) or **File → Save** (`Ctrl+S`) | Active layer file only (`layers/layer_XX.yaml`) |
| **Save Site Settings** (Site tab) | `structure.yaml` — site size, placement, offsets, layer order, paths, group visibility |

The window title shows `(unsaved)` when layers or site settings need saving. Switching layers with unsaved edits asks **Save / Discard / Cancel**.

**Render** always reads from **disk**. Save before generating, or the editor will offer to save first.

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

## Render tab

1. Check the **render types** you want (top view, facades, materials, worldgen, …).
2. Click **Generate Renders**.
3. Progress appears in the status bar.
4. Use **Open schematic output folder** to view files under `output/schematics/{output_folder}/`.

Worldgen needs Amulet installed — see [worldgen.md](worldgen.md). Details of each render type: [render-types.md](render-types.md).

You can also render from the command line:

```bash
python render_main.py --structure residence --stage 1
```

---

## Keyboard shortcuts

| Shortcut | Action |
| -------- | ------ |
| `Ctrl+S` | Save current layer |
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
7. Open **Render** tab; generate outputs.
8. Open output folder and review schematics.
