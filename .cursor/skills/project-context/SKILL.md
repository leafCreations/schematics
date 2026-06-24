---
name: project-context
description: >-
  Canonical Minecraft and Python requirements for structure_scripts. Use before
  any version lookup, worldgen/assets work, dependency questions, or web search
  about Minecraft. Prevents confusing 26.x with legacy 1.x or Python packaging.
---

# Project Context

Read this **before** web search, wiki lookup, or assumptions about Minecraft versions.

Human doc: [docs/project-info.md](../../docs/project-info.md).

## Hard rules

1. **Java Edition 26.x only** — this project targets year-based releases (26.1.2, 26.2, …).
2. **Legacy 1.x is out of scope** — do not use 1.20, 1.21, or pre-26 numbering for this repo.
3. **Do not web-search generic Minecraft version info** — training data and search snippets often return **1.x** pages and wrong block behavior.
4. **Use trusted sources first:**
   - [docs/project-info.md](../../docs/project-info.md)
   - Repo code/docs (`docs/worldgen.md`, `helpers/worldgen_block_entities.py`)
   - User-provided wiki URLs (see § References)
5. **`packaging==26.2` in requirements.txt is a Python library** — not Minecraft 26.2.

## Quick facts

| Topic | Answer |
| ----- | ------ |
| Edition | Java only (not Bedrock) |
| Template / worldgen | **26.1.2** → `worldgen_templates/v26_1_2/` via `resolve_worldgen_template_dir()` |
| Asset catalog default | **26.2** → `assets/minecraft/` (`DEFAULT_MINECRAFT_VERSION`) |
| Python | 3.11+ |
| Dependencies | `requirements.txt` (pins); `pyproject.toml` (optional groups) |
| Worldgen deps | `pip install -e ".[worldgen]"` |

## When to read this skill

| Task | Action |
| ---- | ------ |
| Worldgen, beds, block entities | Read §26.1 vs 26.2 below + `docs/worldgen.md` |
| Sprite baker / `assets/minecraft/` | Confirm game version for models/textures |
| "What Minecraft version?" | Answer from this skill — **no web search** |
| Adding 26.2 assets (kanban) | Wiki 26.2 page + repo; check **To Do** in `.devtool/features/` |
| Dependency / pip questions | `requirements.txt` + `pyproject.toml` |

## 26.1 vs 26.2 (repo-relevant)

| | 26.1.x (template today) | 26.2 (forward) |
| - | ----------------------- | -------------- |
| Template | **26.1.2** in `worldgen_templates/v26_1_2/` | `worldgen_templates/v26_2/` (Amulet may not support yet) |
| Beds | Special renderer; per-color `minecraft:{color}_bed`; block-entity patch | Standard block models; unified bed properties |
| Code | `helpers/worldgen_block_entities.py`, `docs/worldgen.md` | Kanban + incremental asset work |

Version numbers (data/protocol/pack format): [reference.md](reference.md).

## Web / fetch policy

**Allowed** (when repo docs are insufficient):

- Fetch URLs listed in [docs/project-info.md](../../docs/project-info.md) § Trusted external references
- Read files already in the repo or user uploads in the session

**Avoid:**

- Open web search for "Minecraft 1.21 beds", "latest Minecraft version", etc.
- Mixing Bedrock wiki pages with Java Edition behavior
- Treating PyPI package versions as game versions

If fetch fails, say so and use repo docs — do not substitute 1.x knowledge.

## References (canonical URLs)

- Release changelogs: https://feedback.minecraft.net/hc/en-us/sections/360001186971-Release-Changelogs
- Java Edition 26.2: https://minecraft.wiki/w/Java_Edition_26.2
- Java Edition 26.1.2: https://minecraft.wiki/w/Java_Edition_26.1.2

## Skill feedback

If version confusion caused churn, update this skill, [reference.md](reference.md), or a relevant `.cursor/rules/*.mdc` per [agent-self-evaluation](../agent-self-evaluation/SKILL.md) §6.
