# World Generation

World generation copies a template world and writes blocks via [Amulet](https://github.com/Amulet-Team/Amulet-Core).

## Requirements

1. Create a new world in Minecraft 1.21 or later.
2. Create a `template/` folder in the project root.
3. Copy the world folders/files into `template/`.
4. Install the worldgen optional dependencies:

```bash
pip install -e ".[worldgen]"
```

## Running worldgen

Include `worldgen` in the render list:

```python
from render_main import build_stage_complete_schematics

build_stage_complete_schematics(structure="residence", stage=1, renders="worldgen")
```

Output is written to `output/worlds/{output_folder}/`.

## Amulet install issues

If Amulet fails to build or import, see [../AMULET_INSTALL_NOTES.md](../AMULET_INSTALL_NOTES.md).

You can also run the install helper:

```bash
scripts/install_worldgen.sh
```
