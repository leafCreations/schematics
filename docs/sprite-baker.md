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

If a generated sprite is missing at render time, `helpers/sprite_baker/runtime_bake.py` can compose and cache it on demand for inventory behaviors (slabs, stairs, fences, etc.).

## Source code

* `helpers/sprite_baker/` — composers, cache, block model renderer
* `registries/loader.py` — `_generated_bake_keys()` merges baked keys into texture sets
* `helpers/materials.py` — resolves `generated:{key}` inventory icons
