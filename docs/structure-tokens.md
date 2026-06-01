# Structure Tokens

Cells in structure layers use compact token strings:

| Section       | Meaning          | Example              |
| ------------- | ---------------- | -------------------- |
| Token         | Registry key     | `STAIRS`             |
| `:material`   | Material         | `PLANKS:oak`         |
| `@direction`  | Facing           | `DOOR:oak@north`     |
| `#variant`    | Shape / part     | `STAIRS:oak@north#outer_left` |
| `!rotation`   | Render rotation  | `FURNACE@east!-90`   |
| `.`           | Empty cell       | `.`                  |

Example: `STAIRS:oak@north#outer_left`

## Parsing

Tokens are parsed by `helpers/structure_tokens.py` into a `ParsedToken` with fields `token`, `material`, `direction`, `variant`, and `rotation`.

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

* `site_size` — site footprint in blocks
* `offset_x` / `offset_z` — structure placement on the site
* `stair_local_x` — local X of the entry stair within the structure (defaults to `4`)
* `site_structure_layers` — list positions into `layers` projected onto site Y=0/1 (defaults to `[0, 1]`)
* `worldgen_base_y` — Minecraft Y base for world export (defaults to `-60`)
