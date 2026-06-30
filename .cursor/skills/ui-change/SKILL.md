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
- **Free camera (fc0 — Signature: `floating-camera-fc0-free-nav`):** `helpers/orbit_camera.py` — `camera_position` + azimuth/elevation look; **fc2a (`floating-camera-fc2a-mouse-look`):** **click** 3D view to capture focus; `setMouseTracking(True)` + look on `hasFocus()`; `BlankCursor` while focused; **Esc** releases; **fc2b (`floating-camera-fc2b-scroll-move-speed`):** **3D** scroll or **+** / **-** adjusts `viewer.orbit_camera_move_speed` multiplier (±0.05/step, clamp **0.2–1.0**, default **0.65×** — fc3b narrowed fc2b); transient **Move speed: N.N×** on **`_OrbitViewHost` sibling QLabel** in `preview_panel.py` (orbit emits `move_speed_feedback` — **not** child of QOpenGLWidget); **never QPainter in `paintGL`**; hold-fly uses **delta-time** — **not** mouse look or dolly; **hold** **WASD** / arrows / Space / Shift via `_held_movement_keys` + `_movement_timer` (`keyReleaseEvent`, `focusOutEvent` clears) — Signature: `floating-camera-fc0-hold-fly`. **fc1b look forward (Signature: `floating-camera-fc1b-look-forward`):** W/S/↑/↓ → `move_along_look` (full look vector); A/D/←/→ → `move_on_plane` strafe only; **`right_vector` = cross(forward, up)** so strafe matches mouse look — Signature: `floating-camera-fc0-strafe-right`; Space/Shift world ±Y unchanged; overlay hint documents click/Esc/scroll. **fc1 reset (Signature: `floating-camera-fc1-reset-projection`):** **R** → `reset_camera_to_default()` (`default_exterior_eye`, azimuth 0.7, elevation 0.45); overlay hint documents **R**; `_projection_near_plane` / `_projection_far_plane` scale with `bounds_radius`. **fc1c pose persistence:** `viewer.orbit_camera_poses` map (`{structure}/{stage}` keys) via `OrbitCameraPose` / `set_orbit_camera_pose(structure, stage, …)`; `PreviewPanel.set_orbit_pose_scope`; save on **3D→2D**, Viewer tab leave, **structure switch** (`_persist_editor_settings` before `execve`), exit; restore on **3D** entry — Signature: `floating-camera-fc1c-pose-persistence`. **fc3 camera HUD:** `_hud_panel` (header cog + text) via `format_camera_hud_lines` + `OrbitMeshData.hud_voxel_map` / offsets; `format_hud_block_label` → `format_entry_label` for materialized names (e.g. Oak Log); pref `viewer.orbit_camera_hud` (default on); **Viewer → Camera HUD** / **F3** (`_sync_viewer_menu_actions` — enabled Viewer tab + **3D** only); refresh after pointer/keyboard/mesh upload. **fc3a crosshair:** center reticle — Signature: `floating-camera-fc3a-crosshair`. **fc3b HUD settings:** **Viewer → HUD Properties…** + HUD cog → `CameraHudSettingsDialog`; placement (`viewer.orbit_camera_hud_placement`), crosshair pref (`viewer.orbit_camera_hud_crosshair`), speed slider — Signature: `floating-camera-fc3b-hud-settings`.

### 3D orbit camera — pre-review QA (Floating Camera)

Before **review** on cards touching `OrbitPreviewWidget` keyboard movement — Signature:
`floating-camera-fc0-hold-fly`; parent ff: `ff-feature-floating-camera-reset-fc1-2026-06-28-skill-01-a8ee8053`.

| Check | Pass criteria |
| ----- | ------------- |
| Hold Space | Ascends continuously until release |
| Hold Shift | Descends continuously until release |
| Hold W/S or ↑/↓ | Moves continuously along **look vector** (Y changes when pitched — fc1b) |
| Hold A/D or ←/→ | Strafes continuously on **horizontal plane** |
| Focus loss | `focusOutEvent` clears `_held_movement_keys` and stops timer |
| Auto-repeat release | `keyReleaseEvent` ignores `event.isAutoRepeat()` — do not discard held keys |
| Open Recent pose (fc1c) | Stage A **3D** pose → Open Recent stage B **3D** → return to stage A **3D** restores A — Signature: `floating-camera-fc1c-pose-persistence` |
| Mouse look (fc2a) | **Click** 3D view to capture (`grabMouse`/`grabKeyboard`); cursor hidden until **Esc**; look continues outside preview bounds — Signature: `floating-camera-fc2a-mouse-look` |
| Camera HUD (fc3) | **Viewer → Camera HUD** toggles top-right Facing/Position/Looking at; materialized tokens show catalog name; `(none)` in open air; pref survives restart — Signature: `floating-camera-fc3-orientation-hud` |
| HUD crosshair (fc3a) | Center-screen white reticle when **Camera HUD** on and **3D** active; click-to-capture + hidden cursor + **Esc** release — Signature: `floating-camera-fc3a-crosshair` |
| HUD settings (fc3b) | **Viewer → HUD Panel** / **HUD Properties…** / HUD cog / **F3**; **menu toggle text ↔ modal checkbox labels**; placement + crosshair prefs + speed slider **0.2–1.0×** — Signature: `floating-camera-fc3b-hud-settings` |
| Scroll move speed (fc2b) | **3D** scroll or **+** / **-** on **`_OrbitViewHost`** sibling label; clamp **0.2–1.0** step **±0.05**; test **scroll and keyboard**; delta-time fly; mouse look **unchanged**; **never** QPainter in `paintGL` — Signature: `floating-camera-fc2b-scroll-move-speed`, `orbit-shader-attribute-blackout` |
| HUD look-ray accuracy | Full-cell DDA is fc3 ship default — **validate with fc3a crosshair** before geometry-raycast bugs; `bug-orbit-hud-look-ray-geometry-fc3-followup` **closed Done 2026-06-29** (crosshair QA: Looking at correct) — Signature: `floating-camera-fc3-orientation-hud`, `floating-camera-fc3a-crosshair` |
| Tests | `pytest tests/test_orbit_preview.py -q -k "hold or movement_timer or autorepeat"` green |

### Orbit render class (four tiers)

Classify tokens with `helpers.orbit_render_class.orbit_render_class(raw_token)` before editing orbit geometry — Signature: `orbit-render-class-routing`. Full glossary: `docs/render-types.md` § Orbit render class.

| Class | Edit here | Do not |
| ----- | --------- | ------ |
| `solid_cube` | `orbit_greedy_mesh.py` greedy pass | — |
| `partial_box` | `orbit_partial_mesh.py` AABB + atlas | Edit greedy mesh for slab/stair boxes |
| `attachable_box` | `orbit_attachable_mesh.py` custom AABBs | Put attachables in `partial_worlds` |
| `block_model` | `orbit_block_model_mesh.py` JSON faces (`TORCH`, `LANTERN`, `TRAPDOOR:*`, `BED:*`) | Edit greedy mesh or sprite-bake on AABBs |

**Trapdoor taxonomy:** `orbit_render_class("TRAPDOOR:…")` is always `block_model` (open and closed).
Sub-geometry (open plate vs closed half) is resolved in attachable/block-model helpers — not a
separate render class.

**Do not edit `orbit_greedy_mesh.py` for torch/lantern/trapdoor** — those are `block_model`, not `solid_cube`.

### Orbit preview — lessons learned (C3b partial blocks)

Before adding geometry for “transparent” or “missing” partial-block faces, **check textures first**:

1. **Stairs / slabs — opaque tiles** — Editor top-down stair/slab bakes use L-masks or half-height masks (~50% transparent pixels). Orbit box faces must use **full solid-block tiles** (`_orbit_solid_material_face_token`: `PLANKS:{material}` for plank materials; `minecraft:{material}` for stone/cobblestone), not masked `STAIRS:*` / `SLAB:*` bakes.
2. **Fences / walls — masked bakes + discard** — Post/arm boxes are full-height; rail **gaps** live in the 2D adjacency-mask bake, not geometry. Keep masked `FENCE:*` / `WALL:*` bakes; fragment shader `if (sample.a < 0.05) discard` in `_FRAGMENT_SHADER_TEXTURED`. **Do not** map fence faces to solid `PLANKS:*` (fills gaps with wood). Stairs/slabs use opaque atlas tiles — discard is safe for them.
3. **Do not void-fill stairs** — Extra boxes in the L-void with masked textures made QA worse. Prefer corner-probe culling on lower `+Y` + riser strip + plank faces.
4. **Manual QA** — `structures/test/stage1` (oak stairs); `residence/stage1` (oak vs mossy cobblestone, **fences**); `well/stage1` (**cobblestone** stairs, **walls**). Top / front / side / bottom views.
5. **Tests** — opaque: `test_orbit_stair_face_textures_are_opaque`, `test_orbit_slab_face_textures_are_opaque`, `test_orbit_cobblestone_stair_face_textures_are_opaque`, `test_lower_stair_slab_top_face_visible_on_open_half`; masked fence/wall: `test_orbit_fence_side_texture_uses_masked_bake`, `test_orbit_wall_side_texture_uses_masked_bake`; **`facing_block`:** `test_furnace_orbit_vertical_faces_resolve_front_and_side`; full orbit mapping in [targeted-testing/reference.md](../targeted-testing/reference.md).
7. **Greedy shell vs per-block faces** — `_solid_face_visible` culls same-token neighbors only; **material boundaries** emit vertical faces (embedded `CRAFTING_TABLE`). Side textures: `_resolve_orbit_catalog_block_face` → `{block}_side.png`; fluids without side PNG use `catalog_block_texture_name` + `_apply_orbit_catalog_schematic_tint` (`get_texture_for_render`). Test: `test_water_orbit_faces_apply_schematic_blue_tint`.
8. **Catalog functionals** — `SMOKER` / `BLAST_FURNACE` are registry **`facing_block`** tokens (`facing` + `lit` blockstates), not bare `minecraft:*` solids. Orbit front/side/top like `FURNACE`; `;lit=true` → `_front_on.png`. Animated `_on` strips (`smoker_front_on.png` + `.mcmeta`) load **frame 0 only** via `helpers/block_texture_load.py` (2D + 3D). Legacy `minecraft:smoker` cells resolve to registry picker entries (`requires_direction`, **Lit**) via `_ensure_picker_entry_indexes` + `cell_token_matches_picker_entry`.
9. **Slab roof decks** — bottom `SLAB` layers use neighbor-cell `box_face_occluded` + `_slab_deck_bottom_face_occluded` (hide −Y and shared vertical faces). Isolated single slab keeps exterior −Y. Tests: `test_slab_deck_7x7_minus_y_faces_culled`, `test_slab_deck_mesh_has_no_minus_y_normals`.
10. **Solid beside slab/stair** — greedy shell skips full faces toward `partial_worlds`; `_collect_solid_slab_neighbor_strip_faces` restores strips via `iter_solid_neighbor_face_restore_rects` (slab upper/lower half; stair open-half via 2×2 face probe). Tests: `test_solid_emits_upper_strip_face_toward_bottom_slab`, `test_solid_emits_open_half_strip_beside_cobblestone_and_stair`.
11. **C4 attachables** — `helpers/orbit_attachable_mesh.py` must ship with `orbit_partial_mesh.py` routing (`attachable_boxes_for_cell`, `is_orbit_box_behavior`, `is_partial_volume_behavior`) and `orbit_greedy_mesh.py` `solid_cells` / `partial_worlds` updates — Signature: `c4-attachable-partial-mesh-routing`. Chest neighbor pairing; trapdoor open models + `@direction` rotation. **Bed (3D):** `block_model` — `{color}_bed_head` / `{color}_bed_foot` JSON + `textures/block/` via `orbit_block_model_mesh.py`; per-cell models; `bed_partner_occludes_face` — Signature: `orbit-bed-block-model-faces`. **Chest (3D):** schematic bakes on attachable AABBs via `_resolve_orbit_attachable_bake_face_texture` — chest faces from `chest_front*.png` (front + latch), `chest_back_left/right.png` (double back), `chest_side.png` (single back + ends); top/bottom from `chest_top*.png` (double halves split on merged `chest_span`) — Signature: `orbit-chest-schematic-face-templates`; tests `-k "chest or bed"`. **Chest (2D grid):** `GridTextureCache` → `compile_texture_set("top")` → `CHEST#left|#right` from `compose_chest_top_schematic` (`chest_top_left/right.png`) — **not** `chest_back_*` (orbit back only); stale `generated/top/` skipped when custom templates are newer (`chest_compose_source_paths`, `_chest_generated_cache_is_stale`) — restart app or `GridTextureCache.clear_cache()` after template rebakes — Signature: `chest-generated-top-cache-stale`, `orbit-bed-colored-texture-keys`. **Doors:** `#lower` / `#upper` are **separate layer cells**. **Greedy `partial_worlds`:** `slab` + `stairs` only. **Torch/lantern/trapdoor/bed:** JSON element faces via `orbit_block_model_mesh.py` — not 2D `compose_*` bakes on AABB faces. **Direction Y-rotation:** tables keyed `N`/`S`/`E`/`W` from `normalize_direction()` — Signature: `orbit-attachable-direction-rotation-keys`. **Beds:** `_BED_Y_ROTATION` (`N=0,E=90,S=180,W=270`) — pillow authored on model north; not `_BOX_Y_ROTATION` — Signature: `orbit-bed-direction-rotation`. **Hanging lanterns:** `{variant_model}_hanging` (`_resolve_lantern_model_name`) — not hardcoded `lantern_hanging` — Signature: `orbit-lantern-hanging-variant`. Tests: `tests/test_orbit_attachable_mesh.py`.
12. **Orbit shader UV** — hybrid: greedy solid faces use `tileFrac(worldPos)` when `aFaceUv.x < 0`
    (sentinel `-1` in `mesh.uvs`); block-model element quads upload model-local corner UVs via
    `element_face_corner_uvs` + `_face_uv_buffer`. Atlas uploads without GL flip:
    `atlasUv.y=small → PIL top`; `mix(v_bottom, v_top, fv)` → `fv=1` samples PIL top (Mc_v=0).
    Face UV table: `up/south` v-axis and `east/north` u-axis are inverted vs naïve assignment;
    `west` is the canonical correct reference. Partial VBO/shader changes black out the preview
    (Signatures: `orbit-shader-attribute-blackout`, `orbit-block-model-face-uv`). Re-apply C4
    routing separately from UV work.
13. **Top/side crease seam** — grass/dirt_path gaps: `expand_orbit_quad_corners` (+Y on side tops), `_resolve_orbit_side_face_texture`, `_force_opaque_orbit_face` — Signature: `orbit-top-side-seam-geometry`. Greedy solids stay on `tileFrac`; do not move seam fix to block-model UV path.
14. **Block-model compose order** — `element_face_corners_in_block_space`: element tilt first, then block Y around `(8,8,8)`; rotate emitted normals — wall torches lean correctly for all facings.

Details: `docs/render-types.md` § Orbit partial blocks — lessons learned; § Attachables & functionals (C4).
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

## Properties brush — lit defaults

`PropertiesPanel.show_picker_entry` must match registry defaults for **Lit**:

| Behavior | Default **Lit** combo | Source |
| -------- | --------------------- | ------ |
| `campfire` | `"true"` | `DEFAULT_CAMPFIRE_LIT` in `helpers/campfire_state.py` |
| `facing_block` (furnace, smoker, …) | `"false"` | Unlit front unless user toggles |

Test: `test_campfire_facing_and_lit_in_build_placement_token` in `tests/test_properties_panel.py`.

## Properties brush — live apply to selected cell

When a **Grid cell** is selected and matches the active palette entry (`cell_token_matches_picker_entry`):

- **Material**, **Direction**, **Variant** combo changes emit `brush_inspector_changed` (from `_on_brush_option_changed` only — **not** from `show_picker_entry`).
- **Hanging**, **Open**, **Lit** emit `brush_blockstate_changed` (unchanged).
- `MainWindow._apply_inspector_to_selected_cell` builds `build_placement_token()` and calls `_set_cell` when the token differs.

**Do not** emit `brush_inspector_changed` from `show_picker_entry` / `sync_brush_from_cell` — palette switches must not overwrite unrelated selected cells.

Signature: `properties-inspector-live-apply`.

Tests: `test_brush_inspector_changed_emits_on_variant_combo_not_on_picker_entry`, `test_apply_inspector_to_selected_slab_variant_updates_cell`, `test_apply_inspector_skips_when_palette_entry_does_not_match_cell`, `test_apply_inspector_trapdoor_open_uses_build_placement_token`.

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
