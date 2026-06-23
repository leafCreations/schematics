# Render Types

Entry point: `build_stage_complete_schematics()` in `render_main.py`.

## Quick start

From the project root (with venv active):

```bash
python render_main.py
```

Or from Python:

```python
from render_main import build_stage_complete_schematics

build_stage_complete_schematics(structure="residence", stage=1, renders="all")
```

## Available renderers

| Render name          | CLI value           | Description                          |
| -------------------- | ------------------- | ------------------------------------ |
| `top_view`           | `top_view`          | Layer-by-layer floor blueprint panels |
| `roof`               | `roof`              | Roof blueprint panels                |
| `structure_facades`  | `structure_facades` | Structure side-view elevations       |
| `path`               | `path`              | Landscaping and path top-down plans  |
| `site_facades`       | `site_facades`      | Site cross-section elevations        |
| `materials`          | `materials`         | Material inventory sheet             |
| `worldgen`           | `worldgen`          | Generate structure in a Minecraft world |
| `all`                | `all`               | Run all renderers above              |

## Examples

Generate all render types:

```python
build_stage_complete_schematics(structure="residence", stage=1, renders="all")
```

Top-down blueprints only:

```python
build_stage_complete_schematics(structure="residence", stage=1, renders="top_view")
```

Multiple specific renderers:

```python
build_stage_complete_schematics(
    structure="residence",
    stage=1,
    renders=["top_view", "roof", "materials"],
)
```

## Output

Schematic PNGs:

```text
output/schematics/{output_folder}/
```

Generated worlds:

```text
output/worlds/{output_folder}/v{version}/
```

Example schematic outputs:

* `Structure_floor_1.png` — floor blueprint sheets
* `{name}_structure_facades.png` — structure elevations
* `{name}_site_topdown.png` — site path plans
* `{name}_site_facades.png` — site cross-sections
* `{name}_materials_list.png` — materials inventory

Before rendering blocks that use the sprite baker, run the relevant bake commands in [sprite-baker.md](sprite-baker.md).
