# World Generation

World generation copies a template world and writes blocks via [Amulet](https://github.com/Amulet-Team/Amulet-Core).

## Requirements

See [project-info.md](project-info.md) for supported Minecraft versions (**Java 26.x**; legacy 1.x is not supported).

1. Create a new world in **Minecraft Java 26.1.2** and copy it into `worldgen_templates/v26_1_2/`. Add `worldgen_templates/v26_2/` when targeting **26.2**.
2. Create a `worldgen_templates/` folder in the project root (if it does not exist).
3. Copy the world folders/files into the versioned subfolder (e.g. `worldgen_templates/v26_1_2/`).
4. Legacy `template/` at the project root is still supported as a fallback.
5. Install the worldgen optional dependencies:

```bash
pip install -e ".[worldgen]"
```

## Running worldgen

Include `worldgen` in the render list:

```python
from render_main import build_stage_complete_schematics

build_stage_complete_schematics(structure="residence", stage=1, renders="worldgen")
```

**Version:** pass `worldgen_version` to `build_stage_complete_schematics` / `run_stage_renders`, or use `--worldgen-version 26.2` on the CLI. The editor reads **`version`** from the structure manifest (`structures/{name}/structure.yaml`) when worldgen runs. Templates resolve under `worldgen_templates/v{version}/` via `resolve_worldgen_template_dir()`.

Output is written to `output/worlds/{output_folder}/v{version}/` (for example `output/worlds/residence/v26_2/`), matching the template folder naming under `worldgen_templates/`.

In the editor **Viewer** tab, **Open World Folder** opens that path after a successful **Generate World** (or **All Renders** including worldgen) in the current session. Schematic PNGs remain under `output/schematics/{output_folder}/` — use **Open Output Folder** for those.

## Beds on Minecraft Java 26.1

Beds use a special renderer in 26.1 (they move to standard block models in 26.2). Amulet writes the correct `minecraft:*_bed` blockstates, but programmatic placement does not queue all of the follow-up data vanilla placement would.

Worldgen uses a two-pass placement strategy:

1. **Pass 1** — shell blocks (walls, floors, chests, etc.)
2. **Pass 2** — multi-block couplings (beds, doors)

After Amulet saves the world, a region-file patch injects `block_entities`, `PostProcessing`, and `block_ticks` entries for each bed. This covers cases where Amulet drops bed block entities during encode and where a neighbor block update is required to initialize the renderer.

If a bed still appears invisible after regenerating, place or break a block beside it once to force a local block update.

Amulet does not expose a `dimension.send_changes()` API; chunk commits use `level.commit_chunk()` and `level.save()` as today.

## Amulet install issues

If Amulet fails to build or import, see [../AMULET_INSTALL_NOTES.md](../AMULET_INSTALL_NOTES.md).

You can also run the install helper:

```bash
scripts/install_worldgen.sh
```
