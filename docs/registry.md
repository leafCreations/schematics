# Registry System

Block behavior definitions live in `registries/behaviors/*.yaml`. UI palette groupings live in `registries/palettes/*.yaml`. Each behavior entry can define:

* `ui` — editor metadata (label, palette tab, required fields, variants)
* `behavior` — placement logic (solid, fence, door, stairs, etc.)
* `minecraft` — block id, variants, and blockstate templates
* `render` — texture mappings, background colors, inventory images
* `defaults` — default direction, variant, shape, etc.
* `visibility` — e.g. `interior: false` to hide blocks from site/path views

Materials list labels come from the generated block catalog (`registries/generated/catalog.json`), not from the behavior registry. See [Block catalog](#block-catalog) below.

## Layout

```
registries/
  behaviors/     # Semantic tokens (GRASS, STAIRS, DOOR, …)
  palettes/      # UI groups: tokens + optional minecraft: block ids
  generated/     # catalog.json from assets
  loader.py
```

Palettes reference semantic tokens and/or raw Minecraft block ids:

```text
registries/palettes/
  terrain.yaml      # Dirt, grass, cobblestone, …
  wood.yaml           # Log, planks
  functional.yaml     # Furnace, crafting table, chest, door, bed
  building.yaml       # Slab, fence, stairs
  lighting.yaml       # Torch, lantern, soul lantern, copper lanterns (`hanging` blockstate)
  …
```

Structure layers can use either semantic tokens (`PLANKS:oak`) or catalog-backed cells (`minecraft:stone`). The latter synthesizes a solid behavior entry at lookup time.

## Example behavior entries

```yaml
GRASS:
  behavior: solid
  minecraft:
    block: minecraft:grass_block
  render:
    textures:
      top: grass_block_top.png
    background_color: [95, 160, 75]

FURNACE:
  behavior: facing_block
  defaults:
    direction: north
  minecraft:
    block: minecraft:furnace
    blockstates:
      facing: "{direction}"
  render:
    textures:
      top: furnace_front.png
  visibility:
    interior: false
```

## Texture loading

Textures are loaded from `assets/minecraft/textures/block/` (and subfolders `block_assets/`, `item_assets/`, `custom/`).

For procedurally composed blocks (fences, stairs, doors, etc.), `compile_texture_set()` prefers baked sprites under `assets/minecraft/generated/` when available. See [sprite-baker.md](sprite-baker.md).

`minecraft:` cells load textures from the catalog when not present in the compiled registry texture set, including materials-list inventory icons.

## Loader API

`registries/loader.py` provides:

* `BLOCK_REGISTRY` — merged behavior entries from `behaviors/*.yaml`
* `BLOCK_PALETTES` — palette definitions from `palettes/*.yaml`
* `reload_registries()` — reload YAML into the module-level dicts (called when the editor starts; palette picker caches are cleared)
* `validate_palettes()` — fail fast on palette refs, behavior shape (`behavior`, `minecraft`), UI placeholder consistency, and missing top textures when `assets/minecraft/textures/block` is present (runs on pre-commit)
* `build_registry_texture_mapping(view)` — token → vanilla texture filename
* `compile_texture_set(view, assets_dir, block_px)` — load textures for schematic rendering
* `compile_inventory_texture_set(assets_dir, block_px)` — load inventory icon textures

`helpers/registry_lookup.py` provides:

* `get_block_entry(parsed)` — behavior registry or synthesized catalog entry
* `registry_lookup_token(parsed)` — lookup key for rendering/worldgen
* `load_catalog_texture_image(parsed, view, size)` — catalog texture fallback

`helpers/block_picker.py` provides the UI-facing picker resolution:

* `list_palettes()` / `resolve_palette(name)` — palette tabs as structured `PickerPalette` / `PickerEntry`
* `picker_entry_for_token(token)` / `picker_entry_for_block_id(block_id)` — single entries
* `enumerate_token_materials(template)` — valid materials/colors for a templated token, derived from the catalog (e.g. `minecraft:{material}_planks` → `oak`, `birch`, …)
* `cell_token(entry, material)` — the structure-layer cell string to write for a selection
* `format_entry_label(entry, material)` — catalog-resolved display label per material

Editor usage: [ui.md](ui.md).

Structure layer cells reference registry tokens or `minecraft:` block ids. See [structure-tokens.md](structure-tokens.md) for the token string format. The structure editor uses the same tokens when painting cells — see [ui.md](ui.md).

## Block catalog

Material inventory labels and future UI block pickers use `registries/generated/catalog.json`, generated from Minecraft assets:

```bash
.venv/bin/python scripts/generate_catalog.py
```

The script reads:

* `assets/minecraft/blockstates/*.json` → block ids (`minecraft:stone`)
* `assets/minecraft/lang/en_us.json` → display names (`block.minecraft.stone` → `"Stone"`)
* `assets/minecraft/textures/block/` → default texture filenames when present

Semantic tokens resolve to Minecraft block ids via the behavior registry; `minecraft:` cells use the catalog directly for names and textures. Regenerate the catalog when assets are updated.
