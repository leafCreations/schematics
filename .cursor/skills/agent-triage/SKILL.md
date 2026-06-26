---
name: agent-triage
description: >-
  Routes agent work in structure_scripts to reduce token use and rework. Use at
  the start of any task, when choosing tools (grep vs explore vs Task), picking
  tests, fixing pre-commit failures, failure-pattern lookup on signals (§1b), editing UI/docs/registry/helpers, or when
  the user asks to limit tokens, avoid churn, or work efficiently in this repo.
---

# Agent Triage

**Repo entry:** [AGENTS.md](../../AGENTS.md) (kanban-first routing). Always-on wrapper: [agent-routing.mdc](../../rules/agent-routing.mdc).

Decide **how** to work before reading files or running commands. Follow this skill first; drill into `.cursor/rules/` and other skills only when the table below says so.

**Every turn ends with** [agent-self-evaluation](../agent-self-evaluation/SKILL.md) §7 handoff — **`### Files used`** (load order) then **`### Self-evaluation`** (`.cursor/rules/agent-self-evaluation.mdc`, alwaysApply).

**During the turn:** track paths and skills/rules loaded in order; use for context-load audit (correct files, no excess, classify-before-read, [AGENTS.md](../../AGENTS.md) freshness).

**Version / Minecraft facts:** read [project-context](../project-context/SKILL.md) before web search or assuming 1.x vs 26.x.

**Planned work:** read [kanban-markdown](../kanban-markdown/SKILL.md) — **To Do** only; card types: **`feature`**, **bug**, **inquiry**, **agent**, **commit-issue**; **prompt verb gate** ([kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc) §2 — `review` → ask-only; `implement` / `update` / `spawn` → agent); no card → ask-only; invalid `labels` → stop; Card Done lessons for **feature / bug / agent / commit-issue** only; resolve Feature Areas → Label Paths + Label Methods; update registry + **`docs/`** after implementation; Python ≤ **100** chars (E501).

## 1. Classify the request

Mirrors [AGENTS.md](../../AGENTS.md) § **Classify quickly** (canonical). On drift, update triage §1 to match AGENTS. **Verify** signals (`run tests`, `commit-ready`) must appear on all three: AGENTS, §1 below, and [reference.md](reference.md) § Classify.

| Signal | Mode | First action |
| ------ | ---- | ------------ |
| **Review** kanban card only (`review …`, bare `@path`) | **Ask-only** | Card + [kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc) §2 — no edits |
| **Update / spawn / implement** card (agent verbs) | **Agent** | Card + label gate; kanban-markdown; prior lessons gate |
| `Kanban: answer inquiry on …` | **Agent** | Inquiry — **Response** on card |
| Card missing / empty / unknown `labels` | **Block** | Stop — user must set valid `labels` |
| Implement / fix / refactor **without** a card | **Ask-only** | No product edits — user must assign or create a kanban card |
| Review QA issue on assigned card | **Review** | kanban-review-qa.mdc + **QA follow-up** + refresh card scope when needed |
| User says **feature / bug / agent / commit-issue** Done | **Governance** | kanban-markdown § Card Done — lessons learned |
| User says **inquiry** Done | **Close only** | No lessons capture |
| AGENTS.md governance audit | **Read-only** | kanban-markdown § Periodic AGENTS.md governance audit |
| Explain / audit / is this correct? | **Ask-only** | Grep + read — no edits |
| Pre-commit failed | **Unblock** / **Review** | §1b pre-commit + self-eval reference |
| Failing test / pytest / ruff / lint (no card) | **Ask-only** / **Unblock** | §1b — diagnose; fix needs kanban card |
| UI wiring / dialog (no card) | **Ask-only** | §1b `ui-dialog-no-persist` — explain only |
| Orbit 3D holes (no card) | **Ask-only** | §1b `orbit-stair-mask-transparency` — explain only |
| Agent handoff / process mistake | **Governance** | §1b self-eval reference patterns |
| Agent created `.tmp-venv` / missing project venv | **Ask-only** / **Unblock** | §1b `agent-no-tmp-venv` |
| Repeated mistake / churn | **Grep** | §1b failure pattern routing |
| Run tests / commit-ready | **Verify** | targeted-testing / pre-commit-pytest.sh |
| Area lesson lookup (kanban + Feature Areas) | **Review first** | lessons-index.yaml + § Lessons by area → `resolve_prior_lessons.py` |

Classify **prompt verb** then card + label ([kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc) §2). **Agent** only with implement/update/spawn verbs. Signature: `kanban-prompt-ask-vs-agent`.

**Governance edits** (paths in [agent-consistency.mdc](../../rules/agent-consistency.mdc) `globs`): after classify, open [reference.md](reference.md) § **Consistency matrix** and § **Drift alert examples** before editing; run [agent-self-evaluation](../agent-self-evaluation/SKILL.md) §6g before handoff; surface drift per § **Governance drift detection** below.

### Governance drift detection

**Not every turn** — only when this turn **edits** governance paths ([agent-consistency.mdc](../../rules/agent-consistency.mdc) `globs`).

1. **Compare** touched artifacts against [reference.md](reference.md) § Consistency matrix (and § Drift alert examples anchors): routing, card types, Signatures, registry paths, `handlers:` symbols.
2. **Fix** mismatches in the same turn when possible ([agent-consistency.mdc](../../rules/agent-consistency.mdc) change table).
3. **If parity still fails** → one prefixed line per mismatch in Context load, §6g, and handoff `- **Drift alerts:**` (optional `[info|warn|critical]`; default `warn`).
4. **Temporary waiver** → `KNOWN_DRIFT: <artifact pair> — <reason>[; expires: …]` in handoff (user-approved only; reference § KNOWN_DRIFT).

Manual grep compare; run `python3 scripts/check_governance_parity.py` for on-demand checks (spawns **todo** drift fix cards per new issue unless `--no-spawn-cards`). Registry checks include `handlers:` malformed lines, cross-area duplicates, and kanban **Label Methods** symbols missing from yaml.

### 1b. Failure-pattern lookup (on signals only)

**Not every turn** — skip on read-only, greenfield implementation, and questions with no failure symptom.

After §1 maps to a **failure** signal (pre-commit/hook, pytest, UI wiring, worldgen, agent handoff/process), grep durable patterns **before** broad exploration:

1. Pick table(s) from [reference.md](reference.md) § Failure pattern routing (area → `reference.md`).
2. `Grep` the error snippet, hook name, test path, log line, or known **Signature** (phase-1 schema: [agent-self-evaluation/SKILL.md](../agent-self-evaluation/SKILL.md) §6f).
3. **Match** → apply **Fix pattern** from the row, then open the owning skill/rule for procedure detail.
4. **No match** → continue §2 discovery; if the same failure recurs in-session, flag as churn candidate for [agent-self-evaluation](../agent-self-evaluation/SKILL.md) §6.

**Example — pre-commit pytest failed, no `commit-issue` card:**

```text
Classify → Commit / pre-commit failed
Grep pre-commit-workflow/reference.md + agent-self-evaluation/reference.md
  e.g. rg "commit-issue|precommit-stash|FAILED tests/" .cursor/skills/pre-commit-workflow/reference.md
Match precommit-stash-old-hooks → stage all scripts/pre-commit-*.sh + on_pre_commit_failure.sh
Then pre-commit-workflow/SKILL.md hook order
```

**Example — dialog OK but layer not saved:**

```text
Grep agent-self-evaluation/reference.md for _persist_dialog_changes or ui-dialog-no-persist
Match → ui-change checklist + ui-dialogs.mdc
```

## 2. Choose discovery tools (token budget)

**Kanban + Feature Areas:** after resolving labels via `docs/feature-areas.yaml`, read the matching block in `docs/lessons-index.yaml` and the row in [reference.md](reference.md) § **Lessons by area** **before** broad `grep` under `.devtool/features/done/`. Then run `scripts/resolve_prior_lessons.py`; open full done cards only when the index + routing row are insufficient ([kanban-prior-lessons-gate.mdc](../../rules/kanban-prior-lessons-gate.mdc)). **Not** the same as §1b **Failure pattern routing** — that table is for failure symptoms only; § Lessons by area is proactive prior-lessons lookup (Signature: `lessons-by-area-routing`).

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
| Agent governance (`AGENTS.md`, agent/kanban skills/rules) | [agent-consistency.mdc](../../rules/agent-consistency.mdc), [reference.md](reference.md) § Consistency matrix, [agent-agents-md-maintenance.mdc](../../rules/agent-agents-md-maintenance.mdc); skim `docs/lessons-index.yaml` **or** `docs/feature-areas.yaml` `lesson_signatures` / `lesson_docs` before grepping all `done/` cards; `resolve_feature_areas.py --lessons "<Area>"` for pointer-only review; Card Done captures should add optional ``artifacts:`` tail per [docs/development.md](../../docs/development.md) § Lessons captured `artifacts:` schema | `pytest tests/test_build_lessons_index.py tests/test_resolve_prior_lessons.py tests/test_resolve_feature_areas.py -q` when lesson/index/registry parsers change |

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
- [ ] On failure signals: §1b pattern grep before broad explore (skip when no failure symptom)
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
- [ ] §6g: governance path edits → consistency prompts (or N/A)
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
| [kanban-markdown](../kanban-markdown/SKILL.md) | To Do queue; bug/inquiry types; **Feature Areas** → **Label Paths** + **Label Methods**; [AGENTS.md](../../AGENTS.md) |
| [docs-maintenance](../docs-maintenance/SKILL.md) | Mandatory `docs/` review/update after implementation — no exceptions |
| [optimize-test-suite](../optimize-test-suite/SKILL.md) | Suite-wide speed/consolidation — **not** normal commits |

Extended tables: [reference.md](reference.md).
