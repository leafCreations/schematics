# Sprite Baker

Many block sprites are composed procedurally from vanilla textures and cached under `assets/generated/`. The renderer loads these via `compile_texture_set()` and material inventory panels use them for generated icons.

`assets/` is gitignored — bake sprites locally after cloning or when adding new block types.

## Bake CLI

```bash
.venv/bin/python scripts/bake_sprites.py --type <type> --view <view> --all --force
```

### Types

| `--type`   | Description                                      |
| ---------- | ------------------------------------------------ |
| `simple`   | Flat solid blocks (grass, cobblestone, planks)   |
| `slab`     | Half-block slabs                                 |
| `stairs`   | Stair shapes (straight, corner variants)         |
| `door`     | Door top/side strips and inventory icons         |
| `bed`      | Bed top/side/inventory from entity atlases       |
| `chest`    | Chest variants                                   |
| `fence`    | Fence post/straight/corner and inventory models    |
| `torch`    | Standing, soul, and wall torches                 |
| `lantern`  | Hanging and soul lanterns from block models      |
| `log`      | Log orientations per material                    |

### Views

| `--view`      | Output folder              | Used for                    |
| ------------- | -------------------------- | --------------------------- |
| `top`         | `assets/generated/top/`    | Top-down schematic panels   |
| `side`        | `assets/generated/side/`   | Side elevations; stair inventory icons |
| `inventory`   | `assets/generated/inventory/` | Material list and panel inventory icons |

### Examples

```bash
# Rebake all oak-relevant stairs for top-down renders
.venv/bin/python scripts/bake_sprites.py --type stairs --view top --all --force

# Door inventory icons for materials panels
.venv/bin/python scripts/bake_sprites.py --type door --view inventory --all --force

# Single key
.venv/bin/python scripts/bake_sprites.py --type fence --view top --key FENCE:oak#cross --force
```

## Cache layout

Baked files use sanitized keys:

* `STAIRS:oak#outer_left` → `assets/generated/top/STAIRS_oak_outer_left.png`
* `DOOR:oak` (inventory) → `assets/generated/inventory/DOOR_oak.png`

## Runtime baking

`compile_texture_set()` and `compile_inventory_texture_set()` load cached sprites from `assets/generated/` first. When a registry-mapped bake key is missing from cache, `helpers/sprite_baker/runtime_bake.py` composes it from vanilla textures, writes the PNG to the cache, and returns it — so fresh clones can render without running the bake CLI first.

Only keys present in the registry texture mapping are baked on demand during compile. Extra material variants listed by `_generated_bake_keys()` are loaded from disk when pre-baked, not composed eagerly during startup.

Material inventory panels use the same path via `load_or_bake_generated_sprite()` for generated icon behaviors.

Pre-baking with the CLI is still useful for CI, bulk updates, and verifying output before commit.

## Source code

* `helpers/sprite_baker/` — composers, cache, block model renderer
* `registries/loader.py` — `_generated_bake_keys()` merges baked keys into texture sets
* `helpers/materials.py` — resolves `generated:{key}` inventory icons
