# Roadmap

## Design goals

* Registry-driven customization
* Modular renderer expansion
* Additional structure presets
* Advanced landscaping systems
* Desktop UI for structure authoring

## Statuses

- Not Started = Item has not been started yet
- Up Next = Item is planned but not yet started
- Planned = Item is ready for implementation and will be started soon
- In Progress = Item is currently being worked on
- Completed = Item has been completed and is ready for use

## UI

| Status | Item |
| ------ | ---- |
| Completed | Agent triage skill — [`.cursor/skills/agent-triage/SKILL.md`](../.cursor/skills/agent-triage/SKILL.md) |
| Completed | Agent repo-map skill — [`.cursor/skills/repo-map/SKILL.md`](../.cursor/skills/repo-map/SKILL.md) |
| Completed | Agent targeted-testing skill — [`.cursor/skills/targeted-testing/SKILL.md`](../.cursor/skills/targeted-testing/SKILL.md) |
| Completed | Agent pre-commit workflow skill — [`.cursor/skills/pre-commit-workflow/SKILL.md`](../.cursor/skills/pre-commit-workflow/SKILL.md) |
| Completed | Agent ui-change skill — [`.cursor/skills/ui-change/SKILL.md`](../.cursor/skills/ui-change/SKILL.md) |
| Completed | Agent self evaluation skill — [`.cursor/skills/agent-self-evaluation/SKILL.md`](../.cursor/skills/agent-self-evaluation/SKILL.md) (exit review + skill feedback loop) |
| Completed | User Added 26.2 assets. |
| Completed | Slim and structure assets/minecraft — [assets.md](assets.md) (`prune`, `migrate_project_assets`, `dedupe` scripts) |
| Completed | Add 26.2 blocks to the proper category (cinnabar/sulfur in terrain and building palettes) |
| Completed | Worldgen version selection — modal when worldgen is included; templates from `worldgen_templates/` (`WorldgenVersionDialog`, `--worldgen-version` CLI) |
| Completed | Colored palette category — `registries/palettes/colored.yaml` (empty; blocks added later) |
| Completed | Natural palette category — `registries/palettes/natural.yaml` (empty; blocks added later) |
| Completed | Redstone palette category — `registries/palettes/redstone.yaml` (empty; blocks added later) |
| Completed | Ore palette category — `registries/palettes/ore.yaml` (empty; blocks added later) |
| Completed | Populate Natural tab blocks — `registries/palettes/natural.yaml` (overworld / nether / end) |
| Completed | Populate Ore tab blocks — `registries/palettes/ore.yaml` (overworld / nether) |
| Completed | In-app schematic preview — evaluation and recommendation (see [In-app schematic preview](#in-app-schematic-preview-recommendation) below) |
| Up Next | In-app 2D blueprint preview on the Render tab (Phase A — recommended first implementation) |
| Up Next | Populate Colored tab blocks — `registries/palettes/colored.yaml` |
| Up Next | Populate Redstone tab blocks — `registries/palettes/redstone.yaml` |
| Not Started | In-app structure metadata editing |
| Not Started | Multiple structures per site — each selectable and nudged independently on the Site tab |
| Not Started | Lightweight 3D orbit preview (Phase C — optional, after 2D preview) |
| Not Started | Allow for custom mod assets |

See [ui.md](ui.md) for the current editor guide.

The Site tab today assumes **one** structure per stage (`offset_x` / `offset_z` on a single layer footprint). Nudge and placement are intentionally per-footprint so a later model can register many structures (each with its own offset and layer reference) without redoing the UX.

## Registry and rendering

| Status | Item |
| ------ | ---- |
| In Progress | `WALL` behavior token — registry entry, adjacency, sprite baker (`compose_wall`, `wall_model`), schematic utils |
| Up Next | 26.2 bed block models — retire 26.1 entity-atlas bed baker when `assets/minecraft/` targets 26.2 ([project-info.md](project-info.md), [sprite-baker.md](sprite-baker.md)) |
| Up Next | Populate Building palette catalog blocks — bricks, glass, copper variants beyond templated `SLAB` / `FENCE` / `WALL` / `STAIRS` / `TRAPDOOR` tokens |
| Up Next | `worldgen_templates/v26_2/` template world for default 26.2 worldgen output |
| Not Started | Custom mod catalog entries — extend `catalog.json` generation for non-vanilla block ids |
| Not Started | Datapack structure and loot generation |

## In-app schematic preview (recommendation)

The editor already previews structures in **2D**: layer grids and the Site tab use the same `compile_texture_set()` / sprite-baker pipeline as blueprint renders. The Render tab runs `render_main.py` and writes PNGs to `output/schematics/`; there is no embedded preview yet.

Layer YAML is the source of truth in the editor — do **not** add an NBT/.schem parser path for in-app preview. Build from `SchematicContext` and existing renderers.

### Recommended phased approach

| Phase | Approach | Value | Effort | New dependencies |
| ----- | -------- | ----- | ------ | ---------------- |
| **A** | **2D blueprint preview in the Render tab** | See floor plans, facades, and materials without leaving the app | Low | None (Pillow + PySide6 already present) |
| **B** | **Post-render gallery + zoom/pan** | Replace “open folder” as the primary feedback loop | Low–medium | None |
| **C** | **Lightweight 3D orbit view** (`QOpenGLWidget`) | Rotate around the structure; useful for height and roof checks | High | Optional OpenGL only |
| **D** | **Worldgen shortcut** | Open last generated world folder or launch Minecraft | Low | None (worldgen stack optional) |
| **E** | **Embedded WebGL** (prismarine-viewer + `QWebEngine`) | Full chunk fidelity, best for whole-world context | Very high | Qt WebEngine, Node.js subprocess |

**Start with Phase A.** It reuses `build_stage_complete_schematics()` or individual renderer functions, renders to a temp file or in-memory `PIL.Image`, and displays the result in a scrollable widget on the Render tab. Unsaved edits still require save-first (same rule as today).

Phase B extends A with a thumbnail strip for all selected render types and basic zoom/pan (`QScrollArea` + scale factor).

Phase C is optional. If pursued:

* Build a voxel mesh from stacked layers via existing context builders (not from exported schematics).
* Use **greedy meshing** and **face culling** — one combined mesh per structure, not one cube per block.
* Sample textures from `compile_texture_set()` / catalog fallback into a single atlas.
* Expect extra work for partial blocks (stairs, fences, walls, doors) where 2D bakers already solve the hard cases; 3D may show simplified boxes for complex blockstates initially.

Phase D complements preview: after a worldgen render, offer **Open output world** (folder) on the Render tab. True in-game validation without building a renderer.

Defer Phase E unless the goal shifts to embedded chunk/world viewing. It adds Qt WebEngine and often a Node sidecar; **26.x** block-model coverage in third-party viewers should be verified before committing.

### Options evaluated (not recommended as first step)

| Option | Why defer |
| ------ | --------- |
| prismarine-viewer (WebGL) as the first preview | Heavy deps; structure authoring already has accurate 2D renders; 26.x model support uncertain |
| Ursina / Panda3D | Separate window or process; breaks single-window PySide6 editor UX |
| Amulet Map Editor renderer reuse | wxPython + PyOpenGL stack; different GUI framework |
| Per-block entities (50k `Entity` cubes) | Unusable performance at real structure sizes |
| nbtschematic / anvil-parser for preview | Duplicates layer YAML; editor never loads .schem for editing |

### Performance notes

* Structure layers in this project are typically modest (tens of thousands of cells across all layers, not full chunks).
* 2D blueprint renders are already optimized (sprite cache, baked fences/stairs/walls).
* Any 3D path must merge visible faces into a single draw call; never instantiate one mesh per block.

### Implementation sketch (Phase A)

1. Add `PreviewPanel` on the Render tab (below generate / open-folder actions).
2. On **Generate**, optionally run `top_view` (or user-selected types) to a temp directory under `output/schematics/_preview/`.
3. Load the primary PNG into a `QLabel` or custom zoom widget; show path and timestamp.
4. Wire `RenderWorker` completion signal to refresh the preview (same worker as today).
5. Tests: mock renderer output path; no GPU required.

## Planned palette content

Block lists for upcoming palette population work. Use dimension sections (`overworld`, `nether`, `end`) where noted.

Implemented palettes are kept here as reference. Upcoming work: Colored and Redstone tabs below.

### Natural tab

Implemented in `registries/palettes/natural.yaml`. Variant keys are shown in parentheses.

#### Overworld

| Block | Catalog id |
| ----- | ---------- |
| Dirt | `minecraft:dirt` (variants: coarse, rooted) |
| Dirt Path | `minecraft:dirt_path` |
| Grass Block | `minecraft:grass_block` (variants: podzol, mycelium) |
| Moss Block | `minecraft:moss_block` |
| Mud | `minecraft:mud` |
| Clay | `minecraft:clay` |
| Sand | `minecraft:sand` (variant: red) |
| Gravel | `minecraft:gravel` |
| Soul Sand | `minecraft:soul_sand` |
| Soul Soil | `minecraft:soul_soil` |
| Stone | `minecraft:stone` (variant: smooth) |
| Granite | `minecraft:granite` (variant: polished) |
| Diorite | `minecraft:diorite` (variant: polished) |
| Andesite | `minecraft:andesite` (variant: polished) |
| Deepslate | `minecraft:deepslate` (variants: polished, chiseled) |
| Cobbled Deepslate | `minecraft:cobbled_deepslate` |
| Tuff | `minecraft:tuff` (variant: polished) |
| Calcite | `minecraft:calcite` |
| Dripstone Block | `minecraft:dripstone_block` |
| Cobblestone | `minecraft:cobblestone` (variant: mossy) |
| Cinnabar | `minecraft:cinnabar` (variant: chiseled) |
| Sulfur | `minecraft:sulfur` (variant: chiseled) |
| Sulfur Spike | `minecraft:sulfur_spike` |
| Snow Block | `minecraft:snow_block` |
| Powder Snow | `minecraft:powder_snow` |
| Ice | `minecraft:ice` (variants: packed, blue) |
| Obsidian | `minecraft:obsidian` |
| Bedrock | `minecraft:bedrock` |

#### Nether

| Block | Catalog id |
| ----- | ---------- |
| Netherrack | `minecraft:netherrack` |
| Soul Sand | `minecraft:soul_sand` |
| Soul Soil | `minecraft:soul_soil` |
| Basalt | `minecraft:basalt` (variants: smooth, polished) |
| Blackstone | `minecraft:blackstone` (variant: polished) |
| Bedrock | `minecraft:bedrock` |

#### End

| Block | Catalog id |
| ----- | ---------- |
| End Stone | `minecraft:end_stone` |
| Bedrock | `minecraft:bedrock` |

### Ore tab

Implemented in `registries/palettes/ore.yaml`. Deepslate ore variants use the `deepslate` variant key on each overworld ore entry.

#### Overworld

| Block | Catalog id |
| ----- | ---------- |
| Coal Ore | `minecraft:coal_ore` (variant: deepslate) |
| Iron Ore | `minecraft:iron_ore` (variant: deepslate) |
| Copper Ore | `minecraft:copper_ore` (variant: deepslate) |
| Gold Ore | `minecraft:gold_ore` (variant: deepslate) |
| Redstone Ore | `minecraft:redstone_ore` (variant: deepslate) |
| Lapis Lazuli Ore | `minecraft:lapis_ore` (variant: deepslate) |
| Diamond Ore | `minecraft:diamond_ore` (variant: deepslate) |
| Emerald Ore | `minecraft:emerald_ore` (variant: deepslate) |
| Raw Iron Block | `minecraft:raw_iron_block` |
| Raw Copper Block | `minecraft:raw_copper_block` |
| Raw Gold Block | `minecraft:raw_gold_block` |
| Amethyst Block | `minecraft:amethyst_block` |
| Budding Amethyst | `minecraft:budding_amethyst` |
| Amethyst Cluster | `minecraft:amethyst_cluster` |

#### Nether

| Block | Catalog id |
| ----- | ---------- |
| Nether Gold Ore | `minecraft:nether_gold_ore` |
| Ancient Debris | `minecraft:ancient_debris` |

### Colored tab (up next)

Target file: `registries/palettes/colored.yaml`. Group by material family; use variant keys for dye colors where the catalog uses separate block ids (e.g. `minecraft:white_wool` with variants `orange`, `magenta`, …) or list common anchors and rely on `enumerate_token_materials` for templated families.

| Family | Catalog pattern / anchor ids |
| ------ | ---------------------------- |
| Wool | `minecraft:white_wool` (+ color variants) |
| Carpet | `minecraft:white_carpet` (+ color variants) |
| Terracotta | `minecraft:white_terracotta` (+ color variants) |
| Glazed terracotta | `minecraft:white_glazed_terracotta` (+ color variants) |
| Concrete | `minecraft:white_concrete` (+ color variants) |
| Concrete powder | `minecraft:white_concrete_powder` (+ color variants) |
| Stained glass | `minecraft:white_stained_glass` (+ color variants) |
| Stained glass pane | `minecraft:white_stained_glass_pane` (+ color variants) |
| Shulker box | `minecraft:white_shulker_box` (+ color variants) |

Verify each id against `registries/generated/catalog.json` after asset updates; omit entries missing textures.

### Redstone tab (up next)

Target file: `registries/palettes/redstone.yaml`. Flat list (no dimension sections). Prefer catalog ids present in `catalog.json`; add behavior entries later if a block needs facing or powered state in the editor.

| Block | Catalog id |
| ----- | ---------- |
| Redstone Wire | `minecraft:redstone_wire` |
| Redstone Torch | `minecraft:redstone_torch` |
| Redstone Block | `minecraft:redstone_block` |
| Redstone Lamp | `minecraft:redstone_lamp` |
| Repeater | `minecraft:repeater` |
| Comparator | `minecraft:comparator` |
| Observer | `minecraft:observer` |
| Piston | `minecraft:piston` |
| Sticky Piston | `minecraft:sticky_piston` |
| Hopper | `minecraft:hopper` |
| Dropper | `minecraft:dropper` |
| Dispenser | `minecraft:dispenser` |
| Lever | `minecraft:lever` |
| Stone Button | `minecraft:stone_button` |
| Oak Button | `minecraft:oak_button` |
| Stone Pressure Plate | `minecraft:stone_pressure_plate` |
| Oak Pressure Plate | `minecraft:oak_pressure_plate` |
| Heavy Weighted Pressure Plate | `minecraft:heavy_weighted_pressure_plate` |
| Light Weighted Pressure Plate | `minecraft:light_weighted_pressure_plate` |
| Tripwire Hook | `minecraft:tripwire_hook` |
| Target | `minecraft:target` |
| Note Block | `minecraft:note_block` |
| Daylight Detector | `minecraft:daylight_detector` |
| Slime Block | `minecraft:slime_block` |
| Honey Block | `minecraft:honey_block` |

Omit ids not present in the generated catalog until assets are added. Redstone ore remains in the Ore tab.

## Future plans

* **Render preview system** — Phase A/B in [In-app schematic preview](#in-app-schematic-preview-recommendation) (embedded 2D, then gallery)
* **Structure preset browser** — pick starter layouts from `structures/` without CLI flags
* **Theme/style packs** — swap palette subsets or default materials per pack
* **Advanced terrain generation** — only if flat-world assumptions change ([worldgen.md](worldgen.md) model today)
* **Multi-biome support** — site-level biome tags for path/ground materials
* **Animated build progression renders** — layer visibility sequence export (GIF or frame strip)
* **Multiple structures per site** — see UI table; manifest model extension
* **In-app metadata editing** — structure identity fields without raw YAML
* **26.2 as default asset overlay** — flip editor default from 26.1.2 when bed/wall bake paths are validated on 26.2
