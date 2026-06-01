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

Structure definitions live in `structures/{structure}/stage{N}_structure.py`. Each file must define `STRUCTURE_CONFIG` with `layers`, `grid`, `name`, and `output_folder`.

The `grid` object supports:

* `site_size` — site footprint in blocks
* `offset_x` / `offset_z` — structure placement on the site
* `stair_local_x` — local X of the entry stair within the structure (defaults to `4`)
* `site_structure_layers` — list positions into `layers` projected onto site Y=0/1 (defaults to `[0, 1]`)
* `worldgen_base_y` — Minecraft Y base for world export (defaults to `-60`)
