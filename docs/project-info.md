# Project Info

Canonical facts about **structure_scripts** and its Minecraft target. Agents and contributors should read this before assuming version numbers or searching the web.

## Minecraft target

| Fact | Value |
| ---- | ----- |
| Edition | **Java Edition only** (not Bedrock) |
| Supported game versions | **26.x** (year-based releases, e.g. 26.1.2, 26.2) |
| **Not supported** | Legacy **1.x** numbering (1.20, 1.21, etc.) — different product era |
| Template world | **Java 26.1.2** — create/copy into `template/` ([worldgen.md](worldgen.md)) |
| Structure packages | Per-structure manifest **`version`** (`26.1.2` / `26.2`) on `structures/{name}/structure.yaml` — drives palette filtering and worldgen |
| Forward work | **26.2** assets and block-model changes ([roadmap.md](roadmap.md)) |

### Version numbering (avoid confusion)

Minecraft Java moved to **calendar-year style** versions starting with **26.x** (2026). When docs or code say `26.1`, `26.1.2`, or `26.2`, they mean **Minecraft**, not Python packages.

**Common trap:** `packaging==26.2` in `requirements.txt` is the Python [**packaging**](https://pypi.org/project/packaging/) library — **not** the Minecraft release.

### Reference versions (infobox summary)

| Version | Role here | Data version | Protocol | Resource pack | Data pack | Min Java |
| ------- | --------- | ------------ | -------- | ------------- | --------- | -------- |
| [26.1.2](https://minecraft.wiki/w/Java_Edition_26.1.2) | **Current template / worldgen target** | 4790 | 775 | 84.0 | 101.1 | Java SE 25 |
| [26.2](https://minecraft.wiki/w/Java_Edition_26.2) | **Next asset target** (e.g. bed block models) | 4903 | 776 | 88.0 | 107.1 | Java SE 25 |

Code notes:

- **26.1.x** — beds use a special renderer; worldgen patches block entities ([worldgen.md](worldgen.md), `helpers/worldgen_block_entities.py`).
- **26.2** — beds move to standard block models; unified `minecraft:bed` style properties.

Do **not** infer these numbers from generic web search — use the links below or this table.

## Python / dependencies

| Fact | Value |
| ---- | ----- |
| Language | **Python 3.11+** |
| App libraries | `requirements.txt` — pinned versions for the full dev/worldgen environment |
| Install groups | `pyproject.toml` — `[project.optional-dependencies]` (`dev`, `worldgen`, `ui`) |
| Worldgen stack | Amulet (`amulet-core`, etc.) — see [worldgen.md](worldgen.md) |

```bash
pip install -e ".[dev]"        # tests, ruff, pre-commit
pip install -e ".[worldgen]"   # Amulet world writing
pip install -e ".[ui]"         # PySide6 editor
```

For a reproducible environment matching CI/local pins, use `requirements.txt`.

## Trusted external references

Use these for Minecraft **26.x** facts. Avoid guessing or searching for **1.x** release pages.

| Resource | URL |
| -------- | --- |
| Official release changelogs | https://feedback.minecraft.net/hc/en-us/sections/360001186971-Release-Changelogs |
| Java Edition 26.2 (wiki) | https://minecraft.wiki/w/Java_Edition_26.2 |
| Java Edition 26.1.2 (wiki) | https://minecraft.wiki/w/Java_Edition_26.1.2 |

Agents: see [`.cursor/skills/project-context/SKILL.md`](../.cursor/skills/project-context/SKILL.md) — do not web-search Minecraft version info without reading that skill first.

## Related docs

| Doc | Contents |
| --- | -------- |
| [worldgen.md](worldgen.md) | Template world, Amulet, bed placement |
| [sprite-baker.md](sprite-baker.md) | Vanilla assets under `assets/minecraft/` |
| [assets.md](assets.md) | Asset layout, prune script, versioned extracts |
| [project-structure.md](project-structure.md) | Repo layout |
