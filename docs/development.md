# Development Setup

Requires **Python 3.11+**.

On Ubuntu and other PEP 668 systems, use a virtual environment rather than installing into the system Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Virtualenv for agents:** use **`.venv` only** — never create `.tmp-venv` or other
throwaway venvs in the repo (Signature: `agent-no-tmp-venv`). If `.venv` is
missing, run the commands above or ask the user to set it up before running
pytest. Staging a venv tree breaks the ruff hook (Signature:
`precommit-ruff-staged-venv`).

For world generation, also install the optional Amulet stack:

```bash
pip install -e ".[dev,worldgen]"
```

For the desktop structure editor, install the `[ui]` extra and see [ui.md](ui.md).

```bash
pip install -e ".[dev,ui]"
python -m ui --structure residence --stage 1
```

PySide6 6.5+ needs a few X11 libraries that pip does not install. If startup fails with
`Could not load the Qt platform plugin "xcb"` or mentions `xcb-cursor0`, install:

```bash
sudo apt install libxcb-cursor0
```

Optional but recommended on multi-monitor X11 setups:

```bash
sudo apt install libxcb-xinerama0
```

On a Wayland session you can often bypass X11 entirely:

```bash
QT_QPA_PLATFORM=wayland python -m ui --structure residence --stage 1
```

The editor runs a preflight check on Linux and prints these instructions when the
libraries are missing. Full UI guide: [ui.md](ui.md).

See [worldgen.md](worldgen.md) and [../AMULET_INSTALL_NOTES.md](../AMULET_INSTALL_NOTES.md) if Amulet install fails.

## Git hooks

Install hooks (Ruff, palette validation, targeted pytest on each commit):

```bash
pre-commit install
```

**Default commit** runs:

1. **Ruff** — fix/format staged Python, re-stage
2. **`validate_palettes()`** — registry/palette integrity
3. **Targeted pytest** — `scripts/pre-commit-pytest.sh` maps staged paths to related tests (see the `case` branches in that script). Unmapped or core changes (e.g. `registries/loader.py`, `conftest.py`) run the **full** suite.

When a **`git commit`** hook fails (`PRE_COMMIT=1`), a **`commit-issue`** kanban card may be written under `.devtool/features/` (label `commit-issue`) with hook output and failed test files. The hook prints `commit-issue card created: .devtool/features/commit-issue-<hook>-<timestamp>.md` after ruff/pytest/palette failure. **Manual** agent runs of `scripts/pre-commit-pytest.sh` during implementation do **not** spawn cards — Signature: `precommit-no-card-on-manual-hook`. Disable with `SKIP_COMMIT_ISSUE_CARD=1`. Cards are local (`.devtool/` is gitignored). If commit fails but no card appears, stage hook infra (`scripts/pre-commit-*.sh`, `scripts/on_pre_commit_failure.sh`, `scripts/create_commit_issue_card.py`) — pre-commit stashes unstaged hook changes (`precommit-stash-old-hooks` in pre-commit-workflow reference). Durable hook patterns: `.cursor/skills/pre-commit-workflow/reference.md` § Failure patterns.

**Full test suite** (before a PR or after a large refactor):

```bash
pytest
# or via hooks on all files:
pre-commit run pytest --all-files
```

**Run all hooks without committing:**

```bash
pre-commit run --all-files
```

Fix lint/format issues manually at any time:

```bash
scripts/ruff-fix
```

**Commit without pytest** (Ruff and palette checks still run):

```bash
gcn -m "your message"              # shell alias (see ~/.bashrc)
scripts/gcn -m "your message"      # same, from repo scripts/
scripts/commit-no-pytest -m "..."  # long name
```

Same as `SKIP=pytest git commit …`. Run `pytest` yourself before pushing when you use this.

## Running checks

```bash
ruff check .
ruff format .
pytest                    # full suite
pre-commit run --all-files
```

While editing, run only the tests you care about, e.g. `pytest tests/test_ui_document.py -q`.

## Cursor agent workflow

Agent routing and kanban process live outside application code:

- [AGENTS.md](../AGENTS.md) — entry point; **prompt verb gate** (`review` → ask-only; `implement` / `update` / `spawn` → agent); card types; Card Done lessons + **forward-looking feedback** (`card-done-forward-feedback`) scope
- [kanban-card-gates.mdc](../.cursor/rules/kanban-card-gates.mdc) — §2 Ask-only vs Agent prompts (canonical table)
- [kanban-markdown/SKILL.md](../.cursor/skills/kanban-markdown/SKILL.md) — card lifecycle; **prior lessons gate** before Decisions/CA; registry maintenance
- [kanban-markdown/reference.md](../.cursor/skills/kanban-markdown/reference.md) — card templates, audit checklist, examples (load on demand; gc1)
- `python scripts/resolve_feature_areas.py "<label>"` — paths; `--handlers` for registry entry-point symbols; `--lessons` for curated `lesson_signatures` / `lesson_docs`
- `python3 scripts/resolve_prior_lessons.py --epic "<Epic>" "<Feature Area>" --paths …` — done/archived-card lessons + open commit-issue overlap + **Registry lesson pointers** when present
- `python3 scripts/check_lessons_coverage.py` — Lessons Coverage Metric audit (C1–C4); `--card`, `--strict`, `--json`
- `python3 scripts/build_lessons_index.py` — regenerate `docs/lessons-index.yaml` from Card Done captures; `--check` for stale index; `--dry-run` to stdout; `--sync-registry` proposes `lesson_*` keys in `docs/feature-areas.yaml` (dry-run; add `--write` to apply)

### Lessons reference index

Committed registry of promoted lessons grouped by feature area (paths + Signatures only — not full card prose).

| Field | Meaning |
| ----- | ------- |
| `version` | Schema version (`1`) |
| `generated_at` | ISO-8601 UTC timestamp from last generator run |
| `areas.<label>.signatures` | Promotion Signatures grep'd from done/archived cards |
| `areas.<label>.done_cards` | Relative paths to cards with `## Lessons captured` |
| `areas.<label>.artifacts` | Governance links (skills, rules, docs) from lesson bullets |

Refresh after **Card Done** lessons capture or before a quarterly governance audit:

```bash
python3 scripts/build_lessons_index.py
python3 scripts/build_lessons_index.py --check   # exit 1 when stale
```

**Agent read order (kanban pre-implementation):** skim the card's area block in `docs/lessons-index.yaml`, then [agent-triage/reference.md](../.cursor/skills/agent-triage/reference.md) § **Lessons by area**, then `resolve_prior_lessons.py` — open full done cards only when still ambiguous ([kanban-prior-lessons-gate.mdc](../.cursor/rules/kanban-prior-lessons-gate.mdc)).

When `.devtool/features/` is absent (CI clone without kanban), the generator skips writing; tests use `tmp_path` fixtures.

Epic `LessonsReferenceIndex` (li0–li3) — index build (this section), structured `artifacts:` on cards, registry pointers, triage routing.

### Lessons Coverage Metric

Measures how effectively lessons from **Done** and **commit-issue** cards flow into durable artifacts and back into new card work via the **prior lessons gate**. Epic `LessonsCoverageMetric` (lc0–lc3).

**Related workflow:**

- [**Card Done** lessons capture](../.cursor/skills/kanban-markdown/SKILL.md) — `feature` / `bug` / `agent` / `commit-issue` cards; optional ``artifacts:`` tail (schema below)
- [**Prior lessons gate**](../.cursor/rules/kanban-prior-lessons-gate.mdc) — run before **Decisions** / **Corrective Action** on active cards
- [`resolve_prior_lessons.py`](../scripts/resolve_prior_lessons.py) — surfaces `done/` + `archived/` lessons, registry pointers, commit-issue overlap; `--audit` delegates to coverage lib
- [**Periodic governance audit**](#periodic-governance-audit) — quarterly checklist includes `check_lessons_coverage.py` when `done/` exists

**v1 rollout:** lc0 spec → lc1 `check_lessons_coverage.py` → lc2 C2/C3 heuristics → lc3 CI drift. First automation targeted **C1 + C4**; full C2/C3 scoring landed in lc2.

| ID | Name | Formula (summary) |
| -- | ---- | ----------------- |
| C1 | Capture Coverage | done cards with ≥1 resolvable promotion / done cards with `## Lessons captured` |
| C2 | Promotion Quality | correctly typed refs / total governance refs (skip cards with zero refs) |
| C3 | Consumption Coverage | surfaced lesson cards / expanded relevant set (`surfaced / relevant`) |
| C4 | Application Coverage | surfaced lessons cited in `**Prior lessons**` / surfaced lessons on active cards |

| ID | Inputs (numerator / denominator) |
| -- | -------------------------------- |
| C1 | **Num:** closed cards (`done/` + `archived/`) whose `## Lessons captured` has ≥1 on-disk governance path or Signature row in pre-commit-workflow / agent-self-evaluation reference tables. **Den:** cards with non-empty `## Lessons captured`. |
| C2 | **Num:** governance refs (from ``artifacts:`` or **Governance** bullets) with correct artifact type. **Den:** total refs on cards that promoted at least one ref (cards with zero refs skipped). |
| C3 | **Num:** done/archived lesson cards returned by `find_done_lessons()` (or `find_done_lessons_strict()`). **Den:** expanded relevance set per active card — epic, feature area, **Label Paths**, optional **Context** links (`--strict` drops epic-only match). |
| C4 | **Num:** surfaced lessons cited in `**Prior lessons (YYYY-MM-DD):**` under **Decisions** / **Corrective Action**. **Den:** surfaced lessons on active cards (`todo` / `in-progress` / `review`) that have **Label Paths** + plan section. |

**Composite:** equal weights — `0.25 × (C1 + C2 + C3 + C4)` (N/A sub-metrics count as 100%).

**Interpretation:** 90–100 excellent · 75–89 good · 60–74 at risk · &lt;60 governance failure.

**Audit CLI:**

```bash
python3 scripts/check_lessons_coverage.py              # human report; exit 1 when composite < 75
python3 scripts/check_lessons_coverage.py --json
python3 scripts/check_lessons_coverage.py --card .devtool/features/foo.md   # C3 for one card
python3 scripts/check_lessons_coverage.py --strict   # C3: epic alone does not match
python3 scripts/resolve_prior_lessons.py --audit all # C1+C4 subset or full via shared lib
```

**C1** counts resolvable governance paths (on disk) and Signatures (rows in pre-commit-workflow or agent-self-evaluation reference tables).

**C2 — promotion quality** scores whether promoted artifacts use the correct type:

| Artifact path pattern | Expected type |
| --------------------- | ------------- |
| `.cursor/skills/` | skill |
| `.cursor/rules/*.mdc` | rule |
| `*/reference.md` | reference table |
| `` Signature `foo` `` / `sig:` | row in pre-commit-workflow or agent-self-evaluation reference |
| `docs/` | doc |

When a lesson bullet includes structured `artifacts:` (see schema below), C2 uses typed prefixes; otherwise it falls back to **Governance** link heuristics on the same bullet.

**C3 — consumption coverage** compares `find_done_lessons()` output to an expanded relevance set per active card:

- epic match (unless `--strict`)
- feature area label in card body
- path overlap with **Label Paths**
- optional: **Context** links to `done/*.md` or `archived/*.md`

`--strict` calls `find_done_lessons_strict()` — epic alone does not match; require label or path overlap. Report is `surfaced / relevant` per card; default run aggregates across active cards (`todo` / `in-progress` / `review`).

**C4** scans active cards with **Label Paths** and **Decisions** / **Corrective Action** for `**Prior lessons**` citations vs resolver output. The parser captures text after `**Prior lessons (YYYY-MM-DD):**` until the next line starting with `**` or a `##` heading — avoid bold line breaks inside the block. Cites done/archived card stems (`name-YYYY-MM-DD.md`, commit-issue `…T….md`, `governance-drift-registry-{hash}.md`) and Signature backticks.

**Scope:** `.devtool/features/done/` and `archived/` are gitignored — CI clones without kanban get N/A denominators; tests use `tmp_path` fixtures. Do not commit `.devtool/`.

**Local vs CI:** `check_lessons_coverage.py` and `check_governance_parity.py` skip lessons-coverage drift when neither `done/` nor `archived/` exists under `.devtool/features/` (clean clones, CI without kanban). Optional local hook: `scripts/pre-commit-lessons-coverage.sh` (not enabled in `.pre-commit-config.yaml` by default — add a `lessons-coverage` hook entry manually to fail commits when composite &lt; 75%).

**Governance drift:** `check_governance_parity.py` invokes the same audit when done data exists; composite &lt; 75% emits `Lessons coverage drift alert:` with C1–C4 breakdown (`warn` for 60–74%, `critical` for &lt; 60%). Spawns a **todo** card `lessons-coverage-drift-YYYY-MM-DD` (epic `LessonsCoverageMetric`, label `agent`) unless `--no-spawn-cards`. Spawn body includes all **agent** card sections with `_TBD_` placeholders — not **Corrective Action** alone.

Implementation: `scripts/check_lessons_coverage.py`, `scripts/lessons_coverage_lib.py`; tests `tests/test_check_lessons_coverage.py`. **Parser SSOT:** card/done parsers (`_parse_frontmatter`, `_lessons_excerpt`, `parse_artifacts_line`, …) live in `resolve_prior_lessons.py`; `lessons_coverage_lib.py` imports them (no duplicate parsers). **Test fixtures:** kanban `tmp_path` tests monkeypatch `FEATURES_DIR` on `resolve_prior_lessons` and `check_lessons_coverage`, plus `REPO_ROOT` on `lessons_coverage_lib` — `build_report` stores card paths via `relative_to(REPO_ROOT)`.

### Feature area lesson pointers (li2)

Optional per-area keys in `docs/feature-areas.yaml`:

| Key | Meaning |
| --- | ------- |
| `lesson_signatures` | Curated promotion Signatures (≤8) — grep targets without opening done cards |
| `lesson_docs` | Developer doc paths (≤5) — highlights from lesson captures |

**Manual curation first:** seed and trim lists when closing cards; keep highlights small, not full index dumps.

**Automation suggests only:** `python3 scripts/build_lessons_index.py --sync-registry` prints proposed `lesson_*` diffs from `docs/lessons-index.yaml` (dry-run). Add `--write` to apply when you accept the proposal.

```bash
python3 scripts/resolve_feature_areas.py --lessons "Render Preview"
python3 scripts/resolve_feature_areas.py --agents-parity "Render Preview"
python3 scripts/resolve_prior_lessons.py "Render Preview" --paths helpers/orbit_face_textures.py
```

**`--agents-parity` (gs3):** prints `agents_skill`, `agents_rules`, `lesson_routing_row`, and whether the `lesson_routing_row` anchor appears in [agent-triage/reference.md](../.cursor/skills/agent-triage/reference.md) § **Lessons by area** (`lessons_by_area_row: found|missing|n/a`). Use during kanban pre-implementation review alongside `--lessons`. Single area label per invocation is typical.

```bash
pytest tests/test_resolve_feature_areas.py -q -k agents_parity
```

Dual **Feature Area** labels on a card union pointers from each resolved area.

### Governance area schema (gs0)

Optional per-area keys in `docs/feature-areas.yaml` for **mechanical** agent routing and parity checks — so prior-lessons gates and `check_governance_parity.py` do not rely on parsing AGENTS.md markdown tables.

| Key | Type | Purpose |
| --- | ---- | ------- |
| `agents_skill` | string | Primary skill stem (e.g. `ui-change`) — gate step loads `.cursor/skills/{stem}/SKILL.md` |
| `agents_rules` | list | Rule stems under `.cursor/rules/` with optional `#signature` (e.g. `ui-panels.mdc`, `testing.mdc#orbit-animated-texture-strip`) |
| `lesson_routing_row` | string \| null | Anchor label in [agent-triage/reference.md](../.cursor/skills/agent-triage/reference.md) § **Lessons by area** first column; `null` when `lessons-index.yaml` area block is enough |

**Relationship to lesson pointers and index:**

| Artifact | Role |
| -------- | ---- |
| `lesson_signatures` / `lesson_docs` (li2) | Curated grep/doc highlights per area — manual curation; `--lessons` on `resolve_feature_areas.py` |
| `docs/lessons-index.yaml` | Committed index of promoted Signatures, done cards, artifacts — built by `build_lessons_index.py` |
| `lesson_routing_row` | Links an area to a row in triage § **Lessons by area** for pre-implementation read order |
| `agents_skill` / `agents_rules` | Links an area to load-when-touching skills and scoped rules (`check_area_schema_parity` in `check_governance_parity.py` — gs2) |

All governance keys are **optional** and **backward compatible** — areas without them behave as today until gs1 seeds high-traffic areas.

**Out of scope (gs0–gs3):** editing or generating AGENTS.md **Area → skills & rules** table rows from yaml — **gs4 complete** (below).

**gs4 (complete):** `scripts/sync_agents_area_table.py` — `--check` exits non-zero on drift; `--write` / `--fix` updates the AGENTS area table from yaml `agents_skill` / `agents_rules` for seeded areas. Integrated into `check_governance_parity.py`. Signature: `governance-area-schema-agents-table-sync`.

```bash
python3 scripts/sync_agents_area_table.py --check
python3 scripts/sync_agents_area_table.py --write   # refresh AGENTS table only
pytest tests/test_check_governance_parity.py tests/test_sync_agents_area_table.py -q -k area_table
```

**gs3 (complete):** `--agents-parity` on `resolve_feature_areas.py`; pytest `agents_parity` tests; pre-commit maps `feature-areas.yaml` / parity script changes to schema tests.

**Registry path compare (schema-internal):** `check_registry_parity` compares **Agent Workflow** `paths` with skill/rule links extracted from AGENTS area rows. Paths validated elsewhere are excluded via `is_schema_internal_registry_path` / `filter_registry_compare_paths`: `docs/lessons-index.yaml`, `scripts/build_lessons_index.py`, `scripts/resolve_*.py`, and **Lessons Coverage Metric** tooling (`scripts/check_lessons_coverage.py`, `scripts/lessons_coverage_lib.py`, `scripts/pre-commit-lessons-coverage.sh`, `tests/test_check_lessons_coverage.py`). Do not add script paths to AGENTS area table columns — register them under **Agent Workflow** `paths` + `handlers:` instead.

**gs1 seed areas (complete):** Render Preview, Agent Workflow, Properties Panel, Feature Area Registry, Palette Registry — `agents_skill`, `agents_rules`, `lesson_routing_row` in `docs/feature-areas.yaml`.

Epic `GovernanceAreaSchema` (gs0–gs3) — **complete**. Epic `AgentsTableSync` (gs4) — **complete** — AGENTS area table sync from yaml.

### Lessons captured `artifacts:` schema

Optional **machine-readable tail** on each `## Lessons captured` lesson bullet. When present, `build_lessons_index.py` and `resolve_prior_lessons.py` prefer `artifacts:` over free-form **Governance** link heuristics.

**Per-lesson template:**

```markdown
- **Symptom:** animated furnace front tiles multiple openings in orbit preview.
- **Fix:** load frame 0 via `load_block_texture_image`; golden tests use same helper.
  - artifacts: skill:project-context, rule:testing.mdc#orbit-animated-texture-strip, doc:render-types.md, sig:orbit-animated-texture-strip, test:tests/test_block_texture_load.py
```

| Prefix | Value | Indexed as |
| ------ | ----- | ---------- |
| `skill:` | skill folder name (e.g. `project-context`) or full `.cursor/skills/…/SKILL.md` | skill path under `.cursor/skills/` |
| `rule:` | `filename.mdc` or `filename.mdc#signature` anchor | `.cursor/rules/filename.mdc` (anchor for humans) |
| `doc:` | doc basename or `docs/…` path (`.md`, `.yaml`, `.yml`) | path under `docs/` |
| `sig:` | promotion Signature slug | `areas.<label>.signatures` (not an artifact path) |
| `test:` | pytest file path | `tests/…` path in `areas.<label>.artifacts` |

One `artifacts:` sub-bullet per lesson (comma-separated entries). Cards without `artifacts:` still work — parsers fall back to **Governance** markdown links and inline `` `sig:signature-slug` `` backticks on lesson bullets (Signature: `lessons-index-inline-sig-backtick`).

**`doc:` notes:** Markdown basenames may omit `.md` (`doc:render-types` → `docs/render-types.md`). Registry YAML under `docs/` **must** include the extension (`doc:lessons-index.yaml`, `doc:feature-areas.yaml`) — extensionless registry stems such as `doc:lessons-index` are skipped (Signature: `artifacts-doc-yaml-normalize`). Use `rule:` for `.mdc` files, not `doc:`.

**Overlap with `LessonsCoverageMetric` lc2:** structured `artifacts:` is preferred for C2 promotion-quality scoring; parsers prefer `artifacts:` over **Governance** heuristics when present ([`check_lessons_coverage.py`](../scripts/check_lessons_coverage.py) — `audit_promotion_quality`).

* [AGENTS.md](../AGENTS.md) — entry index for Cursor agents
* [Consistency matrix](../.cursor/skills/agent-triage/reference.md#consistency-matrix) — governance artifact parity lookup
* [Drift alert examples](../.cursor/skills/agent-triage/reference.md#drift-alert-examples) — six named prefixes for parity warnings (matrix / audit anchors)
* **Surfacing:** governance-edit turns — Context load (self-eval §2b check 5), §6g, handoff `- **Drift alerts:**` — [agent-self-evaluation/SKILL.md](../.cursor/skills/agent-self-evaluation/SKILL.md) §6g; detection — [agent-triage/SKILL.md](../.cursor/skills/agent-triage/SKILL.md) § Governance drift detection
* `.cursor/rules/agent-consistency.mdc` — same-turn parity when editing governance skills, rules, or `AGENTS.md`
* Self-eval §6g — [agent-self-evaluation/SKILL.md](../.cursor/skills/agent-self-evaluation/SKILL.md) — end-of-turn consistency prompts when those paths change

### Periodic governance audit

Suggested **quarterly** (or after large agent/kanban epics): create a todo audit card and assign the agent to compare artifacts read-only:

```bash
python3 scripts/create_governance_audit_card.py
```

Full procedure: [kanban-markdown/SKILL.md](../.cursor/skills/kanban-markdown/SKILL.md) § Periodic AGENTS.md governance audit. Options: `--date YYYY-MM-DD`, `--force` to overwrite same-day card.

Checklist summary:

1. AGENTS.md Every turn ↔ agent-triage ↔ agent-routing.mdc
2. Card types ↔ kanban-*.mdc ↔ kanban-markdown
3. Failure-pattern Signatures ↔ reference tables ↔ [Consistency matrix](../.cursor/skills/agent-triage/reference.md#consistency-matrix)
4. `feature-areas.yaml` `handlers:` (malformed, cross-area duplicates) ↔ kanban **Label Methods** on open cards
5. Handoff format ↔ agent-self-evaluation §7
6. docs/development.md agent section ↔ AGENTS.md
7. Lessons coverage: `python3 scripts/check_lessons_coverage.py` when `.devtool/features/done/` exists; composite &lt; 75% should match `check_governance_parity.py` `Lessons coverage drift alert:` output

Record drift on the audit card **## Audit findings**; spawn fix cards per bullet — do not fix silently during the audit turn.

### On-demand parity check

Ad-hoc drift detection between audits (uses phase 1 alert prefixes — paste output into Context load / handoff):

```bash
python3 scripts/check_governance_parity.py
python3 scripts/check_governance_parity.py --line-counts   # gc0 baseline sizes (exit 0)
```

Options: `--quiet` (exit code only). `--plain` omits `[severity]` prefixes. **`--no-spawn-cards`** skips kanban card creation. By default, each new drift issue spawns a **todo** card under `.devtool/features/` (epic `GovernanceDriftAlert`, priority from severity) with **## Alert**, **## Feature Areas**, **## Label Paths**, and **## Corrective Action** — duplicates skipped when the same alert already has an open card. **Lessons coverage** drift (when `.devtool/features/done/` or `archived/` exists) uses epic `LessonsCoverageMetric`, label `agent`, and card id `lessons-coverage-drift-YYYY-MM-DD`. Registry checks include optional `handlers:` symbols (malformed lines, duplicates across areas, kanban **Label Methods** missing from yaml).

### Governance compaction (gc0 baseline)

Epic **GovernanceCompact** — measure token churn before shrinking skills/rules. Signature: `governance-compact-baseline`.

**Report (on demand):**

```bash
python3 scripts/check_governance_parity.py --line-counts
```

Prints artifact line counts (sorted), named duplication-pair section sizes, and all `alwaysApply: true` rules with a governance vs other tag. Exit **0** — informational only; does not run parity checks or spawn drift cards.

**Baseline table (2026-06-27 snapshot)** — regenerate with `--line-counts` after gc1+ edits:

| Artifact | Lines | Notes |
| -------- | ----- | ----- |
| `.cursor/skills/kanban-markdown/SKILL.md` | 341 | Lifecycle + gates (gc1 — was 1171) |
| `.cursor/skills/kanban-markdown/reference.md` | 525 | Card templates + audit detail (gc1) |
| `.cursor/skills/agent-self-evaluation/SKILL.md` | 309 | Handoff §7 compact + §6c consolidate gate (gc4) |
| `.cursor/skills/agent-triage/reference.md` | 246 | Consistency matrix + failure routing |
| `AGENTS.md` | 203 | Entry routing + Classify quickly (gc4 End handoff pointer) |
| `.cursor/skills/agent-triage/SKILL.md` | 209 | Turn lifecycle §1 |
| `kanban-*.mdc` (8 files) | 456 | Sum — card-type scoped rules |
| `agent-*.mdc` (4 files) | 211 | Sum — routing / self-eval / consistency |
| **Baseline total** | **2531** | 18 files in `GOVERNANCE_COMPACT_BASELINE_GLOBS` (gc1 + reference.md) |

**Duplication pairs** (section line counts — same prose maintained in multiple places):

| Pair | Lines (approx.) | gc1+ action |
| ---- | --------------- | ----------- |
| Classify quickly (`AGENTS.md`) | 21 | gc2 — ≤5-row summary; reference § Classify canonical |
| Classify §1 (`agent-triage/SKILL.md`) | 51 | gc2 — pointer only; no duplicate table |
| Classify signals (`reference.md`) | 23 | gc2 — canonical full signal table |
| AGENTS `### Card types` | 14 | Link to kanban rules; drop prose |
| `kanban-markdown/SKILL.md` (lifecycle) | 341 | gc1 complete — card detail in reference.md |
| `kanban-markdown/reference.md` | 525 | gc1 — templates, examples, audit checklist |
| `kanban-*.mdc` (sum) | 456 | Scoped load — keep; dedupe from skill |

**Always-on rules** (`alwaysApply: true`):

| Rule | Lines | Tag |
| ---- | ----- | --- |
| `.cursor/rules/testing.mdc` | 164 | governance |
| `.cursor/rules/agent-routing.mdc` | 79 | governance |
| `.cursor/rules/kanban-card-gates.mdc` | 60 | governance |
| `.cursor/rules/worldgen.mdc` | 58 | other |
| `.cursor/rules/model-routing.mdc` | 57 | other |
| `.cursor/rules/agent-self-evaluation.mdc` | 38 | governance (gc4 — §7 pointer) |
| **Total** | **462** | **347** governance-related |

**Success criteria → measurable signals** (parent inquiry: reduce governance token churn):

| Goal | Signal | Tool / gate |
| ---- | ------ | ----------- |
| Smaller always-on surface | Governance always-on line count ↓ | `--line-counts`; gc3 toggles `alwaysApply` |
| Less duplicated prose | Classify trio + kanban skill/rule sum ↓ | `--line-counts` duplication pairs |
| Routing stays correct | Zero drift alerts | `check_governance_parity.py` exit 0 |
| Agents still hand off | `### Files used` + `### Self-evaluation` every turn | `agent-self-evaluation.mdc` (always-on) |
| Registry parity | `handlers:` + schema keys aligned | `check_area_schema_parity`, `--agents-parity` |

gc1+ cards set explicit line-count targets from this baseline; gc3 completes scoped card-type rule load.

**gc3 — kanban rule globs (complete):** Card-type `kanban-*-cards.mdc` use
`globs: .devtool/features/**/*.md` and `alwaysApply: false` (landed with gc1; gc3 validates +
documents). [kanban-card-gates.mdc](../.cursor/rules/kanban-card-gates.mdc) remains always-on.
[agent-triage/SKILL.md](../.cursor/skills/agent-triage/SKILL.md) §1 — after label gate, load
**exactly one** scoped card-type rule per `labels` (mapping in [agent-routing.mdc](../.cursor/rules/agent-routing.mdc)
§ Kanban card type; not all `kanban-*.mdc`). Signature:
`governance-compact-kanban-rule-globs`; enforced by `check_kanban_rule_globs` in
`check_governance_parity.py`.

**Manual QA (gc3):** In Cursor chat, `@`-attach a **bug** card under `.devtool/features/` and
confirm bug-card constraints still apply (e.g. **Corrective Action** not **Decisions**). Repeat for
one **agent** card if glob behavior is uncertain. If Cursor ignores rule globs, keep
`alwaysApply: true` on card-type rules and note the waiver on the card — compaction falls back to
gc1/gc2 prose reduction only.

**gc6 — classify task types (complete):** After prompt-verb / card gate, agents route by work kind
(governance, docs-only, code, refactor, inquiry, multi-file, rule/skill) via
[agent-triage/reference.md](../.cursor/skills/agent-triage/reference.md) § **Task types** — Signature:
`governance-compact-classify-task-types`. Task types live under reference § Classify (subsection);
not AGENTS summary rows.

**gc2 — Classify SSOT (complete):** Full signal table in reference § Classify only — Signature:
`governance-compact-classify-ssot`. AGENTS § Classify quickly ≤5-row summary; triage §1 pointer;
`check_classify_parity` enforces fingerprint, anchor coverage, and summary caps.

**gc4 — self-eval handoff compaction (complete):** Canonical compact handoff in
[agent-self-evaluation/SKILL.md](../.cursor/skills/agent-self-evaluation/SKILL.md) §7 — Signature:
`governance-compact-self-eval-handoff`. AGENTS End handoff and
[agent-self-evaluation.mdc](../.cursor/rules/agent-self-evaluation.mdc) point to §7 (no duplicate
full template). Read-only turns: §6 mental check + one-line `none (read-only)` handoff fields.
Implementation: grep + consolidate-before-expand gate (§6c/§6d).

**gc5 extension (forward-feedback tightening):** After gc5 baseline, reference § Forward-looking
feedback adds **Impact Scope**, **References**, **Mitigation** on max-tier items, **Importance**
when ≥2 items share max risk, and top-3 chat surfacing on Card Done turns — Signature stays
`card-done-forward-feedback`; legacy done cards without new fields remain valid.

## Dependencies

Runtime (via `pyproject.toml`):

* `Pillow`
* `PyYAML`
* `amulet-core` (world generation only; optional extra)

Dev (optional `[dev]` extra):

* `pytest`
* `ruff`
* `pre-commit`
