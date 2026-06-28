# Minecraft assets

Vanilla Minecraft **client resource** files live under `assets/` (gitignored). The project does not ship the full game jar — extract resources locally after cloning.

Target layout after setup (source `minecraft_*` extracts can be deleted once dedupe completes):

```text
assets/
  icons/                      # UI toolbar icons
  ui/                         # UI SVG assets
  project/
    custom/                   # Bed/chest schematic templates (project-owned)
    generated/                # Sprite bake cache (regeneratable)
  versions/
    base/                     # Shared vanilla files across game versions
    26_1_2/                   # 26.1.2-only deltas (worldgen era)
    26_2/                     # 26.2-only deltas (render/catalog era)
  minecraft/                  # Active merged resource tree (hardlinks)
```

Future datapack loot work will use a separate **data** extract (`assets/minecraft_data/`), not these client folders.

## Setup after clone

1. Extract Minecraft **client** resources into versioned folders (e.g. `assets/minecraft_26_2/`).
2. Prune unused client folders:

```bash
.venv/bin/python scripts/prune_minecraft_assets.py --all-versioned
```

3. Move project-owned assets out of the vanilla trees:

```bash
.venv/bin/python scripts/migrate_project_assets.py
```

4. Deduplicate versioned extracts and materialize the active tree:

```bash
.venv/bin/python scripts/dedupe_minecraft_assets.py --clean
```

This writes `assets/versions/` and merges **26.2** into `assets/minecraft/` via hardlinks.

5. Generate catalog and bake sprites:

```bash
.venv/bin/python scripts/generate_catalog.py
# See docs/sprite-baker.md for bake commands
```

## Required vanilla paths (prune allowlist)

After pruning, each Minecraft resource extract contains only:

| Path | Used for |
| ---- | -------- |
| `blockstates/` | Block catalog generation |
| `lang/en_us.json` | Catalog display names |
| `models/block/` | Sprite baker block models |
| `textures/block/` | Schematic rendering and palette validation |
| `textures/item/` | Campfire brush preview, some inventory icons |
| `textures/entity/bed/` | Bed sprite baking (26.1 entity-atlas path) |
| `textures/entity/chest/` | Chest entity atlases (64×64 unwrap) — source for 2D schematic and orbit attachable bakes |

When `assets/minecraft/textures/entity/bed/` is absent after dedupe, bed baking resolves atlases from
`assets/versions/26_1_2/textures/entity/bed/` via `helpers.paths.resolve_entity_bed_textures_folder()`.
Chest entity atlases resolve similarly via `resolve_entity_chest_textures_folder()` for
`compose_chest` / `compose_chest_side_schematic` orbit attachable faces.

Project-owned paths live under `assets/project/`:

| Path | Used for |
| ---- | -------- |
| `project/custom/` | Bed/chest schematic PNG templates |
| `project/generated/` | Baked sprite cache |

## Scripts

| Script | Purpose |
| ------ | ------- |
| `scripts/prune_minecraft_assets.py` | Remove unused vanilla client folders |
| `scripts/migrate_project_assets.py` | Move `custom/` and `generated/` to `assets/project/` |
| `scripts/dedupe_minecraft_assets.py` | Build `assets/versions/` and materialize `assets/minecraft/` |
| `scripts/generate_catalog.py` | Build `registries/generated/catalog.json` |

```bash
# Preview prune
.venv/bin/python scripts/prune_minecraft_assets.py --all-versioned --dry-run

# Print prune allowlist
.venv/bin/python scripts/prune_minecraft_assets.py --list-manifest

# Dedupe without rewriting assets/minecraft
.venv/bin/python scripts/dedupe_minecraft_assets.py --materialize none
```

Allowlist code: [`helpers/minecraft_asset_manifest.py`](../helpers/minecraft_asset_manifest.py).

## Discarded folders

Removed by the prune script:

- `sounds/`, `sounds.json`
- `lang/*` except `en_us.json`
- `items/`, `models/item/`
- `font/`, `texts/`, `resourcepacks/`, `shaders/`, `post_effect/`, `particles/`, `equipment/`, `atlases/`, `waypoint_style/`
- Most of `textures/` except `block/`, `item/`, and `entity/bed|entity/chest`
- Root metadata such as `_all.json`, `gpu_warnlist.json`

## Future work

See [roadmap.md](roadmap.md):

- **Datapack export** — `assets/minecraft_data/` for loot tables and tags
- **Select world version to generate** — switch materialized `assets/minecraft/` between 26.1.2 and 26.2 overlays

## Related docs

| Doc | Contents |
| --- | -------- |
| [sprite-baker.md](sprite-baker.md) | Baking `project/generated/` sprites |
| [registry.md](registry.md) | Texture loading and catalog |
| [project-info.md](project-info.md) | Supported Minecraft versions |
