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

### 3D orbit preview (Viewer tab)

Toggle **3D** on the preview panel to view a greedy-meshed exterior shell built from the **in-memory** editor document via `SchematicContext` (not from session PNGs or exported schematics).

| Aspect | Behavior |
| ------ | -------- |
| Data source | `structure_config_from_document` → `build_schematic_context` → `helpers/orbit_greedy_mesh.py` + `helpers/orbit_partial_mesh.py` |
| Refresh | Same `_preview_stale` / unsaved-document rules as 2D; `MeshBuildWorker` off UI thread |
| Rendering | `OrbitPreviewWidget` (`QOpenGLWidget`) — one VBO + one texture atlas; per-block texture tiling via world-space `fract()` in the fragment shader |
| Greedy shell (C2+) | Solid cells merge coplanar faces for performance. **Vertical faces** emit when the neighbor is **air** or a **different token** (material boundary) — embedded functionals (e.g. `CRAFTING_TABLE` in a plank floor) show side quads at token boundaries. Same-token neighbors still cull mutual faces. ±Y uses the same rule across layers. |
| Textures (C3a) | `helpers/orbit_face_textures.py` — face-normal-aware `resolve_cell_texture()`; atlas tiles at `BLOCK_PX` (30); greedy merge keyed by texture signature. **`facing_block`** (`FURNACE`, `SMOKER`, `BLAST_FURNACE`): `facing` + `lit` blockstates; vertical face matching `@direction` → `{block}_front.png` or `{block}_front_on.png` when `;lit=true`; other vertical faces → `render.side`; orbit **`+Y`/`-Y`** → `{block}_top.png`. Legacy `minecraft:smoker` aliases to `SMOKER`. **Solid/catalog functionals** without facing (e.g. `CRAFTING_TABLE`): `{block}_side.png` on vertical faces. |
| Partial blocks (C3b) | `slab`, `stairs`, `fence`, `wall` — simplified axis-aligned boxes (half slabs, stair treads, fence post/arms). Orbit **slabs** and **stairs** use **full solid-block tiles** on box faces (`_orbit_solid_material_face_token`), not 2D half/L-mask bakes. Orbit **fences** and **walls** keep **2D masked adjacency bakes** on thin box faces; fragment shader **alpha-discards** low-α atlas samples (`sample.a < 0.05`) so rail gaps show background (stairs/slabs stay opaque tiles — safe with discard). Orbit **stairs** mirror south-authored boxes on **+Z** then rotate by `@direction` (`corner_stair_facing_rotation`, same as 2D worldgen); `;half=top` flips tread Y placement. Straight stairs add a thin **riser box** at the tread/void boundary. **Culling:** partial `box_face_occluded` uses **same-cell** boxes; **slab** faces also consult **neighbor-cell** boxes (`group_orbit_boxes_by_world`). Bottom-slab **−Y** is culled when the cell below has occupancy or when the slab shares a horizontal edge with another bottom slab of the same token (roof-deck / ceiling policy). **Solids** beside half-slabs emit a **vertical strip** (`_collect_solid_slab_neighbor_strip_faces`) — upper half beside bottom slab, lower beside `#top`. Stairs still use same-cell culling only. Horizontal slab faces use corner probes; coplanar tread tops drop duplicate riser `+Y`; greedy solids skip full faces toward other `partial_worlds`. |
| Interaction | Drag to orbit; scroll to zoom |
| Performance | An 8×8 flat layer merges to **12 triangles** (six merged quads) vs **768** for C1 per-block boxes — see `tests/test_orbit_greedy_mesh.py` |
| Deferred | Torches, lanterns, beds, chests — may stay boxes/billboards; full JSON block models for every type |

Unit tests: `tests/test_orbit_preview.py`, `tests/test_orbit_greedy_mesh.py`, `tests/test_orbit_partial_mesh.py` (no GPU required in CI).

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
| Wrong stair facing | South-authored boxes not mirrored before rotation | `_mirror_stair_boxes_local_z` then `corner_stair_facing_rotation` | Rotating boxes without Z mirror |

**QA fixtures:** `structures/test/stage1` (oak stairs + cobblestone row); `residence/stage1` L0 oak run vs mossy cobblestone; `well/stage1` L0 **`STAIRS:cobblestone`** flight.

**Regression tests:** `test_orbit_stair_face_textures_are_opaque`, `test_orbit_slab_face_textures_are_opaque`, `test_orbit_fence_side_texture_uses_masked_bake`, `test_orbit_wall_side_texture_uses_masked_bake`, `test_orbit_cobblestone_stair_face_textures_are_opaque`, `test_lower_stair_slab_top_face_visible_on_open_half`, `test_slab_deck_7x7_minus_y_faces_culled`, `test_slab_deck_mesh_has_no_minus_y_normals`, riser/culling tests in `test_orbit_partial_mesh.py`.
