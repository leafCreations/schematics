# Project Structure

```text
helpers/
  constants.py          # Render type names and BLOCK_PX
  context.py            # SchematicContext dataclass
  cells.py              # Structure/site cell lookup
  facade_projection.py  # Compass elevation projection for facade renderers
  fonts.py              # Shared DejaVu font loading for blueprint renderers
  grid.py               # Site/structure dimension helpers
  layers.py             # Layer grouping and floor/roof blueprint dispatch
  path_geometry.py      # Path, trim, and lighting layout on the site
  materials.py          # Material resolution, counting, and inventory building
  render_image.py       # Shared canvas creation for blueprint PNGs
  landscape_utils.py    # Path and site map generation
  paths.py              # Asset and output directory paths, schematic output naming
  pipeline.py           # Render name validation and normalization
  registry_blocks.py    # Shared Minecraft block ID / blockstate resolution
  structure_loader.py   # Structure config validation and context building
  structure_tokens.py   # Token parsing (material, direction, variant)
  types.py              # TypedDicts and type aliases
  utils.py              # Structure loading and texture helpers
  utils_schematics.py   # Token resolution, texture paste, colors
  sprite_baker/         # Procedural sprite baking (see sprite-baker.md)

registries/
  blocks.yaml           # Block registry
  loader.py             # Registry load and texture compilation

renderers/
  registry.py           # Render name → handler dispatch table
  layer_panel.py        # Shared floor/roof panel renderer
  top_view.py           # Floor blueprint entry point
  roof.py               # Roof blueprint entry point
  structure_facades.py  # Structure elevation facades
  path_view.py          # Site path and landscaping plans
  site_facades.py       # Site cross-section elevations
  materials.py          # Materials inventory sheet
  worldgen.py           # Minecraft world generation

structures/
  residence/
    stage1_structure.py
    stage2_structure.py

assets/
  textures/block/       # Vanilla block textures (not in repo; see .gitignore)
  generated/            # Baked schematic sprites (not in repo; see sprite-baker.md)

scripts/
  bake_sprites.py       # CLI to bake generated sprites
  ruff-fix              # Run ruff check --fix and format

output/
  schematics/           # Rendered PNG blueprints
  worlds/               # Generated Minecraft worlds

template/               # Base world copied for worldgen

render_main.py          # Pipeline entry point (dispatches via renderers/registry.py)
pyproject.toml
docs/                   # Extended documentation
```
