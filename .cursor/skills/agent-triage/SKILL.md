---
name: agent-triage
description: >-
  Routes agent work in structure_scripts to reduce token use and rework. Use at
  the start of any task, when choosing tools (grep vs explore vs Task), picking
  tests, fixing pre-commit failures, editing UI/docs/registry/helpers, or when
  the user asks to limit tokens, avoid churn, or work efficiently in this repo.
---

# Agent Triage

**Repo entry:** [AGENTS.md](../../AGENTS.md) (kanban-first routing). Always-on wrapper: [agent-routing.mdc](../../rules/agent-routing.mdc).

Decide **how** to work before reading files or running commands. Follow this skill first; drill into `.cursor/rules/` and other skills only when the table below says so.

**Every turn ends with** [agent-self-evaluation](../agent-self-evaluation/SKILL.md) §7 handoff (`.cursor/rules/agent-self-evaluation.mdc`, alwaysApply).

**Version / Minecraft facts:** read [project-context](../project-context/SKILL.md) before web search or assuming 1.x vs 26.x.

**Planned work:** read [kanban-markdown](../kanban-markdown/SKILL.md) — **To Do** only; **ignore Backlog**; card types: **feature** (default), **bug** (`labels` includes `bug`), **inquiry** (`labels` includes `inquiry`); pre-implementation card review before feature/bug code; inquiry cards get **`## Response`** only (research, no code by default); resolve **`## Feature Areas`** → **`## Label Paths`** via `docs/feature-areas.yaml` when areas are set; agent writes **`## Decisions`** (feature) or **`## Corrective Action`** + **`## Root Cause (current code)`** (bug) before `in-progress`; **MUST** update `docs/feature-areas.yaml` after every **implementation**; **MUST** review and update **`docs/`** per [docs-maintenance](../docs-maintenance/SKILL.md) (no exceptions); **MUST** mark **`## Acceptance Criteria` `[x]`** before feature/bug `in-progress` → `review`; do **not** use `docs/roadmap.md`.

## 1. Classify the request

| Signal | Mode | First action |
| ------ | ---- | ------------ |
| Explain, review, audit, "is this correct?" | **Read-only** | No edits. Grep/Read only. |
| Fix one error, rename, small doc fix; bug found, fix bug, bug reported; failing test, ruff/lint, typo, quick fix | **Surgical** | Grep → Read 1–3 files → minimal edit |
| Feature, multi-file, refactor | **Implementation** | Read [repo-map](../repo-map/SKILL.md) + [reference.md](reference.md) area map → targeted reads → [docs-maintenance](../docs-maintenance/SKILL.md) before Review |
| Planned work / implement from card; "kanban", card path or title | **Review first** — [kanban-markdown](../kanban-markdown/SKILL.md): feature/bug → implement; **inquiry** → **`## Response`** only. **Default work queue** when not in Ask mode — see [AGENTS.md](../../AGENTS.md) |
| Commit / pre-commit failed | **Unblock** | [pre-commit-workflow](../pre-commit-workflow/SKILL.md) → fix reported hook |
| "Run tests" / verify | **Verify** | [targeted-testing](../targeted-testing/SKILL.md) — smallest test set |
| User will commit / "commit-ready" | **Verify** | `scripts/pre-commit-pytest.sh` on staged files → green → optional `record-pytest-pass.sh` (also required before kanban **Review**) |

If the user is in **Ask mode**, stop at read-only even when they say "fix".

**Surgical vs kanban:** Ad-hoc bugs and one-file fixes are **Surgical** — no card review, no column moves. Use the kanban row only when the user assigns a **To Do** card (path, id, title) or asks to implement planned board work.

## 2. Choose discovery tools (token budget)

**Default cap:** after **3** file reads, prefer `Grep` or `SemanticSearch` instead of opening more whole files.

| Situation | Use | Avoid |
| --------- | --- | ----- |
| Known symbol, path, or error line | `Grep` | Task / broad explore |
| 1–2 obvious files | `Read` those files | Reading `main_window.py` wholesale |
| "Where is X?" unknown | `Grep` then `SemanticSearch` | Parallel Task agents for one needle |
| Large unfamiliar subsystem | **One** Task `explore` (medium) | Multiple explores + full tree reads |
| UI manual check | [run-ui skill](../run-ui/SKILL.md) | Launching UI for docs-only edits |

**Do not** launch Task subagents for questions answerable with a single grep.

## 3. Area → rules and docs (read only if touching that area)

| Area changed | Read first | Tests (default) |
| ------------ | ---------- | --------------- |
| `ui/widgets/*` panel | `.cursor/rules/ui-panels.mdc`, [ui-change](../ui-change/SKILL.md) | Matching `tests/test_*panel*.py` |
| `ui/*` dialog | `.cursor/rules/ui-dialogs.mdc`, [ui-change](../ui-change/SKILL.md) | Dialog + `tests/test_main_window.py` if wired |
| Grid toolbar split button | `.cursor/rules/ui-split-buttons.mdc` | `tests/test_main_window.py` |
| `registries/` (new token / behavior) | `registries/validate.py`, [repo-map](../repo-map/SKILL.md) § Templated block families | `tests/test_palette_integrity.py`, `tests/test_block_picker.py` |
| Structure YAML / loader | `docs/structure-tokens.md` (manifest + `stage.yaml`) | `tests/test_structure_loader.py` |
| `helpers/*` | Matching `tests/test_<module>.py` | See [reference.md](reference.md) |
| `docs/*` only | — | No pytest unless code also changed |
| Worldgen | `.cursor/rules/worldgen.mdc`, [project-context](../project-context/SKILL.md) | `tests/test_worldgen_*.py` subset; template via `resolve_worldgen_template_dir()` not `template/` |
| Version / assets / dependencies | [project-context](../project-context/SKILL.md), `docs/project-info.md` | As area touched |

Full path→test map: `scripts/pre-commit-pytest.sh` (source of truth).

## 4. Testing discipline

Follow [targeted-testing](../targeted-testing/SKILL.md). Summary:

Before **any** pytest run, state in one line: **which tests** and **why**.

1. Map changed paths to tests via `scripts/pre-commit-pytest.sh` cases or `.cursor/rules/testing.mdc`.
2. Run the **smallest** set that covers the change.
3. On failure: fix → rerun **failed + related** tests only.
4. Escalate to full `pytest` only when:
   - `conftest.py`, `registries/loader.py`, `render_main.py`, or similar core files changed
   - targeted tests pass but risk is cross-cutting
   - user asks before PR / large refactor

After a green run on staged files:

```bash
scripts/record-pytest-pass.sh
```

**Do not** assert exact terrain/catalog **block counts** in tests — use membership, helpers, or counts derived from `resolve_palette("terrain")` (see `tests/palette_helpers.py`).

## 5. Pre-commit loop

Follow [pre-commit-workflow](../pre-commit-workflow/SKILL.md). Summary — hooks in order: **ruff** → **validate_palettes** → **targeted pytest**.

## 6. Model and scope (`.cursor/rules/model-routing.mdc`)

| Work | Model tier |
| ---- | ---------- |
| Explain, docstring, tiny question | Cheapest (Haiku-class) |
| Normal multi-file edit | Sonnet-class default |
| Single-file lint/test fix | Composer-class |
| Whole-codebase architecture | Opus-class only when user asks |

**Scope:** one problem per turn when possible. No drive-by refactors, doc sweeps, or test-suite optimization unless requested.

## 7. Structure package reminder (avoids doc/code churn)

```text
structures/{name}/structure.yaml     # manifest: dimension, grid, site_ground, stages[]
structures/{name}/stage{N}/stage.yaml   # identity, layer_files
structures/{name}/stage{N}/layers/*.yaml
```

Save targets: layers → layer files; site settings → manifest + `stage.yaml`. Details: `docs/structure-tokens.md`.

## 8. End-of-task checklist (mandatory)

**Every response** must end with [agent-self-evaluation](../agent-self-evaluation/SKILL.md) §7 handoff block. Enforced by `.cursor/rules/agent-self-evaluation.mdc` (`alwaysApply: true`). No exceptions for Ask mode, trivial answers, or read-only work.

```
- [ ] Request classified (read-only vs surgical vs implementation)
- [ ] Discovery used grep/targeted read, not unnecessary explore
- [ ] Only relevant rules/docs opened
- [ ] Tests named before run; full suite only if justified
- [ ] Before commit: `scripts/pre-commit-pytest.sh` green on staged paths (not stale earlier run)
- [ ] After test fix: re-ran hook scope, not only the single failed file
- [ ] Pre-commit failures addressed in hook order
- [ ] No unrelated files changed
- [ ] Kanban implementation: `docs/feature-areas.yaml` updated when code shipped (feature/bug); inquiry → **Response** on card; bug → **Corrective Action** not **Decisions**
- [ ] Code changes: `docs/` reviewed and updated per [docs-maintenance](../docs-maintenance/SKILL.md) (no exceptions)
- [ ] §6: implementation turns updated **≥1 skill and ≥1 rule**; read-only may use `none (read-only)`
- [ ] ### Self-evaluation block present as last section of response
```

## Related skills

| Skill | When |
| ----- | ---- |
| [project-context](../project-context/SKILL.md) | Minecraft 26.x facts; no 1.x web lookup |
| [repo-map](../repo-map/SKILL.md) | Where code/docs live; structure layout; path→test hints |
| [targeted-testing](../targeted-testing/SKILL.md) | Pick and run pytest for changed paths |
| [pre-commit-workflow](../pre-commit-workflow/SKILL.md) | Fix commit hook failures in order |
| [ui-change](../ui-change/SKILL.md) | Editor UI panels, dialogs, wiring |
| [agent-self-evaluation](../agent-self-evaluation/SKILL.md) | End-of-task review + skill & rule feedback loop |
| [run-ui](../run-ui/SKILL.md) | Launch editor after UI changes |
| [kanban-markdown](../kanban-markdown/SKILL.md) | To Do queue; bug/inquiry types; **Feature Areas** → **Label Paths**; [AGENTS.md](../../AGENTS.md) |
| [docs-maintenance](../docs-maintenance/SKILL.md) | Mandatory `docs/` review/update after implementation — no exceptions |
| [optimize-test-suite](../optimize-test-suite/SKILL.md) | Suite-wide speed/consolidation — **not** normal commits |

Extended tables: [reference.md](reference.md).
