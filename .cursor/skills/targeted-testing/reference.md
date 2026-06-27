# Targeted Testing — Reference

Mirrors `scripts/pre-commit-pytest.sh`. When in doubt, grep that script for the path you changed.

**Hook/pytest failure patterns** (stash, scope mismatch, no card): [pre-commit-workflow/reference.md](../pre-commit-workflow/reference.md) § Failure patterns — signatures `precommit-*`. Path→test map below.

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
| `helpers/fence_adjacency.py`, `helpers/wall_blockstates.py` | `test_fence_adjacency`, `test_wall_blockstates`, `test_utils_schematics_fence`, `test_utils_schematics_wall`, `test_sprite_baker_fence*`, `test_sprite_baker_wall` |
| `helpers/lantern_placement.py` | `test_lantern_placement`, `test_sprite_baker_lantern` |
| `helpers/paths.py`, `layers.py`, `layer_management.py` | `test_layers`, `test_layer_management` |
| `helpers/materials.py`, `collect_material_tokens.py` | `test_materials`, `test_collect_material_tokens` |
| `helpers/landscape_utils.py`, `path_geometry.py`, `path_strip.py` | `test_landscape_utils`, `test_path_geometry`, `test_path_strip`, `test_path_lighting`, `test_site_display_lighting` |
| `helpers/utils_schematics.py`, `facade_projection.py` | `test_utils_schematics`, `test_facade_projection`, `test_utils_schematics_*` |
| `helpers/sprite_baker/*` | `test_sprite_baker_*`, `test_sprite_baker_cache` |
| `helpers/block_catalog.py` | `test_block_catalog`, `test_block_picker` |
| `helpers/pipeline.py`, `paths.py`, `render_image.py`, `fonts.py` | `test_paths`, `test_pipeline`, `test_fonts` |
| `helpers/site_ground.py`, `structure_metadata.py` | `test_ui_document`, `test_site_cells`, `test_structure_metadata` |
| `helpers/orbit_greedy_mesh.py`, `orbit_texture_atlas.py` | `test_orbit_preview`, `test_orbit_greedy_mesh` |
| `helpers/orbit_render_class.py` — agent dispatch taxonomy (Signature: `orbit-render-class-routing`) | `test_orbit_render_class.py` — classify token before editing orbit helpers; trapdoor open/closed → `block_model`; glossary `docs/render-types.md` § Orbit render class |
| Partial vs solid culling | `test_orbit_partial_mesh.py` — riser + `test_lower_stair_slab_top_face_visible_on_open_half`, `test_orbit_stair_face_textures_are_opaque`, `test_orbit_cobblestone_stair_face_textures_are_opaque`, `test_orbit_fence_side_texture_uses_masked_bake`, `test_orbit_wall_side_texture_uses_masked_bake` |
| `helpers/orbit_partial_mesh.py`, `orbit_face_textures.py`, `orbit_preview_widget.py` | `test_orbit_partial_mesh` (+ greedy/preview when mesh integration changes). Stair/slab opaque tiles; fence/wall masked bakes + shader discard. |
| `helpers/orbit_attachable_mesh.py`, `partial_worlds` QA (lantern/fence wall hole) | `test_orbit_attachable_mesh.py` — `test_plank_face_toward_lantern_neighbor_is_not_culled`, `test_plank_face_toward_fence_neighbor_is_not_culled`, `test_greedy_mesh_plank_beside_fence_has_exterior_face`, `test_slab_neighbor_still_in_partial_worlds` |
| `helpers/orbit_block_model_mesh.py`, torch/lantern/trapdoor element faces (Signature: `orbit-attachable-block-model-faces`) | `test_orbit_attachable_mesh.py` — `test_wall_torch_uses_block_model_faces_not_sprite_bake_on_aabb`, `test_wall_torch_against_plank_culls_back_face` |
| `helpers/orbit_attachable_mesh.py` direction Y-rotation (`N`/`S`/`E`/`W` keys; Signature: `orbit-attachable-direction-rotation-keys`) | `test_orbit_attachable_mesh.py` — `test_wall_torch_rotation_follows_token_direction`, `test_door_plate_rotates_with_direction` |
| `helpers/sprite_baker/block_model.py` compose order (element rot then block Y; Signature: `orbit-block-model-compose-order`) | `test_orbit_attachable_mesh.py` — `test_wall_torch_tip_leans_in_facing_direction` |
| `helpers/orbit_partial_mesh.py` `iter_solid_neighbor_face_restore_rects` (Signature: `orbit-stair-solid-face-restore`) | `test_orbit_partial_mesh.py` — `test_solid_emits_open_half_strip_beside_cobblestone_and_stair`, `test_solid_emits_restored_face_toward_partial_stair_neighbor` |
| `helpers/orbit_face_textures.py` `_apply_orbit_catalog_schematic_tint` (water side fallback) | `test_orbit_greedy_mesh.py` — `test_water_orbit_faces_apply_schematic_blue_tint` |
| `helpers/orbit_greedy_mesh.py` `expand_orbit_quad_corners`; `orbit_face_textures.py` `_resolve_orbit_side_face_texture`, `_force_opaque_orbit_face` (grass/dirt_path seam — geometry/texture only, no `aFaceUv`) | `test_orbit_greedy_mesh.py` — `-k "expand_orbit or dirt_path_side or cobblestone_orbit_side"` |
| `helpers/orbit_attachable_mesh.py` `_resolve_lantern_model_name` (variant hanging models) | `test_orbit_attachable_mesh.py` — `test_copper_lantern_hanging_uses_variant_hanging_model` |

### Orbit stair “missing faces” — diagnose first

| Check | Command / test |
| ----- | -------------- |
| Transparent pixels in face bake | `test_orbit_stair_face_textures_are_opaque` — must pass before adding mesh |
| Pink fallback on `facing_block` vertical faces | `test_furnace_orbit_vertical_faces_resolve_front_and_side`, `test_furnace_orbit_front_signature_uses_topdown_texture`, `test_furnace_orbit_top_face_uses_block_cap_not_front`, `test_furnace_orbit_front_vertical_face_upright_for_all_directions` |
| Embedded solid / crafting table sides | `test_solid_face_visible_at_material_boundary`, `test_embedded_crafting_table_has_vertical_faces`, `test_crafting_table_orbit_side_uses_catalog_side_texture` |
| Catalog functional side/cap (smoker, blast furnace) | `test_smoker_facing_block_orbit_side_top_and_front`, `test_smoker_lit_front_uses_on_texture`, `test_blast_furnace_facing_block_orbit_textures`, `test_minecraft_smoker_alias_uses_facing_block_registry` |
| Lit `_on` animated strip (stacked fire openings) | `test_block_texture_load.py` (`animation_first_frame`, `load_block_texture_image`); `test_furnace_lit_front_unchanged_single_frame`, `test_smoker_lit_topdown_uses_first_animation_frame` — assert via `load_block_texture_image`, not full-strip resize |
| Lower slab open half culled | `test_lower_stair_slab_top_face_visible_on_open_half` |
| Minimal visual repro | `structures/test/stage1` → Viewer **3D** |
| Integration | `residence/stage1` stair run vs mossy cobblestone |

**Lesson:** holes in tread/side/bottom are often **masked α + shader discard**, not missing quads. See `docs/render-types.md` § Orbit partial blocks — lessons learned.
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

`test_worldgen_functional_blocks` chest NBT case uses **`residence` stage 1** (double chest in `layer_01.yaml`); `well` has no chest tokens.
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
| `orbit_preview_widget.py`, `mesh_build_worker.py` | `test_orbit_preview`, `test_orbit_greedy_mesh` (skip `view_matrix` test in headless CI) |
| `palette_panel.py` | `test_palette_panel.py` |
| `grid.py` | `test_grid_scrollbars.py` + grid tests if present |
| `properties_panel.py` | `test_properties_panel.py` |
| `site_grid.py` | site/worldgen-related tests if behavior changed |

## Commit verification (avoid hook surprises)

Agents often run a narrow test set during development, then commit fails because the hook chose a **different** scope.

| Situation | What to run before commit |
| --------- | ------------------------- |
| Any multi-file / cross-package change | `scripts/pre-commit-pytest.sh` (read first line) |
| `render_main.py` staged | Full suite (hook always) |
| Palette YAML moved blocks between tabs | `test_palette_integrity`, `test_block_picker`, `test_sprite_baker_simple`, `test_registry_phase_b` |
| `helpers/terrain_tokens.py` | `test_terrain_tokens`, `test_sprite_baker_simple` |
| `structures/**` layer cells changed | `test_worldgen_functional_blocks`, `test_structure_loader` |
| Fixed one failing test | Re-run `scripts/pre-commit-pytest.sh` — see `precommit-pytest-scope-mismatch` in [pre-commit-workflow/reference.md](../pre-commit-workflow/reference.md) |

## structures/ and scripts/

| Staged path | Tests |
| ----------- | ----- |
| `structures/*` | `test_structure_loader`, `test_ui_document`, `test_worldgen_functional_blocks`, `test_worldgen_chest` |
| `helpers/terrain_tokens.py` | `test_terrain_tokens`, `test_sprite_baker_simple`, `test_palette_integrity`, `test_block_picker` |
| `tests/test_*.py` | that test file only |
| `scripts/migrate_structure_to_yaml.py` | `test_structure_loader` |
| `scripts/bake_sprites.py`, `generate_catalog.py` | `test_sprite_baker_*`, `test_block_catalog` |
| `scripts/build_lessons_index.py`, `scripts/resolve_prior_lessons.py` | `test_build_lessons_index`, `test_resolve_prior_lessons`; `-k parse_artifacts` after `_normalize_doc_ref` / `parse_artifacts_line` edits |
| `scripts/check_lessons_coverage.py`, `scripts/lessons_coverage_lib.py`, `scripts/check_governance_parity.py`, `scripts/pre-commit-lessons-coverage.sh` | `test_check_lessons_coverage`, `test_check_governance_parity`; `-k lessons_coverage or threshold` — Signature: `lessons-coverage-ci-drift`. **Fixtures:** monkeypatch `REPO_ROOT` on both `lessons_coverage_lib` and `resolve_prior_lessons` when using `tmp_path` kanban dirs (`build_report` uses `relative_to(REPO_ROOT)`) |

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
