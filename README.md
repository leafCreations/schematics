# Minecraft Schematics Renderer

A modular Minecraft schematic rendering and world-generation toolkit written in Python.

This project generates:

* Top-down schematic blueprints
* Roof plans
* Structure side-view facades
* Site landscaping blueprints
* Site elevation cross-sections
* Material inventory sheets
* Minecraft world generation output

The renderer is designed around a registry-driven architecture using YAML block definitions and modular rendering pipelines.

---

# Features

* Registry-driven block rendering
* Texture-based blueprint rendering
* Multi-render pipeline architecture
* Shared rendering context system
* Path and landscaping generation
* Layer-by-layer schematic visualization
* Material inventory generation
* Future UI-ready render selection system

---

# Project Structure

```text
helpers/
  context.py
  paths.py
  render_utils.py
  utils_schematics.py
  landscape_utils.py

registries/
  blocks.yaml
  loader.py

renderers/
  top_view.py
  roof.py
  side_view.py
  path_view.py
  site_facades.py
  materials.py

structures/
  residence/
    stage1/
    stage2/

world_gen/

assets/
output/

render_main.py
```

---
# World Gen Requirements

1. Create a new world in Minecraft 26.1 or greater.
2. create a folder called "template"
3. Copy the world folders/files into the template directory

---

# Development Setup

## Install Pre-Commit:

```bash
pip install ruff pre-commit
```

Install Git hooks:

```bash
pre-commit install
```

Run checks manually:

```bash
ruff check .
ruff format .
pre-commit run --all-files
```

The pre-commit hook will automatically run Ruff before each commit.

## Requirements

* Python 3.13+
* Pillow (PIL)
* PyYAML

Install dependencies:

```bash
pip install pillow pyyaml
```

---

# Registry System

The project uses a centralized YAML registry:

```text
registries/blocks.yaml
```

Each block entry can define:

* Minecraft block mapping
* Texture mappings
* Background colors
* Display names
* Render categories

Example:

```yaml
G:
  minecraft:
    block: minecraft:grass_block

  schematic:
    top_texture: "grass_block_top.png"
    background_color: [95, 160, 75]

  display_name: "Grass Block"
```

---

# Running the Renderer

The main entry point is:

```python
build_stage_complete_schematics()
```

located in:

```text
render_main.py
```

---

# Example Usage

## Generate All Render Types

```python
from render_main import build_stage_complete_schematics

build_stage_complete_schematics(structure="residence", stage=1, renders="all")
```

---

## Generate Only Top-Down Blueprints

```python
from render_main import build_stage_complete_schematics

build_stage_complete_schematics(structure="residence", stage=1, renders="top_view")
```

---

## Generate Multiple Specific Renderers

```python
from render_main import build_stage_complete_schematics

build_stage_complete_schematics(
    structure="residence", stage=1, renders=["top_view", "roof", "materials"]
)
```

---

# Available Render Types

| Render Name    | Description                         |
| -------------- | ----------------------------------- |
| `top_view`     | Layer-by-layer blueprint panels     |
| `roof`         | Roof blueprint render               |
| `side_view`    | Structure facade elevations         |
| `path`         | Landscaping and path top-down plans |
| `site_facades` | Site cross-section elevations       |
| `materials`    | Material inventory sheets           |
' `worldgen`     | Generates structure in a world      |
| `all`          | Execute all renderers               |

---

# Output

Generated files are written to:

```text
output/
```

Example outputs:

* Structure blueprint sheets
* Roof plans
* Site maps
* Elevation renders
* Materials lists

---

# Design Goals

This project is being structured to support:

* Future PySide6 desktop UI integration
* Modular renderer expansion
* Additional structure presets
* Advanced landscaping systems
* Minecraft world export pipelines
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

---
