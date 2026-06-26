# Agent Triage — Reference

**Repo routing index:** [AGENTS.md](../../AGENTS.md). **Always-on wrapper:** [agent-routing.mdc](../../rules/agent-routing.mdc).

Quick lookup for path→test mapping and entry points. Source of truth for hooks: `scripts/pre-commit-pytest.sh`.

**Governance parity:** when editing `AGENTS.md`, agent/kanban skills or rules → [Consistency matrix](#consistency-matrix) + [agent-consistency.mdc](../../rules/agent-consistency.mdc) + [agent-self-evaluation/SKILL.md](../agent-self-evaluation/SKILL.md) §6g. **Drift alert format:** [§ Drift alert examples](#drift-alert-examples) (five prefixes; optional `[severity]`). **Periodic audit:** [kanban-markdown/SKILL.md](../kanban-markdown/SKILL.md) § Periodic AGENTS.md governance audit — user runs `python3 scripts/create_governance_audit_card.py`.

## Consistency matrix

Which artifacts must agree after a governance change. **Notes** are grep targets — do not copy full lifecycle or Fix pattern prose here. Checklist detail: [agent-consistency.mdc](../../rules/agent-consistency.mdc). End-of-turn: self-eval §6g.

| Artifact | Must match | Notes |
| -------- | ---------- | ----- |
| [AGENTS.md](../../AGENTS.md) **Every turn** | [agent-triage/SKILL.md](SKILL.md) §1/§1b, [agent-routing.mdc](../../rules/agent-routing.mdc) lifecycle | Steps `1`–`5`, `1b`; Classify quickly rows |
| [agent-routing.mdc](../../rules/agent-routing.mdc) | AGENTS.md turn lifecycle, card types | `START →` block; discovery budget |
| [agent-triage/SKILL.md](SKILL.md) | AGENTS.md Classify + Every turn | §1 ↔ Classify quickly; [reference.md](reference.md) § Classify mirror; § Lessons by area |
| [agent-self-evaluation/SKILL.md](../agent-self-evaluation/SKILL.md) §7 handoff | AGENTS.md End handoff, [agent-self-evaluation.mdc](../../rules/agent-self-evaluation.mdc) | `### Files used`, `### Self-evaluation` fields |
| [agent-self-evaluation/reference.md](../agent-self-evaluation/reference.md) § Common failure patterns | Rules (**Signature** only), § Failure pattern routing below, [testing.mdc](../../rules/testing.mdc) | Five columns per §6f |
| [pre-commit-workflow/reference.md](../pre-commit-workflow/reference.md) § Failure patterns | [targeted-testing/reference.md](../targeted-testing/reference.md), testing.mdc `precommit-*` | Area hook patterns |
| [kanban-markdown/SKILL.md](../kanban-markdown/SKILL.md) card sections | `kanban-*.mdc`, AGENTS.md card types table | **Card label gate**; `feature` / `bug` / `agent` / `inquiry` / `commit-issue`; lessons **only** feature/bug/agent/commit-issue; **no card** → ask-only |
| [docs/development.md](../../docs/development.md) Cursor agent workflow | AGENTS.md, agent-consistency.mdc | When user-facing agent docs change |
| [docs/feature-areas.yaml](../../docs/feature-areas.yaml) governance keys | AGENTS.md Maintaining table, docs/development.md § Governance area schema | `agents_skill`, `agents_rules`, `lesson_routing_row`; **gs0–gs3 complete** — Signature `governance-area-schema-defer-agents-table` (no AGENTS **Area → skills & rules** sync until follow-up epic); parity via `check_area_schema_parity` + `--agents-parity` |

### Four check types → matrix rows

| Check type | Grep / compare |
| ---------- | -------------- |
| **Schema** | `reference.md` § Failure patterns columns; rules cite Signature not Fix pattern |
| **Routing** | AGENTS.md Every turn ↔ triage §1/§1b ↔ agent-routing.mdc |
| **Card-type** | AGENTS.md `labels` table ↔ kanban-markdown § ↔ each `kanban-*.mdc` |
| **Failure-pattern** | Signature in rule/triage exists in a reference row; docs/development.md mentions patterns when hook workflow changes |
| **Registry** | `docs/feature-areas.yaml` **Agent Workflow** `paths` ↔ AGENTS.md area → skills & rules; `handlers:` malformed/duplicate symbols; kanban **Label Methods** ↔ registry `handlers:`; periodic audit **Area table** |

## Drift alert examples

Named warning lines for governance parity (epic **GovernanceDriftAlerts**). **Surfacing:** Context load §2b check 5, self-eval §6g, handoff `- **Drift alerts:**` when governance paths edited and parity not fixed — [agent-triage/SKILL.md](SKILL.md) § Governance drift detection. **Not every turn.**

| Prefix | Check type | Anchor (matrix / audit) | Example |
| ------ | ---------- | ----------------------- | ------- |
| `Schema drift alert:` | **Schema** | [agent-self-evaluation/reference.md](../agent-self-evaluation/reference.md) § Common failure patterns — five columns per §6f | `Schema drift alert:` New Signature `ui-dialog-persist` — add row to reference § Common failure patterns and triage § Failure pattern routing |
| `Routing drift alert:` | **Routing** | AGENTS.md Every turn / Classify ↔ triage §1/§1b ↔ agent-routing.mdc; audit **Routing** | `Routing drift alert:` AGENTS Classify row "Agent handoff" missing in triage §1 |
| `Card-type drift alert:` | **Card-type** | AGENTS card types ↔ `kanban-*.mdc` ↔ kanban-markdown; audit **Card types** | `Card-type drift alert:` Frontmatter label `refactor` on card — add AGENTS card types row + `kanban-refactor-cards.mdc` |
| `Failure-pattern drift alert:` | **Failure-pattern** | Signature in rule or triage exists in a reference row; audit **Failure patterns** | `Failure-pattern drift alert:` Rule cites `precommit-palette-top-texture` — no row in pre-commit-workflow or self-eval reference |
| `Registry drift alert:` | **Registry** | `docs/feature-areas.yaml` governance schema (`agents_skill`, `agents_rules`, `lesson_routing_row`, `lesson_signatures`) + **Agent Workflow** `paths` ↔ AGENTS area → skills & rules (schema-internal lesson paths excluded); `handlers:` malformed/duplicate; kanban **Label Methods** ↔ registry; audit **Area table** | `Registry drift alert:` feature-areas.yaml **Agent Workflow** `agents_skill` `bad-skill` — missing `.cursor/skills/bad-skill/SKILL.md` |

**Use:** paste one line per mismatch when comparing artifacts (manual grep, `python3 scripts/check_governance_parity.py`, or audit findings). Do not invent prefixes outside this table.

### Drift severity (optional prefix)

Severity is **optional** on hand-written lines — **default `warn`** when omitted (backward compatible with phase 1–3 examples above).

| Severity | When to use | Example |
| -------- | ----------- | ------- |
| `info` | Cosmetic / low-impact doc drift; user acknowledged | `[info] Registry drift alert:` AGENTS Maintaining link text differs from kanban skill — align wording |
| `warn` | **Default** — routing, card-type, registry parity not fixed same turn | `[warn] Routing drift alert:` AGENTS Classify row "Agent handoff" missing in triage §1 |
| `critical` | Broken Signature cites, schema violations, handoff blockers | `[critical] Failure-pattern drift alert:` Rule cites `orphan-sig` — no reference row |

`check_governance_parity.py` emits `[severity]` by default (`--plain` for phase 1–3 format). Script mapping: routing/card-type/registry → `warn`; failure-pattern → `critical`. **Spawn:** by default writes one **todo** kanban card per new issue (epic `GovernanceDriftAlert`; priority `low|medium|high` from severity) with **## Alert**, **## Feature Areas**, **## Label Paths**, **## Corrective Action** — `--no-spawn-cards` to disable; skips duplicate **## Alert** text.

### KNOWN_DRIFT (temporary waiver)

When the **user** approves intentional temporary drift, suppress fix-in-same-turn and record:

```text
KNOWN_DRIFT: <artifact pair> — <reason>[; expires: <YYYY-MM-DD or note>]
```

| Field | Required | Example |
| ----- | -------- | ------- |
| **artifact pair** | yes | `AGENTS Classify ↔ triage §1` |
| **reason** | yes | `phase 4 card in review — classify row lands next commit` |
| **expires** | no | `; expires: 2026-07-01` or `; expires: after governance-drift-severity phase 4 done` |

Place in handoff `- **Drift alerts:**` as `KNOWN_DRIFT: …` (no `[severity]` bracket). Do not use for silent drift — user must approve.

## Classify the request (signals)

**Canonical:** [AGENTS.md](../../AGENTS.md) § Classify quickly. [SKILL.md](SKILL.md) §1 mirrors it; failure signals → §1b + § Failure pattern routing below.

| Signal | Mode | First action (short) |
| ------ | ---- | -------------------- |
| **Review** kanban card only (`review …`, bare `@path`) | Ask-only | kanban-card-gates §2 — no edits |
| **Update / spawn / implement** card (agent verbs) | Agent | kanban-markdown + prior lessons gate |
| `Kanban: answer inquiry on …` | Agent | Inquiry **Response** |
| Card missing / empty / unknown `labels` | Block | Stop — user fixes frontmatter `labels` |
| Implement / fix without a card | Ask-only | No product edits — kanban card required |
| Review QA on assigned card | Review | kanban-review-qa.mdc + **QA follow-up** + refresh card scope |
| User says feature / bug / agent / commit-issue Done | Governance | kanban-markdown § Card Done — lessons learned |
| User says inquiry Done | Close only | No lessons capture |
| AGENTS.md governance audit | Read-only | kanban-markdown § Periodic AGENTS.md governance audit |
| Explain / audit / is this correct? | Ask-only | Grep + read |
| Pre-commit failed | Unblock / Review | §1b pre-commit + self-eval reference |
| Failing test / pytest / ruff (no card) | Ask-only / Unblock | §1b failure pattern routing |
| UI wiring / dialog (no card) | Ask-only | §1b `ui-dialog-no-persist` |
| Orbit 3D holes (no card) | Ask-only | §1b `orbit-stair-mask-transparency` |
| Agent handoff / process mistake | Governance | §1b self-eval reference patterns |
| Agent `.tmp-venv` / missing venv | Ask-only / Unblock | §1b `agent-no-tmp-venv` |
| Repeated mistake / churn | Grep | §1b failure pattern routing |
| Run tests / commit-ready | Verify | targeted-testing / pre-commit-pytest.sh |
| Area lesson lookup (kanban + Feature Areas) | Review first | lessons-index.yaml + § Lessons by area → `resolve_prior_lessons.py` |

**Kanban + agent verb for implementation** — [kanban-markdown](../kanban-markdown/SKILL.md). Signatures: `kanban-prompt-ask-vs-agent`, `kanban-lessons-label-scope`.

## Lessons by area (read before card grep)

After resolving **`## Feature Areas`** or agent **`## Feature Area`** — **before** broad `grep` under `.devtool/features/done/`. Read order: (1) [docs/lessons-index.yaml](../../docs/lessons-index.yaml) area block, (2) matching row below, (3) `scripts/resolve_prior_lessons.py`, (4) full done card only when still ambiguous. Cite **Signature** or index path — do not duplicate Fix pattern prose. Exhaustive area keys: `lessons-index.yaml` `areas:`.

| Signal / Feature Area | Read first |
| --------------------- | ---------- |
| Kanban card with **Feature Areas** / **Feature Area** | `docs/lessons-index.yaml` area block → this table → `resolve_prior_lessons.py` — [kanban-prior-lessons-gate.mdc](../../rules/kanban-prior-lessons-gate.mdc) |
| **Render Preview** — animated lit fronts | `lessons-index.yaml` `Render Preview`; Signature `orbit-animated-texture-strip` → [testing.mdc](../../rules/testing.mdc); [ui-change/SKILL.md](../ui-change/SKILL.md) § Orbit |
| **Render Preview** — stair / fence / wall holes | `lessons-index.yaml` `Render Preview`; Signatures `orbit-stair-mask-transparency`, `orbit-fence-mask-transparency` → [ui-change/SKILL.md](../ui-change/SKILL.md) § Orbit lessons |
| Pre-commit / hook / pytest scope | `lessons-index.yaml` `Agent Workflow` or `_uncategorized`; [pre-commit-workflow/reference.md](../pre-commit-workflow/reference.md) § Failure patterns; `precommit-stash-old-hooks`, `precommit-ruff-staged-venv`, `agent-no-tmp-venv` |
| **Properties Panel** — `MainWindow.__new__` tests | `lessons-index.yaml` `Properties Panel`; Signature `precommit-mainwindow-__new__-test` → [testing.mdc](../../rules/testing.mdc) |
| **Agent Workflow** — routing / kanban / index | `lessons-index.yaml` `Agent Workflow`; Signatures `feature-areas-lesson-pointers`, `kanban-prompt-ask-vs-agent`; [kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc) §2; [kanban-markdown/SKILL.md](../kanban-markdown/SKILL.md) § Prior lessons gate |
| **Agent Workflow** — governance area schema (gs0–gs3) | `lessons-index.yaml` `Agent Workflow`; `resolve_feature_areas.py --agents-parity`; `check_area_schema_parity`; Signatures `governance-area-schema-defer-agents-table`, `governance-area-schema-parity-tests` |
| **Feature Area Registry** — lesson pointers | `lessons-index.yaml` `Feature Area Registry`; `docs/feature-areas.yaml` `lesson_signatures` / `lesson_docs`; `resolve_feature_areas.py --lessons` |
| **Palette Registry** — texture / orbit overlap | `lessons-index.yaml` `Palette Registry`; Signature `orbit-animated-texture-strip` |
| Card **Done** / lessons index refresh | [docs/development.md](../../docs/development.md) § Lessons captured `artifacts:`; `scripts/build_lessons_index.py` |
| Card Done `artifacts:` — registry yaml under `docs/` | Signature `artifacts-doc-yaml-normalize` → explicit `doc:…yaml` (not extensionless); [docs/development.md](../../docs/development.md) § Lessons captured `artifacts:` |
| All areas (exhaustive) | [docs/lessons-index.yaml](../../docs/lessons-index.yaml) — grouped Signatures, done cards, artifacts per area |

## Failure pattern routing (grep on signals only)

Run after §1 classifies a **failure** — not on every turn. Grep **Trigger snippet** or **Signature** in the listed `reference.md` § Failure patterns table; apply **Fix pattern** before deep exploration. Schema: [agent-self-evaluation/SKILL.md](../agent-self-evaluation/SKILL.md) §6f. Procedure: [agent-triage/SKILL.md](SKILL.md) §1b.

| Failure signal (§1 classify) | Grep in | Example signatures / trigger snippets |
| ---------------------------- | ------- | --------------------------------------- |
| Pre-commit / hook / ruff / palette validate | [pre-commit-workflow/reference.md](../pre-commit-workflow/reference.md) § Failure patterns | `precommit-stash-old-hooks`, `precommit-pytest-scope-mismatch`, `precommit-ruff-staged-venv`, `validate-palettes`, `ruff` |
| Pytest scope / hook surprise / hardcoded counts | [pre-commit-workflow/reference.md](../pre-commit-workflow/reference.md) + [agent-self-evaluation/reference.md](../agent-self-evaluation/reference.md) § Common failure patterns | `precommit-pytest-scope-mismatch`, `palette-hardcoded-count`, `FAILED tests/` |
| UI wiring / dialog / persist | [agent-self-evaluation/reference.md](../agent-self-evaluation/reference.md) § Common failure patterns | `ui-dialog-no-persist`, `_persist_dialog_changes` |
| Orbit 3D holes / transparent stairs | [agent-self-evaluation/reference.md](../agent-self-evaluation/reference.md) § Common failure patterns | `orbit-stair-mask-transparency`, `test_orbit_stair_face_textures_are_opaque` |
| Worldgen / placement / functional blocks | [agent-self-evaluation/reference.md](../agent-self-evaluation/reference.md) + `.cursor/rules/worldgen.mdc` | `residence` stage 1 for chest NBT tests (see worldgen rule) |
| `kanban-no-card-implement` | implement without card | §1b `kanban-no-card-implement` → [kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc) |
| `kanban-prompt-ask-vs-agent` | edits on `review @card` only; bare `@path` | §1b `kanban-prompt-ask-vs-agent` → kanban-card-gates §2; upgrade to `review and update` / `implement` |
| `kanban-missing-label` | invalid card `labels` | §1b `kanban-missing-label` → kanban-markdown § Card label gate |
| `kanban-lessons-label-scope` | lessons on inquiry Done | §1b `kanban-lessons-label-scope` → [kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc) |
| Agent handoff / kanban / AGENTS.md / self-eval | [agent-self-evaluation/reference.md](../agent-self-evaluation/reference.md) § Common failure patterns | `self-eval-skipped`, `kanban-roadmap-queue`, `agents-md-stale`, `handoff-missing-files-context`, `agent-no-tmp-venv` |
| Card Done `artifacts:` / lessons index bad `doc:` paths | [agent-self-evaluation/reference.md](../agent-self-evaluation/reference.md) § Common failure patterns | `artifacts-doc-yaml-normalize`, `lessons-index.yaml.md`, `doc:lessons-index` |
| Governance area schema / parity drift | [agent-self-evaluation/reference.md](../agent-self-evaluation/reference.md) § Common failure patterns | `governance-area-schema-parity-tests`, `governance-area-schema-defer-agents-table`, `Registry drift alert`, `check_governance_parity` |
| Structure YAML paths | [agent-self-evaluation/reference.md](../agent-self-evaluation/reference.md) § Common failure patterns | `yaml-stage1-structure-yaml`, `stage1/structure.yaml` |

**No match:** proceed with normal discovery; note recurring failures for self-eval §6 churn.

### Example — pre-commit failure

```text
User: commit failed on pytest; no commit-issue card in .devtool/features/

1. Classify → Unblock / pre-commit failed
2. Grep:
     rg "commit-issue|precommit-stash|FAILED" .cursor/skills/pre-commit-workflow/reference.md
     rg "precommit-" .cursor/skills/agent-self-evaluation/reference.md
3. Match precommit-stash-old-hooks → stage hook scripts + pre-commit install
4. Else match precommit-pytest-scope-mismatch → scripts/pre-commit-pytest.sh on staged paths
5. Open pre-commit-workflow/SKILL.md for hook order; commit-issue card rule if capture expected
```

## Entry points

| Concern | Module / doc |
| ------- | ------------- |
| Render pipeline | `render_main.py` → `renderers/registry.py` |
| Structure load/save | `helpers/structure_loader.py`, `ui/document.py` |
| Block registry | `registries/loader.py`, `helpers/registry_lookup.py` |
| Palette / picker UI | `helpers/block_picker.py`, `ui/widgets/palette_panel.py` |
| Grid editing | `ui/widgets/grid.py`, `ui/main_window.py` (orchestration) |
| Site / paths | `helpers/path_geometry.py`, `helpers/site_ground.py`, `ui/widgets/site_grid.py` |
| Worldgen export | `renderers/worldgen.py`, `helpers/worldgen_*.py` |
| Token grammar | `helpers/structure_tokens.py`, `docs/structure-tokens.md` |

## Common path → pytest mapping

Use `.venv/bin/pytest … -q` from repo root.

| Changed path(s) | Start with |
| --------------- | ---------- |
| `helpers/cells.py` | `tests/test_cells.py` |
| `helpers/block_picker.py`, `helpers/registry_*.py` | `tests/test_block_picker.py`, `tests/test_palette_integrity.py` |
| `helpers/materials.py` | `tests/test_materials.py` |
| `helpers/structure_loader.py`, `helpers/structure_tokens.py` | `tests/test_structure_loader.py`, `tests/test_structure_tokens.py` |
| `helpers/path_geometry.py`, `helpers/path_strip.py` | `tests/test_path_geometry.py`, `tests/test_path_strip.py` |
| `registries/**` | `tests/test_palette_integrity.py`, `tests/test_registry_phase_b.py` |
| `ui/document.py`, `ui/editor_*.py` | `tests/test_ui_document.py` |
| `ui/widgets/palette_panel.py` | `tests/test_palette_panel.py` |
| `ui/widgets/grid.py` | `tests/test_grid_scrollbars.py` + grid-related tests |
| `ui/main_window.py` | `tests/test_main_window.py` |
| `renderers/worldgen.py`, `helpers/worldgen_*.py` | `tests/test_worldgen_*.py` (see pre-commit script list) |
| `helpers/paths.py`, `helpers/structure_loader.py` | `tests/test_paths.py`, `tests/test_structure_loader.py`, `tests/test_worldgen_functional_blocks.py` |
| `docs/**` only | *(none)* |

When in doubt, grep `scripts/pre-commit-pytest.sh` for the file you changed.

## Before commit

Run `scripts/pre-commit-pytest.sh` on **staged** files — same script as the hook. After fixing a failure, re-run that script (or full suite if it says full suite), not only the single failed test file. See [targeted-testing](../targeted-testing/SKILL.md) §5–§6.

## Forces full pytest suite (pre-commit)

These staged paths trigger **full suite** in the hook:

- `tests/conftest.py`, `pyproject.toml`, `render_main.py`
- `helpers/context.py`, `registries/loader.py`, `helpers/utils.py`

## UI file size hints

| File | Note |
| ---- | ---- |
| `ui/main_window.py` | Orchestration only — grep for handler name; avoid full read |
| `ui/widgets/grid.py` | Large — read targeted line ranges |
| `ui/document.py` | Manifest + stage save logic |

## Qt tests

PySide6 tests may segfault in sandboxed shells. If pytest dies with SIGSEGV on UI tests, rerun with full permissions or run the specific UI test file locally.

## Decision flow

```mermaid
flowchart TD
  A[New request] --> B{Question only?}
  B -->|yes| C[Read-only tools]
  B -->|no| D{Failure signal?}
  D -->|yes| P[§1b grep reference.md tables]
  P --> E
  D -->|no| E{Known path/symbol?}
  E -->|yes| F[Grep + Read 1-3 files]
  E -->|no| G{Broad scope?}
  G -->|narrow| F
  G -->|broad| H[One explore OR semantic search]
  F --> I{Area}
  I -->|ui| J[ui-panels / ui-dialogs rules]
  I -->|registry| K[palette_integrity tests]
  I -->|docs| L[Edit docs only]
  J --> M[Targeted pytest]
  K --> M
  L --> N[Done if no code]
  M --> O{Commit?}
  O -->|yes| Q[ruff → palettes → pytest]
```
