---
name: ui-change
description: >-
  Checklist for structure_scripts editor UI changes under ui/. Use when adding or
  modifying panels, dialogs, grid toolbar, properties brush, site tab, palette,
  main_window wiring, or user-facing editor behavior documented in docs/ui.md.
  After changes, review and update docs/ per docs-maintenance (no exceptions).
---

# UI Change

Checklist for PySide6 editor work. Minimize churn: follow existing patterns; wire in `main_window.py`; test narrowly.

Start with [agent-triage](../agent-triage/SKILL.md) and [repo-map](../repo-map/SKILL.md).

## Before editing

| Touching | Read |
| -------- | ---- |
| New/refactored panel | `.cursor/rules/ui-panels.mdc` |
| Modal dialog / prompt | `.cursor/rules/ui-dialogs.mdc` |
| Selector/Eraser split toolbar | `.cursor/rules/ui-split-buttons.mdc` |
| New preference / tooltip | `.cursor/rules/ui-properties.mdc` |
| User-facing behavior | `docs/ui.md`, `docs/editor-properties.md` |

**Do not** read all rules for a one-line label fix.

## Panel checklist

1. Subclass `QGroupBox` — **no** title in `super().__init__()`.
2. Title row via `ui/widgets/panel_header.py`:
   - `create_simple_titled_panel_layout` — title only
   - `create_titled_panel_layout` — title + header buttons
   - `create_nested_group_layout` — nested sections (properties panel)
3. Header icons: 18px — `panel_icon_size()`, `make_panel_tool_button()`.
4. Panel emits signals (`*_requested`); **wire in `ui/main_window.py` only**.
5. Hiding panels: update `_update_palette_column_layout()` or `_update_structure_tools_column_layout()` so columns don’t leave gaps.

## Dialog checklist

1. Subclass `QDialog` in `ui/widgets/`.
2. Use `ui/dialog_layout.py`: `create_dialog_shell`, `apply_dialog_field_style` (32px), `create_dialog_button_box`.
3. **No** `QInputDialog` for new prompts — use `InputTextDialog`.
4. Hint: **"Changes are saved when you click OK."**
5. On accept: `main_window._persist_dialog_changes(...)` — don’t only set dirty flags.

## Grid toolbar

- Tools live in `ui/widgets/layer_tools_panel.py` / `LayerActionToolbar`.
- Toolbar icons: 22px — `toolbar_icon_size()`.
- Split buttons: menu pops from **container** bottom-left (see ui-split-buttons.mdc).

## Viewer tab (preview)

- **Preview** panel: `ui/widgets/preview_panel.py`; gallery nav + zoom: `ui/widgets/preview_toolbar.py` (**Preview Toolbar** feature area).
- Zoom resets to 100% on Viewer tab open — wire in `main_window._on_tab_changed` if adding tab-level preview behavior.
- **Open Structure / Open Recent:** `_restart_editor_for_structure` bypasses `_block_if_render_in_progress` when `_render_is_preview` (process `execve` replaces the editor); export/worldgen renders still block with “opening another structure.”
- **Viewer preview zoom:** persisted in `viewer.preview_zoom_percent` (`editor_settings.yaml`); restored on **Viewer** tab open via `PreviewPanel.restore_saved_zoom()`. Toolbar **slider** + **Reset** + wheel; **Viewer** menu (after **Structure** in menu bar; Zoom In/Out/Reset) enabled on Viewer tab only.
- **3D orbit preview:** **2D | 3D** toggle on `PreviewPanel`; lazy `OrbitPreviewWidget` (`QOpenGLWidget`); mesh via `helpers/orbit_mesh.py` + `MeshBuildWorker`; stale refresh in `MainWindow._ensure_orbit_mesh`. Do not instantiate GL widgets at import time (headless pytest). **`QMatrix4x4.lookAt`** in Qt6/PySide6 takes three **`QVector3D`** (eye, center, up) — not nine floats.

### Orbit preview — lessons learned (C3b partial blocks)

Before adding geometry for “transparent” or “missing” partial-block faces, **check textures first**:

1. **Stairs / slabs — opaque tiles** — Editor top-down stair/slab bakes use L-masks or half-height masks (~50% transparent pixels). Orbit box faces must use **full solid-block tiles** (`_orbit_solid_material_face_token`: `PLANKS:{material}` for plank materials; `minecraft:{material}` for stone/cobblestone), not masked `STAIRS:*` / `SLAB:*` bakes.
2. **Fences / walls — masked bakes + discard** — Post/arm boxes are full-height; rail **gaps** live in the 2D adjacency-mask bake, not geometry. Keep masked `FENCE:*` / `WALL:*` bakes; fragment shader `if (sample.a < 0.05) discard` in `_FRAGMENT_SHADER_TEXTURED`. **Do not** map fence faces to solid `PLANKS:*` (fills gaps with wood). Stairs/slabs use opaque atlas tiles — discard is safe for them.
3. **Do not void-fill stairs** — Extra boxes in the L-void with masked textures made QA worse. Prefer corner-probe culling on lower `+Y` + riser strip + plank faces.
4. **Manual QA** — `structures/test/stage1` (oak stairs); `residence/stage1` (oak vs mossy cobblestone, **fences**); `well/stage1` (**cobblestone** stairs, **walls**). Top / front / side / bottom views.
5. **Tests** — opaque: `test_orbit_stair_face_textures_are_opaque`, `test_orbit_slab_face_textures_are_opaque`, `test_orbit_cobblestone_stair_face_textures_are_opaque`, `test_lower_stair_slab_top_face_visible_on_open_half`; masked fence/wall: `test_orbit_fence_side_texture_uses_masked_bake`, `test_orbit_wall_side_texture_uses_masked_bake`; **`facing_block`:** `test_furnace_orbit_vertical_faces_resolve_front_and_side`; full orbit mapping in [targeted-testing/reference.md](../targeted-testing/reference.md).
7. **Greedy shell vs per-block faces** — `_solid_face_visible` culls same-token neighbors only; **material boundaries** emit vertical faces (embedded `CRAFTING_TABLE`). Side textures: `_resolve_orbit_catalog_block_face` → `{block}_side.png`.
8. **Catalog functionals** — `SMOKER` / `BLAST_FURNACE` are registry **`facing_block`** tokens (`facing` + `lit` blockstates), not bare `minecraft:*` solids. Orbit front/side/top like `FURNACE`; `;lit=true` → `_front_on.png`. Legacy `minecraft:smoker` cells resolve to registry picker entries (`requires_direction`, **Lit**) via `_ensure_picker_entry_indexes` + `cell_token_matches_picker_entry`.
9. **Slab roof decks** — bottom `SLAB` layers use neighbor-cell `box_face_occluded` + `_slab_deck_bottom_face_occluded` (hide −Y and shared vertical faces). Isolated single slab keeps exterior −Y. Tests: `test_slab_deck_7x7_minus_y_faces_culled`, `test_slab_deck_mesh_has_no_minus_y_normals`.
10. **Solid beside slab** — greedy shell skips full faces toward `partial_worlds`; `_collect_solid_slab_neighbor_strip_faces` restores **upper** vertical strip beside bottom slab (lower beside `#top`). Tests: `test_solid_emits_upper_strip_face_toward_bottom_slab`.

Details: `docs/render-types.md` § Orbit partial blocks — lessons learned.
- Update `docs/ui.md` Viewer table and `docs/feature-areas.yaml` when adding preview controls.

## Render panel (Viewer tab actions)

- `ui/widgets/render_panel.py` — export/worldgen/**Open Output Folder**/**Open World Folder** buttons (no schematic path label). World folder enables only after successful worldgen this session (`set_worldgen_output_available`).
- Worldgen enablement: `RenderPanel.set_worldgen_template_available` from `main_window._sync_render_output_hint` after `resolve_worldgen_template_dir`.

## Persistence — what saves where

| UI surface | Saves to |
| ---------- | -------- |
| Structure grid cells | `layers/layer_NN.yaml` — Save Layer |
| Site settings, paths, groups order | Manifest `structure.yaml` + `stage.yaml` — Save Site Settings |
| Layer dialog OK | Auto-save via `_persist_dialog_changes` |
| View prefs (tooltips, axis labels) | `~/.config/structure_scripts/editor_settings.yaml` |

Details: `docs/structure-tokens.md`, `docs/editor-properties.md`.

## main_window.py

- **Orchestration only** — grep for similar handler before reading whole file.
- New panel: `addWidget` + layout updater + View menu if dismissible.
- Tool sync: `_sync_layer_tool_panels()` pattern for paint/selector/eraser visibility.

## Tests

Use [targeted-testing](../targeted-testing/SKILL.md) — **not** full suite.

| Changed | Run |
| ------- | --- |
| `ui/widgets/palette_panel.py` | `tests/test_palette_panel.py` |
| `ui/widgets/grid.py` | `tests/test_grid_scrollbars.py` + related |
| `ui/widgets/properties_panel.py` | `tests/test_properties_panel.py` |
| `ui/document.py` | `tests/test_ui_document.py` |
| `ui/main_window.py` | `tests/test_main_window.py` |
| Dialog widget | dialog tests if present + main_window if wired |

Qt tests may need full shell permissions (segfault in sandbox).

## Manual verify

After non-trivial UI changes:

```bash
bash scripts/run-ui residence 1
```

Use **View → Reload Window** (`Ctrl+Shift+Q`) after code edits instead of full restart when possible. See [run-ui](../run-ui/SKILL.md).

## Docs (mandatory)

After **any** user-visible or workflow change, review and update **`docs/`** in the same turn — [docs-maintenance](../docs-maintenance/SKILL.md). **No exceptions**; do not defer.

Typical targets:

- `docs/ui.md` — developer reference
- `docs/structure-editor-guide.md` — user workflow
- `docs/editor-properties.md` — controls and save targets
- `docs/render-types.md` — preview/export paths when render pipeline changes

Grep `docs/` for stale terms (old tab names, removed buttons, “not yet implemented”) before handoff.

## Do not

- `QGroupBox("Title")` for panel names
- Per-menu stylesheets — use `configure_ui_menus()` / global menu style
- Business logic heavy in widgets — delegate to helpers
- Full pytest after every widget tweak
- Launch UI for docs-only commits

## End checklist

```
- [ ] panel_header / dialog_layout patterns used
- [ ] Signals wired in main_window.py
- [ ] Column layout updated if panel show/hide changed
- [ ] _persist_dialog_changes on dialog OK
- [ ] Targeted UI tests run
- [ ] docs/ reviewed and updated per [docs-maintenance](../docs-maintenance/SKILL.md)
```

Panel refactor backlog: `docs/ui-panel-refactor.md`.
