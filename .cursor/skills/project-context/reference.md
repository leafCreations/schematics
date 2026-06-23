# Project Context — Reference

## Version infobox (from Minecraft Wiki)

Summarized for agent use — full pages at the URLs in [SKILL.md](SKILL.md).

### Java Edition 26.1.2

| Field | Value |
| ----- | ----- |
| Release | April 9, 2026 |
| Data version | 4790 |
| Protocol version | 775 |
| Resource pack format | 84.0 |
| Data pack format | 101.1 |
| Minimum Java | Java SE 25 |
| Wiki | https://minecraft.wiki/w/Java_Edition_26.1.2 |

**Project use:** default worldgen template `worldgen_templates/v26_1_2/`; Amulet export tested against data version 4790.

### Java Edition 26.2 (“Chaos Cubed”)

| Field | Value |
| ----- | ----- |
| Release | June 16, 2026 |
| Data version | 4903 |
| Protocol version | 776 |
| Resource pack format | 88.0 |
| Data pack format | 107.1 |
| Minimum Java | Java SE 25 |
| Wiki | https://minecraft.wiki/w/Java_Edition_26.2 |

**Project use:** target for new assets and block-model behavior (see roadmap).

## Wrong assumptions (do not repeat)

| Wrong | Right |
| ----- | ----- |
| “Minecraft 1.26” or “1.21.4” for this repo | **26.1.2** / **26.2** (year-based) |
| `packaging==26.2` → game version 26.2 | Python **packaging** package on PyPI |
| Web search “minecraft bed block entity 1.21” | `docs/worldgen.md` + `worldgen_block_entities.py` |
| Bedrock edition behavior | Java Edition only |
| `helpers/worldgen_block_entities.py` docstring “1.26” | Means Java **26.x** era, not version 1.26 |

## Dependency files

| File | Purpose |
| ---- | ------- |
| `requirements.txt` | Full pinned environment (Amulet, Pillow, pytest, etc.) |
| `pyproject.toml` | Package metadata; optional extras `dev`, `worldgen`, `ui` |
| `README.md` | Quick start: `pip install -e ".[dev]"` |

Worldgen-specific pins live in both `requirements.txt` and `[project.optional-dependencies].worldgen`.

## Repo paths tied to game version

| Path | Version note |
| ---- | ------------ |
| `worldgen_templates/v26_1_2/` | World created in **26.1.2** (default worldgen) |
| `worldgen_templates/v26_2/` | World created in **26.2** (forward; Amulet may not support data 4903 yet) |
| `template/` | Legacy fallback (deprecated) |
| `assets/minecraft/` | Vanilla jar extract; must match target game version for bakes |
| `registries/generated/catalog.json` | Built from assets + behaviors |

## Changelog source

Official Mojang release notes (all editions):

https://feedback.minecraft.net/hc/en-us/sections/360001186971-Release-Changelogs

Use for “what changed in 26.2” — not legacy 1.x wikis.
