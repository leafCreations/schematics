---
name: repo-map
description: >-
  One-page map of structure_scripts layout, entry points, save targets, and
  path-to-test hints. Use when starting work in this repo, asking where code
  lives, editing structures YAML, UI, registry, worldgen, or render pipeline,
  or before broad codebase exploration.
---

# Repo Map

Compact index for **structure_scripts**. **Routing:** [AGENTS.md](../../AGENTS.md). Pair with [agent-triage](../agent-triage/SKILL.md) for *how* to work; this skill is *where* things live.

## Top-level layout

```text
helpers/           Shared logic (loaders, tokens, grid, paths, worldgen, sprite_baker/)
registries/        behaviors/*.yaml, palettes/*.yaml, generated/catalog.json, loader.py
renderers/         Blueprint + worldgen render handlers
structures/        Structure packages (manifest + stages + layers)
ui/                PySide6 structure editor
scripts/           CLI, pre-commit helpers, bake_sprites, generate_catalog
docs/              User and developer documentation
config/            Default editor_settings.yaml
assets/minecraft/  Vanilla textures/models (often gitignored locally)
output/            schematics/ and worlds/
worldgen_templates/  Versioned base worlds for worldgen (v26_1_2/, v26_2/; gitignored)
assets/project/    Project-owned custom templates + generated sprite cache
render_main.py     CLI render entry point
```

Full tree: [docs/project-structure.md](../../docs/project-structure.md).

## Structure packages (critical)

**Do not** assume `structures/{name}/stage{N}/structure.yaml` — that layout is obsolete.

```text
structures/{name}/structure.yaml       # manifest
structures/{name}/stage{N}/stage.yaml  # per-stage identity + layer_files
structures/{name}/stage{N}/layers/layer_NN.yaml
```

| What | File(s) | Editor action |
| ---- | ------- | ------------- |
| Site size, placement, paths, dimension | Manifest `structure.yaml` | Save Site Settings |
| Layer list order, groups metadata | Manifest + `stage.yaml` | Save Site Settings |
| Stage name, `layer_files` | `stage.yaml` | Save Site Settings |
| Painted cells | `layers/layer_NN.yaml` | Save Layer |
| Group, visibility, worldgen `index` | Layer YAML | Save Layer / dialogs |

Loader merges manifest into stage at read time: `helpers/structure_loader.py`, `ui/document.py`.

Details: [docs/structure-tokens.md](../../docs/structure-tokens.md#structure-packages).

## Feature areas (kanban cards)

Users tag kanban cards with **`## Feature Areas`** (product labels). Agents resolve labels to file paths and **methods/symbols** using [docs/feature-areas.yaml](../../docs/feature-areas.yaml) during pre-implementation card review — see [kanban-markdown](../kanban-markdown/SKILL.md) § Feature Areas (**Label Paths** + **Label Methods**).

```bash
python scripts/resolve_feature_areas.py "Render Preview" "Render Selection"
python scripts/resolve_feature_areas.py --list
```

After every implementation, agents **must** update `docs/feature-areas.yaml` when paths change and **review/update `docs/`** per [docs-maintenance](../docs-maintenance/SKILL.md). See [kanban-markdown](../kanban-markdown/SKILL.md) § Feature area registry.

## Subsystem entry points

| Subsystem | Start here | Docs |
| --------- | ---------- | ---- |
| **Render CLI** | `render_main.py`, `renderers/registry.py` | [render-types.md](../../docs/render-types.md) |
| **Block registry** | `registries/loader.py`, `helpers/registry_lookup.py` | [registry.md](../../docs/registry.md) — templated families: [reference.md](reference.md) § Templated block families |
| **Palette / picker** | `helpers/block_picker.py`, `registries/palettes/` | [registry.md](../../docs/registry.md) |
| **Cell tokens** | `helpers/structure_tokens.py` | [structure-tokens.md](../../docs/structure-tokens.md) |
| **Structure editor** | `ui/main_window.py`, `ui/document.py` | [ui.md](../../docs/ui.md) |
| **Grid paint/erase** | `ui/widgets/grid.py`, `helpers/grid_brush.py` | [ui.md](../../docs/ui.md) |
| **Site / paths** | `helpers/path_geometry.py`, `helpers/site_ground.py`, `ui/widgets/site_grid.py` | [ui.md](../../docs/ui.md) |
| **Worldgen** | `renderers/worldgen.py`, `helpers/worldgen_*.py` | [worldgen.md](../../docs/worldgen.md) |
| **Sprite icons** | `helpers/sprite_baker/`, `scripts/bake_sprites.py` | [sprite-baker.md](../../docs/sprite-baker.md) |
| **Catalog** | `scripts/generate_catalog.py`, `registries/generated/catalog.json` | [registry.md](../../docs/registry.md) |

## Large files — grep before full read

| File | Why |
| ---- | --- |
| `ui/main_window.py` | Orchestration; search handler name |
| `ui/widgets/grid.py` | Grid + tools; read line ranges |
| `helpers/utils_schematics.py` | Texture resolution |
| `registries/loader.py` | Registry compile + textures |

## Common “where is X?”

| Looking for | Grep / open |
| ----------- | ----------- |
| Render type list | `renderers/registry.py` |
| Palette validation | `registries/validate.py` |
| Pre-commit test mapping | `scripts/pre-commit-pytest.sh` |
| Layer save / dirty state | `ui/document.py`, `ui/main_window.py` |
| Fence / wall adjacency icons | `helpers/fence_adjacency.py`, `helpers/wall_blockstates.py` |
| Bed worldgen patch | `helpers/worldgen_region_patch.py` |
| Terrain legacy tokens | `helpers/terrain_tokens.py` |
| Editor prefs | `config/editor_settings.yaml`, `ui/app_settings.py` |

## Changed path → tests (quick)

Use `.venv/bin/pytest … -q`. Full map: [reference.md](reference.md) and `scripts/pre-commit-pytest.sh`.

| You changed | Run first |
| ----------- | --------- |
| `helpers/block_picker.py`, `registries/` | `tests/test_block_picker.py`, `tests/test_palette_integrity.py` |
| `ui/document.py`, structure YAML | `tests/test_ui_document.py`, `tests/test_structure_loader.py` |
| `ui/widgets/palette_panel.py` | `tests/test_palette_panel.py` |
| `ui/widgets/grid.py` | `tests/test_grid_scrollbars.py` (+ grid-related if any) |
| `ui/main_window.py` | `tests/test_main_window.py` |
| `helpers/materials.py` | `tests/test_materials.py` |
| `helpers/path_geometry.py`, `path_strip.py` | `tests/test_path_geometry.py`, `tests/test_path_strip.py` |
| `renderers/worldgen.py` | `tests/test_worldgen_*.py` (see pre-commit script) |
| `helpers/paths.py`, `helpers/structure_loader.py` | `tests/test_paths.py`, `tests/test_worldgen_functional_blocks.py` |
| `registries/` (new token) | `tests/test_palette_integrity.py`, `tests/test_block_picker.py`, fence/wall baker tests if procedural |

**Full suite triggers:** `conftest.py`, `registries/loader.py`, `render_main.py`, `helpers/context.py`, unmapped `*.py`.

## Project skills (`.cursor/skills/`)

| Skill | Use |
| ----- | --- |
| [project-context](../project-context/SKILL.md) | Minecraft 26.x target, deps, trusted URLs |
| [agent-triage](../agent-triage/SKILL.md) | Start every task — tool choice, token budget |
| [targeted-testing](../targeted-testing/SKILL.md) | Pick and run pytest |
| [pre-commit-workflow](../pre-commit-workflow/SKILL.md) | Commit hook failures |
| [ui-change](../ui-change/SKILL.md) | Editor UI work |
| [agent-self-evaluation](../agent-self-evaluation/SKILL.md) | End-of-task review + update skills from learnings |
| [run-ui](../run-ui/SKILL.md) | Launch editor |
| [kanban-markdown](../kanban-markdown/SKILL.md) | To Do queue; **Feature Areas** → **Label Paths** + **Label Methods**; `docs/feature-areas.yaml` + `docs/` |
| [docs-maintenance](../docs-maintenance/SKILL.md) | Mandatory `docs/` review/update after implementation |
| [optimize-test-suite](../optimize-test-suite/SKILL.md) | Suite optimization only |

## Kanban (agents)

| Location | Agent use |
| -------- | --------- |
| `.devtool/features/*.md` with `status: "todo"` | **Work queue** — read **`## Feature Areas`**; resolve via [docs/feature-areas.yaml](../../docs/feature-areas.yaml) |
| `.devtool/features/*.md` with `status: "backlog"` | **Ignore** — user-managed |
| `.devtool/features/done/*.md` | **Done** — user-managed after app review |
| [kanban-markdown](../kanban-markdown/SKILL.md) | Column rules and card edits |

Do **not** treat [roadmap.md](../../docs/roadmap.md) as the live task queue.

## Docs index

| Doc | Contents |
| --- | -------- |
| [project-info.md](../../docs/project-info.md) | Minecraft 26.x target, deps, trusted URLs |
| [structure-editor-guide.md](../../docs/structure-editor-guide.md) | User workflow |
| [editor-properties.md](../../docs/editor-properties.md) | What saves where |
| [roadmap.md](../../docs/roadmap.md) | Legacy planning notes (superseded by kanban for agents) |

Extended tables: [reference.md](reference.md).
