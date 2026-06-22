# Structure Tokens

Cells in structure layers use compact token strings:

| Section       | Meaning          | Example              |
| ------------- | ---------------- | -------------------- |
| Token         | Registry key     | `STAIRS`             |
| `:material`   | Material         | `PLANKS:oak`         |
| `@direction`  | Facing           | `DOOR:oak@north`     |
| `#variant`    | Shape / part     | `STAIRS:oak@north#outer_left` |
| `;states`     | Blockstate overrides | `LANTERN;hanging=false` |
| `!rotation`   | Render rotation  | `FURNACE@east!-90`   |
| `.`           | Empty cell       | `.`                  |

Example: `STAIRS:oak@north#outer_left`

## Parsing

Tokens are parsed by `helpers/structure_tokens.py` into a `ParsedToken` with fields `token`, `material`, `direction`, `variant`, `states`, and `rotation`.

Blockstate overrides use `;key=value` (comma-separated for multiple keys). Example: `LANTERN#soul;hanging=true`. Omit the clause to let worldgen infer placement (lanterns use the cell on the layer above).

## Structure packages

Each structure is a folder under `structures/{structure}/` with a **manifest** and one folder per stage:

```text
structures/residence/
  structure.yaml          # manifest: dimension, grid, site_ground, stages[]
  stage1/
    stage.yaml            # per-stage: structure, stage, name, layer_files
    layers/
      layer_00.yaml       # index, group, cells grid
      layer_01.yaml
  stage2/
    stage.yaml
    layers/
      ...
```

### Manifest (`structures/{structure}/structure.yaml`)

Shared across stages for the same structure package:

* **`dimension`** — `overworld`, `nether`, or `end` (default terrain palette filter and worldgen dimension)
* **`grid`** — site size, placement, offsets, path settings, group lists (see [grid fields](#grid-fields) below)
* **`site_ground`** — 2D path/trim cell grid for the site tab and path renders
* **`stages`** — list of stage entries, each with `stage`, `path` (e.g. `stage1/stage.yaml`), and `output_folder`

The loader merges manifest `dimension`, `grid`, and `site_ground` into each stage at load time (`helpers/structure_loader.py`).

### Stage file (`stage{N}/stage.yaml`)

Per-stage identity and layer list:

* **`structure`** — lowercase slug (e.g. `residence`)
* **`stage`** — integer stage number
* **`name`** — display title, derived as `{Structure title} Stage {N}` (e.g. `Residence Stage 1`). The editor sets this automatically.
* **`layer_files`** — explicit list of `layers/layer_NN.yaml` paths (recommended)

`output_folder` (`stage{N}_{structure}`) is stored on the manifest `stages[]` entry; the editor derives it from structure + stage.

Layers load via:

* **`layer_files`** — explicit list (recommended; used by the editor)
* **`layers/layer_*.yaml`** — auto-discovered when `layer_files` is omitted (CLI)
* **inline `layers`** — list of layer dicts in a single YAML file (CLI/render only; the editor requires split files)

Legacy Python modules (`stage{N}_structure.py`) still load if no YAML exists but are **deprecated** — use `scripts/migrate_structure_to_yaml.py` and the manifest + `stage.yaml` layout above.

### Layer list index vs worldgen `index`

These are different concepts:

| Field | Where | Meaning |
| ----- | ----- | ------- |
| **List position** | Order in `layer_files` / discovered files | `0` = first file, `1` = second, … Used by `grid.site_structure_layers` (which layers appear on the site preview at Y=0/1). |
| **`index` in each layer file** | `layers/layer_NN.yaml` | Worldgen Minecraft Y offset: `actual_y = worldgen_base_y + index`. Must be **unique** across layers. |

Example: `site_structure_layers: [0, 2]` projects the 1st and 3rd layer files onto the site tab, while each file’s `index: 4` places that layer at Y=`worldgen_base_y + 4` in the exported world.

### Grid fields

The `grid` object (on the manifest) supports:

* `site_width` / `site_depth` — site footprint in blocks (x × z; may differ, e.g. 20×10)
* `site_size` — legacy shorthand for a square site (`site_width` and `site_depth` both set to this value)
* `offset_x` / `offset_z` — structure placement on the site (north-west corner of the structure footprint)
* `placement` — optional editor anchor (`top_left`, `top_center`, …, `center`, `bottom_right`); offsets are derived from site dimensions
* `groups` — ordered list of layer group names (empty groups allowed)
* `hidden_groups` — group names omitted from renders
* `path_width` — painted path strip width (odd integer; default `3`)
* `path_orientation` — default path brush orientation (`horizontal` or `vertical`)
* `trim_block` — block token for path trim (default `minecraft:gravel`; legacy `GRAVEL` still resolves)
* `path_variety_blocks` — tokens mixed into the path band besides `minecraft:dirt_path` (default: `minecraft:gravel`, `minecraft:dirt`, `minecraft:cobblestone`, `minecraft:mossy_cobblestone`)
* `path_center_local_x` — local X within the structure footprint used to center **auto-generated** paths when `site_ground` has no painted path (defaults to half the structure width). Not related to STAIRS blocks; painted paths in `site_ground` take precedence. `stair_local_x` is a deprecated alias.
* `site_structure_layers` — list positions into `layers` projected onto site Y=0/1 (defaults to `[0, 1]`)
* `worldgen_base_y` — Minecraft Y base for world export (defaults to `-60`)

### Layer file fields

Each `layers/layer_NN.yaml` contains:

* **`cells`** — 2D array of token strings (or `.` for empty)
* **`group`** — layer group name (optional string)
* **`index`** — worldgen Y offset (`actual_y = worldgen_base_y + index`); must be unique per stage
* **`visible`** — omit when `true`; set `false` to hide from renders
* **`description`** — optional label shown in the layer list (editor Add/Edit layer dialog)

### Catalog and legacy terrain cells

Structure layers may use semantic registry tokens (`PLANKS:oak`) or catalog-backed `minecraft:` ids (`minecraft:stone`). Legacy terrain tokens (`GRASS`, `COBBLESTONE#mossy`, …) still resolve via `helpers/terrain_tokens.py`; run `scripts/migrate_terrain_tokens.py` to convert them to catalog ids.

## Editor

The structure editor builds placement strings from palette selections using `helpers/block_picker.py` → `cell_token()`. Rotation (`!degrees`) is not exposed in the UI yet; set it manually in YAML if needed. See [ui.md](ui.md).
