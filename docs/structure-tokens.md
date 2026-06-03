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

## Structure files

Structure definitions live under `structures/{structure}/stage{N}/`:

```text
structures/residence/stage1/
  structure.yaml      # metadata, grid, layer file list
  layers/
    layer_00.yaml     # index, group, cells grid
    layer_01.yaml
    ...
```

Legacy Python modules (`stage{N}_structure.py`) are still supported if no YAML folder exists.

Each stage must define `structure`, `stage`, `name`, `output_folder`, `grid`, and either `layer_files` or inline `layers`.

The `grid` object supports:

* `site_width` / `site_depth` — site footprint in blocks (x × z; may differ, e.g. 20×10)
* `site_size` — legacy shorthand for a square site (`site_width` and `site_depth` both set to this value)
* `offset_x` / `offset_z` — structure placement on the site (north-west corner of the structure footprint)
* `placement` — optional editor anchor (`top_left`, `top_center`, …, `center`, `bottom_right`); offsets are derived from site dimensions
* `path_center_local_x` — local X within the structure footprint used to center **auto-generated** paths when `site_ground` has no painted path (defaults to half the structure width). Not related to STAIRS blocks; painted paths in `site_ground` take precedence. `stair_local_x` is a deprecated alias.
* `trim_block` — block token for path trim (default `GRAVEL`)
* `path_variety_blocks` — list of tokens mixed into the path band besides `DIRT_PATH` (default: all of `GRAVEL`, `DIRT`, `COBBLESTONE`, `COBBLESTONE#mossy`)
* `site_structure_layers` — list positions into `layers` projected onto site Y=0/1 (defaults to `[0, 1]`)
* `worldgen_base_y` — Minecraft Y base for world export (defaults to `-60`)

## Editor

The structure editor builds placement strings from palette selections using `helpers/block_picker.py` → `cell_token()`. Rotation (`!degrees`) is not exposed in the UI yet; set it manually in YAML if needed. See [ui.md](ui.md).
