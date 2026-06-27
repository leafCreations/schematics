# Sprite Baker

Many block sprites are composed procedurally from vanilla textures and cached under `assets/project/generated/`. The renderer loads these via `compile_texture_set()` and material inventory panels use them for generated icons.

`assets/` is gitignored — place Minecraft resources under `assets/minecraft/` and bake sprites locally after cloning or when adding new block types.

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
| `trapdoor` | Trapdoor half-cell top/side and inventory icons |
| `bed`      | Bed top/side/inventory from entity atlases       |
| `chest`    | Chest variants                                   |
| `fence`    | Fence post/straight/corner and inventory models    |
| `torch`    | Standing, soul, and wall torches                 |
| `lantern`  | Hanging and soul lanterns from block models      |
| `campfire` | Campfire and soul campfire from block models     |
| `log`      | Log orientations per material                    |

### Views

| `--view`      | Output folder              | Used for                    |
| ------------- | -------------------------- | --------------------------- |
| `top`         | `assets/project/generated/top/`    | Top-down schematic panels   |
| `side`        | `assets/project/generated/side/`   | Side elevations; stair inventory icons |
| `inventory`   | `assets/project/generated/inventory/` | Material list and panel inventory icons |

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

* `STAIRS:oak#outer_left` → `assets/project/generated/top/STAIRS_oak_outer_left.png`
* `DOOR:oak` (inventory) → `assets/project/generated/inventory/DOOR_oak.png`

## Runtime baking

`compile_texture_set()` and `compile_inventory_texture_set()` load cached sprites from `assets/project/generated/` first. When a registry-mapped bake key is missing from cache, `helpers/sprite_baker/runtime_bake.py` composes it from vanilla textures, writes the PNG to the cache, and returns it — so fresh clones can render without running the bake CLI first.

Only keys present in the registry texture mapping are baked on demand during compile. Extra material variants listed by `_generated_bake_keys()` are loaded from disk when pre-baked, not composed eagerly during startup.

Material inventory panels use the same path via `load_or_bake_generated_sprite()` for generated icon behaviors.

The **3D orbit preview** reuses the same `compile_texture_set()` top/side maps (`ctx.topdown_textures`, `ctx.sideview_textures`) when sampling block faces into `helpers/orbit_texture_atlas.py`.

Pre-baking with the CLI is still useful for CI, bulk updates, and verifying output before commit.

### Stair top-down riser ghost

Straight and corner stair **top** bakes composite two layers at bake time:

1. **Tread** — full opacity (`build_stair_top_mask`)
2. **Riser ghost** — tread-complement (L-void) at ~45% alpha; RGB lightened ~28% toward white
   (`STAIR_RISER_GHOST_LIGHTEN`) so gray stone/brick risers read lighter on Top Down grids.

Side and inventory stair bakes are unchanged. After changing `compose_stairs`, rebake top stairs:

```bash
.venv/bin/python scripts/bake_sprites.py --type stairs --view top --all --force
```

Runtime `compile_texture_set()` will compose missing cache entries on demand; pre-bake avoids first-open lag.

Catalog materials ending in ``_brick`` (and plain ``brick`` from ``minecraft:brick_stairs``)
resolve to ``*_bricks.png`` via ``stairs_texture_material()`` in ``plank_materials.py``.

Non-plank catalog stems (``purpur``, ``quartz``, smooth variants, waxed cut copper) use
``stairs_texture_filename_candidates()`` — tries ``{alias}.png``, ``{material}_block.png``,
``{material}_block_top.png``, plus explicit aliases (``purpur`` → ``purpur_block.png``,
``smooth_quartz`` → ``quartz_block_bottom.png``, ``waxed_cut_copper`` → ``cut_copper.png``, …).

**QA gate:** after changing stair texture resolution, run full catalog rebake — oak-only tests miss
non-wood filename gaps (``brick`` → ``bricks.png``, ``purpur`` → ``purpur_block.png``):

```bash
.venv/bin/python scripts/bake_sprites.py --type stairs --view top --all --force
```

Signature: ``stairs-rebake-all-texture-qa``. Long-term: material-family taxonomy
(``inquiry-material-family-taxonomy-2026-06-27``) may replace heuristic aliases.

## Source code

* `helpers/sprite_baker/` — composers, cache, block model renderer
* `registries/loader.py` — `_generated_bake_keys()` merges baked keys into texture sets
* `helpers/materials.py` — resolves `generated:{key}` inventory icons
