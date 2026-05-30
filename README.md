# Minecraft Schematics Renderer

A modular Minecraft schematic rendering and world-generation toolkit written in Python.

This project generates:

* Top-down schematic blueprints (floor layers)
* Roof plans
* Structure side-view facades
* Site landscaping and path blueprints
* Site elevation cross-sections
* Material inventory sheets
* Minecraft world output (via Amulet)

The renderer uses a registry-driven architecture with YAML block definitions, a shared `SchematicContext`, and modular rendering pipelines.

---

# Features

* Registry-driven block rendering (`registries/blocks.yaml`)
* Texture-based blueprint rendering (top and side views)
* Multi-render pipeline with selective render execution
* Shared rendering context and grid helpers
* Path and landscaping generation
* Layer-by-layer schematic visualization with per-panel inventory
* Material inventory generation
* Minecraft world export via `amulet-core`

---

# Project Structure

```text
helpers/
  constants.py          # Render type names and BLOCK_PX
  context.py            # SchematicContext dataclass
  cells.py              # Structure/site cell lookup
  facade_projection.py  # Compass elevation projection for facade renderers
  fonts.py              # Shared DejaVu font loading for blueprint renderers
  grid.py               # Site/structure dimension helpers
  layers.py             # Layer grouping and floor/roof blueprint dispatch
  path_geometry.py      # Path, trim, and lighting layout on the site
  materials.py          # Material resolution, counting, and inventory building
  render_image.py       # Shared canvas creation for blueprint PNGs
  landscape_utils.py    # Path and site map generation
  paths.py              # Asset and output directory paths, schematic output naming
  pipeline.py           # Render name validation and normalization
  registry_blocks.py    # Shared Minecraft block ID / blockstate resolution
  structure_loader.py   # Structure config validation and context building
  structure_tokens.py   # Token parsing (material, direction, variant)
  types.py              # TypedDicts and type aliases
  utils.py              # Structure loading and texture helpers
  utils_schematics.py   # Token resolution, texture paste, colors

registries/
  blocks.yaml           # Block registry
  loader.py             # Registry load and texture compilation

renderers/
  registry.py           # Render name → handler dispatch table
  layer_panel.py        # Shared floor/roof panel renderer
  top_view.py           # Floor blueprint entry point
  roof.py               # Roof blueprint entry point
  structure_facades.py  # Structure elevation facades
  path_view.py          # Site path and landscaping plans
  site_facades.py       # Site cross-section elevations
  materials.py          # Materials inventory sheet
  worldgen.py           # Minecraft world generation

structures/
  residence/
    stage1_structure.py
    stage2_structure.py

assets/                 # Block textures (not in repo; see .gitignore)
output/
  schematics/           # Rendered PNG blueprints
  worlds/               # Generated Minecraft worlds
template/               # Base world copied for worldgen

render_main.py          # Pipeline entry point (dispatches via renderers/registry.py)
pyproject.toml
```

---

# Development Setup

Requires **Python 3.11+**.

On Ubuntu and other PEP 668 systems, use a virtual environment rather than installing into the system Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Install Git hooks:

```bash
pre-commit install
```

Run checks manually:

```bash
ruff check .
ruff format .
pytest
pre-commit run --all-files
```

The pre-commit hook runs Ruff and pytest before each commit.

### Dependencies

Runtime (via `pyproject.toml`):

* `Pillow`
* `PyYAML`
* `amulet-core` (world generation only)

Dev (optional):

* `pytest`
* `ruff`
* `pre-commit`

---

# World Gen Requirements

World generation copies a template world and writes blocks via Amulet.

1. Create a new world in Minecraft 1.21 or later.
2. Create a `template/` folder in the project root.
3. Copy the world folders/files into `template/`.

See [AMULET_INSTALL_NOTES.md](AMULET_INSTALL_NOTES.md) if you hit Amulet build or install issues.

---

# Registry System

Block definitions live in `registries/blocks.yaml`. Each entry can define:

* `behavior` — placement logic (solid, fence, door, stairs, etc.)
* `minecraft` — block id, variants, and blockstate templates
* `render` — texture mappings, background colors, inventory images
* `defaults` — default direction, variant, shape, etc.
* `visibility` — e.g. `interior: false` to hide blocks from site/path views
* `display_name` / `category` — materials list grouping

Example:

```yaml
GRASS:
  behavior: solid
  minecraft:
    block: minecraft:grass_block
  render:
    textures:
      top: grass_block_top.png
    background_color: [95, 160, 75]

FURNACE:
  behavior: facing_block
  defaults:
    direction: north
  minecraft:
    block: minecraft:furnace
    blockstates:
      facing: "{direction}"
  render:
    textures:
      top: furnace_front.png
  visibility:
    interior: false
```

Textures are loaded from `assets/textures/block/` (and subfolders `block_assets/`, `item_assets/`, `custom/`).

---

# Running the Renderer

Entry point: `build_stage_complete_schematics()` in `render_main.py`.

From the project root (with venv active):

```bash
python render_main.py
```

Or from Python:

```python
from render_main import build_stage_complete_schematics

build_stage_complete_schematics(structure="residence", stage=1, renders="all")
```

Structure definitions are loaded from `structures/{structure}/stage{N}_structure.py`. Each file must define `STRUCTURE_CONFIG` with `layers`, `grid`, `name`, and `output_folder`.

The `grid` object supports:

* `site_size` — site footprint in blocks
* `offset_x` / `offset_z` — structure placement on the site
* `stair_local_x` — local X of the entry stair within the structure (defaults to `4`)
* `site_structure_layers` — list positions into `layers` projected onto site Y=0/1 (defaults to `[0, 1]`)
* `worldgen_base_y` — Minecraft Y base for world export (defaults to `-60`)

---

# Example Usage

## Generate all render types

```python
from render_main import build_stage_complete_schematics

build_stage_complete_schematics(structure="residence", stage=1, renders="all")
```

## Generate only top-down blueprints

```python
build_stage_complete_schematics(structure="residence", stage=1, renders="top_view")
```

## Generate multiple specific renderers

```python
build_stage_complete_schematics(
    structure="residence",
    stage=1,
    renders=["top_view", "roof", "materials"],
)
```

---

# Structure Tokens

Cells in structure layers use compact token strings:

| Section       | Meaning          | Example              |
| ------------- | ---------------- | -------------------- |
| Token         | Registry key     | `STAIRS`             |
| `:material`   | Material         | `PLANKS:oak`         |
| `@direction`  | Facing           | `DOOR:oak@north`     |
| `#variant`    | Shape / part     | `STAIRS:oak@north#outer_left` |
| `!rotation`   | Render rotation  | `FURNACE@east!-90`   |
| `.`           | Empty cell       | `.`                  |

Example: `STAIRS:oak@north#outer_left`

---

# Available Render Types

| Render name          | Constant / CLI value   | Description                          |
| -------------------- | ---------------------- | ------------------------------------ |
| `top_view`           | `top_view`             | Layer-by-layer floor blueprint panels |
| `roof`               | `roof`                 | Roof blueprint panels                |
| `structure_facades`  | `structure_facades`    | Structure side-view elevations       |
| `path`               | `path`                 | Landscaping and path top-down plans  |
| `site_facades`       | `site_facades`         | Site cross-section elevations        |
| `materials`          | `materials`            | Material inventory sheet             |
| `worldgen`           | `worldgen`             | Generate structure in a Minecraft world |
| `all`                | `all`                  | Run all renderers above              |

---

# Output

Schematic PNGs are written to:

```text
output/schematics/{output_folder}/
```

Generated worlds are written to:

```text
output/worlds/{output_folder}/
```

Example schematic outputs:

* `Structure_floor_1.png` — floor blueprint sheets
* `{name}_structure_facades.png` — structure elevations
* `{name}_site_topdown.png` — site path plans
* `{name}_site_facades.png` — site cross-sections
* `{name}_materials_list.png` — materials inventory

---

# Design Goals

* Future PySide6 desktop UI integration
* Modular renderer expansion
* Additional structure presets
* Advanced landscaping systems
* Registry-driven customization

---

# Future Plans

* Interactive desktop UI
* Render preview system
* Schematic editor
* Structure preset browser
* Theme/style packs
* Advanced terrain generation
* Multi-biome support
* Animated build progression renders
