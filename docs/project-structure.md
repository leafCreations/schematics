# Project Structure

```text
helpers/
  constants.py              # Render type names and BLOCK_PX
  context.py                # SchematicContext dataclass
  cells.py                  # Structure/site cell lookup (layer_array_index = layers list position)
  facade_projection.py      # Compass elevation projection for facade renderers
  fonts.py                  # Shared DejaVu font loading for blueprint renderers
  grid.py                   # Site/structure dimension helpers
  grid_brush.py             # Paint brush fill/outline helpers for the editor grid
  grid_cells.py             # Grid cell iteration utilities
  grid_labels.py            # Column/row axis labels (A8-style addressing)
  grid_placement.py         # Site placement anchors and offset math
  layers.py                 # Layer grouping and floor/roof blueprint dispatch
  layer_groups.py           # Group rename, visibility, reorder
  layer_management.py       # Layer create/delete/reorder and worldgen index
  layer_rotation.py         # 90° structure rotation (all layers)
  layer_visibility.py       # Per-layer render visibility
  path_geometry.py          # Path, trim, and lighting layout on the site
  path_strip.py             # Path brush strips along site rows/columns
  path_lighting.py          # Fence/torch posts on long trim runs
  materials.py              # Material resolution, counting, and inventory building
  render_image.py           # Shared canvas creation for blueprint PNGs
  landscape_utils.py        # Path and site map generation
  site_ground.py            # Site ground cell grid helpers
  paths.py                  # Asset and output directory paths, schematic output naming
  pipeline.py               # Render name validation and normalization
  registry_blocks.py        # Shared Minecraft block ID / blockstate resolution
  registry_lookup.py        # Behavior + catalog block entry resolution
  block_picker.py           # UI palette resolution and placement tokens
  block_catalog.py          # Generated catalog.json access
  palette_sections.py       # Terrain palette dimension sections
  terrain_tokens.py         # Legacy terrain token migration and defaults
  structure_loader.py       # Structure config validation and context building
  structure_metadata.py     # Structure identity (name, output_folder)
  structure_tokens.py       # Token parsing (material, direction, variant)
  cell_clipboard.py         # Grid copy/paste/move region helpers
  brush_preview.py          # Eraser and brush hover previews
  catalog_texture_exceptions.py  # Catalog texture fallbacks
  campfire_state.py         # Campfire blockstate helpers
  log_materials.py          # Log material enumeration
  fence_adjacency.py        # Fence connection resolution
  lantern_placement.py      # Lantern hanging inference for worldgen
  trapdoor_state.py         # Trapdoor blockstate helpers
  types.py                  # TypedDicts and type aliases
  utils.py                  # Structure loading and texture helpers
  utils_schematics.py       # Token resolution, texture paste, colors
  worldgen_block_entities.py   # Bed block entity export (Java 26.1)
  worldgen_block_updates.py    # Post-placement block updates
  worldgen_chunk_writer.py     # Chunk commit helper for Amulet export
  worldgen_multiblock.py       # Deferred bed/door placement pass
  worldgen_region_patch.py     # Region-file bed patch after save
  worldgen_site.py             # Site ground and path lighting for worldgen
  sprite_baker/             # Procedural sprite baking (see sprite-baker.md)

registries/
  behaviors/                # Semantic block behavior definitions (building, functional, lighting, wood)
  palettes/                 # UI palette groupings (tokens + minecraft: ids)
  generated/                # catalog.json from assets
  loader.py                 # Registry load, texture compile, bake keys
  validate.py               # Palette/behavior/catalog integrity checks

ui/
  __main__.py               # CLI: python -m ui
  main_window.py            # PySide6 editor shell (see ui.md)
  document.py               # StructureDocument load/save (manifest + stage.yaml)
  app_settings.py           # Editor settings YAML load/save
  editor_prefs.py           # Preference accessors
  editor_history.py         # Undo/redo stack
  editor_materials.py       # Shared inventory context for the UI
  materials_icons.py        # Inventory icon cache
  platform.py               # Linux Qt preflight
  texture_cache.py          # Grid icon cache
  dialog_layout.py          # Shared modal dialog metrics
  icon_theme.py             # Bundled icon theme
  menu_style.py             # Global QMenu styling
  tooltip_style.py          # Global QToolTip styling
  toolbar_icons.py          # Grid header and panel icons
  selector_mode.py          # Selector rectangle / same-block modes
  render_worker.py          # Background QThread render jobs
  reload.py                 # Editor process reload helper
  site_cells.py             # Site ↔ structure coordinate mapping
  widgets/                  # Palette, grid, properties, and panel widgets

renderers/
  registry.py               # Render name → handler dispatch table
  layer_panel.py            # Shared floor/roof panel renderer
  top_view.py               # Floor blueprint entry point
  roof.py                   # Roof blueprint entry point
  structure_facades.py      # Structure elevation facades
  path_view.py              # Site path and landscaping plans
  site_facades.py           # Site cross-section elevations
  materials.py              # Materials inventory sheet
  worldgen.py               # Minecraft world generation

structures/
  residence/
    structure.yaml          # manifest (dimension, grid, site_ground, stages)
    stage1/
      stage.yaml            # per-stage identity and layer_files
      layers/
    stage2/
      stage.yaml
      layers/
  well/
    structure.yaml
    stage1/ … stage2/

assets/
  minecraft/                # Vanilla resource pack (textures, models, blockstates, lang, …)
    textures/block/         # Block textures for rendering (not in repo; see .gitignore)
    generated/              # Baked schematic sprites (not in repo; see sprite-baker.md)
  icons/                    # Freedesktop icon theme for the structure editor toolbar

scripts/
  bake_sprites.py           # CLI to bake generated sprites
  generate_catalog.py       # Build registries/generated/catalog.json from assets
  migrate_structure_to_yaml.py  # Convert stage{N}_structure.py to YAML layout
  migrate_terrain_tokens.py # Convert legacy terrain tokens to minecraft: ids
  install_worldgen.sh       # Amulet/worldgen dependency helper
  run_ui.sh / run-ui        # Launch the structure editor
  pre-commit-*.sh           # Hook helpers (ruff, palettes, pytest)
  ruff-fix                  # Run ruff check --fix and format
  gcn / commit-no-pytest    # Commit helpers (skip pytest when needed)

config/
  editor_settings.yaml      # Default editor preferences (panel visibility, tooltips)

output/
  schematics/               # Rendered PNG blueprints
  worlds/                   # Generated Minecraft worlds

template/                   # Base world copied for worldgen (Minecraft Java 26.1.2)

render_main.py              # Pipeline entry point (dispatches via renderers/registry.py)
pyproject.toml
docs/                       # Extended documentation
```

Structure package layout details: [structure-tokens.md](structure-tokens.md).
