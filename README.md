# Minecraft Schematics Renderer

A modular Minecraft schematic rendering and world-generation toolkit written in Python.

Generates top-down blueprints, roof plans, structure and site facades, path layouts, material inventory sheets, and Minecraft worlds (via Amulet).

Registry-driven architecture: YAML block definitions, shared `SchematicContext`, modular render pipelines.

## Quick start

Requires **Python 3.11+**. Targets **Minecraft Java Edition 26.x** (see [docs/project-info.md](docs/project-info.md)).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

Place Minecraft client resources under versioned folders, then run the asset setup scripts — see [docs/assets.md](docs/assets.md). `assets/` is not in the repo.

```bash
.venv/bin/python scripts/prune_minecraft_assets.py --all-versioned
.venv/bin/python scripts/migrate_project_assets.py
.venv/bin/python scripts/dedupe_minecraft_assets.py --clean
.venv/bin/python scripts/generate_catalog.py   # if catalog missing/outdated
.venv/bin/python scripts/bake_sprites.py --type simple --view top --all --force
.venv/bin/python scripts/bake_sprites.py --type stairs --view top --all --force
.venv/bin/python scripts/bake_sprites.py --type fence --view top --all --force
# See docs/sprite-baker.md for full bake commands
```

Run the residence stage 1 renderer:

```bash
python render_main.py
```

Or from Python:

```python
from render_main import build_stage_complete_schematics

build_stage_complete_schematics(structure="residence", stage=1, renders="top_view")
```

Outputs go to `output/schematics/{output_folder}/`.

## Documentation

| Guide | Contents |
| ----- | -------- |
| [docs/structure-editor-guide.md](docs/structure-editor-guide.md) | **Structure Editor user guide** — how to use the desktop UI |
| [docs/development.md](docs/development.md) | Venv, dependencies, Ruff, pre-commit, pytest (product setup) |
| [docs/governance/](docs/governance/) | Agent/kanban handbook — lessons, parity, audit, compaction |
| [docs/project-structure.md](docs/project-structure.md) | Repository layout |
| [docs/registry.md](docs/registry.md) | Behavior registry, palettes, and texture loading |
| [docs/ui.md](docs/ui.md) | Structure editor technical reference (PySide6) |
| [docs/assets.md](docs/assets.md) | Asset layout, prune script, versioned extracts |
| [docs/sprite-baker.md](docs/sprite-baker.md) | Baking `assets/project/generated/` sprites |
| [docs/render-types.md](docs/render-types.md) | Renderers, examples, output paths |
| [docs/worldgen.md](docs/worldgen.md) | Template world and Amulet export |
| [docs/roadmap.md](docs/roadmap.md) | Design goals and future plans |
| [AMULET_INSTALL_NOTES.md](AMULET_INSTALL_NOTES.md) | Amulet build troubleshooting |

## Features

* Registry-driven block rendering (`registries/behaviors/`, `registries/palettes/`)
* PySide6 structure editor for layer YAML ([user guide](docs/structure-editor-guide.md))
* Procedural sprite baker with cached generated textures
* Top and side schematic views with per-panel material inventory
* Multi-render pipeline with selective execution
* Path and landscaping generation
* Minecraft world export via `amulet-core`
