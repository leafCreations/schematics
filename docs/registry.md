# Registry System

Block definitions live in `registries/blocks.yaml`. Each entry can define:

* `behavior` — placement logic (solid, fence, door, stairs, etc.)
* `minecraft` — block id, variants, and blockstate templates
* `render` — texture mappings, background colors, inventory images
* `defaults` — default direction, variant, shape, etc.
* `visibility` — e.g. `interior: false` to hide blocks from site/path views
* `display_name` / `category` — materials list grouping

## Example entries

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

Textures are loaded from `assets/textures/block/` (and subfolders `block_assets/`, `item_assets/`, `custom/`).

For procedurally composed blocks (fences, stairs, doors, etc.), `compile_texture_set()` prefers baked sprites under `assets/generated/` when available. See [sprite-baker.md](sprite-baker.md).

## Loader API

`registries/loader.py` provides:

* `BLOCK_REGISTRY` — parsed YAML entries
* `build_registry_texture_mapping(view)` — token → vanilla texture filename
* `compile_texture_set(view, assets_dir, block_px)` — load textures for schematic rendering
* `compile_inventory_texture_set(assets_dir, block_px)` — load inventory icon textures

Structure layer cells reference registry tokens. See [structure-tokens.md](structure-tokens.md) for the token string format.
