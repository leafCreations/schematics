# Targeted Testing — Reference

Mirrors `scripts/pre-commit-pytest.sh`. When in doubt, grep that script for the path you changed.

## Full-suite triggers (always)

These staged paths force **entire suite**:

- `tests/conftest.py`
- `pyproject.toml`, `setup.py`
- `render_main.py`
- `helpers/context.py`
- `registries/loader.py`
- `helpers/utils.py`

Also: unmapped `*.py` changes, or >20 targeted test files accumulated.

## helpers/

| Staged path | Tests |
| ----------- | ----- |
| `helpers/structure_loader.py`, `helpers/structure_tokens.py` | `test_structure_loader`, `test_structure_tokens`, `test_ui_document` |
| `helpers/cells.py` | `test_cells` |
| `helpers/block_picker.py`, `registry_lookup.py`, `registry_blocks.py` | `test_block_picker`, `test_registry_blocks`, `test_registry_phase_b`, `test_palette_integrity` |
| `helpers/grid.py` | `test_grid` |
| `helpers/grid_cells.py`, `grid_placement.py` | `test_grid_cells`, `test_grid_placement` |
| `helpers/layer_rotation.py` | `test_layer_rotation` |
| `helpers/fence_adjacency.py` | `test_fence_adjacency`, `test_utils_schematics_fence`, `test_sprite_baker_fence*` |
| `helpers/lantern_placement.py` | `test_lantern_placement`, `test_sprite_baker_lantern` |
| `helpers/paths.py`, `layers.py`, `layer_management.py` | `test_layers`, `test_layer_management` |
| `helpers/materials.py`, `collect_material_tokens.py` | `test_materials`, `test_collect_material_tokens` |
| `helpers/landscape_utils.py`, `path_geometry.py`, `path_strip.py` | `test_landscape_utils`, `test_path_geometry`, `test_path_strip`, `test_path_lighting`, `test_site_display_lighting` |
| `helpers/utils_schematics.py`, `facade_projection.py` | `test_utils_schematics`, `test_facade_projection`, `test_utils_schematics_*` |
| `helpers/sprite_baker/*` | `test_sprite_baker_*`, `test_sprite_baker_cache` |
| `helpers/block_catalog.py` | `test_block_catalog`, `test_block_picker` |
| `helpers/pipeline.py`, `paths.py`, `render_image.py`, `fonts.py` | `test_paths`, `test_pipeline`, `test_fonts` |
| `helpers/site_ground.py`, `structure_metadata.py` | `test_ui_document`, `test_site_cells`, `test_structure_metadata` |
| `helpers/worldgen_*.py` | See worldgen row below |
| `helpers/*` (other) | `test_utils` |

## registries/

| Staged path | Tests |
| ----------- | ----- |
| `registries/validate.py`, `palettes/*`, `behaviors/*`, `generated/*` | `test_palette_integrity`, `test_registry_reload`, `test_registry_phase_b`, `test_block_picker` |

## renderers/

| Staged path | Tests |
| ----------- | ----- |
| `renderers/worldgen.py`, `helpers/worldgen_*.py` | `test_worldgen_chest`, `test_worldgen_tokens`, `test_worldgen_site`, `test_worldgen_bed`, `test_worldgen_region_patch`, `test_worldgen_functional_blocks`, `test_lantern_placement`, `test_fence_adjacency` |
| `renderers/*` (other) | `test_facade_projection`, `test_layers`, `test_pipeline`, `test_render_panel` |

## ui/

| Staged path | Tests |
| ----------- | ----- |
| `ui/document.py`, `editor_history.py`, `editor_materials.py`, `app_settings.py`, `editor_prefs.py` | `test_ui_document`, `test_editor_history` |
| `ui/texture_cache.py`, `materials_icons.py`, `site_cells.py` | `test_texture_cache`, `test_site_cells` |
| `ui/main_window.py`, `ui/widgets/*`, `toolbar_icons.py`, … | `test_ui_*`, `test_main_window`, `test_render_panel`, `test_texture_cache`, `test_structure_metadata` |
| `ui/*` (other) | `test_ui_*`, `test_main_window` |

Widget-specific shortcuts (manual edits, narrower than hook):

| Widget / area | Prefer |
| ------------- | ------ |
| `palette_panel.py` | `test_palette_panel.py` |
| `grid.py` | `test_grid_scrollbars.py` + grid tests if present |
| `properties_panel.py` | `test_properties_panel.py` |
| `site_grid.py` | site/worldgen-related tests if behavior changed |

## structures/ and scripts/

| Staged path | Tests |
| ----------- | ----- |
| `structures/*` | `test_structure_loader`, `test_ui_document` |
| `tests/test_*.py` | that test file only |
| `scripts/migrate_structure_to_yaml.py` | `test_structure_loader` |
| `scripts/bake_sprites.py`, `generate_catalog.py` | `test_sprite_baker_*`, `test_block_catalog` |

## Convention fallback

If `tests/test_<module>.py` exists for `helpers/<module>.py` and the path is not in the script, run that single file first.

## Example commands

```bash
# Registry + picker change
.venv/bin/pytest tests/test_block_picker.py tests/test_palette_integrity.py -q

# Single failure isolation
.venv/bin/pytest tests/test_materials.py::test_resolve_material_display_name_uses_catalog -q

# UI panel
.venv/bin/pytest tests/test_palette_panel.py -q

# Pre-commit parity
pre-commit run pytest
```

## record-pytest-pass

After manual green run matching staged files:

```bash
scripts/record-pytest-pass.sh
```

Writes `.pytest-precommit-pass` with staged hash; valid 30 minutes.

## Skip pytest on commit (user/agent explicit)

```bash
SKIP=pytest git commit ...
# or scripts/gcn / scripts/commit-no-pytest
```

User should still run targeted tests manually before push.
