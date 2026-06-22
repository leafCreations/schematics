# Repo Map — Reference

## Manifest vs stage fields

### Manifest (`structures/{name}/structure.yaml`)

| Field | Role |
| ----- | ---- |
| `dimension` | overworld / nether / end |
| `grid` | site_width, site_depth, offset_x/z, placement, groups, path_* |
| `site_ground` | 2D path/trim grid |
| `stages[]` | `stage`, `path`, `output_folder` per stage |

### Stage (`stage{N}/stage.yaml`)

| Field | Role |
| ----- | ---- |
| `structure`, `stage`, `name` | Identity |
| `layer_files` | Ordered layer paths |

### Layer (`layers/layer_NN.yaml`)

| Field | Role |
| ----- | ---- |
| `cells` | 2D token grid |
| `index` | Worldgen Y offset (`worldgen_base_y + index`) |
| `group`, `visible`, `description` | Editor / render metadata |

## Registry layout

```text
registries/
  behaviors/     building.yaml, functional.yaml, lighting.yaml, wood.yaml
  palettes/      terrain.yaml (catalog ids by dimension), wood, functional, …
  generated/     catalog.json
  loader.py      BLOCK_REGISTRY, compile_texture_set, …
  validate.py    validate_palettes()
```

Terrain blocks use **catalog** `minecraft:` ids in `palettes/terrain.yaml`, not legacy `GRASS` tokens. Legacy cells still resolve via `helpers/terrain_tokens.py`.

## Render pipeline

```text
render_main.py
  └── renderers/registry.py  →  top_view, roof, structure_facades, path,
                               site_facades, materials, worldgen
  └── helpers/context.py     SchematicContext
  └── helpers/structure_loader.py
```

Output: `output/schematics/{output_folder}/`, `output/worlds/{output_folder}/`.

## UI module map

```text
ui/
  main_window.py       Shell, menus, panel wiring, dirty/save
  document.py          StructureDocument load/save
  editor_history.py    Undo stack
  app_settings.py      ~/.config/structure_scripts/editor_settings.yaml
  widgets/
    palette_panel.py   Block picker
    grid.py            Structure layer grid
    site_grid.py       Site preview
    properties_panel.py  Brush inspector
    *_panel.py         Feature panels
    layer_tools_panel.py  Grid header toolbar
```

## Worldgen helpers

| Module | Role |
| ------ | ---- |
| `worldgen_multiblock.py` | Deferred bed/door pass |
| `worldgen_block_entities.py` | Bed block entities (Java 26.1) |
| `worldgen_region_patch.py` | Post-save region patch |
| `worldgen_site.py` | Site ground + path lighting export |
| `worldgen_chunk_writer.py` | Chunk commit helper |

## Pre-commit pytest mapping (selected)

From `scripts/pre-commit-pytest.sh` — grep the script for paths not listed here.

| Staged path pattern | Tests added |
| ------------------- | ----------- |
| `helpers/structure_loader.py` | `test_structure_loader`, `test_structure_tokens`, `test_ui_document` |
| `helpers/block_picker.py` | `test_block_picker`, `test_registry_blocks`, `test_palette_integrity`, … |
| `helpers/materials.py` | `test_materials`, `test_collect_material_tokens` |
| `helpers/landscape_utils.py`, `path_geometry.py`, `path_strip.py` | path/landscape/site lighting tests |
| `helpers/sprite_baker/*` | `test_sprite_baker_*`, `test_sprite_baker_cache` |
| `registries/validate.py`, `palettes/*`, `behaviors/*` | `test_palette_integrity`, `test_registry_*`, `test_block_picker` |
| `renderers/worldgen.py`, `helpers/worldgen_*` | all `test_worldgen_*` listed in script |
| `ui/document.py` | `test_ui_document`, `test_editor_history` |
| `ui/widgets/*`, `ui/main_window.py` | `test_ui_*`, `test_main_window`, … |
| `structures/*` | `test_structure_loader`, `test_ui_document` |

## Test helpers

| File | Role |
| ---- | ---- |
| `tests/palette_helpers.py` | Dynamic terrain palette counts (avoid hard-coded catalog sizes) |
| `tests/conftest.py` | Shared `ctx` fixture, `requires_assets` marker |

## Assets and optional deps

| Extra | Install | For |
| ----- | ------- | --- |
| `[dev]` | `pip install -e ".[dev]"` | pytest, ruff, pre-commit |
| `[ui]` | `pip install -e ".[ui]"` | PySide6 editor |
| `[worldgen]` | `pip install -e ".[worldgen]"` | Amulet world export |

Block textures: `assets/minecraft/textures/block/` (required for grid icons and renders).

## Cursor rules (on demand)

| Rule | When |
| ---- | ---- |
| `.cursor/rules/testing.mdc` | Always applied — targeted pytest |
| `.cursor/rules/ui-panels.mdc` | Panel UI |
| `.cursor/rules/ui-dialogs.mdc` | Dialogs |
| `.cursor/rules/worldgen.mdc` | Worldgen placement model |
| `.cursor/rules/model-routing.mdc` | Model choice |
