# Minecraft Schematics Renderer

A modular Minecraft schematic rendering and world-generation toolkit written in Python.

Generates top-down blueprints, roof plans, structure and site facades, path layouts, material inventory sheets, and Minecraft worlds (via Amulet).

Registry-driven architecture: YAML block definitions, shared `SchematicContext`, modular render pipelines.

## Quick start

Requires **Python 3.11+**.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

Bake block sprites (required before first render; `assets/` is not in the repo):

```bash
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
| [docs/development.md](docs/development.md) | Venv, dependencies, Ruff, pre-commit, pytest |
| [docs/project-structure.md](docs/project-structure.md) | Repository layout |
| [docs/registry.md](docs/registry.md) | `blocks.yaml` and texture loading |
| [docs/structure-tokens.md](docs/structure-tokens.md) | Cell token syntax (`:material`, `@direction`, `#variant`) |
| [docs/sprite-baker.md](docs/sprite-baker.md) | Baking `assets/generated/` sprites |
| [docs/render-types.md](docs/render-types.md) | Renderers, examples, output paths |
| [docs/worldgen.md](docs/worldgen.md) | Template world and Amulet export |
| [docs/roadmap.md](docs/roadmap.md) | Design goals and future plans |
| [AMULET_INSTALL_NOTES.md](AMULET_INSTALL_NOTES.md) | Amulet build troubleshooting |

## Features

* Registry-driven block rendering (`registries/blocks.yaml`)
* Procedural sprite baker with cached generated textures
* Top and side schematic views with per-panel material inventory
* Multi-render pipeline with selective execution
* Path and landscaping generation
* Minecraft world export via `amulet-core`
