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

## In-app preview (editor Viewer tab)

The editor preview uses a **separate session directory** from export output:

```text
output/schematics/_preview/{session_uuid}/
```

Each editor process gets one UUID. Preview files use fixed names (not the `{name}_` export prefix), for example:

| Preview dropdown | Session PNG examples |
| ---------------- | -------------------- |
| Top Down | `Structure_{group_slug}_y{N}.png` per visible layer in the group |
| Structure Facades | `Structure_facades_{N\|S\|W\|E}.png` |
| Site Facades | `Site_facades_{N\|S\|W\|E}.png` |
| Site Top Down | `Site_topdown_y{layer_y}.png` (e.g. `y-1`, `y0`, `y1`) |
| Materials List | `Materials_list.png` |

**Export Render** on the Viewer tab writes the matching export file(s) under `output/schematics/{output_folder}/` (see table above). Preview session folders are deleted when the app closes, when you open a different structure/stage, when you open a newly created structure, or when you reload the window.

### 2D Top Down preview (Viewer tab)

Top-down cells use `helpers/utils_schematics.py` → `resolve_cell_texture` / `paste_topdown_token` with baked sprites from `compile_texture_set()`.

| Aspect | Behavior |
| ------ | -------- |
| Stairs (`behavior: stairs`) | Top bakes composite **tread** (full α) + **riser ghost** (~45% α, RGB lightened toward white on L-void) via `compose_stairs` / `build_stair_riser_top_mask`. Masks are **south-facing** at bake time. At paste time, **straight and corner** shapes rotate with `corner_stair_facing_rotation` + `rotate_texture_by_degrees` — **not** `rotate_directional_texture`. Matches 3D orbit tread placement and worldgen. Tests: `test_paste_straight_stair_matches_worldgen_facing`, `test_paste_corner_stair_matches_worldgen_facing`, `test_stair_riser_ghost_distinct_from_slab_void`. Rebake top stairs after compositor changes (`scripts/bake_sprites.py --type stairs --view top --all --force`). |
| Fences / walls | Adjacency-mask variants from `resolve_fence_connections` at paste time. |

### 3D orbit preview (Viewer tab)

Toggle **3D** on the preview panel to view a greedy-meshed exterior shell built from the **in-memory** editor document via `SchematicContext` (not from session PNGs or exported schematics).

| Aspect | Behavior |
| ------ | -------- |
| Data source | `structure_config_from_document` → `build_schematic_context` → `helpers/orbit_greedy_mesh.py` + `helpers/orbit_partial_mesh.py` |
| Refresh | Same `_preview_stale` / unsaved-document rules as 2D; `MeshBuildWorker` off UI thread |
| Rendering | `OrbitPreviewWidget` (`QOpenGLWidget`) — one VBO + one texture atlas; per-block texture tiling via world-space `fract()` in the fragment shader |
| Greedy shell (C2+) | Solid cells merge coplanar faces for performance. **Vertical faces** emit when the neighbor is **air** or a **different token** (material boundary) — embedded functionals (e.g. `CRAFTING_TABLE` in a plank floor) show side quads at token boundaries. Same-token neighbors still cull mutual faces. ±Y uses the same rule across layers. |
| Textures (C3a) | `helpers/orbit_face_textures.py` — face-normal-aware `resolve_cell_texture()`; atlas tiles at `BLOCK_PX` (30); greedy merge keyed by texture signature. **`minecraft:*` catalog caps** (water, lava, grass): `{block}_top.png` on ±Y; fluids without `{block}_side.png` fall back to `catalog_block_texture_name` (`water_still.png`) on vertical faces; **`get_texture_for_render`** schematic tint on catalog loads. **`facing_block`** (`FURNACE`, `SMOKER`, `BLAST_FURNACE`): `facing` + `lit` blockstates; vertical face matching `@direction` → `{block}_front.png` or `{block}_front_on.png` when `;lit=true` (animated `_on` PNGs: crop **first frame** via companion `.mcmeta` — `helpers/block_texture_load.py`); other vertical faces → `render.side`; orbit **`+Y`/`-Y`** → `{block}_top.png`. 2D top-down and structure/site facades (when `@direction` matches the elevation) use `helpers/facing_block_textures.py`. Legacy `minecraft:smoker` aliases to `SMOKER`. **Solid/catalog functionals** without facing (e.g. `CRAFTING_TABLE`): `{block}_side.png` on vertical faces. |
| Partial blocks (C3b) | `slab`, `stairs`, `fence`, `wall` — simplified axis-aligned boxes (half slabs, stair treads, fence post/arms). Orbit **slabs** and **stairs** use **full solid-block tiles** on box faces (`_orbit_solid_material_face_token`), not 2D half/L-mask bakes. Orbit **fences** and **walls** keep **2D masked adjacency bakes** on thin box faces; fragment shader **alpha-discards** low-α atlas samples (`sample.a < 0.05`) so rail gaps show background (stairs/slabs stay opaque tiles — safe with discard). Orbit **stairs** mirror south-authored boxes on **+Z** then rotate by `@direction` (`corner_stair_facing_rotation`, same as 2D worldgen); `;half=top` flips tread Y placement. Straight stairs add a thin **riser box** at the tread/void boundary. **Culling:** partial `box_face_occluded` uses **same-cell** boxes; **slab** faces also consult **neighbor-cell** boxes (`group_orbit_boxes_by_world`). Bottom-slab **−Y** is culled when the cell below has occupancy or when the slab shares a horizontal edge with another bottom slab of the same token (roof-deck / ceiling policy). **Solids** beside half-slabs emit a **vertical strip** (`_collect_solid_slab_neighbor_strip_faces`) — upper half beside bottom slab, lower beside `#top`. Stairs still use same-cell culling only. Horizontal slab faces use corner probes; coplanar tread tops drop duplicate riser `+Y`; greedy solids skip full faces toward other `partial_worlds`. |
| Attachables & functionals (C4) | `torch`, `lantern`, `trapdoor`, `bed` — JSON block-model **element faces** with per-face UV crops (`helpers/orbit_block_model_mesh.py`); AABB bounds from `orbit_attachable_mesh.py` are for culling/bounds only — **not** 2D sprite bakes on box faces. Wall torch rotates with `@direction`; hanging `LANTERN` / `COPPER_LANTERN` use `{variant_model}_hanging` (not hardcoded `lantern_hanging`). Colored beds (`BED:{color}@direction#head|foot`) use `{color}_bed_head` / `{color}_bed_foot` JSON models + `textures/block/` PNGs; each paired cell renders its own model at its world origin. `chest` — neighbor pairing merges left+right into one low-profile AABB (secondary cell skipped). `door` — full-height thin plate per layer cell (`#lower` / `#upper`). Uses partial-box face pass for chest/door only — not greedy full cubes. **Greedy `partial_worlds`:** `slab` + `stairs` only — solids keep faces beside fence/wall/attachables. |
| Interaction | **Free camera:** **click** the **3D** view to capture the pointer for look (system cursor hidden; **Esc** releases); while captured, mouse movement adjusts azimuth/elevation (**independent** of fly-speed multiplier); **scroll wheel** or **+** / **-** adjusts keyboard fly speed multiplier (not camera dolly; transient **Move speed: N.N×** label ~2s); **hold** **W** / **↑** or **S** / **↓** move forward/back along the full look vector (vertical when pitched); **hold** **A** / **←** or **D** / **→** strafe on the horizontal plane; **hold** Space / Shift ascend / descend on world ±Y; **R** resets to default exterior pose (`default_exterior_eye`, azimuth 0.7, elevation 0.45) for the current mesh. Speed persists as `viewer.orbit_camera_move_speed` (default **0.65×**). Near/far clip planes scale with `bounds_radius` (not fixed 0.1 / 2000) to reduce interior z-fighting |
| Performance | An 8×8 flat layer merges to **12 triangles** (six merged quads) vs **768** for C1 per-block boxes — see `tests/test_orbit_greedy_mesh.py` |
| Deferred | Campfire, sign, banner, animated chest lid / door swing; full JSON for every block type |

#### Orbit render class (agent glossary)

Before editing orbit preview geometry, classify each token with
`helpers.orbit_render_class.orbit_render_class(raw_token)` — **do not** conflate with
Minecraft blockstate “block” or a generic “mesh” label. Stairs are non-cube but **not**
attachables.

| Class | Examples | Primary module | Signatures / tests |
| ----- | -------- | -------------- | ------------------ |
| `solid_cube` | `minecraft:cobblestone`, planks, `CRAFTING_TABLE` | `helpers/orbit_greedy_mesh.py` — greedy `solid_cells` pass | Greedy shell culling tests in `tests/test_orbit_greedy_mesh.py` |
| `partial_box` | `SLAB:*`, `STAIRS:*`, `FENCE:*`, `WALL:*` | `helpers/orbit_partial_mesh.py` — AABB boxes + atlas faces | `orbit-stair-mask-transparency`, `orbit-fence-mask-transparency`; `tests/test_orbit_partial_mesh.py` |
| `attachable_box` | `CHEST:*`, `DOOR:*` | `helpers/orbit_attachable_mesh.py` — custom AABBs, neighbor pairing | `c4-attachable-partial-mesh-routing`; `tests/test_orbit_attachable_mesh.py` |
| `block_model` | `TORCH`, `LANTERN`, `COPPER_LANTERN#*`, `TRAPDOOR:*` (open and closed), `BED:*` | `helpers/orbit_block_model_mesh.py` — JSON element faces; closed trapdoor may use thin AABB bounds in attachable helper for culling only | `orbit-attachable-block-model-faces`, `orbit-lantern-hanging-variant`, `orbit-bed-block-model-faces`; `tests/test_orbit_attachable_mesh.py -k block_model`; `tests/test_orbit_render_class.py` |

2D schematic / materials views for colored beds still sample entity-atlas sprite bakes via
`compile_texture_set` keys `BED:{color}#head|foot` — 3D orbit uses block models only.

**Chest orbit facing** — `_resolve_orbit_attachable_bake_face_texture`
(`helpers/orbit_face_textures.py`) maps world side normals to front / back / end roles from block
`@direction` (same compass policy as `facing_block`). **Chest**
side faces compose from `chest_front*.png` (front, latch), `chest_back_left.png` /
`chest_back_right.png` (double back halves), and `chest_side.png` (single back + ends). Top and
bottom compose from `chest_top*.png`; merged double-chest AABBs split top/front/back along
`chest_span`. Tests: `test_orbit_bed_head_and_foot_block_models_differ`,
`test_orbit_chest_side_front_differs_from_end`,
`test_orbit_chest_side_latch_only_on_front`, `test_chest_is_attachable_box`.

Open vs closed trapdoor (`;open=true` / `;open=false`) changes **model and rotation** inside the
`block_model` path — not the taxonomy class. Signature: `orbit-render-class-routing`.

**Routing mistakes to avoid:** sprite bakes on torch/lantern AABBs (use `block_model`); attachables in
greedy `partial_worlds` (slab + stairs only); editing `orbit_greedy_mesh.py` for torch/lantern geometry.
Signature: `orbit-render-class-routing`.

Unit tests: `tests/test_orbit_preview.py`, `tests/test_orbit_greedy_mesh.py`, `tests/test_orbit_partial_mesh.py`, `tests/test_orbit_attachable_mesh.py`, `tests/test_orbit_render_class.py` (no GPU required in CI).

### Orbit partial blocks — lessons learned (C3b QA, 2026-06)

Shipped after `residence` stage 1 + `structures/test/stage1` manual Verify. Use this before adding geometry or culling for “missing stair faces.”

| Symptom | Likely cause | Fix (preferred) | Avoid |
| ------- | ------------ | --------------- | ----- |
| Rectangular holes on tread tops, sides, or bottoms | 2D stair **L-mask bakes** (~50% transparent α) + orbit shader **alpha discard** | `resolve_orbit_face_texture` → full solid tiles per face (`PLANKS:{material}` for plank stairs/slabs; `minecraft:{material}` for stone); render atlas samples opaque | Reusing `resolve_cell_texture` on `STAIRS:*` / `SLAB:*` for 3D box faces |
| Black / see-through slab deck tops | 2D slab **half-mask** bakes (50% transparent α on `+Y`) | `_resolve_orbit_slab_face_texture` → `_orbit_solid_material_face_token` | Half-masked `SLAB:*` topdown bakes on orbit quads |
| Black voids in fence rail gaps | 2D fence **adjacency-mask** bakes + opaque shader (no discard) | Keep masked `FENCE:*` / `WALL:*` bakes; shader `if (sample.a < 0.05) discard` | Forcing `alpha = 1.0` on transparent texels |
| Solid wood filling fence rail gaps (QA) | Solid `PLANKS:*` tiles on full-height post quads | Masked bakes + shader discard (same as above) | Applying slab/stair opaque-tile policy to fences |
| Flat solid color on stone stairs (e.g. cobblestone) | `PLANKS:{material}` does not resolve for non-plank materials | `_orbit_solid_material_face_token` — plank list → `PLANKS:*`; else `minecraft:{material}` | Mapping every stair to `PLANKS:{material}` |
| “Missing” lower tread from top view | Center-only `box_face_occluded` probe; tread covers half of lower `+Y` | **Corner probes** on horizontal faces (`±Y`) — emit if any corner is open | Extra void-fill boxes to “cap” the L-void |
| Duplicate / flickering tread top | Riser and tread share `y=1` plane | Coplanar `+Y` dedup (upper-half boxes only; skip lower slab) | — |
| Slab roof deck leaks interior / perimeter side strips | `box_face_occluded` same-cell only; every slab emits −Y and ±X/±Z | Neighbor-cell occlusion for slabs; deck −Y cull when below empty but horizontally connected (`_slab_deck_bottom_face_occluded`) | — |
| Mossy bleed through L-void at oblique angles | No geometry in open half (expected for 2-box model) | Greedy solids skip faces toward `partial_worlds`; same-cell riser box | Filling void with solid boxes + masked textures |
| Solid face hole above bottom slab | Full solid face culled toward `partial_worlds` | `_collect_solid_slab_neighbor_strip_faces` — upper strip beside bottom slab, lower beside `#top` | Emitting full solid faces through slabs (z-fight) |
| Solid face hole beside stairs (L-void) | Full solid face culled toward stair in `partial_worlds`; strip pass was slab-only | `iter_solid_neighbor_face_restore_rects` — 2×2 face probe restores open-half UV rects | Emitting full solid faces through tread (z-fight) |
| Attachables render as 1×1 cubes / attachable pytest fails after partial revert | `orbit_attachable_mesh.py` staged without `orbit_partial_mesh.py` routing | `attachable_boxes_for_cell` dispatch; `is_orbit_box_behavior` / `is_partial_volume_behavior`; greedy `solid_cells` excludes attachables | Staging attachable helper alone; `git checkout HEAD` on partial mesh without re-wiring |
| Dark seam between top and side on solid blocks | Multi-face catalog PNGs vs unified cobblestone texture; side normal outset skips +Y; transparent side PNG rows | `expand_orbit_quad_corners` +Y on side tops; `_resolve_orbit_side_face_texture` unified path; `_force_opaque_orbit_face` | `aFaceUv` / hybrid shader UV (Signature: `orbit-top-side-seam-geometry`) |
| Six torch sprites / wrong attachable texture on AABB faces | 2D `compose_torch` bake tiled on every AABB face | `_collect_block_model_element_faces` + `orbit_block_model_mesh.py` per-face UV crops | Sprite bakes on attachable box faces (Signature: `orbit-attachable-block-model-faces`) |
| Flat bed slab / wrong blanket in 3D orbit | Entity-atlas sprite bakes on merged bed AABB | `BED:*` in `block_model` — `{color}_bed_head` / `{color}_bed_foot` JSON + `textures/block/`; `bed_partner_occludes_face` | Merged AABB + `_iter_bed_face_parts` sprite split (Signature: `orbit-bed-block-model-faces`) |
| Pillow at bed center / head part reversed | `_BOX_Y_ROTATION` on bed (`@north` → 180° flips pillow toward foot) | `_BED_Y_ROTATION` — pillow on model north edge; `N=0,E=90,S=180,W=270` | Door/chest rotation table on beds (Signature: `orbit-bed-direction-rotation`) |
| Pillow at head/foot junction (white in middle) | `tileFrac(worldPos.xz)` on +Y — `fract(1.0)==fract(2.0)` at integer block edges | Block-model quads upload `aFaceUv` from `element_face_corner_uvs`; greedy faces use sentinel `-1` + `tileFrac` | Rotation-only fix without per-vertex UV (Signature: `orbit-block-model-face-uv`) |
| Wrong texture placements across all block-model faces | `element_face_corner_uvs` had up/south v-axis and east/north u-axis inverted: atlas uploads without GL flip so `fv=1 → PIL top (Mc_v=0)`; initial UVs assigned `fv=0` there | Corrected all six face UV tables; inline directional comments; regression test verifies `fv≈1` at pillow-end, `fv≈0` at junction | (Signature: `orbit-block-model-face-uv`) |
| Wall torches same direction / upside-down lean | Y-rotation keyed `south`/`north` or compose order wrong | `_WALL_TORCH_Y_ROTATION` on `N`/`S`/`E`/`W`; element rotation before block Y in `block_model.py` | Lowercase direction keys (Signature: `orbit-attachable-direction-rotation-keys`) |
| Copper lantern renders as iron lantern | Hanging hardcoded `lantern_hanging` | `_resolve_lantern_model_name` → `{model}_hanging` | Single hanging model for all lantern tokens (Signature: `orbit-lantern-hanging-variant`) |
| Wrong stair facing | South-authored boxes not mirrored before rotation | `_mirror_stair_boxes_local_z` then `corner_stair_facing_rotation` | Rotating boxes without Z mirror |
| Stacked fire openings on lit smoker / blast furnace front | Full animated PNG strip resized to one face | `helpers/block_texture_load.py` — crop frame 0 when `.mcmeta` has `animation`; lit filename via `helpers/facing_block_textures.py` | Resizing `smoker_front_on.png` / `blast_furnace_front_on.png` without mcmeta check |

**QA fixtures:** `structures/test/stage1` (oak stairs + cobblestone row); `residence/stage1` L0 oak run vs mossy cobblestone; `well/stage1` L0 **`STAIRS:cobblestone`** flight.

**Regression tests:** `test_orbit_stair_face_textures_are_opaque`, `test_orbit_slab_face_textures_are_opaque`, `test_orbit_fence_side_texture_uses_masked_bake`, `test_orbit_wall_side_texture_uses_masked_bake`, `test_orbit_cobblestone_stair_face_textures_are_opaque`, `test_lower_stair_slab_top_face_visible_on_open_half`, `test_slab_deck_7x7_minus_y_faces_culled`, `test_slab_deck_mesh_has_no_minus_y_normals`, riser/culling tests in `test_orbit_partial_mesh.py`.
